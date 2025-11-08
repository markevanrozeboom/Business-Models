# 🚀 Agentic Business Evaluation System

> **An automated business idea evaluation and financial modeling system using specialized AI agents powered by Claude.**

Transform business ideas into comprehensive investment reports in minutes, not days. This system uses 6 specialized AI agents working together to provide VC-quality analysis with market research, financial modeling, and strategic recommendations.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Quick Start Guide](#quick-start-guide)
- [System Architecture](#system-architecture)
- [Installation](#installation)
- [Usage Guide](#usage-guide)
- [Gmail & Google Forms Integration](#gmail--google-forms-integration)
- [Configuration](#configuration)
- [Understanding the Workflow](#understanding-the-workflow)
- [Output Files](#output-files)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)
- [Development](#development)
- [FAQ](#faq)

---

## 🎯 Overview

### What This System Does

The Agentic Business Evaluation System automatically evaluates business ideas by:

1. **Gathering** comprehensive business information through structured interviews
2. **Researching** market dynamics and competitive landscape
3. **Analyzing** business viability using professional VC/PE frameworks
4. **Modeling** financial projections with unit economics and scenarios
5. **Validating** all outputs for consistency and quality
6. **Synthesizing** everything into executive-ready reports

### Who Should Use This

- **Venture Capitalists** evaluating deal flow
- **Entrepreneurs** validating business ideas
- **Incubators/Accelerators** screening applications
- **Corporate Innovation Teams** assessing new ventures
- **Business Consultants** conducting market analysis

### Key Benefits

✅ **Speed**: 5-15 minutes vs. days of manual analysis
✅ **Consistency**: Standardized evaluation framework every time
✅ **Comprehensiveness**: Market research + financials + risk assessment in one
✅ **Quality**: VC-grade analysis with confidence scoring
✅ **Scalability**: Evaluate hundreds of ideas efficiently
✅ **Multiple Input Methods**: Accept submissions via Python API, Gmail, or Google Forms
✅ **Interactive Follow-ups**: Automatically asks for missing information via email

---

## ⚡ Quick Start Guide

### 1. Get Your API Key

1. Sign up at [Anthropic Console](https://console.anthropic.com/)
2. Navigate to API Keys section
3. Create a new API key
4. Save it securely (you'll need it in step 4)

### 2. Clone the Repository

```bash
git clone https://github.com/your-username/Business-Models.git
cd Business-Models
```

### 3. Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate          # Mac/Linux
# OR
venv\Scripts\activate              # Windows

# Verify activation
which python                       # Mac/Linux
# OR
where python                       # Windows
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure API Key

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file and add your API key
# Mac/Linux:
nano .env

# Windows:
notepad .env
```

Add this line to `.env`:
```
ANTHROPIC_API_KEY=sk-ant-your-actual-api-key-here
```

### 6. Run Your First Evaluation

```bash
python examples/run_evaluation.py
```

This runs an evaluation on the example business (CloudSync Pro) and generates:
- Comprehensive analysis report
- Financial model (Excel spreadsheet)
- Workflow state (JSON)

**Expected Runtime**: 5-15 minutes
**Expected Cost**: $1-3 in API calls

---

## 🏗️ System Architecture

### The Agent Hierarchy

```
                    ┌─────────────────────────────────┐
                    │    ORCHESTRATOR AGENT           │
                    │  (Workflow Management)          │
                    └─────────────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│ INTAKE AGENT  │       │RESEARCH AGENT │       │ANALYSIS AGENT │
│               │       │               │       │               │
│ Gathers info  │       │ Market data   │       │ VC-style      │
│ Validates     │       │ Competitors   │       │ evaluation    │
│ completeness  │       │ Benchmarks    │       │ Risk scoring  │
└───────────────┘       └───────────────┘       └───────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                        ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│FINANCIAL AGENT│       │VALIDATION     │       │SYNTHESIS AGENT│
│               │       │AGENT          │       │               │
│ P&L models    │       │               │       │ Final report  │
│ Unit econ     │       │ Quality checks│       │ Executive     │
│ Scenarios     │       │ Confidence    │       │ summary       │
└───────────────┘       └───────────────┘       └───────────────┘
```

### Agent Roles

| Agent | Purpose | Key Outputs |
|-------|---------|-------------|
| **Orchestrator** | Coordinates workflow, manages handoffs | Workflow state, audit trail |
| **Intake** | Structured information gathering | Complete business submission (JSON) |
| **Research** | Market & competitive intelligence | Market brief, 5-10 comparables |
| **Analysis** | Business model evaluation | Scorecard, risk matrix |
| **Financial** | Financial modeling | 3-year projections (Excel), unit economics |
| **Validation** | Quality assurance | Validation report, confidence scores |
| **Synthesis** | Report generation | Executive summary, final report |

---

## 💿 Installation

### Prerequisites Checklist

- [ ] Python 3.10 or higher installed
- [ ] pip package manager available
- [ ] Git installed
- [ ] Anthropic API account created
- [ ] API key obtained

### Detailed Installation Steps

#### Step 1: Verify Python Version

```bash
python --version
# Should show: Python 3.10.x or higher
```

If you need to install Python:
- **Mac**: `brew install python@3.10`
- **Windows**: Download from [python.org](https://www.python.org/downloads/)
- **Linux**: `sudo apt install python3.10`

#### Step 2: Clone Repository

```bash
git clone https://github.com/your-username/Business-Models.git
cd Business-Models
```

#### Step 3: Create Virtual Environment

**Why?** Isolates project dependencies from your system Python.

```bash
# Create venv
python3 -m venv venv

# Activate
source venv/bin/activate          # Mac/Linux
venv\Scripts\activate              # Windows

# Confirm activation (should show venv path)
which python
```

#### Step 4: Install Dependencies

```bash
# Upgrade pip first (recommended)
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

**Expected packages**: anthropic, pydantic, pandas, openpyxl, and more.

#### Step 5: Environment Configuration

```bash
# Copy template
cp .env.example .env

# Edit with your favorite editor
nano .env        # or vim, code, notepad, etc.
```

**Required configuration**:
```env
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
```

**Optional configurations** (with defaults):
```env
# Model settings
DEFAULT_MODEL=claude-sonnet-4-5-20250929
DEFAULT_MAX_TOKENS=4096
DEFAULT_TEMPERATURE=0.7

# Thresholds
COMPLETENESS_THRESHOLD=80       # Intake completeness required
CONFIDENCE_THRESHOLD=70         # Below this triggers human review

# Output directories
OUTPUT_DIR=./outputs
REPORTS_DIR=./reports
MODELS_DIR=./models

# Logging
LOG_LEVEL=INFO
ENVIRONMENT=development
```

#### Step 6: Verify Installation

```bash
# Run test suite
pytest

# Should see: X passed in Y seconds
```

---

## 📘 Usage Guide

### Method 1: Run Example Evaluation

**Easiest way to get started:**

```bash
python examples/run_evaluation.py
```

**What happens:**
1. Loads example business (CloudSync Pro) from `examples/example_submission.txt`
2. Runs complete 7-phase evaluation workflow
3. Generates outputs in `outputs/`, `models/`, `reports/` directories
4. Prints comprehensive summary to console

**Timeline:**
- Phase 1 (Intake): ~30 seconds
- Phase 2 (Research/Analysis): ~3-5 minutes
- Phase 3 (Financial): ~2-3 minutes
- Phase 4 (Validation): ~1-2 minutes
- Phase 5 (Synthesis): ~2-3 minutes
- **Total**: 5-15 minutes

### Method 2: Python API

**For programmatic use:**

```python
from src.workflow import BusinessEvaluationWorkflow

# Initialize workflow engine
workflow = BusinessEvaluationWorkflow()

# Your business description
business_description = """
We're building XYZ Corp - a SaaS platform for [target market]...

[Include: problem, solution, market, team, traction, financials]
"""

# Run evaluation
result = workflow.evaluate_business(
    business_description=business_description,
    save_results=True  # Saves to disk
)

# Check status
if result.is_complete:
    print("✅ Evaluation complete!")
    workflow.print_summary(result)

    # Access specific sections
    print(f"\nOverall Score: {result.final_report.overall_score}/10")
    print(f"Recommendation: {result.final_report.recommendation}")

    for finding in result.final_report.key_findings:
        print(f"  • {finding}")

elif result.requires_human_review:
    print("⚠️  Requires human review")
    print(f"Reason: {result.validation_report.human_review_reason}")

else:
    print("❌ Evaluation failed")
    print(f"Error: {result.error_message}")

# Get workflow summary
summary = workflow.get_workflow_summary(result)
print(f"\nDuration: {summary['duration_seconds']:.1f} seconds")
print(f"Validation confidence: {summary['validation_confidence']}%")
```

### Method 3: Command Line Interface

**For quick evaluations:**

```bash
# Direct text input
python -m src.workflow "We're building a B2B SaaS platform..."

# From file
python -m src.workflow --file my_business.txt

# With custom output directory
OUTPUT_DIR=./my_outputs python -m src.workflow --file input.txt
```

### Method 4: Custom Integration

**Integrate into your own application:**

```python
from src.agents.orchestrator import OrchestratorAgent
from src.models.schemas import WorkflowState

# Create orchestrator
orchestrator = OrchestratorAgent()

# Run workflow
workflow_state = orchestrator.execute_workflow(business_description)

# Access results programmatically
if workflow_state.business_analysis:
    score = workflow_state.business_analysis.overall_score
    risks = workflow_state.business_analysis.risks

if workflow_state.financial_model:
    base_case = workflow_state.financial_model.scenarios[1]
    revenue_y3 = base_case.year3_revenue
```

---

## 📧 Gmail & Google Forms Integration

### NEW: Accept Submissions via Email and Web Forms!

The system now supports receiving business evaluation requests through:
- **Gmail** - Monitor your inbox for evaluation requests
- **Google Forms** - Collect structured submissions via web form

When submissions are incomplete, the system automatically:
- Identifies missing information
- Generates follow-up questions
- Sends questions via email
- Processes responses when complete

### Quick Setup

1. **Enable APIs** in Google Cloud Console:
   - Gmail API
   - Google Forms API

2. **Download OAuth credentials** as `credentials.json`

3. **Run Gmail Monitor**:
   ```bash
   python examples/gmail_monitor.py
   ```

4. **Or Run Google Forms Monitor**:
   ```bash
   python examples/forms_monitor.py --form-id YOUR_FORM_ID
   ```

📖 **Full Setup Guide**: See [INTEGRATION_SETUP.md](INTEGRATION_SETUP.md) for detailed instructions.

### Example Email Submission

Send an email to your monitored Gmail account with:

**Subject**: Business Evaluation Request

**Body**:
```
Business Name: TechFlow AI
Industry: B2B SaaS
Problem: Sales teams waste 20 hours/week on manual data entry
Solution: AI-powered sales automation platform
Target Market: Mid-market B2B companies ($10M-$500M revenue)
Revenue Model: $199/user/month subscription
Team: 3 technical co-founders with 10+ years experience
Seeking: $2M seed round
```

The system will:
1. Process your submission
2. Ask follow-up questions if needed (via email)
3. Run the complete evaluation
4. Send you the results via email

---

## ⚙️ Configuration

### Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | *Required* | Your Anthropic API key |
| `DEFAULT_MODEL` | `claude-sonnet-4-5-20250929` | Claude model to use |
| `DEFAULT_MAX_TOKENS` | `4096` | Max tokens per response |
| `DEFAULT_TEMPERATURE` | `0.7` | Temperature for generation |
| `COMPLETENESS_THRESHOLD` | `80` | Min completeness to proceed (%) |
| `CONFIDENCE_THRESHOLD` | `70` | Min confidence before human review (%) |
| `ENABLE_HUMAN_REVIEW` | `true` | Whether to check for human review |
| `OUTPUT_DIR` | `./outputs` | Workflow state output directory |
| `REPORTS_DIR` | `./reports` | Reports output directory |
| `MODELS_DIR` | `./models` | Financial models directory |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `ENVIRONMENT` | `development` | Environment name |

### Agent Configuration (YAML)

Edit `configs/agent_config.yaml` to customize agent behavior:

```yaml
# Example: Make Research Agent more thorough
research:
  name: "Research Agent"
  model: "claude-sonnet-4-5-20250929"
  max_tokens: 12000                    # Increase for more detail
  temperature: 0.3                     # Lower for more factual
  min_comparable_companies: 8          # Find more comparables
  max_comparable_companies: 15

# Example: Make Analysis more conservative
analysis:
  temperature: 0.2                     # More consistent scoring
  evaluation_dimensions:
    - name: "Team Quality"
      weight: 0.25                     # Increase team importance
    - name: "Market Opportunity"
      weight: 0.25
```

---

## 🔄 Understanding the Workflow

### The 7 Phases Explained

#### Phase 1: Intake (Structured Information Gathering)

**Duration**: 30 seconds - 2 minutes
**Agent**: Intake Agent

**What happens:**
1. Receives your business description
2. Extracts structured information:
   - Business overview (name, industry, stage, problem, solution)
   - Value proposition and differentiators
   - Market information (TAM/SAM/SOM)
   - Business model (revenue, pricing, costs)
   - Financial projections
   - Team composition and traction
3. Calculates completeness score (0-100%)
4. Must achieve 80%+ to proceed

**Output**: `BusinessSubmission` object with all gathered data

**Tips for best results:**
- Provide comprehensive business description upfront
- Include specific numbers (revenue, market size, team size)
- Mention competitors and differentiators
- Describe traction and milestones

#### Phase 2: Research & Analysis (Parallel Execution)

**Duration**: 3-7 minutes
**Agents**: Research Agent + Analysis Agent (run simultaneously)

##### Research Agent:
- Searches for market data and trends
- Identifies 5-10 comparable companies
- Gathers industry benchmarks (CAC, LTV, margins, growth rates)
- Assesses opportunities and threats

**Output**: `MarketResearch` with competitive landscape

##### Analysis Agent:
- Scores business across 6 dimensions:
  1. Team Quality (20% weight)
  2. Market Opportunity (25% weight)
  3. Product/Solution (20% weight)
  4. Business Model (15% weight)
  5. Competitive Position (10% weight)
  6. Traction/Validation (10% weight)
- Calculates weighted overall score (0-10)
- Identifies and categorizes risks
- Provides strategic recommendations

**Output**: `BusinessAnalysis` with scorecard and risk matrix

#### Phase 3: Financial Modeling

**Duration**: 2-4 minutes
**Agent**: Financial Modeling Agent

**What happens:**
1. Builds 3-year monthly P&L projections
2. Calculates unit economics:
   - CAC (Customer Acquisition Cost)
   - LTV (Lifetime Value)
   - LTV:CAC ratio (target: >3x)
   - Payback period (target: <12 months)
   - Contribution margin
   - Gross margin
3. Creates 3 scenarios:
   - **Optimistic**: Strong execution, 70th percentile
   - **Base**: Expected case, 50th percentile
   - **Pessimistic**: Challenges occur, 30th percentile
4. Generates Excel spreadsheet with formulas

**Output**: `FinancialModel` + Excel file with projections

**Excel sheets included:**
- Summary: Business overview + unit economics
- Scenarios: Side-by-side scenario comparison
- Unit Economics: Detailed calculations

#### Phase 4: Validation

**Duration**: 1-3 minutes
**Agent**: Validation Agent

**Quality checks performed:**

1. **Financial Consistency**
   - Revenue/cost/profit calculations correct
   - Unit economics internally consistent
   - Growth rates realistic for stage/industry
   - Margins within industry norms

2. **Data Quality**
   - Sources are real and verifiable
   - Companies mentioned exist
   - Metrics are realistic
   - No hallucinations detected

3. **Reasonableness Tests**
   - Market size claims (TAM > SAM > SOM)
   - Growth projections appropriate for stage
   - Unit economics match benchmarks
   - Risk assessments are appropriate

4. **Cross-referencing**
   - Analysis aligns with research
   - Financials match analysis assumptions
   - No contradictions across outputs

**Output**: `ValidationReport` with confidence scores

**Human review triggered if:**
- Overall confidence < 70%
- Critical issues found
- Significant inconsistencies detected
- Sources unverifiable

#### Phase 5: Synthesis

**Duration**: 2-4 minutes
**Agent**: Synthesis Agent

**What happens:**
1. Aggregates findings from all agents
2. Generates executive summary (1-2 pages):
   - Bottom-line recommendation (INVEST/PASS/MONITOR)
   - Overall score and justification
   - 3-5 key findings
   - Critical risks
   - Next steps
3. Creates detailed sections:
   - Market Analysis
   - Business Evaluation
   - Financial Analysis
   - Risk Assessment
4. Compiles all sources and audit trail

**Output**: `FinalReport` ready for executive review

#### Phase 6: Human Review (Conditional)

**When triggered:**
- Validation confidence < threshold
- Critical issues flagged
- User manually requests review

**Reviewer actions:**
- Examine flagged sections
- Approve as-is
- Request agent modifications
- Override specific conclusions
- Add commentary

#### Phase 7: Delivery

**Final deliverables:**
1. **Workflow State JSON** - Complete audit trail
2. **Financial Model Excel** - Interactive spreadsheet
3. **Final Report** - Structured analysis
4. **Console Summary** - Key findings

---

## 📦 Output Files

### 1. Workflow State JSON

**Location**: `outputs/workflow_<id>_<timestamp>.json`

**Contents:**
```json
{
  "submission_id": "abc-123-def",
  "current_phase": "completed",
  "is_complete": true,
  "business_submission": { ... },
  "market_research": { ... },
  "business_analysis": { ... },
  "financial_model": { ... },
  "validation_report": { ... },
  "final_report": { ... },
  "phase_history": [ ... ]
}
```

**Use for:**
- Programmatic access to all data
- Audit trail
- Re-processing
- Integration with other systems

### 2. Financial Model Excel

**Location**: `models/<business_name>_<timestamp>.xlsx`

**Sheets:**

1. **Summary**
   - Business overview
   - Unit economics (CAC, LTV, ratios)
   - Key metrics

2. **Scenarios**
   - Side-by-side comparison
   - Optimistic / Base / Pessimistic
   - Year 1-3 revenue, costs, profit

3. **Unit Economics**
   - Detailed calculations
   - Assumptions documented
   - Benchmarks included

**Features:**
- All formulas intact
- Easy to modify assumptions
- Professional formatting

### 3. Final Report (in JSON)

**Structure:**
```json
{
  "executive_summary": "...",
  "recommendation": "INVEST / PASS / MONITOR",
  "overall_score": 7.5,
  "market_analysis": "...",
  "business_evaluation": "...",
  "financial_analysis": "...",
  "risk_assessment": "...",
  "key_findings": ["...", "..."],
  "critical_assumptions": ["...", "..."],
  "next_steps": ["...", "..."]
}
```

---

## 💡 Examples

### Example 1: SaaS Business

See `examples/example_submission.txt` for CloudSync Pro - a complete B2B SaaS evaluation.

Run it:
```bash
python examples/run_evaluation.py
```

### Example 2: Minimal Input

```python
from src.workflow import BusinessEvaluationWorkflow

workflow = BusinessEvaluationWorkflow()

# Even minimal input works (agents will ask questions)
result = workflow.evaluate_business("""
FitTrack: Mobile app for personalized fitness coaching using AI.
Target: Health-conscious millennials.
Revenue: $10/month subscription.
Team: 3 co-founders (fitness + tech backgrounds).
Seeking: $500K seed round.
""")

workflow.print_summary(result)
```

### Example 3: Batch Processing

```python
from src.workflow import BusinessEvaluationWorkflow
import json

workflow = BusinessEvaluationWorkflow()

# Load multiple businesses
with open('batch_submissions.json', 'r') as f:
    businesses = json.load(f)

results = []
for biz in businesses:
    result = workflow.evaluate_business(biz['description'])
    results.append({
        'name': biz['name'],
        'score': result.final_report.overall_score if result.final_report else 0,
        'recommendation': result.final_report.recommendation if result.final_report else 'N/A'
    })

# Sort by score
results.sort(key=lambda x: x['score'], reverse=True)

print("\n📊 BATCH EVALUATION RESULTS")
for r in results:
    print(f"{r['name']}: {r['score']:.1f}/10 - {r['recommendation']}")
```

---

## 🔧 Troubleshooting

### Common Issues

#### Issue: "ModuleNotFoundError: No module named 'anthropic'"

**Solution:**
```bash
# Verify venv is activated
which python  # Should show venv path

# Reinstall dependencies
pip install -r requirements.txt
```

#### Issue: "Error: ANTHROPIC_API_KEY not found"

**Solution:**
```bash
# Check .env file exists
ls -la .env

# Verify key is set
cat .env | grep ANTHROPIC_API_KEY

# If missing, add it:
echo "ANTHROPIC_API_KEY=your-key-here" >> .env
```

#### Issue: "Rate limit exceeded" (429 error)

**Solution:**
```bash
# The system will retry automatically
# To reduce rate limits, decrease parallelism:

# Edit src/agents/orchestrator.py
# Comment out parallel execution, run sequentially instead
```

#### Issue: "Timeout after 5 minutes"

**Solution:**
```bash
# Increase timeout in .env
echo "AGENT_TIMEOUT=600" >> .env

# Or in code:
from src.utils.config import settings
settings.agent_timeout = 600
```

#### Issue: Low confidence scores

**Causes:**
- Insufficient business information provided
- Vague or generic descriptions
- Missing key data (financials, market size, etc.)

**Solution:**
- Provide more detailed business description
- Include specific numbers and metrics
- Mention competitors and differentiators
- Describe team experience and traction

#### Issue: Excel file not generated

**Solution:**
```bash
# Check openpyxl is installed
pip list | grep openpyxl

# Reinstall if needed
pip install openpyxl

# Check models directory exists and is writable
mkdir -p models
chmod 755 models
```

### Debug Mode

Enable detailed logging:

```bash
# Set in .env
LOG_LEVEL=DEBUG

# Or in code
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Getting Help

1. **Check logs**: Look in console output for error details
2. **Review outputs**: Check `outputs/` directory for workflow state
3. **Test connection**: Verify Anthropic API key works:
   ```python
   from anthropic import Anthropic
   client = Anthropic(api_key="your-key")
   response = client.messages.create(
       model="claude-sonnet-4-5-20250929",
       max_tokens=100,
       messages=[{"role": "user", "content": "Hi"}]
   )
   print(response.content[0].text)
   ```
4. **Run tests**: `pytest -v` to verify installation
5. **Open issue**: Report bugs on GitHub with logs

---

## 🚀 Advanced Usage

### Customizing Agent Behavior

#### Example: More Conservative Analysis

```yaml
# configs/agent_config.yaml
analysis:
  temperature: 0.1              # Very consistent
  evaluation_dimensions:
    - name: "Team Quality"
      weight: 0.30              # Emphasize team more
    - name: "Traction/Validation"
      weight: 0.20              # Emphasize proven traction
```

#### Example: Deeper Research

```python
from src.agents.research import ResearchAgent

# Override defaults
research = ResearchAgent()
research.max_tokens = 16000     # More detailed analysis
research.min_comparable_companies = 10
```

### Custom Workflow Modifications

```python
from src.agents.orchestrator import OrchestratorAgent

class CustomOrchestrator(OrchestratorAgent):
    def execute_workflow(self, initial_submission):
        # Add custom pre-processing
        enhanced_submission = self.preprocess(initial_submission)

        # Run standard workflow
        result = super().execute_workflow(enhanced_submission)

        # Add custom post-processing
        result = self.postprocess(result)

        return result
```

### Integration Examples

#### Slack Bot

```python
from slack_bolt import App
from src.workflow import BusinessEvaluationWorkflow

app = App(token=os.environ["SLACK_BOT_TOKEN"])
workflow = BusinessEvaluationWorkflow()

@app.command("/evaluate")
def evaluate_business(ack, command, say):
    ack()
    say("🔄 Evaluating your business... This takes 5-15 minutes.")

    result = workflow.evaluate_business(command['text'])

    if result.is_complete:
        say(f"✅ Evaluation complete!\n"
            f"Score: {result.final_report.overall_score}/10\n"
            f"Recommendation: {result.final_report.recommendation}")
    else:
        say("❌ Evaluation failed. Please try again.")
```

#### REST API

```python
from fastapi import FastAPI
from src.workflow import BusinessEvaluationWorkflow

app = FastAPI()
workflow = BusinessEvaluationWorkflow()

@app.post("/evaluate")
async def evaluate_endpoint(description: str):
    result = workflow.evaluate_business(description)
    return {
        "status": "complete" if result.is_complete else "incomplete",
        "score": result.final_report.overall_score if result.final_report else None,
        "recommendation": result.final_report.recommendation if result.final_report else None
    }
```

---

## 🛠️ Development

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html
open htmlcov/index.html

# Specific test
pytest tests/test_agents.py::TestIntakeAgent::test_completeness_calculation

# Verbose
pytest -v -s
```

### Code Quality

```bash
# Format code
black src/ tests/

# Check formatting
black --check src/

# Lint
flake8 src/ tests/

# Type check
mypy src/
```

### Adding New Agents

1. Create file: `src/agents/my_agent.py`
2. Inherit from `BaseAgent`
3. Implement required methods
4. Add to orchestrator
5. Add tests
6. Update config

---

## ❓ FAQ

**Q: How much does it cost to run?**
A: ~$1-3 per evaluation, depending on input size and model usage.

**Q: How long does it take?**
A: 5-15 minutes end-to-end, depending on API latency.

**Q: Can I use it offline?**
A: No, requires internet connection for Anthropic API.

**Q: Is the data secure?**
A: Data is sent to Anthropic's API. Review their [privacy policy](https://www.anthropic.com/privacy).

**Q: Can I customize the evaluation criteria?**
A: Yes! Edit `configs/agent_config.yaml` to adjust weights and parameters.

**Q: Does it actually search the web?**
A: Currently uses Claude's training data. Web search integration is on the roadmap.

**Q: Can I evaluate multiple businesses at once?**
A: Yes, see "Batch Processing" example above.

**Q: What if the evaluation is wrong?**
A: Human review recommended for decisions. Use confidence scores as guidance.

---

## 📄 License

[Specify your license here]

## 🤝 Contributing

Contributions welcome! Please see CONTRIBUTING.md for guidelines.

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/Business-Models/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/Business-Models/discussions)
- **Email**: support@your-domain.com

---

## 🙏 Acknowledgments

Built with:
- [Anthropic Claude](https://www.anthropic.com/claude) - AI foundation
- [Pydantic](https://pydantic.dev/) - Data validation
- [OpenPyXL](https://openpyxl.readthedocs.io/) - Excel generation
- [pytest](https://pytest.org/) - Testing framework

---

**Ready to evaluate your first business?** 🚀

```bash
python examples/run_evaluation.py
```
