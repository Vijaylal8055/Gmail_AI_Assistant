import json
import os
from datetime import datetime, timedelta
import streamlit as st
from dotenv import load_dotenv

# ────────────────────────────────────────────────
# Import required functions from mail_service.py
# ────────────────────────────────────────────────
from mail_service import list_emails, get_email_detail

# ────────────────────────────────────────────────
# Load environment variables
# ────────────────────────────────────────────────
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file. Please add it.")

# ────────────────────────────────────────────────
# Google Generative AI
# ────────────────────────────────────────────────
import google.generativeai as genai

genai.configure(api_key=GEMINI_API_KEY)

# Use a model that exists in your list
model = genai.GenerativeModel("gemini-2.5-flash")

# ────────────────────────────────────────────────
# Parse user command into structured action
# ────────────────────────────────────────────────
def parse_command(user_input, current_view, current_email_id=None):
    """
    Parse natural language command into structured action using Gemini.
    Returns dict with 'action' and 'params'.
    """
    prompt = f"""
You are an AI assistant that parses user commands for an email app.
Extract the intent and parameters strictly as JSON.

User command: "{user_input}"

Current view: {current_view}
Current open email ID (if in detail view): {current_email_id or 'None'}

Possible actions:
- "compose": Open compose view and fill to, subject, body
- "filter_inbox": Apply filters to inbox (params: unread (bool), sender (str), keyword (str), date_range (str like "last 10 days" or "this week"))
- "open_email": Open a specific email (params: sender or keyword to find latest match)
- "reply": Reply to current open email (no extra params needed)
- "unknown": If command doesn't match

Respond **only** with valid JSON, no extra text, no markdown, no explanations:
{{
  "action": "compose" | "filter_inbox" | "open_email" | "reply" | "unknown",
  "params": {{ ... relevant key-value pairs ... }}
}}
"""

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.2,
                top_p=0.95,
                max_output_tokens=1024,
                response_mime_type="application/json"
            )
        )

        raw_text = response.text.strip()

        # Clean up potential markdown/code blocks
        if raw_text.startswith("```json"):
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1].strip()

        parsed = json.loads(raw_text)
        return parsed

    except Exception as e:
        st.error(f"Gemini API error: {str(e)}")
        return {"action": "unknown", "params": {}}


# ────────────────────────────────────────────────
# Execute the parsed action
# ────────────────────────────────────────────────
def execute_action(action_data, service):
    """
    Execute the parsed action by updating Streamlit session state.
    action_data: dict containing 'action' and 'params'
    service: Gmail API service instance
    """
    action = action_data.get("action", "unknown")
    params = action_data.get("params", {})

    if action == "compose":
        st.session_state['view'] = 'compose'
        st.session_state['to'] = params.get('to', '')
        st.session_state['subject'] = params.get('subject', '')
        st.session_state['body'] = params.get('body', '')
        st.rerun()

    elif action == "filter_inbox":
        query = ''
        if params.get('unread', False):
            query += 'is:unread '
        if sender := params.get('sender'):
            query += f'from:{sender} '
        if keyword := params.get('keyword'):
            query += f'{keyword} '
        if date_range := params.get('date_range', '').lower():
            if 'week' in date_range or 'this week' in date_range:
                date_str = (datetime.now() - timedelta(days=7)).strftime('%Y/%m/%d')
                query += f'after:{date_str} '
            elif '10 days' in date_range or 'last 10 days' in date_range:
                date_str = (datetime.now() - timedelta(days=10)).strftime('%Y/%m/%d')
                query += f'after:{date_str} '
        st.session_state['emails'] = list_emails(service, query=query.strip())
        st.session_state['view'] = 'inbox'
        st.rerun()

    elif action == "open_email":
        sender = params.get('sender', '')
        if sender:
            emails = list_emails(service, query=f'from:{sender}')
            if emails:
                st.session_state['current_email_id'] = emails[0]['id']
                st.session_state['view'] = 'detail'
                st.rerun()
        else:
            st.info("Could not identify which email to open.")

    elif action == "reply":
        if current_id := st.session_state.get('current_email_id'):
            detail = get_email_detail(service, current_id)
            if detail:
                st.session_state['view'] = 'compose'
                st.session_state['to'] = detail['sender']
                st.session_state['subject'] = f"Re: {detail['subject']}"
                st.session_state['body'] = f"\n\n> {detail['body'].replace('\n', '\n> ')}"
                st.rerun()

    else:
        st.info("Sorry, I didn't understand that command.")
        