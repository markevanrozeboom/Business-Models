# Gmail & Google Forms Integration Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Business Evaluation System                        │
│                   with Gmail & Forms Integration                     │
└─────────────────────────────────────────────────────────────────────┘

                              INPUT SOURCES
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌──────────────┐          ┌──────────────┐          ┌──────────────┐
│  Direct API  │          │    Gmail     │          │ Google Forms │
│              │          │  Integration │          │ Integration  │
│  Python API  │          │              │          │              │
│  (original)  │          │  Monitor     │          │  Monitor     │
└──────────────┘          │  Inbox       │          │  Form        │
        │                 │              │          │  Responses   │
        │                 └──────────────┘          └──────────────┘
        │                         │                         │
        │                         └─────────┬───────────────┘
        │                                   │
        │                                   ▼
        │                         ┌──────────────────┐
        │                         │ Email Questioner │
        │                         │                  │
        │                         │ • Completeness   │
        │                         │   Analysis       │
        │                         │ • Follow-up      │
        │                         │   Questions      │
        │                         │ • Thread         │
        │                         │   Management     │
        │                         └──────────────────┘
        │                                   │
        └───────────────────┬───────────────┘
                            │
                            ▼
                ┌─────────────────────────┐
                │  Intake Agent           │
                │                         │
                │  Extract & Structure    │
                │  Business Information   │
                └─────────────────────────┘
                            │
                            ▼
                ┌─────────────────────────┐
                │  Orchestrator Agent     │
                │                         │
                │  Workflow Management    │
                └─────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Research   │    │  Analysis   │    │  Financial  │
│   Agent     │    │   Agent     │    │    Agent    │
└─────────────┘    └─────────────┘    └─────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                ┌─────────────────────────┐
                │  Validation Agent       │
                │                         │
                │  Quality Checks         │
                └─────────────────────────┘
                            │
                            ▼
                ┌─────────────────────────┐
                │  Synthesis Agent        │
                │                         │
                │  Final Report           │
                └─────────────────────────┘
                            │
                            ▼
                       OUTPUT FILES
                     (JSON, Excel, etc.)
                            │
                            ▼
                ┌─────────────────────────┐
                │  Email Results          │
                │  to Submitter           │
                └─────────────────────────┘
```

## Integration Flow Diagram

### Complete Submission (80%+ completeness)

```
User Email/Form
      │
      ▼
Extract Info ──→ Completeness: 85%
      │
      ▼
Start Evaluation
      │
      ▼
Generate Reports
      │
      ▼
Email Results
```

### Incomplete Submission (with Follow-ups)

```
User Email/Form
      │
      ▼
Extract Info ──→ Completeness: 45%
      │
      ▼
Identify Missing Info
      │
      ▼
Generate Questions
      │
      ▼
Send Email Follow-up (Round 1)
      │
      ▼
Wait for Response
      │
      ▼
User Replies
      │
      ▼
Merge & Re-extract ──→ Completeness: 68%
      │
      ▼
Still < 80%? ──→ Send Follow-up (Round 2)
      │               │
      │               ▼
      │         Wait for Response
      │               │
      │               ▼
      │         User Replies
      │               │
      │               ▼
      │         Merge & Re-extract ──→ Completeness: 82%
      │               │
      ▼               ▼
Now >= 80%! ────────┘
      │
      ▼
Start Evaluation
      │
      ▼
Generate Reports
      │
      ▼
Email Results
```

## Module Responsibilities

### Gmail Integration (`gmail_integration.py`)
- **Purpose**: Interface with Gmail API
- **Key Functions**:
  - Authenticate via OAuth 2.0
  - Monitor inbox for trigger keywords
  - Fetch unread messages
  - Parse email content (text/html)
  - Send emails
  - Reply to existing threads
  - Mark as read
  - Add labels

### Google Forms Integration (`google_forms_integration.py`)
- **Purpose**: Interface with Google Forms API
- **Key Functions**:
  - Authenticate via OAuth 2.0
  - Fetch form responses
  - Parse form data
  - Alternative: Read from Google Sheets
  - Format as business description
  - Provide form template

### Email Questioner (`email_questioner.py`)
- **Purpose**: Manage interactive follow-up conversations
- **Key Functions**:
  - Analyze submission completeness
  - Identify missing information categories:
    - Business overview
    - Solution description
    - Market information
    - Revenue model
    - Pricing strategy
    - Financial projections
    - Team information
  - Generate targeted questions
  - Send follow-up emails
  - Track conversation threads
  - Merge responses with original data
  - Handle multi-round conversations

## Data Flow

### Email Processing

```
Gmail Message
    │
    ├─ Headers (from, subject, date)
    │
    ├─ Body (text/html/multipart)
    │
    └─ Thread ID
          │
          ▼
Email Questioner
    │
    ├─ Extract business info
    │
    ├─ Calculate completeness
    │
    └─ Decide: Complete or Follow-up?
          │
          ├─ Complete ──→ Start Evaluation
          │
          └─ Incomplete ──→ Send Questions
                              │
                              └─ Track in active_conversations
```

### Form Processing

```
Google Form Response
    │
    ├─ Response ID
    │
    ├─ Email address
    │
    ├─ Timestamp
    │
    └─ Answers (key-value pairs)
          │
          ▼
Format as Description
    │
    ├─ Map questions to fields
    │
    └─ Create text description
          │
          ▼
Email Questioner
    │
    └─ (same flow as email)
```

## Configuration Options

### Environment Variables
```env
# Gmail Integration
GMAIL_CHECK_INTERVAL=300          # Check every 5 minutes
GMAIL_MAX_RESULTS=10              # Max emails per check
GMAIL_WATCH_LABEL=INBOX           # Label to monitor

# Follow-up Questions  
MAX_FOLLOW_UP_ROUNDS=3            # Max question rounds
FOLLOW_UP_RESPONSE_TIMEOUT_HOURS=48  # Response timeout

# Google Forms
GOOGLE_FORM_ID=your_form_id       # Form to monitor
```

### Command-Line Arguments

**Gmail Monitor**:
```bash
--credentials PATH      # OAuth credentials file
--token PATH           # Token cache file
--interval SECONDS     # Check interval
--max-results N        # Max emails per check
--single-run          # Check once and exit
```

**Forms Monitor**:
```bash
--form-id ID          # Google Form ID
--credentials PATH    # OAuth credentials file
--token PATH         # Token cache file
--interval SECONDS   # Check interval
--single-run        # Check once and exit
--show-form-template # Show form template
```

## File Structure

```
Business-Models/
├── src/
│   └── integrations/
│       ├── __init__.py
│       ├── gmail_integration.py       (Gmail API wrapper)
│       ├── google_forms_integration.py (Forms API wrapper)
│       └── email_questioner.py        (Follow-up logic)
│
├── examples/
│   ├── gmail_monitor.py              (Gmail daemon)
│   └── forms_monitor.py              (Forms daemon)
│
├── tests/
│   └── test_integrations.py          (Unit tests)
│
├── INTEGRATION_SETUP.md              (Detailed setup guide)
├── INTEGRATION_QUICKSTART.md         (Quick reference)
└── credentials.json.example          (OAuth template)
```

## Security Architecture

### Authentication Flow
```
First Run:
  1. Read credentials.json (OAuth client ID/secret)
  2. Open browser for user consent
  3. User authorizes application
  4. Save token to token.pickle
  
Subsequent Runs:
  1. Load token from token.pickle
  2. If expired, refresh automatically
  3. If invalid, re-authenticate
```

### Scopes Required

**Gmail API**:
- `gmail.readonly` - Read messages
- `gmail.send` - Send emails
- `gmail.modify` - Mark as read, add labels

**Google Forms API**:
- `forms.responses.readonly` - Read form responses
- `spreadsheets.readonly` - Read linked sheets (optional)

### Security Best Practices
- ✅ OAuth 2.0 (no passwords stored)
- ✅ Token files gitignored
- ✅ Credentials never committed
- ✅ Minimal scopes requested
- ✅ Token refresh automatic
- ✅ Local-only token storage

## Error Handling

### Gmail Integration
- **No credentials**: Clear error message with setup instructions
- **Authentication failed**: Delete token and retry
- **API rate limit**: Automatic retry with backoff
- **Network error**: Log and continue on next interval
- **Parse error**: Skip message and continue

### Google Forms Integration
- **Invalid Form ID**: Clear error message
- **No responses**: Log and continue monitoring
- **Parse error**: Skip response and continue
- **Sheet not found**: Fall back to Forms API

### Email Questioner
- **Incomplete after max rounds**: Proceed with what we have
- **Response timeout**: Mark conversation as stale
- **Invalid response**: Parse best effort, send clarification
- **Thread lost**: Create new thread if needed

## Performance Considerations

### Monitoring Efficiency
- **Default interval**: 5 minutes (300 seconds)
- **Faster for testing**: 30-60 seconds
- **Production**: 5-10 minutes optimal
- **Background mode**: Use nohup or systemd

### API Quotas
- **Gmail API**: 1 billion quota units/day (plenty)
- **Forms API**: 600 read requests/minute
- **Rate limiting**: Built-in retry with exponential backoff

### Resource Usage
- **Memory**: ~50-100 MB per monitor process
- **CPU**: Minimal (mostly waiting)
- **Network**: Minimal (only API calls)
- **Disk**: Logs and token files (~1 MB)

## Monitoring & Logs

### What Gets Logged
- Authentication events
- New messages/responses detected
- Completeness calculations
- Follow-up questions sent
- Evaluation start/completion
- Errors and warnings

### Log Levels
- **INFO**: Normal operations
- **WARNING**: Recoverable issues
- **ERROR**: Failed operations
- **DEBUG**: Detailed flow (development)

### Example Log Output
```
[INFO] Gmail monitor initialized successfully
[INFO] Checking for new business evaluation requests...
[INFO] Found 2 business evaluation requests
[INFO] Processing message from user@example.com: Business Evaluation Request
[INFO] Initial submission completeness: 45%
[INFO] Incomplete submission. Follow-up questions sent.
[INFO] Check complete. Processed 2 new requests
```

## Future Enhancements

### Potential Features
- [ ] Webhook support for real-time notifications
- [ ] Slack integration
- [ ] Microsoft Teams integration
- [ ] SMS notifications via Twilio
- [ ] Web dashboard for monitoring
- [ ] Admin panel for template management
- [ ] Automated A/B testing of question templates
- [ ] Analytics on completion rates
- [ ] Multi-language support

---

**Architecture Version**: 1.0  
**Last Updated**: November 2024  
**Components**: 3 integration modules, 2 monitor scripts, comprehensive documentation
