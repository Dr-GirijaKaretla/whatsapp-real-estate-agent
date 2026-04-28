# WhatsApp Real Estate Agent

An AI-powered WhatsApp chatbot for real estate businesses — built with Claude (Anthropic) and Twilio.

Clients can search properties, book viewings, and get answers, all through WhatsApp. Business owners get admin commands to manage listings, leads, and appointments from the same chat.

---

## Features

| Feature | Description |
|---|---|
| **Property Search** | Clients describe what they want; the agent finds matching listings |
| **Property Details** | Full specs, pricing, amenities on demand |
| **Appointment Booking** | Schedule property viewings with conflict detection |
| **Lead Capture** | Automatically collects client name, budget, and preferences |
| **FAQ Answering** | Answers process, pricing, and document questions |
| **Admin Commands** | Business owner can add listings, view leads & appointments via WhatsApp |
| **Human Escalation** | Client can request a human agent at any time |
| **Conversation Memory** | Agent remembers context within each conversation |

---

## Tech Stack

- **AI**: [Claude](https://anthropic.com) (Anthropic) — conversational agent with tool use
- **WhatsApp**: [Twilio](https://twilio.com/whatsapp) — WhatsApp Business API
- **Server**: Flask + Gunicorn
- **Database**: SQLite (dev) / PostgreSQL (production)
- **ORM**: SQLAlchemy

---

## Project Structure

```
whatsapp-real-estate-agent/
├── app.py                    ← Flask webhook server (entry point)
├── agent/
│   ├── core.py               ← Agentic loop (Claude + tool use)
│   ├── tools.py              ← Tool definitions sent to Claude
│   ├── memory.py             ← Per-lead conversation history
│   └── prompts.py            ← System prompts
├── database/
│   ├── models.py             ← SQLAlchemy models (Property, Lead, Appointment)
│   └── connection.py         ← DB engine + session management
├── handlers/
│   ├── property.py           ← Property search, details, add
│   ├── lead.py               ← Lead upsert and summary
│   ├── appointment.py        ← Booking, cancellation, listing
│   └── faq.py                ← FAQ / knowledge-base answers
├── services/
│   └── whatsapp.py           ← Twilio send/receive wrapper
├── utils/
│   └── validators.py         ← Twilio signature verification
├── .env.example              ← Environment variable template
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

---

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/whatsapp-real-estate-agent.git
cd whatsapp-real-estate-agent
```

### 2. Install dependencies

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in:

| Variable | Where to get it |
|---|---|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) |
| `TWILIO_ACCOUNT_SID` | [console.twilio.com](https://console.twilio.com) → Dashboard |
| `TWILIO_AUTH_TOKEN` | Twilio Console → Dashboard |
| `TWILIO_WHATSAPP_NUMBER` | Twilio Console → Messaging → Senders → WhatsApp |
| `ADMIN_PHONES` | Your own WhatsApp number (E.164 format, e.g. `+12125551234`) |

### 4. Run the server

```bash
python app.py
```

The server starts on `http://localhost:5000`.

### 5. Expose your local server to the internet

Twilio needs a public URL to send webhooks to. Use [ngrok](https://ngrok.com) during development:

```bash
ngrok http 5000
```

Copy the HTTPS URL (e.g. `https://abc123.ngrok.io`).

### 6. Configure Twilio Webhook

1. Go to [console.twilio.com](https://console.twilio.com)
2. Navigate to **Messaging → Senders → WhatsApp**
3. Set the webhook URL to: `https://abc123.ngrok.io/webhook/whatsapp`
4. Method: **HTTP POST**
5. Save

### 7. Test on WhatsApp

- For the **Twilio Sandbox**: Send the sandbox join code (shown in Twilio console) from your WhatsApp to the sandbox number
- Then send any message to start chatting with your agent!

---

## Deployment

### Option A — Railway / Render / Heroku (easiest)

1. Push this repo to GitHub
2. Connect your GitHub repo to Railway/Render
3. Set all environment variables in the platform's settings panel
4. Deploy — your webhook URL will be `https://your-app.railway.app/webhook/whatsapp`
5. Update the Twilio webhook URL to point to your deployed app

### Option B — Docker

```bash
cp .env.example .env   # fill in your values
docker-compose up -d
```

### Option C — VPS / DigitalOcean

```bash
# On your server
git clone <repo>
cd whatsapp-real-estate-agent
pip install -r requirements.txt
cp .env.example .env   # fill in values
gunicorn app:app --bind 0.0.0.0:5000 --workers 2 --daemon
```

Set up nginx as a reverse proxy and add an SSL certificate (Let's Encrypt).

---

## Admin Commands

Set your phone number in `ADMIN_PHONES` in `.env` to unlock admin features.

Send these commands from your WhatsApp:

| Command | Description |
|---|---|
| `/add_listing` | Add a new property (agent will ask for details) |
| `/leads` | View all leads |
| `/leads new` | View only new leads |
| `/appointments` | View today's appointments |
| `/appointments tomorrow` | View tomorrow's appointments |

---

## Example Conversation

```
Client:  Hi, I'm looking for a 2 bedroom apartment to rent in Miami under $2,500/month

Agent:   Hi! I'm Alex from [Agency]. I'd love to help you find the perfect place!
         Let me search for 2BHK apartments for rent in Miami under $2,500.

         Found 3 properties:

         #1 — 2BHK Ocean View Apartment
         📍 South Beach, Miami
         📐 950 sqft  |  💰 $2,200/mo
         🏷️ RENT | Apartment

         #2 — Modern 2BHK in Downtown Miami
         📍 Brickell, Miami
         📐 880 sqft  |  💰 $2,400/mo
         🏷️ RENT | Apartment

         Reply with a property number (e.g. #1) for full details, or "book #1" to schedule a viewing.

Client:  Book #1 this Saturday at 10am

Agent:   ✅ Viewing Booked!

         📍 Ocean View Apartment
         👤 [Client Name]
         📅 Saturday, 15 June 2025 at 10:00 AM
         🔖 Booking ID: #7

         We'll send a reminder the day before. Reply "cancel #7" to cancel.
```

---

## Adding Properties

You can add properties via:
1. **WhatsApp admin command**: `/add_listing` (agent guides you through it)
2. **Direct database**: Use any SQLite client to insert into the `properties` table
3. **Custom admin API**: Extend `app.py` to add a REST endpoint for bulk imports

---

## Production Checklist

- [ ] Set `SKIP_TWILIO_VALIDATION=false` (validates all webhook requests)
- [ ] Use PostgreSQL instead of SQLite (`DATABASE_URL=postgresql://...`)
- [ ] Set `FLASK_DEBUG=false`
- [ ] Use HTTPS for your webhook URL
- [ ] Set strong, unique values for all secrets
- [ ] Test the full booking flow end-to-end before go-live
- [ ] Upgrade to a Twilio WhatsApp Business number (not sandbox) for production

---

## License

MIT — free to use, modify, and distribute.
