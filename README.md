# 🔥 Rizz Coach

> AI-powered text message analyzer. Paste your convo, get a rizz score + 3 better responses. No cap.

**[Live Demo →](https://your-app.vercel.app)**

Built for Gen Z. Free forever. No account needed.

## Features

- 🎯 5 scenarios — first text, asking out, left on read, situationship, was ghosted
- 📊 Rizz score 0–10 with brutal honesty
- 💬 3 ranked alternative responses with vibe tags
- 📋 Click any response to copy it
- 🔒 No data stored, no login, no BS

## Deploy Your Own (Free)

### 1. Fork this repo

### 2. Deploy to Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new)

### 3. Add your OpenRouter API key

In Vercel dashboard → Settings → Environment Variables:
```
OPENROUTER_API_KEY = sk-or-v1-...
```

Get a free key at [openrouter.ai](https://openrouter.ai) — free models available.

### 4. Done

Vercel auto-deploys. Your key stays private on the server — nobody can see it.

## Run Locally

```bash
git clone https://github.com/yourusername/rizz-coach
cd rizz-coach
pip install -r requirements.txt
export OPENROUTER_API_KEY="sk-or-v1-..."
vercel dev
```

## Stack

- **Frontend** — Vanilla HTML/CSS/JS (zero dependencies)
- **Backend** — Python serverless function on Vercel
- **AI** — OpenRouter (free Llama 3.3 70B by default)

## License

MIT — do whatever
