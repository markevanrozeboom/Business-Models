"""Gmail Integration for receiving business evaluation requests via email."""

import os
import pickle
import base64
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..utils.logger import get_logger


# Gmail API scopes needed
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]


class GmailIntegration:
    """
    Gmail Integration for monitoring inbox and sending emails.
    
    This class provides functionality to:
    - Monitor Gmail inbox for business evaluation requests
    - Send follow-up questions via email
    - Mark processed emails as read
    """
    
    def __init__(
        self,
        credentials_path: str = 'credentials.json',
        token_path: str = 'token.pickle',
        watch_label: str = 'INBOX',
        trigger_subject_keywords: Optional[List[str]] = None
    ):
        """
        Initialize Gmail integration.
        
        Args:
            credentials_path: Path to OAuth 2.0 credentials JSON file
            token_path: Path to save/load OAuth token
            watch_label: Gmail label to monitor (default: INBOX)
            trigger_subject_keywords: Keywords in subject that trigger evaluation
                (e.g., ['business evaluation', 'evaluate business', 'business idea'])
        """
        self.logger = get_logger("integration.gmail")
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.watch_label = watch_label
        self.trigger_keywords = trigger_subject_keywords or [
            'business evaluation',
            'evaluate business',
            'business idea',
            'startup evaluation',
            'evaluate startup'
        ]
        
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Gmail API using OAuth 2.0."""
        creds = None
        
        # Load existing token if available
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, let user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                self.logger.info("Refreshing expired credentials")
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"Gmail credentials file not found at {self.credentials_path}. "
                        "Please download OAuth 2.0 credentials from Google Cloud Console."
                    )
                
                self.logger.info("Starting OAuth flow for Gmail authentication")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials for future use
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('gmail', 'v1', credentials=creds)
        self.logger.info("Gmail authentication successful")
    
    def check_for_new_requests(
        self,
        max_results: int = 10,
        since_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Check inbox for new business evaluation requests.
        
        Args:
            max_results: Maximum number of emails to check
            since_hours: Only check emails from the last N hours
        
        Returns:
            List of email messages with business evaluation requests
        """
        try:
            # Calculate timestamp for filtering
            since_date = datetime.utcnow() - timedelta(hours=since_hours)
            query_date = since_date.strftime('%Y/%m/%d')
            
            # Build query to find unread emails with trigger keywords
            query_parts = [
                'is:unread',
                f'after:{query_date}',
                f'label:{self.watch_label}'
            ]
            
            # Add keyword filters
            keyword_query = ' OR '.join([f'subject:"{kw}"' for kw in self.trigger_keywords])
            query_parts.append(f'({keyword_query})')
            
            query = ' '.join(query_parts)
            
            self.logger.info(f"Searching Gmail with query: {query}")
            
            # Search for matching messages
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                self.logger.info("No new business evaluation requests found")
                return []
            
            # Fetch full message details
            full_messages = []
            for msg in messages:
                full_msg = self._get_message_details(msg['id'])
                if full_msg:
                    full_messages.append(full_msg)
            
            self.logger.info(f"Found {len(full_messages)} business evaluation requests")
            return full_messages
            
        except HttpError as error:
            self.logger.error(f"Gmail API error: {error}")
            return []
    
    def _get_message_details(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full details of a specific message.
        
        Args:
            message_id: Gmail message ID
        
        Returns:
            Dictionary with message details including sender, subject, body
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            headers = message['payload']['headers']
            
            # Extract relevant headers
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
            date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
            
            # Extract message body
            body = self._extract_message_body(message['payload'])
            
            return {
                'id': message_id,
                'sender': sender,
                'subject': subject,
                'date': date,
                'body': body,
                'thread_id': message['threadId']
            }
            
        except HttpError as error:
            self.logger.error(f"Error fetching message {message_id}: {error}")
            return None
    
    def _extract_message_body(self, payload: Dict[str, Any]) -> str:
        """
        Extract plain text body from message payload.
        
        Args:
            payload: Message payload from Gmail API
        
        Returns:
            Plain text body of the message
        """
        body = ""
        
        if 'body' in payload and 'data' in payload['body']:
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        elif 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
                elif part['mimeType'] == 'multipart/alternative' and 'parts' in part:
                    # Recursively search for text/plain in multipart messages
                    body = self._extract_message_body(part)
                    if body:
                        break
        
        return body
    
    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        thread_id: Optional[str] = None
    ) -> bool:
        """
        Send an email (optionally as part of an existing thread).
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            thread_id: Optional thread ID to reply in existing conversation
        
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            
            # Create message object for Gmail API
            create_message = {
                'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()
            }
            
            # Add thread ID if replying to existing thread
            if thread_id:
                create_message['threadId'] = thread_id
            
            self.service.users().messages().send(
                userId='me',
                body=create_message
            ).execute()
            
            self.logger.info(f"Email sent to {to}: {subject}")
            return True
            
        except HttpError as error:
            self.logger.error(f"Error sending email to {to}: {error}")
            return False
    
    def mark_as_read(self, message_id: str) -> bool:
        """
        Mark a message as read.
        
        Args:
            message_id: Gmail message ID
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            
            self.logger.info(f"Message {message_id} marked as read")
            return True
            
        except HttpError as error:
            self.logger.error(f"Error marking message {message_id} as read: {error}")
            return False
    
    def add_label(self, message_id: str, label_name: str) -> bool:
        """
        Add a label to a message.
        
        Args:
            message_id: Gmail message ID
            label_name: Name of label to add
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get or create label
            label_id = self._get_or_create_label(label_name)
            
            if not label_id:
                return False
            
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'addLabelIds': [label_id]}
            ).execute()
            
            self.logger.info(f"Label '{label_name}' added to message {message_id}")
            return True
            
        except HttpError as error:
            self.logger.error(f"Error adding label to message {message_id}: {error}")
            return False
    
    def _get_or_create_label(self, label_name: str) -> Optional[str]:
        """
        Get label ID or create new label if it doesn't exist.
        
        Args:
            label_name: Name of the label
        
        Returns:
            Label ID or None if error
        """
        try:
            # Get all labels
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            
            # Check if label exists
            for label in labels:
                if label['name'] == label_name:
                    return label['id']
            
            # Create new label
            label = {
                'name': label_name,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show'
            }
            
            created_label = self.service.users().labels().create(
                userId='me',
                body=label
            ).execute()
            
            self.logger.info(f"Created new label: {label_name}")
            return created_label['id']
            
        except HttpError as error:
            self.logger.error(f"Error getting/creating label {label_name}: {error}")
            return None
