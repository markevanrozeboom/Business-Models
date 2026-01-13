# Quick Reference: Gmail & Google Forms Integration

## Quick Start

### 1. Gmail Integration - Monitor DEDICATED Email Inbox

**IMPORTANT**: Use a DEDICATED email account (e.g., evaluations@yourcompany.com)

```bash
# First time setup (one-time)
# 1. Create dedicated Gmail account (evaluations@yourcompany.com)
# 2. Download credentials.json from Google Cloud Console
# 3. Place in project root
# 4. Run script and authenticate with DEDICATED account

# Run the monitor
python examples/gmail_monitor.py

# Or check once and exit
python examples/gmail_monitor.py --single-run
```

**Users send evaluation requests TO**: evaluations@yourcompany.com
- **Subject**: "Business Evaluation Request"  
- **Body**: Their business description

**System responds FROM**: evaluations@yourcompany.com
- Follow-up questions sent to original sender
- Results sent to original sender

### 2. Google Forms Integration - Web Form Submissions

```bash
# First time setup
# 1. Create a Google Form for business evaluations
# 2. Get the Form ID from URL: /d/FORM_ID/edit
# 3. Download credentials.json (same as Gmail)

# Run the monitor
python examples/forms_monitor.py --form-id YOUR_FORM_ID

# Or check once and exit
python examples/forms_monitor.py --form-id YOUR_FORM_ID --single-run
```

---

## How It Works

### Complete Submission Flow
```
User sends email/form → System extracts info (85% complete) 
→ Evaluation starts immediately → Results sent via email
```

### Incomplete Submission Flow (with Follow-ups)
```
User sends email/form → System extracts info (45% complete)
→ System identifies missing: financials, team, market size
→ System sends email with 5 follow-up questions
→ User replies with answers
→ System re-checks (now 82% complete)
→ Evaluation starts → Results sent via email
```

---

## Configuration

### Gmail Trigger Keywords

Emails with these keywords in subject trigger evaluation:
- "business evaluation"
- "evaluate business"  
- "business idea"
- "startup evaluation"
- "evaluate startup"

### Check Intervals

```bash
# Every 5 minutes (default)
python examples/gmail_monitor.py

# Every 10 minutes
python examples/gmail_monitor.py --interval 600

# Every 30 seconds (testing)
python examples/gmail_monitor.py --interval 30
```

### Follow-up Question Limits

By default:
- **Max rounds**: 3 follow-up question rounds
- **Timeout**: 48 hours to respond
- **Threshold**: 80% completeness required

Configure in code:
```python
questioner = EmailQuestioner(
    gmail_integration=gmail,
    max_follow_up_rounds=5,      # More rounds
    response_timeout_hours=72    # Longer timeout
)
```

---

## Common Commands

### Gmail Monitor

```bash
# Continuous monitoring (production)
python examples/gmail_monitor.py

# Single check (testing)
python examples/gmail_monitor.py --single-run

# Custom credentials location
python examples/gmail_monitor.py --credentials /path/to/creds.json

# More frequent checks
python examples/gmail_monitor.py --interval 60

# Background mode (Linux/Mac)
nohup python examples/gmail_monitor.py > gmail.log 2>&1 &
```

### Google Forms Monitor

```bash
# Continuous monitoring
python examples/forms_monitor.py --form-id ABC123

# Single check
python examples/forms_monitor.py --form-id ABC123 --single-run

# Show form template
python examples/forms_monitor.py --show-form-template

# Custom check interval
python examples/forms_monitor.py --form-id ABC123 --interval 120
```

---

## Files Created

### Gmail Integration
- `credentials.json` - OAuth credentials (from Google Cloud Console)
- `token.pickle` - Saved authentication token
- `gmail_monitor.log` - Log file (if using nohup)

### Google Forms Integration  
- `credentials.json` - OAuth credentials (same file as Gmail)
- `token_forms.pickle` - Saved authentication token
- `processed_responses.json` - Tracks processed form submissions

**All credential files are gitignored automatically!**

---

## Troubleshooting

### "No emails found"
- Check subject has a trigger keyword
- Email must be unread in the dedicated account's inbox
- Try `--since-hours 48` to look further back
- Verify you're monitoring the correct dedicated account

### "Authentication failed"
- Delete `token.pickle` and re-authenticate
- **IMPORTANT**: Authenticate with your DEDICATED evaluation account, not personal account
- Verify credentials.json is valid
- Check APIs are enabled in Google Cloud Console

### "Wrong account authenticated"
- Delete `token.pickle`
- Run monitor again
- When browser opens, sign in with DEDICATED account (evaluations@yourcompany.com)

### "Form responses not found"
- Verify Form ID is correct (from URL)
- Enable "Collect email addresses" in form settings
- Ensure Google Forms API is enabled

### "Follow-up emails not sending"
- Check Gmail API has "send" permission
- Verify token.pickle has correct scopes
- Re-authenticate if needed

---

## Email Format Examples

### Minimal Email (will trigger follow-up)
```
Subject: Business Evaluation Request

Business: QuickShip
We're building same-day delivery for local businesses.
```

### Complete Email (no follow-up needed)
```
Subject: Evaluate my startup

Business Name: QuickShip  
Industry: Logistics Tech
Stage: MVP with 10 pilot customers

Problem: Local businesses lose sales due to slow delivery.
Customers want same-day, get 3-5 days.

Solution: AI-powered routing platform connecting local businesses
with gig drivers for same-day delivery.

Target: Small retailers ($1M-$10M revenue) in major metros
Market: $50B last-mile delivery market, targeting $1B SAM

Revenue: $2/delivery + $99/month platform fee
Pricing: Businesses pay, we take 20% of delivery fee

Financials: 
- Year 1: $500K revenue, 100 businesses
- Year 2: $2M revenue, 500 businesses  
- Year 3: $5M revenue, 1,500 businesses
- Gross margin: 40%

Team: 
- CEO: 10 years logistics at Amazon
- CTO: Ex-Uber engineer
- COO: Retail operations expert

Traction: 10 pilot customers, $20K MRR, 85% retention

Seeking: $1.5M seed to expand to 3 cities
```

---

## Security Notes

✅ Credentials are OAuth 2.0 - no passwords stored  
✅ Tokens saved locally, never committed to git  
✅ All credential files auto-gitignored  
✅ Scopes limited to only what's needed  
⚠️ Keep credentials.json secure  
⚠️ Don't share token files

---

## Support

📖 Full Setup Guide: [INTEGRATION_SETUP.md](INTEGRATION_SETUP.md)  
📖 Main Documentation: [README.md](README.md)  
🐛 Issues: [GitHub Issues](https://github.com/markevanrozeboom/Business-Models/issues)

---

**Ready to go?** 

```bash
python examples/gmail_monitor.py --single-run
```
