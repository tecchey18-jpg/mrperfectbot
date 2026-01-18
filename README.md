# 🚀 Terabox Link Extractor Bot

Industrial-grade Telegram bot that extracts direct download links from Terabox share URLs.

## Features

- 🛡️ **2026-Level Stealth** - Comprehensive anti-detection with fingerprint randomization
- 🔄 **Multi-Layer Extraction** - Network, JavaScript, and DOM-based extraction
- 🤖 **Human-Like Behavior** - Bezier mouse curves, natural typing, realistic timing
- 🔁 **Auto-Recovery** - Automatic retry with fresh fingerprint on failure
- 🌐 **Multi-Domain Support** - Works with terabox.com, 1024tera.com, and more

## Quick Start

### Prerequisites

- Python 3.11+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))

### Local Development

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/telebot.git
cd telebot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Set environment variable
export BOT_TOKEN=your_telegram_bot_token  # Linux/Mac
# or: set BOT_TOKEN=your_telegram_bot_token  # Windows

# Run the bot
python main.py
```

### Docker

```bash
# Build image
docker build -t terabox-bot .

# Run container
docker run -e BOT_TOKEN=your_token terabox-bot
```

## Deploy to Render

### Option 1: Using render.yaml Blueprint

1. Push this repo to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com/)
3. Click **New** → **Blueprint**
4. Connect your GitHub repo
5. Render will auto-detect `render.yaml`
6. Add `BOT_TOKEN` in Environment Variables
7. Deploy!

### Option 2: Manual Setup

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **New** → **Background Worker**
3. Connect your GitHub repo
4. Configure:
   - **Environment**: Docker
   - **Dockerfile Path**: `./Dockerfile`
5. Add Environment Variable:
   - `BOT_TOKEN` = your Telegram bot token
6. Deploy!

## GitHub Actions (Auto-Deploy)

To enable automatic deployment on push:

1. Go to your Render Dashboard → Service → Settings
2. Copy your **Service ID**
3. Go to Account Settings → API Keys → Create API Key
4. In GitHub repo → Settings → Secrets → Actions, add:
   - `RENDER_API_KEY`: Your Render API key
   - `RENDER_SERVICE_ID`: Your service ID

Now every push to `main` will trigger a deploy!

## Supported Domains

- terabox.com
- 1024tera.com
- teraboxapp.com
- 4funbox.co
- mirrobox.com
- nephobox.com
- freeterabox.com
- And many more...

## Architecture

```
┌─────────────────┐     ┌──────────────────┐
│  Telegram Bot   │────▶│  Extraction      │
│   (aiogram)     │     │  Pipeline        │
└─────────────────┘     └──────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│ Layer 1:      │     │ Layer 2:      │     │ Layer 3:      │
│ Network       │────▶│ JavaScript    │────▶│ DOM           │
│ Interception  │     │ Inspection    │     │ Automation    │
└───────────────┘     └───────────────┘     └───────────────┘
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                               ▼
                    ┌──────────────────┐
                    │ Layer 4:         │
                    │ Recovery         │
                    │ (New Fingerprint)│
                    └──────────────────┘
```

## Stealth Features

| Feature | Description |
|---------|-------------|
| WebDriver Evasion | Removes all automation indicators |
| Chrome Runtime | Injects realistic `window.chrome` object |
| Canvas Fingerprint | Adds imperceptible noise per session |
| Audio Fingerprint | Randomizes AudioContext output |
| WebGL Spoofing | Matches GPU to platform |
| Client Hints | Full SEC-CH-UA header emulation |
| Permissions API | Realistic permission states |
| Battery API | Spoofed realistic values |
| Timing Protection | Sub-ms jitter on performance.now() |

## License

MIT License - Use responsibly and respect Terms of Service.
