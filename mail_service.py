import os
import pickle
import base64
from email.mime.text import MIMEText
from datetime import datetime
import streamlit as st
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.cloud import pubsub_v1

# Scopes for Gmail API
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_gmail_service():
    """Authenticate and return Gmail API service"""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return build('gmail', 'v1', credentials=creds)


def list_emails(service, label='INBOX', query='', max_results=20):
    """
    List emails with sender, subject, preview, date, unread status.
    Uses format='metadata' to get headers without full body.
    """
    try:
        results = service.users().messages().list(
            userId='me',
            labelIds=[label],
            q=query,
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        emails = []
        
        for msg in messages:
            # Use 'metadata' format to include headers
            msg_data = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata'
            ).execute()
            
            # Extract headers safely
            headers = msg_data.get('payload', {}).get('headers', [])
            
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            date_raw = msg_data.get('internalDate', '0')
            date = datetime.fromtimestamp(int(date_raw) / 1000).strftime('%Y-%m-%d %H:%M')
            
            emails.append({
                'id': msg['id'],
                'sender': sender,
                'subject': subject,
                'preview': msg_data.get('snippet', '(No preview available)'),
                'date': date,
                'unread': 'UNREAD' in msg_data.get('labelIds', [])
            })
        
        return emails
    
    except HttpError as e:
        st.error(f"Error listing emails: {e}")
        return []
    except Exception as e:
        st.error(f"Unexpected error in list_emails: {e}")
        return []


def get_email_detail(service, msg_id):
    """Get full content of a single email"""
    try:
        msg = service.users().messages().get(
            userId='me',
            id=msg_id,
            format='full'
        ).execute()
        
        payload = msg.get('payload', {})
        headers = payload.get('headers', [])
        
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        
        # Extract body (prefer plain text)
        body = ''
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    break
        else:
            data = payload.get('body', {}).get('data', '')
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        return {
            'sender': sender,
            'subject': subject,
            'body': body or '(No content available)'
        }
    
    except HttpError as e:
        st.error(f"Error reading email {msg_id}: {e}")
        return None
    except Exception as e:
        st.error(f"Unexpected error in get_email_detail: {e}")
        return None


def send_email(service, to, subject, body):
    """Send a plain text email"""
    try:
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body = {'raw': raw}
        
        sent_message = service.users().messages().send(
            userId='me',
            body=body
        ).execute()
        
        st.success(f"Email sent successfully! Message ID: {sent_message['id']}")
    
    except HttpError as e:
        st.error(f"Error sending email: {e}")
    except Exception as e:
        st.error(f"Unexpected error sending email: {e}")


def setup_push_notifications(service, project_id, topic_name='gmail-notifications'):
    """Set up Gmail push notifications via Pub/Sub"""
    try:
        request = {
            'labelIds': ['INBOX'],
            'labelFilterBehavior': 'INCLUDE',
            'topicName': f'projects/{project_id}/topics/{topic_name}'
        }
        response = service.users().watch(userId='me', body=request).execute()
        st.info("Push notifications watch setup successful.")
        return response
    except HttpError as e:
        st.error(f"Error setting up Gmail watch: {e}")
        return None
    