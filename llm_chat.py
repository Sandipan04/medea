import requests
import json

class access_ollama():
    def __init__(self, serverip="10.10.0.170", port=11434, model="llama3:70b-instruct", message_file=None):
        self.server = serverip
        self.port = 11434
        self.endpoint = f"http://{self.server}:{self.port}/api/chat"
        self.model = model
        self.headers  = {
            'Content-Type': 'application/json',
            # Include any necessary authorization headers if required
            # 'Authorization': 'Bearer YOUR_ACCESS_TOKEN'
        }
        self.user_template = {
            "role": "user",
            "content": None
        }
        self.file = message_file
        self.messages = self.file_handler(filename=self.file)
        self.stream = False

    def file_handler(self, filename, text=None):
        with open(filename, 'r+') as f:
            doc = f.read()
            if not text:
                m = []
                lines =  doc.splitlines()[1:]
                for line in lines:
                    broken = self.split(line)
                    d = dict({broken[i]: broken[i+2] for i in range(1, len(broken), 4)})
                    m.append(d)
                return  m
            else:
                if not doc.endswith('\n'):
                    f.write('\n')
                f.write(json.dumps(text))

    def split(self, s):
        l = []
        prev = 0
        for curr in range(1, len(s)):
            if s[curr] == "\"" and s[curr-1] != "\\":
                l.append(s[prev+1:curr])
                prev = curr
        return l

    def chat_with_ollama(self):
        data = {
            'model': self.model,
            'messages': self.messages,
            'stream': self.stream
        }

        response = requests.post(self.endpoint, headers=self.headers, data=json.dumps(data))

        try:
            response = requests.post(self.endpoint, headers=self.headers, data=json.dumps(data))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None

    def input_handler(self, user_input):
        current = self.user_template.copy()
        current["content"] = user_input
        self.messages.append(current)
        self.file_handler(filename=self.file, text=current)
        response = self.chat_with_ollama()
        if response:
            response = response["message"]
            self.messages.append(response)
            self.file_handler(self.file, text=response)
            return response["content"]
