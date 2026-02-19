import streamlit as st
from mail_service import get_gmail_service, list_emails, get_email_detail, send_email
from ai_assistant import parse_command
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import time

load_dotenv()

st.set_page_config(page_title="Gmail AI Assistant", page_icon="📧", layout="wide")

# Initialize session state FIRST
if 'service' not in st.session_state:
    st.session_state['service'] = get_gmail_service()
if 'view' not in st.session_state:
    st.session_state['view'] = 'inbox'
if 'emails' not in st.session_state:
    st.session_state['emails'] = list_emails(st.session_state['service'])
if 'current_email_id' not in st.session_state:
    st.session_state['current_email_id'] = None
if 'execution_log' not in st.session_state:
    st.session_state['execution_log'] = []

# Custom execute_action with detailed feedback
def execute_action_with_feedback(action_data, service):
    """Execute action and provide detailed feedback"""
    action = action_data.get("action", "unknown")
    params = action_data.get("params", {})
    
    if action == "compose":
        st.session_state['view'] = 'compose'
        st.session_state['to'] = params.get('to', '')
        st.session_state['subject'] = params.get('subject', '')
        st.session_state['body'] = params.get('body', '')
        
        if params.get('to'):
            feedback_msg = f"📝 Opening compose window for: {params.get('to')}"
        else:
            feedback_msg = "📝 Opening compose window"
        
        st.session_state['execution_log'].append(feedback_msg)
        st.rerun()

    elif action == "filter_inbox":
        query = ''
        filter_desc = []
        
        if params.get('unread', False):
            query += 'is:unread '
            filter_desc.append("unread")
            
        if sender := params.get('sender'):
            query += f'from:{sender} '
            filter_desc.append(f"from {sender}")
            
        if keyword := params.get('keyword'):
            query += f'{keyword} '
            filter_desc.append(f"containing '{keyword}'")
            
        if date_range := params.get('date_range', '').lower():
            if 'week' in date_range or 'this week' in date_range:
                date_str = (datetime.now() - timedelta(days=7)).strftime('%Y/%m/%d')
                query += f'after:{date_str} '
                filter_desc.append("from last week")
            elif '10 days' in date_range or 'last 10 days' in date_range:
                date_str = (datetime.now() - timedelta(days=10)).strftime('%Y/%m/%d')
                query += f'after:{date_str} '
                filter_desc.append("from last 10 days")
        
        st.session_state['emails'] = list_emails(service, query=query.strip())
        st.session_state['view'] = 'inbox'
        
        filter_text = ", ".join(filter_desc) if filter_desc else "all emails"
        email_count = len(st.session_state['emails'])
        feedback_msg = f"🔍 Showing {email_count} emails - Filtered by: {filter_text}"
        
        st.session_state['execution_log'].append(feedback_msg)
        st.rerun()

    elif action == "open_email":
        sender = params.get('sender', '')
        if sender:
            emails = list_emails(service, query=f'from:{sender}')
            if emails:
                st.session_state['current_email_id'] = emails[0]['id']
                st.session_state['view'] = 'detail'
                feedback_msg = f"📧 Opening latest email from {sender}"
                st.session_state['execution_log'].append(feedback_msg)
                st.rerun()
            else:
                feedback_msg = f"❌ No emails found from {sender}"
                st.session_state['execution_log'].append(feedback_msg)

    elif action == "reply":
        if current_id := st.session_state.get('current_email_id'):
            detail = get_email_detail(service, current_id)
            if detail:
                st.session_state['view'] = 'compose'
                st.session_state['to'] = detail['sender']
                st.session_state['subject'] = f"Re: {detail['subject']}"
                st.session_state['body'] = f"\n\n> {detail['body'].replace('\n', '\n> ')}"
                
                feedback_msg = f"↩️ Replying to: {detail['sender']}"
                st.session_state['execution_log'].append(feedback_msg)
                st.rerun()

    else:
        feedback_msg = f"❓ Command not recognized: {action}"
        st.session_state['execution_log'].append(feedback_msg)

# Process voice command from URL - NO SPINNER, IMMEDIATE EXECUTION
voice_cmd = st.query_params.get('voice_cmd', None)

if voice_cmd:
    # Clear the query parameter
    st.query_params.clear()
    
    try:
        # Parse immediately
        parsed = parse_command(
            voice_cmd,
            st.session_state['view'],
            st.session_state.get('current_email_id')
        )
        
        # Log what we're doing
        st.session_state['execution_log'].append(f"🎤 Voice: '{voice_cmd}' → Action: {parsed.get('action')}")
        
        # Execute immediately - this will call st.rerun()
        execute_action_with_feedback(parsed, st.session_state['service'])
        
    except Exception as e:
        st.session_state['execution_log'].append(f"❌ Voice error: {str(e)}")

# Sidebar
with st.sidebar:
    st.title("🤖 AI Email Assistant")
    st.markdown("---")

    st.subheader("🎤 Voice Commands")
    st.caption("Speak → Auto-executes instantly!")

    # Voice button
    voice_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { padding: 5px; margin: 0; font-family: sans-serif; }
            #voiceBtn {
                width: 100%;
                padding: 14px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
                font-weight: 600;
                margin-bottom: 10px;
            }
            #voiceBtn:hover { opacity: 0.9; }
            #voiceBtn.listening {
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                animation: pulse 1s infinite;
            }
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.7; }
            }
            #status {
                padding: 10px;
                background: #f0f2f6;
                border-radius: 5px;
                font-size: 13px;
                text-align: center;
            }
            .success { background: #d4edda; color: #155724; }
            .error { background: #f8d7da; color: #721c24; }
        </style>
    </head>
    <body>
        <button id="voiceBtn">🎤 Click & Speak</button>
        <div id="status">Ready</div>

        <script>
            const btn = document.getElementById('voiceBtn');
            const status = document.getElementById('status');
            
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            
            if (!SpeechRecognition) {
                status.textContent = '❌ Not supported';
                status.className = 'error';
                btn.disabled = true;
            } else {
                btn.onclick = () => {
                    const recognition = new SpeechRecognition();
                    recognition.lang = 'en-US';

                    recognition.onstart = () => {
                        btn.textContent = '🎙️ Listening...';
                        btn.classList.add('listening');
                        status.textContent = 'Speak now';
                    };

                    recognition.onresult = (e) => {
                        const text = e.results[0][0].transcript;
                        
                        btn.textContent = '✅ Executing...';
                        btn.classList.remove('listening');
                        status.innerHTML = `Heard: "${text}"`;
                        status.className = 'success';
                        
                        // Reload with voice command
                        const url = new URL(window.parent.location);
                        url.searchParams.set('voice_cmd', text);
                        window.parent.location.href = url.toString();
                    };

                    recognition.onerror = (e) => {
                        let msg = '❌ ';
                        if (e.error === 'not-allowed') msg += 'Mic blocked';
                        else if (e.error === 'no-speech') msg += 'No speech';
                        else msg += e.error;
                        
                        status.textContent = msg;
                        status.className = 'error';
                        btn.textContent = '🎤 Click & Speak';
                        btn.classList.remove('listening');
                    };

                    recognition.start();
                };
            }
        </script>
    </body>
    </html>
    """
    
    st.components.v1.html(voice_html, height=100)

    st.markdown("---")
    
    # Manual command input
    user_input = st.text_input(
        "💬 Or type command:", 
        placeholder="e.g., show unread emails",
        key="cmd_input"
    )

    # Manual execute button
    if st.button("▶️ Execute", type="primary", use_container_width=True):
        cmd = user_input.strip()
        
        if cmd:
            try:
                # Parse command
                parsed = parse_command(
                    cmd, 
                    st.session_state['view'], 
                    st.session_state.get('current_email_id')
                )
                
                st.write(f"🧠 Action: **{parsed.get('action')}**")
                
                # Execute with feedback
                execute_action_with_feedback(parsed, st.session_state['service'])
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        else:
            st.warning("⚠️ Enter a command")

    # Execution history
    if st.session_state.get('execution_log'):
        st.markdown("---")
        with st.expander("📜 Command History", expanded=True):
            for log in reversed(st.session_state['execution_log'][-10:]):
                st.text(log)
            if st.button("Clear History"):
                st.session_state['execution_log'] = []
                st.rerun()

    st.markdown("---")
    
    with st.expander("📖 Example Commands"):
        st.markdown("""
        - "show unread emails"
        - "show emails from john"
        - "compose email"
        - "compose email to john@example.com"
        - "open inbox"
        - "show sent emails"
        """)

    st.markdown("---")
    st.subheader("📂 Navigation")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 Inbox", use_container_width=True):
            st.session_state['view'] = 'inbox'
            st.session_state['emails'] = list_emails(st.session_state['service'])
            st.rerun()
        if st.button("📤 Sent", use_container_width=True):
            st.session_state['view'] = 'sent'
            st.rerun()
    with col2:
        if st.button("✉️ Compose", use_container_width=True):
            st.session_state['view'] = 'compose'
            st.rerun()
        if st.button("🔄 Refresh", use_container_width=True):
            st.session_state['emails'] = list_emails(st.session_state['service'])
            st.rerun()

# Main content
if st.session_state['view'] == 'inbox':
    st.title("📥 Inbox")
    
    if not st.session_state['emails']:
        st.info("📭 No emails")
    else:
        st.caption(f"📊 {len(st.session_state['emails'])} emails")
        for email in st.session_state['emails']:
            icon = '🔴' if email['unread'] else '✅'
            with st.expander(f"{icon} {email['sender']} - {email['subject']} ({email['date']})"):
                st.write(email['preview'])
                if st.button("📖 Open", key=f"open_{email['id']}"):
                    st.session_state['current_email_id'] = email['id']
                    st.session_state['view'] = 'detail'
                    st.rerun()

elif st.session_state['view'] == 'compose':
    st.title("✉️ Compose Email")
    
    # Show success message if we got here via voice
    if st.session_state.get('execution_log') and 'compose' in st.session_state['execution_log'][-1]:
        st.success(st.session_state['execution_log'][-1])
    
    to = st.text_input("To", st.session_state.get('to', ''), key="to")
    subject = st.text_input("Subject", st.session_state.get('subject', ''), key="subj")
    body = st.text_area("Body", st.session_state.get('body', ''), height=300, key="body")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📤 Send", type="primary", use_container_width=True):
            if to and subject:
                send_email(st.session_state['service'], to, subject, body)
                
                feedback_msg = f"📧 Email sent to: {to} | Subject: {subject}"
                st.session_state['execution_log'].append(feedback_msg)
                
                st.success(f"✅ Email sent to **{to}**")
                st.info(f"📝 Subject: {subject}")
                
                time.sleep(2)
                
                for k in ['to', 'subject', 'body']:
                    if k in st.session_state:
                        del st.session_state[k]
                
                st.session_state['view'] = 'inbox'
                st.rerun()
            else:
                st.error("❌ To and Subject required")
    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            for k in ['to', 'subject', 'body']:
                if k in st.session_state:
                    del st.session_state[k]
            st.session_state['view'] = 'inbox'
            st.rerun()

elif st.session_state['view'] == 'detail':
    st.title("📧 Email Detail")
    if st.session_state.get('current_email_id'):
        detail = get_email_detail(st.session_state['service'], st.session_state['current_email_id'])
        if detail:
            st.markdown(f"**From:** {detail['sender']}")
            st.markdown(f"**Subject:** {detail['subject']}")
            st.markdown("---")
            st.text(detail['body'])
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("↩️ Reply", type="primary", use_container_width=True):
                    st.session_state['view'] = 'compose'
                    st.session_state['to'] = detail['sender']
                    st.session_state['subject'] = f"Re: {detail['subject']}"
                    st.session_state['body'] = f"\n\n---\n> {detail['body']}"
                    st.rerun()
            with col2:
                if st.button("⬅️ Back", use_container_width=True):
                    st.session_state['view'] = 'inbox'
                    st.rerun()
        else:
            st.error("❌ Error loading email")
    else:
        st.warning("⚠️ No email selected")

elif st.session_state['view'] == 'sent':
    st.title("📤 Sent Emails")
    sent = list_emails(st.session_state['service'], label='SENT')
    if not sent:
        st.info("📭 No sent emails")
    else:
        st.caption(f"📊 {len(sent)} sent")
        for email in sent:
            with st.expander(f"✅ {email['sender']} - {email['subject']} ({email['date']})"):
                st.write(email['preview'])
                if st.button("📖 View", key=f"sent_{email['id']}"):
                    st.session_state['current_email_id'] = email['id']
                    st.session_state['view'] = 'detail'
                    st.rerun()
                    