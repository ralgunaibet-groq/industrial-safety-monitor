"""
Vercel Serverless Function for Image Analysis
Accepts uploaded images and returns hazard analysis
"""

import json
import base64
from io import BytesIO
from PIL import Image
from groq import Groq
from http.server import BaseHTTPRequestHandler

# Hazard detection prompt
HAZARD_PROMPT = """
You are an industrial safety inspector looking at a camera feed
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


def analyze_image(image_base64, api_key):
    """Analyze image using Groq API."""
    try:
        client = Groq(api_key=api_key)
        
        completion = client.chat.completions.create(
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
                                "url": f"data:image/jpeg;base64,{image_base64}",
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
        
        # Extract JSON
        start = msg_content.find('{')
        end = msg_content.rfind('}')
        
        if start != -1 and end != -1:
            json_str = msg_content[start:end+1]
            try:
                data = json.loads(json_str)
                return {"success": True, "data": data}
            except json.JSONDecodeError:
                # Try to find first complete JSON object
                depth = 0
                for i, char in enumerate(json_str):
                    if char == '{':
                        depth += 1
                    elif char == '}':
                        depth -= 1
                        if depth == 0:
                            try:
                                data = json.loads(json_str[:i+1])
                                return {"success": True, "data": data}
                            except:
                                continue
                return {"success": False, "error": "Could not parse JSON response"}
        else:
            return {"success": False, "error": "No JSON found in response"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


class handler(BaseHTTPRequestHandler):
    """Vercel serverless function handler."""
    
    def do_POST(self):
        """Handle POST requests with image data."""
        try:
            # Get content length
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Parse JSON
            data = json.loads(post_data.decode('utf-8'))
            
            # Get API key and image
            api_key = data.get('api_key')
            image_data = data.get('image')  # Base64 encoded
            
            if not api_key:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": "API key is required"
                }).encode())
                return
            
            if not image_data:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": "Image data is required"
                }).encode())
                return
            
            # Remove data URL prefix if present
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            # Analyze the image
            result = analyze_image(image_data, api_key)
            
            # Send response
            self.send_response(200 if result.get('success') else 500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "error": str(e)
            }).encode())
    
    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

