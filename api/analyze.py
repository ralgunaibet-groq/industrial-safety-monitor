"""
Vercel Serverless Function for Image Analysis
Accepts uploaded images and returns hazard analysis
"""

import json
import base64
import sys
import os
from io import BytesIO
from PIL import Image
from groq import Groq
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hazard_config import get_hazard_prompt, HazardConfigError

try:
    HAZARD_PROMPT = get_hazard_prompt()
except HazardConfigError as e:
    print(f"[ERROR] Failed to load hazard configuration: {e}")
    raise


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

