# Gmail and Google Forms Integration Setup Guide

This guide explains how to set up the Business Evaluation System to accept submissions via Gmail and Google Forms, with automatic follow-up questions via email.

## Table of Contents

1. [Overview](#overview)
2. [Google Cloud Console Setup](#google-cloud-console-setup)
3. [Gmail Integration Setup](#gmail-integration-setup)
4. [Google Forms Integration Setup](#google-forms-integration-setup)
5. [Running the Integrations](#running-the-integrations)
6. [Configuration Options](#configuration-options)
7. [Troubleshooting](#troubleshooting)

---

## Overview

The system now supports three ways to initiate business evaluations:

1. **Direct Python API** - Programmatic evaluation (original method)
2. **Gmail Integration** - Monitor a DEDICATED email inbox for evaluation requests
3. **Google Forms Integration** - Collect structured submissions via web form

### How Gmail Integration Works

**IMPORTANT**: This system uses a **DEDICATED EMAIL ADDRESS** for evaluations.

**Setup Model**:
- Create a dedicated Gmail account (e.g., `evaluations@yourcompany.com`)
- Configure the system to monitor THAT dedicated account's inbox
- Users send evaluation requests TO: `evaluations@yourcompany.com`
- System sends follow-ups and results FROM: `evaluations@yourcompany.com` TO: original sender

**Example Flow**:
```
1. User (jane@example.com) sends email TO evaluations@yourcompany.com
2. System monitors evaluations@yourcompany.com inbox
3. System processes request from jane@example.com
4. If incomplete, system sends follow-up FROM evaluations@yourcompany.com TO jane@example.com
5. Jane replies to evaluations@yourcompany.com
6. System sends results FROM evaluations@yourcompany.com TO jane@example.com
```

When submissions are incomplete, the system can automatically:
- Identify missing information
- Generate follow-up questions
- Send questions via email to the submitter
- Process responses and continue evaluation when complete

---

## Google Cloud Console Setup

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter project name (e.g., "Business-Evaluation-System")
4. Click "Create"

### Step 2: Enable Required APIs

1. In the Cloud Console, go to "APIs & Services" → "Library"
2. Search for and enable these APIs:
   - **Gmail API** (for email integration)
   - **Google Forms API** (for form integration)
   - **Google Sheets API** (optional, for form responses in sheets)

### Step 3: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - User Type: External (for testing) or Internal (for organization)
   - App name: "Business Evaluation System"
   - User support email: Your email
   - Developer contact: Your email
   - Click "Save and Continue"
   - Scopes: Skip for now (will be requested during authentication)
   - Test users: Add your email and any other test users
   - Click "Save and Continue"
4. Back to "Create OAuth client ID":
   - Application type: **Desktop app**
   - Name: "Business Evaluation Desktop"
   - Click "Create"
5. Download the credentials JSON file
6. Rename it to `credentials.json`
7. Place it in your project root directory

**Important**: Keep `credentials.json` secure and never commit it to version control!

---

## Gmail Integration Setup

### Prerequisites

- Completed Google Cloud Console setup
- `credentials.json` in project root
- **DEDICATED Gmail account for evaluations** (e.g., evaluations@yourcompany.com)

### Important: Create a Dedicated Email Account

**DO NOT use your personal Gmail account.** Create a dedicated business email:

1. Go to [Gmail](https://mail.google.com)
2. Create a new account specifically for business evaluations
3. Example: `evaluations@yourcompany.com` or `bizeval@yourcompany.com`
4. This account will:
   - Receive evaluation requests from users
   - Send follow-up questions to users
   - Send results back to users

### Installation

Ensure Google API dependencies are installed:

```bash
pip install -r requirements.txt
```

### First-Time Authentication

The first time you run the Gmail integration, it will:

1. Open a browser window for OAuth authentication
2. **IMPORTANT**: Sign in with your DEDICATED evaluation account (evaluations@yourcompany.com)
3. Request permissions for Gmail access (read, send, modify)
4. Save an authentication token as `token.pickle`

**Note**: Future runs will use the saved token without requiring re-authentication.

### Publicizing Your Evaluation Email

Once set up, communicate the dedicated email to users:
- "Send business evaluation requests to: evaluations@yourcompany.com"
- "Include your business information and we'll evaluate it within 24 hours"
- Users send TO this address, receive responses FROM this address

### Gmail Trigger Keywords

By default, the system monitors for emails with these keywords in the subject:
- "business evaluation"
- "evaluate business"
- "business idea"
- "startup evaluation"
- "evaluate startup"

You can customize these in the script or configuration.

### Testing Gmail Integration

1. Start the monitor:
   ```bash
   python examples/gmail_monitor.py --single-run
   ```

2. Send a test email to your monitored Gmail account with:
   - Subject: "Business Evaluation Request"
   - Body: Your business description (or minimal info to test follow-ups)

3. Check the logs to see the processing

---

## Google Forms Integration Setup

### Step 1: Create Your Evaluation Form

You can create a standard business evaluation form with these questions:

1. **Business Name*** (Short answer)
2. **Your Email*** (Email)
3. **Industry/Sector*** (Short answer)
4. **Business Stage*** (Multiple choice: Idea, MVP, Early Stage, Growth)
5. **Problem Statement*** (Paragraph)
6. **Solution Description*** (Paragraph)
7. **Target Customer** (Paragraph)
8. **Unique Value Proposition** (Paragraph)
9. **Market Size (TAM/SAM/SOM)** (Paragraph)
10. **Revenue Model** (Short answer)
11. **Pricing Strategy** (Paragraph)
12. **Financial Projections** (Paragraph)
13. **Team Background** (Paragraph)
14. **Current Traction** (Paragraph)
15. **Funding Sought** (Short answer)
16. **Additional Information** (Paragraph)

*Required fields

**Form Settings:**
- Enable "Collect email addresses" (Settings → Responses)
- Optionally link to a Google Sheet for backup

### Step 2: Get Your Form ID

1. Open your form in edit mode
2. Look at the URL: `https://docs.google.com/forms/d/FORM_ID_HERE/edit`
3. Copy the `FORM_ID_HERE` part
4. Save it - you'll need it to run the monitor

### Step 3: Test Form Integration

To see the recommended form template:
```bash
python examples/forms_monitor.py --show-form-template
```

---

## Running the Integrations

### Gmail Monitor

**Continuous monitoring** (checks every 5 minutes):
```bash
python examples/gmail_monitor.py
```

**Custom check interval** (e.g., every 2 minutes):
```bash
python examples/gmail_monitor.py --interval 120
```

**Single run** (check once and exit):
```bash
python examples/gmail_monitor.py --single-run
```

**Custom credentials path**:
```bash
python examples/gmail_monitor.py --credentials /path/to/credentials.json
```

### Google Forms Monitor

**Basic usage**:
```bash
python examples/forms_monitor.py --form-id YOUR_FORM_ID
```

**Custom check interval**:
```bash
python examples/forms_monitor.py --form-id YOUR_FORM_ID --interval 120
```

**Single run**:
```bash
python examples/forms_monitor.py --form-id YOUR_FORM_ID --single-run
```

### Running as Background Service

**Using nohup** (Linux/Mac):
```bash
nohup python examples/gmail_monitor.py > gmail_monitor.log 2>&1 &
```

**Using screen** (Linux/Mac):
```bash
screen -S gmail-monitor
python examples/gmail_monitor.py
# Press Ctrl+A, then D to detach
# Use 'screen -r gmail-monitor' to reattach
```

**Using Windows Task Scheduler**:
1. Create a batch file:
   ```batch
   @echo off
   cd C:\path\to\Business-Models
   python examples\gmail_monitor.py
   ```
2. Schedule it to run at startup in Task Scheduler

---

## Configuration Options

### Environment Variables

Add to your `.env` file:

```env
# Gmail Integration
GMAIL_CHECK_INTERVAL=300                    # Seconds between checks (default: 300)
GMAIL_MAX_RESULTS=10                        # Max emails per check (default: 10)
GMAIL_WATCH_LABEL=INBOX                     # Label to monitor (default: INBOX)

# Follow-up Questions
MAX_FOLLOW_UP_ROUNDS=3                      # Max question rounds (default: 3)
FOLLOW_UP_RESPONSE_TIMEOUT_HOURS=48         # Hours to wait for response (default: 48)

# Google Forms
FORMS_CHECK_INTERVAL=300                    # Seconds between checks (default: 300)
GOOGLE_FORM_ID=your_form_id_here           # Your form ID
```

### Customizing Trigger Keywords

Edit `examples/gmail_monitor.py`:

```python
gmail = GmailIntegration(
    credentials_path=args.credentials,
    token_path=args.token,
    trigger_subject_keywords=[
        'business evaluation',
        'pitch deck review',
        'startup analysis',
        # Add your custom keywords
    ]
)
```

### Customizing Follow-up Questions

Edit `src/integrations/email_questioner.py` in the `_generate_follow_up_questions` method to customize the questions asked for missing information.

---

## Workflow Example

### Complete Submission (No Follow-up)

1. User sends email with comprehensive business description
2. System extracts information (completeness: 85%)
3. System immediately starts evaluation
4. User receives results email within 15-30 minutes

### Incomplete Submission (With Follow-up)

1. User sends email with basic business idea
2. System extracts information (completeness: 45%)
3. System identifies missing: market size, financials, team
4. System sends email with 5 follow-up questions
5. User replies with additional information
6. System re-evaluates completeness (now 82%)
7. System starts evaluation
8. User receives results email

### Multiple Follow-up Rounds

1. Initial submission (completeness: 30%)
2. Follow-up round 1 → User responds (completeness: 55%)
3. Follow-up round 2 → User responds (completeness: 78%)
4. Follow-up round 3 → User responds (completeness: 85%)
5. Evaluation starts
6. Results sent

---

## Troubleshooting

### "Credentials file not found"

**Solution**: 
1. Ensure `credentials.json` is in the project root
2. Check the path: `--credentials /correct/path/credentials.json`

### "Error 403: Access denied"

**Solution**: 
1. Verify APIs are enabled in Google Cloud Console
2. Check OAuth consent screen is configured
3. Add your test user email to the OAuth consent screen

### "Token expired" or "Invalid credentials"

**Solution**: 
1. Delete `token.pickle` and `token_forms.pickle`
2. Run the monitor again to re-authenticate
3. Ensure your OAuth credentials haven't been revoked

### "No emails found" but you sent one

**Solution**: 
1. Verify your email subject contains a trigger keyword
2. Check `--since-hours` parameter (default: 24)
3. Ensure email isn't marked as read already
4. Try `--max-results 50` to increase search limit

### "Form responses not found"

**Solution**: 
1. Verify Form ID is correct
2. Ensure Google Forms API is enabled
3. Check that form has "Collect email addresses" enabled
4. Try accessing form manually to verify permissions

### Follow-up emails not sending

**Solution**: 
1. Verify Gmail API has "send" permissions
2. Check `token.pickle` has latest scopes
3. Re-authenticate if needed
4. Check email logs for errors

### Memory/Performance Issues

**Solution**: 
1. Increase check interval: `--interval 600` (10 minutes)
2. Reduce max results: `--max-results 5`
3. Run in single-run mode via cron/scheduler
4. Clear old processed IDs periodically

---

## Security Best Practices

1. **Never commit credentials**:
   - Add to `.gitignore`:
     ```
     credentials.json
     token.pickle
     token_forms.pickle
     ```

2. **Limit OAuth scopes**:
   - Only request necessary permissions
   - Review requested scopes during authentication

3. **Rotate credentials**:
   - Periodically regenerate OAuth credentials
   - Revoke old credentials in Google Cloud Console

4. **Secure token storage**:
   - Store `token.pickle` files securely
   - Set appropriate file permissions (e.g., `chmod 600`)

5. **Monitor usage**:
   - Check Google Cloud Console for API usage
   - Set up quotas and alerts

---

## Additional Resources

- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [Google Forms API Documentation](https://developers.google.com/forms/api)
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Project README](../README.md)

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review logs in the console output
3. Open an issue on GitHub
4. Contact the development team

---

**Ready to start?** Follow the setup steps above, then run your first monitor!

```bash
# Gmail
python examples/gmail_monitor.py --single-run

# Google Forms
python examples/forms_monitor.py --form-id YOUR_FORM_ID --single-run
```
