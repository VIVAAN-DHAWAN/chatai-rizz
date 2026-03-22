from http.server import BaseHTTPRequestHandler
import json
import os
import requests

OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

SCENARIOS = {
    'first_text': "First text to someone you're interested in",
    'asking_out': 'Asking someone out on a date',
    'left_on_read': 'Recovering from being left on read',
    'situationship': 'Navigating a situationship',
    'ghosted': 'Coming back after being ghosted',
}

def analyze_conversation(conversation, scenario):
    scenario_desc = SCENARIOS.get(scenario, 'General conversation')

    prompt = f"""Analyze this text message convo and give 3 alternative responses ranked by confidence, plus a rizz score out of 10.

Scenario: {scenario_desc}

Convo:
{conversation}

Rizz Score (0-10):
10 = Flawless, instant W
8-9 = Fire, confident vibes
6-7 = Mid, safe but not the move
4-5 = Kinda cringe, doing too much
2-3 = Big L, sus behavior
0-1 = Disaster, rip the convo

Be brutally honest. Most convos are mid, don't inflate scores.

Respond ONLY with valid JSON, no extra text:
{{
    "rizz_score": <0-10>,
    "roast": "<one brutal honest line about the current conversation>",
    "alternatives": [
        {{
            "response": "<text message response>",
            "confidence": <0.0-1.0>,
            "vibe": "<one word vibe: Smooth/Bold/Playful/Safe/Risky>",
            "reasoning": "<why this works in gen z slang>"
        }}
    ]
}}"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://rizzcoach.vercel.app",
        "X-Title": "Rizz Coach"
    }

    payload = {
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "messages": [
            {
                "role": "system",
                "content": "You are The Rizz Coach - a brutally honest Gen Z texting expert. Use modern slang: mid, fire, W, L, sus, based, slay, no cap, lowkey, highkey, rizz, situationship, understood the assignment, main character energy. Be real, not nice."
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 600
    }

    response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()

    content = response.json()['choices'][0]['message']['content'].strip()

    # Strip markdown fences if present
    if '```json' in content:
        content = content.split('```json')[1].split('```')[0].strip()
    elif '```' in content:
        content = content.split('```')[1].split('```')[0].strip()

    data = json.loads(content)
    data['alternatives'] = sorted(data['alternatives'], key=lambda x: x.get('confidence', 0), reverse=True)
    return data


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
            conversation = data.get('conversation', '').strip()
            scenario = data.get('scenario', 'first_text')

            if not conversation:
                self._respond(400, {"error": "No conversation provided"})
                return

            if not OPENROUTER_API_KEY:
                self._respond(500, {"error": "Server not configured"})
                return

            result = analyze_conversation(conversation, scenario)
            self._respond(200, result)

        except json.JSONDecodeError as e:
            self._respond(500, {"error": f"Failed to parse AI response: {str(e)}"})
        except requests.exceptions.RequestException as e:
            self._respond(500, {"error": f"AI request failed: {str(e)}"})
        except Exception as e:
            self._respond(500, {"error": str(e)})

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def _cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def _respond(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self._cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        pass  # Suppress logs
