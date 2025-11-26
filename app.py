#!/usr/bin/env python3
"""
Flask web app for Industrial Safety Video Analytics
Uses Groq's Maverick model for real-time hazard detection
"""

import os
import cv2
import base64
import json
import time
from flask import Flask, render_template, Response, jsonify, request, session, redirect, url_for
from flask_socketio import SocketIO, emit
import threading
from groq import Groq
import sounddevice as sd
import soundfile as sf
from pathlib import Path
from functools import wraps
from queue import Queue, Empty

# Load environment variables from .env file if it exists
def load_env_file():
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env_file()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'groq-industrial-safety-monitor-secret-key-2024'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
camera = None
analysis_active = False
latest_analysis = None
groq_client = None
tts_lock = threading.Lock()
tts_in_progress = False
announcement_queue = Queue(maxsize=5)  # Limit queue size to prevent overflow
last_incident_description = None  # Track latest announced incident description
active_incident = False  # Whether we currently have an active hazard
stop_playback_flag = False  # Signal to interrupt current audio
last_announcement_time = 0  # Track when last announcement was made

# Hazard lifecycle flags help avoid redundant TTS and UI churn
STATUS_NEW_HAZARD = "new_hazard"
STATUS_SAME_HAZARD = "same_hazard"
STATUS_CLEARED = "cleared"
current_status_flag = STATUS_CLEARED

# Rate limiting
MIN_ANNOUNCEMENT_INTERVAL = 3.0  # Minimum seconds between announcements

# Configuration
ANALYZE_EVERY_SECONDS = 0.5  # Fast detection - analyze every 0.5 seconds

# Hazard detection prompt
HAZARD_PROMPT = """
You are an industrial safety inspector looking at a live camera feed
from an industrial site (factory, plant, warehouse, refinery, construction, etc.).

Your job is to:
- Detect any visible safety hazards or dangerous situations.
- Focus on things like:
  - There is no PPE (no helmet, no safety vest, no goggles, no gloves)
  - People too close to moving machinery or vehicles (forklifts, trucks, cranes)
  - Working at height without fall protection
  - Trip and fall hazards (cables, clutter, obstacles on floor)
  - Fire, smoke, sparks, exposed hot surfaces, spills or leaks
  - People in restricted zones or near dangerous equipment
  - Blocked emergency exits or escape routes
- If nothing looks unsafe, say so clearly.

Respond ONLY as valid JSON with this exact structure:
{
  "hazard_present": true or false,
  "severity": "none" | "low" | "medium" | "high" | "critical",
  "hazard_types": [list of short strings],
  "description": "one or two sentences describing the scene and any hazards",
  "recommended_actions": [list of short actionable recommendations]
}

Do not include any text before or after the JSON.
"""


def frame_to_base64_jpeg(frame):
    """Encode a BGR OpenCV frame as base64 JPEG."""
    max_dim = 1024
    h, w = frame.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        frame = cv2.resize(frame, (int(w * scale), int(h * scale)))

    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    if not ok:
        raise RuntimeError("Failed to encode frame as JPEG")
    return base64.b64encode(buf.tobytes()).decode("utf-8")


def analyze_frame(frame):
    """Send frame to Groq's Maverick model for safety analysis."""
    global groq_client
    
    if groq_client is None:
        return None
    
    try:
        base64_image = frame_to_base64_jpeg(frame)
        
        completion = groq_client.chat.completions.create(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": HAZARD_PROMPT.strip(),
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
            temperature=0.1,
            max_completion_tokens=256,
            top_p=1,
            stream=False,
        )
        
        msg_content = completion.choices[0].message.content
        
        if isinstance(msg_content, list):
            msg_content = "".join(part.get("text", "") for part in msg_content)
        
        # Try to extract JSON if there's extra text
        start = msg_content.find('{')
        end = msg_content.rfind('}')
        
        if start != -1 and end != -1:
            json_str = msg_content[start:end+1]
            try:
                data = json.loads(json_str)
                return data
            except json.JSONDecodeError as je:
                # Try to find the first complete JSON object
                print(f"[WARN] JSON decode error: {je}, attempting to extract first valid JSON")
                # Find all potential JSON objects
                depth = 0
                for i, char in enumerate(json_str):
                    if char == '{':
                        depth += 1
                    elif char == '}':
                        depth -= 1
                        if depth == 0:
                            # Found complete JSON object
                            try:
                                data = json.loads(json_str[:i+1])
                                return data
                            except:
                                continue
                print(f"[ERROR] Could not parse JSON from response")
                return None
        else:
            print(f"[ERROR] No JSON found in response")
            return None
            
    except Exception as e:
        print(f"[ERROR] Analysis failed: {e}")
        return None


def clear_announcement_queue():
    """Remove all pending announcements."""
    while not announcement_queue.empty():
        try:
            announcement_queue.get_nowait()
            announcement_queue.task_done()
        except Empty:
            break


def update_status_flag(new_flag):
    """Update the current status flag; return True if it changed."""
    global current_status_flag
    if current_status_flag == new_flag:
        return False
    current_status_flag = new_flag
    print(f"[STATE] Status flag updated → {new_flag}")
    return True


def announce_situation_clear():
    """Interrupt current audio and announce that the scene is clear."""
    global active_incident, last_incident_description, stop_playback_flag, last_announcement_time
    print("[INFO] Scene clear detected. Interrupting announcements.")
    status_changed = update_status_flag(STATUS_CLEARED)
    
    # Signal current playback to stop
    stop_playback_flag = True
    try:
        sd.stop()
    except Exception:
        pass
    
    # Remove pending hazard announcements and enqueue clear message (only once per change)
    clear_announcement_queue()
    if status_changed:
        try:
            announcement_queue.put("Situation clear. Area is safe. Resume normal operations.", block=False)
            last_announcement_time = time.time()
        except:
            print("[WARN] Could not queue clear announcement (queue full)")
    
    active_incident = False
    last_incident_description = None


def tts_announcement_worker():
    """Background worker that processes the announcement queue."""
    global groq_client, tts_in_progress, announcement_queue, analysis_active, stop_playback_flag
    
    print("[TTS] Announcement worker started")
    
    while analysis_active or not announcement_queue.empty():
        try:
            # Get announcement from queue (with timeout)
            try:
                announcement_text = announcement_queue.get(timeout=1)
            except:
                continue
            
            if not announcement_text or groq_client is None:
                try:
                    announcement_queue.task_done()
                except:
                    pass
                continue
            
            # Acquire lock to prevent multiple simultaneous announcements
            try:
                with tts_lock:
                    tts_in_progress = True
                    
                    try:
                        speech_file_path = "speech.wav"
                        
                        # Generate speech
                        print(f"[TTS] Generating: {announcement_text}")
                        response = groq_client.audio.speech.create(
                            model="playai-tts",
                            voice="Aaliyah-PlayAI",
                            response_format="wav",
                            input=announcement_text,
                        )
                        
                        # Save to file
                        with open(speech_file_path, "wb") as f:
                            f.write(response.read())
                        
                        # Play audio with comprehensive error handling
                        try:
                            data, samplerate = sf.read(speech_file_path, dtype="float32")
                            
                            duration = len(data) / samplerate
                            print(f"[TTS] Playing ({duration:.1f}s): {announcement_text[:40]}...")
                            
                            # Stop any previous audio first
                            try:
                                sd.stop()
                                time.sleep(0.1)  # Give audio system time to clean up
                            except:
                                pass
                            
                            # Play with error handling
                            stop_playback_flag = False
                            try:
                                sd.play(data, samplerate, blocking=False)
                                
                                # Wait manually with checks (faster polling)
                                start_wait = time.time()
                                while time.time() - start_wait < duration + 0.5:
                                    if stop_playback_flag or not analysis_active:
                                        break
                                    time.sleep(0.05)  # Check every 50ms
                                
                                # Stop playback
                                sd.stop()
                                time.sleep(0.1)  # Give audio system time to clean up
                                
                                print("[TTS] Completed")
                            except OSError as ose:
                                # Handle audio system errors gracefully
                                if "Unknown Error" in str(ose) or "err='-50'" in str(ose):
                                    print(f"[WARN] Audio system error (continuing): {ose}")
                                else:
                                    raise
                            
                        except Exception as audio_error:
                            print(f"[WARN] Audio playback failed: {audio_error}")
                            try:
                                sd.stop()
                            except:
                                pass
                    
                    except Exception as e:
                        print(f"[ERROR] TTS generation failed: {e}")
                    
                    finally:
                        tts_in_progress = False
                        try:
                            announcement_queue.task_done()
                        except:
                            pass
                        stop_playback_flag = False
                        # Ensure audio is stopped
                        try:
                            sd.stop()
                        except:
                            pass
                            
            except Exception as lock_error:
                print(f"[ERROR] Lock error: {lock_error}")
                tts_in_progress = False
                try:
                    announcement_queue.task_done()
                except:
                    pass
                    
        except Exception as e:
            print(f"[ERROR] Announcement worker error: {e}")
            tts_in_progress = False
            import traceback
            traceback.print_exc()
    
    # Final cleanup
    try:
        sd.stop()
    except:
        pass
    
    print("[TTS] Announcement worker stopped")


from difflib import SequenceMatcher


def extract_incident_core(description):
    """Extract the core elements of an incident for comparison."""
    desc_lower = description.lower()
    
    # Extract key elements
    actors = []
    actions = []
    objects = []
    locations = []
    
    # Actors
    if 'worker' in desc_lower or 'person' in desc_lower:
        actors.append('worker')
    
    # Actions
    action_words = ['sitting', 'lying', 'kneeling', 'crouching', 'standing', 
                    'handling', 'lifting', 'kicking', 'playing', 'operating']
    for word in action_words:
        if word in desc_lower:
            actions.append(word)
    
    # Objects
    object_words = ['forklift', 'box', 'boxes', 'ball', 'machinery', 'vehicle']
    for word in object_words:
        if word in desc_lower:
            objects.append(word)
    
    # Locations
    location_words = ['floor', 'ground', 'warehouse', 'shelf']
    for word in location_words:
        if word in desc_lower:
            locations.append(word)
    
    return {
        'actors': set(actors),
        'actions': set(actions),
        'objects': set(objects),
        'locations': set(locations)
    }


def incidents_similar(current_description, previous_description, groq_client):
    """Use lightweight heuristics + LLM judge to determine if two incidents are the same."""
    if not previous_description:
        return False, "no previous incident"
    
    current = current_description.lower().strip()
    previous = previous_description.lower().strip()
    
    if not current or not previous:
        return False, "insufficient description"
    
    # Quick heuristic: if they're nearly identical, treat as same
    ratio = SequenceMatcher(None, current, previous).ratio()
    if ratio >= 0.85:
        return True, f"Sequence similarity {ratio:.2f}"
    
    # Extract core incident elements
    current_core = extract_incident_core(current)
    previous_core = extract_incident_core(previous)
    
    # Compare core elements
    actors_match = len(current_core['actors'] & previous_core['actors']) > 0
    actions_match = len(current_core['actions'] & previous_core['actions']) > 0
    objects_match = len(current_core['objects'] & previous_core['objects']) > 0
    locations_match = len(current_core['locations'] & previous_core['locations']) > 0
    
    # Count matching elements
    matches = sum([actors_match, actions_match, objects_match, locations_match])
    
    # If 3+ core elements match, likely same incident
    if matches >= 3 and ratio >= 0.50:
        return True, f"Core elements match ({matches}/4), similarity {ratio:.2f}"
    
    # If all 4 core elements match, definitely same incident
    if matches == 4:
        return True, f"All core elements match, similarity {ratio:.2f}"
    
    # For medium similarity with good element overlap, treat as same
    if ratio >= 0.70 and matches >= 2:
        return True, f"High similarity {ratio:.2f} with {matches} matching elements"
    
    return False, f"Different incident (similarity {ratio:.2f}, {matches}/4 elements match)"


def build_announcement_text(severity, description, recommended_actions):
    """Create a short spoken alert summarizing severity, description, and immediate action."""
    severity_text = severity.capitalize()
    summary = description.strip() if description else "Safety issue detected."
    action = (
        recommended_actions[0].strip()
        if recommended_actions
        else "Take immediate corrective action."
    )
    return f"{severity_text} severity. {summary} Immediate action: {action}"



def analysis_worker():
    """Background thread that analyzes frames periodically."""
    global camera, analysis_active, latest_analysis, groq_client, announcement_queue
    global last_incident_description, active_incident, current_status_flag, last_announcement_time
    
    last_analysis_time = 0
    
    while analysis_active:
        try:
            if camera is None or not camera.isOpened():
                time.sleep(1)
                continue
            
            now = time.time()
            if now - last_analysis_time > ANALYZE_EVERY_SECONDS:
                last_analysis_time = now
                
                ret, frame = camera.read()
                if ret:
                    print("[INFO] Analyzing frame...")
                    analysis = analyze_frame(frame)
                    
                    if not analysis:
                        continue
                    
                    hazard_present = analysis.get("hazard_present", False)
                    severity = analysis.get("severity", "none")
                    hazard_types = analysis.get("hazard_types", [])
                    desc = analysis.get("description", "")
                    recommended = analysis.get("recommended_actions", [])
                    
                    analysis["new_incident"] = False
                    status_flag = current_status_flag
                    
                    if hazard_present and severity != "none":
                        print(f"[INFO] Hazard detected: {severity} - {desc[:80]}...")
                        
                        is_same, reason = incidents_similar(desc, last_incident_description, groq_client)
                        if is_same:
                            print(f"[INFO] ⊘ SAME INCIDENT ({reason}) → continuing monitoring")
                            active_incident = True
                            update_status_flag(STATUS_SAME_HAZARD)
                            status_flag = current_status_flag
                            # Still update UI even for same incident
                            analysis["new_incident"] = False
                            analysis["status_flag"] = status_flag
                            latest_analysis = analysis
                            socketio.emit('analysis_update', analysis)
                            continue  # Skip frame processing
                        else:
                            print(f"[INFO] ✓ NEW INCIDENT ({reason})")
                            
                            # Rate limiting: only announce if enough time has passed
                            now_time = time.time()
                            if now_time - last_announcement_time >= MIN_ANNOUNCEMENT_INTERVAL:
                                announcement = build_announcement_text(severity, desc, recommended)
                                try:
                                    announcement_queue.put(announcement, block=False)
                                    last_announcement_time = now_time
                                    print(f"[INFO] Announcement queued (queue size: {announcement_queue.qsize()})")
                                except:
                                    print(f"[WARN] Announcement queue full, skipping announcement")
                            else:
                                print(f"[INFO] Rate limited: {MIN_ANNOUNCEMENT_INTERVAL - (now_time - last_announcement_time):.1f}s until next announcement")
                            
                            analysis["new_incident"] = True
                            
                            last_incident_description = desc
                            active_incident = True
                            update_status_flag(STATUS_NEW_HAZARD)
                            status_flag = current_status_flag
                    
                    else:
                        if active_incident:
                            announce_situation_clear()
                        else:
                            update_status_flag(STATUS_CLEARED)
                        analysis["new_incident"] = False
                        status_flag = current_status_flag
                    
                    analysis["status_flag"] = status_flag
                    
                    # Update UI with latest analysis
                    latest_analysis = analysis
                    socketio.emit('analysis_update', analysis)
        
        except Exception as e:
            print(f"[ERROR] Analysis worker: {e}")
            import traceback
            traceback.print_exc()
            # Don't let errors crash the worker - keep going
            time.sleep(1)
        
        time.sleep(0.1)  # Fast polling
    
    print("[INFO] Analysis worker stopped")


def generate_frames():
    """Generate video frames for streaming."""
    global camera
    
    while True:
        if camera is None or not camera.isOpened():
            time.sleep(0.1)
            continue
        
        ret, frame = camera.read()
        if not ret:
            break
        
        # Encode frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


def login_required(f):
    """Decorator to require authentication for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'api_key' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function


def validate_groq_api_key(api_key):
    """Validate the Groq API key by making a test request."""
    try:
        test_client = Groq(api_key=api_key)
        # Make a minimal test request to verify the key works
        response = test_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        return True
    except Exception as e:
        print(f"[ERROR] API key validation failed: {e}")
        return False


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    """Handle login page and authentication."""
    if request.method == 'GET':
        # If already logged in, redirect to main page
        if 'api_key' in session:
            return redirect(url_for('index'))
        return render_template('login.html')
    
    # POST request - validate API key
    data = request.get_json()
    api_key = data.get('api_key', '').strip()
    
    if not api_key:
        return jsonify({"error": "API key is required"}), 400
    
    # Validate the API key
    if validate_groq_api_key(api_key):
        session['api_key'] = api_key
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"error": "Invalid API key or authentication failed"}), 401


@app.route('/logout')
def logout():
    """Log out and clear session."""
    session.clear()
    return redirect(url_for('login_page'))


@app.route('/')
@login_required
def index():
    """Serve the main page."""
    return render_template('index.html')


@app.route('/video_feed')
@login_required
def video_feed():
    """Video streaming route."""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/start', methods=['POST'])
@login_required
def start_analysis():
    """Start video analysis."""
    global camera, analysis_active, groq_client, announcement_queue
    global last_incident_description, active_incident, last_announcement_time
    
    # Use API key from session
    api_key = session.get('api_key')
    if not api_key:
        return jsonify({"error": "Not authenticated"}), 401
    
    groq_client = Groq(api_key=api_key)
    last_incident_description = None
    active_incident = False
    last_announcement_time = 0
    update_status_flag(STATUS_CLEARED)
    
    if camera is None:
        camera = cv2.VideoCapture(0)
    
    if not analysis_active:
        analysis_active = True
        
        # Clear any old announcements
        while not announcement_queue.empty():
            try:
                announcement_queue.get_nowait()
                announcement_queue.task_done()
            except:
                break
        
        # Start both workers
        threading.Thread(target=analysis_worker, daemon=True).start()
        threading.Thread(target=tts_announcement_worker, daemon=True).start()
    
    return jsonify({"status": "started"})


@app.route('/stop', methods=['POST'])
@login_required
def stop_analysis():
    """Stop video analysis."""
    global camera, analysis_active, tts_in_progress, announcement_queue
    global last_incident_description, active_incident, last_announcement_time
    
    analysis_active = False
    
    # Clear announcement queue
    while not announcement_queue.empty():
        try:
            announcement_queue.get_nowait()
            announcement_queue.task_done()
        except:
            break
    
    # Stop any ongoing audio
    try:
        sd.stop()
    except:
        pass
    
    tts_in_progress = False
    active_incident = False
    last_incident_description = None
    last_announcement_time = 0
    update_status_flag(STATUS_CLEARED)
    
    if camera is not None:
        camera.release()
        camera = None
    
    # Give time for threads to finish
    time.sleep(0.5)
    
    return jsonify({"status": "stopped"})


@app.route('/status')
@login_required
def get_status():
    """Get current analysis status."""
    return jsonify({
        "active": analysis_active,
        "latest_analysis": latest_analysis
    })


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print('[INFO] Client connected')
    if latest_analysis:
        emit('analysis_update', latest_analysis)


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print('[INFO] Client disconnected')


if __name__ == '__main__':
    print("Starting Industrial Safety Video Analytics Web App...")
    print("Open http://localhost:8080 in your browser")
    socketio.run(app, debug=True, host='0.0.0.0', port=8080, allow_unsafe_werkzeug=True)

