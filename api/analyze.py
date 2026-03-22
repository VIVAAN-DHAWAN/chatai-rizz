from http.server import BaseHTTPRequestHandler
import json
import os
import time
import requests

OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# openrouter/free = auto-selects best available free model, zero cost always
# Falls back through specific free models if auto-router also 429s
PRIMARY_MODEL = "openrouter/auto"
FALLBACK_MODELS = [
    "stepfun/step-3.5-flash:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "mistralai/mistral-7b-instruct:free",
]

# Vision-capable free model for OCR
VISION_MODEL = "openrouter/auto"

SCENARIOS = {
    'first_text': "First text to someone you're interested in",
    'asking_out': 'Asking someone out on a date',
    'left_on_read': 'Recovering from being left on read',
    'situationship': 'Navigating a situationship',
    'ghosted': 'Coming back after being ghosted',
}


def make_request(messages, model, max_tokens=600):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://chatai-rizz.vercel.app",
        "X-Title": "Rizz Coach"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": max_tokens,
    }
    return requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)


def call_with_fallback(messages, max_tokens=600):
    """Try primary model, then fallbacks on 429."""
    models = [PRIMARY_MODEL] + FALLBACK_MODELS
    for i, model in enumerate(models):
        if i > 0:
            time.sleep(1)
        try:
            response = make_request(messages, model, max_tokens)
            if response.status_code == 429:
                continue
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException:
            if i == len(models) - 1:
                raise
            continue
    raise Exception("All models rate limited. Try again in a minute.")


def extract_text_from_image(image_b64, mime_type="image/png"):
    """Use vision AI to extract conversation text from screenshot."""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{image_b64}"}
                },
                {
                    "type": "text",
                    "text": "Extract all the text messages from this screenshot exactly as they appear. Format as a conversation with each message on a new line. Output only the raw conversation text, nothing else."
                }
            ]
        }
    ]
    response = call_with_fallback(messages, max_tokens=500)
    return response.json()['choices'][0]['message']['content'].strip()


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
            "vibe": "<one word: Smooth/Bold/Playful/Safe/Risky>",
            "reasoning": "<why this works in gen z slang>"
        }}
    ]
}}"""

    messages = [
        {
            "role": "system",
            "content": "You are The Rizz Coach - a brutally honest Gen Z texting expert. Use modern slang: mid, fire, W, L, sus, based, slay, no cap, lowkey, highkey, rizz, situationship, understood the assignment, main character energy. Be real, not nice."
        },
        {"role": "user", "content": prompt}
    ]

    response = call_with_fallback(messages)
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
            scenario = data.get('scenario', 'first_text')
            conversation = data.get('conversation', '').strip()
            image_b64 = data.get('image_b64', '').strip()
            mime_type = data.get('mime_type', 'image/png')

            if not OPENROUTER_API_KEY:
                self._respond(500, {"error": "Server not configured"})
                return

            if image_b64:
                conversation = extract_text_from_image(image_b64, mime_type)

            if not conversation:
                self._respond(400, {"error": "No conversation provided"})
                return

            result = analyze_conversation(conversation, scenario)
            result['extracted_text'] = conversation
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
        pass
