"""
SmartTutor - 作业辅导智能体
简单HTML前端
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import json

HTML_CONTENT = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>SmartTutor - Homework Tutor</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        h1 { color: #333; }
        #chat { border: 1px solid #ccc; height: 400px; overflow-y: scroll; padding: 10px; margin-bottom: 10px; background: #f9f9f9; }
        .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .user { background: #e3f2fd; text-align: right; }
        .assistant { background: #f5f5f5; }
        input { width: 70%; padding: 10px; }
        button { padding: 10px 20px; background: #4CAF50; color: white; border: none; cursor: pointer; }
        button:hover { background: #45a049; }
    </style>
</head>
<body>
    <h1>📚 SmartTutor - Homework Tutor</h1>
    <p>Ask math and history homework questions here.</p>
    <div id="chat"></div>
    <input type="text" id="msg" placeholder="Enter a math or history homework question..." onkeypress="if(event.key==='Enter')send()">
    <button onclick="send()">Send</button>

    <script>
        const chat = document.getElementById('chat');
        
        function addMessage(text, isUser) {
            const div = document.createElement('div');
            div.className = 'message ' + (isUser ? 'user' : 'assistant');
            div.innerHTML = isUser ? '<b>You:</b> ' + text : '<b>SmartTutor:</b> ' + text;
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }

        async function send() {
            const input = document.getElementById('msg');
            const message = input.value.trim();
            if (!message) return;
            
            addMessage(message, true);
            input.value = '';
            
            try {
                const res = await fetch('http://localhost:8000/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message})
                });
                const data = await res.json();
                addMessage(data.response || 'No response', false);
            } catch (e) {
                addMessage('Error: ' + e.message, false);
            }
        }
    </script>
</body>
</html>
'''

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode())
        else:
            super().do_GET()

print("Starting simple web frontend at: http://localhost:7860")
HTTPServer(('0.0.0.0', 7860), Handler).serve_forever()
