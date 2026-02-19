# 📧 Gmail AI Assistant

A voice and text-controlled Gmail client built with **Streamlit**, powered by **Google Gemini AI** and the **Gmail API**. Control your inbox using natural language — speak or type commands like "show unread emails", "compose email to john@example.com", or "reply" to the current email.

---

## ✨ Features

- 🎤 **Voice Commands** — Click a button, speak, and actions execute instantly
- 💬 **Text Commands** — Type natural language commands in the sidebar
- 📥 **Inbox Management** — View, filter, and search emails
- ✉️ **Compose & Send** — Draft and send emails with AI-prefilled fields
- 📖 **Email Detail View** — Read full email content
- ↩️ **Reply** — Smart reply with auto-quoted body
- 🔍 **Smart Filtering** — Filter by sender, unread status, keyword, or date range
- 📜 **Command History** — Track executed actions in the sidebar

---

## 🗂️ Project Structure

```
gmail-ai-assistant/
│
├── app.py               # Main Streamlit app — UI, routing, voice handler
├── ai_assistant.py      # Gemini AI command parser and action executor
├── mail_service.py      # Gmail API service — list, read, send emails
├── test_models.py       # Utility script to list available Gemini models
├── credentials.json     # (You provide) Google OAuth2 credentials
├── token.pickle         # (Auto-generated) Saved OAuth2 token
└── .env                 # Environment variables (GEMINI_API_KEY)
```

---

## ⚙️ Prerequisites

- Python 3.9+
- A Google account with Gmail
- Google Cloud project with Gmail API enabled
- Gemini API key from [Google AI Studio](https://aistudio.google.com/)

---

## 🚀 Installation

### 1. Clone or download the project

```bash
git clone <your-repo-url>
cd gmail-ai-assistant
```

### 2. Install dependencies

A `requirements.txt` is included. Install all dependencies with:

```bash
pip install -r requirements.txt
```

Key packages and their minimum versions:

| Package | Version | Purpose |
|---|---|---|
| `streamlit` | ≥1.39.0 | Web UI framework |
| `google-api-python-client` | ≥2.111.0 | Gmail API client |
| `google-auth` | ≥2.35.0 | OAuth2 authentication |
| `google-auth-oauthlib` | ≥1.2.0 | OAuth2 flow |
| `google-generativeai` | ≥0.8.0 | Gemini AI API |
| `python-dotenv` | ≥1.0.0 | `.env` file support |
| `rich` | ≥13.0.0 | Enhanced error display |

### 3. Set up Google Cloud credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing) — note your **Project ID**
3. Enable **Gmail API** under APIs & Services → Library
4. Go to **Credentials → Create Credentials → OAuth 2.0 Client ID**
5. Choose **Desktop App**, download the JSON file
6. Rename it to `credentials.json` and place it in the project root

> **⚠️ Security:** `credentials.json` contains your OAuth client secret. Never commit it to version control. Add it to `.gitignore` immediately.

The downloaded file will have this structure:
```json
{
  "installed": {
    "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "client_secret": "YOUR_CLIENT_SECRET",
    "redirect_uris": ["http://localhost"]
  }
}
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Get your Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey).

### 5. Set up `.gitignore`

Create a `.gitignore` file to protect sensitive files:

```
credentials.json
token.pickle
.env
__pycache__/
*.pyc
```

---

## ▶️ Running the App (Quick Start)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Add credentials.json and .env to project root

# 3. Launch
streamlit run app.py
```

On first run, a browser window will open for Google OAuth2 authentication. Grant Gmail access and a `token.pickle` file will be saved for future sessions.

---

## 🎤 Voice Commands (Examples)

| Command | Action |
|---|---|
| "Show unread emails" | Filters inbox to unread only |
| "Show emails from john" | Filters by sender |
| "Show emails from last week" | Filters by date range |
| "Compose email to alice@example.com" | Opens compose with To prefilled |
| "Open email from support" | Opens latest email from that sender |
| "Reply" | Prepares a reply to the current open email |

---

## 🧩 How It Works

1. **User Input** — Voice (via Web Speech API) or typed text command
2. **AI Parsing** — `parse_command()` in `ai_assistant.py` sends the command to Gemini, which returns a structured JSON action
3. **Action Execution** — `execute_action_with_feedback()` in `app.py` interprets the action and updates Streamlit session state
4. **Gmail API** — `mail_service.py` handles all Gmail interactions (list, read, send)

---

## 🔒 Permissions & Security

- The app uses the `gmail.modify` OAuth scope (read + send, no delete)
- OAuth credentials are stored locally in `token.pickle`
- Your Gemini API key is stored in `.env` and never sent to Gmail
- `credentials.json` and `token.pickle` should be added to `.gitignore`

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---|---|
| `GEMINI_API_KEY not found` | Check your `.env` file has the correct key |
| OAuth popup doesn't open | Delete `token.pickle` and re-run the app |
| Voice button not working | Use Chrome/Edge (Firefox does not support Web Speech API) |
| `HttpError 403` | Ensure Gmail API is enabled in your Google Cloud project |
| Gemini model error | Run `test_models.py` to see available models and update `ai_assistant.py` |

---

## 📄 License

MIT License — free to use and modify.
