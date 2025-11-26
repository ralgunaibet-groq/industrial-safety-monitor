"""
Vercel Serverless Function - Main API endpoint
"""

from http.server import BaseHTTPRequestHandler
import json


class handler(BaseHTTPRequestHandler):
    """Main API handler."""
    
    def do_GET(self):
        """Handle GET requests."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "name": "Industrial Safety Monitor API",
            "version": "1.0.0",
            "endpoints": {
                "/api/analyze": "POST - Analyze an image for safety hazards",
            },
            "usage": {
                "method": "POST",
                "url": "/api/analyze",
                "body": {
                    "api_key": "your_groq_api_key",
                    "image": "base64_encoded_image"
                }
            }
        }
        
        self.wfile.write(json.dumps(response, indent=2).encode())
    
    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

