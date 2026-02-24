import urllib.request
import json
import os

req = urllib.request.Request('https://prompts.chat/api/prompts?perPage=1', headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode())
    with open('api_sample.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
