from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from datetime import datetime, timezone
import random
import os

API_KEY = os.environ.get('API_KEY', 'default_secret')
PORT = 9000
HOST = '127.0.0.1'
os.makedirs("cloud_store", exist_ok=True)

class IngestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Check API key
        api_key = self.headers.get('X-API-Key')
        if api_key != API_KEY:
            self.send_response(401)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Unauthorized'}).encode())
            return
        
        # Check endpoint
        if self.path == '/ingest':
            try:
                # Mock Server overload and server error place holders
                rand_throw_429 = random.random() < 0.05
                rand_throw_500 = random.random() < 0.05

                if rand_throw_429:

                    self.send_response(429)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    error = {'error': 'Server overloaded'}
                    self.wfile.write(json.dumps(error).encode())
                    return
                
                elif rand_throw_500:

                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    error = {'error': 'Server error occured, try again'}
                    self.wfile.write(json.dumps(error).encode())
                    return
                    
                # Read the POST data
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data)
                
                # Validate required fields
                if 'agent_id' not in data or 'batch_id' not in data or 'lines' not in data:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    error = {'error': 'Missing required fields: agent_id, batch_id, lines'}
                    self.wfile.write(json.dumps(error).encode())
                    return
                
                if (not isinstance(data["agent_id"], str)) or (not isinstance(data["batch_id"], str)):
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    error = {'error': 'Batch or agent id are not string, please try again'}
                    self.wfile.write(json.dumps(error).encode())
                    return

                
                # Validate lines is a list
                if not isinstance(data['lines'], list):
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    error = {'error': 'lines must be an array'}
                    self.wfile.write(json.dumps(error).encode())
                    return
                
                # Process the data
                print(f"Agent ID: {data['agent_id']}")
                print(f"Batch ID: {data['batch_id']}")
                print(f"Lines received: {len(data['lines'])}")
                
                # Parse and print each JSONL line
                file_name = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                f = open(f'cloud_store/ingested_{file_name}.jsonl', "a+", encoding="utf-8")

                for i, line in enumerate(data['lines']):
                    f.write(line.rstrip("\n") + "\n")
                        

                
                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    'status': 'success',
                    'message': 'Data ingested',
                    'lines_processed': len(data['lines'])
                }
                self.wfile.write(json.dumps(response).encode())
                
            except json.JSONDecodeError:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                error = {'error': 'Invalid JSON'}
                self.wfile.write(json.dumps(error).encode())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    server = HTTPServer((HOST, PORT), IngestHandler)
    print(f"Server running on http://localhost:{PORT}")
    print(f"API Key: {API_KEY}")
    server.serve_forever()
    