# Agentic Business Evaluation System

An automated business idea evaluation and financial modeling system using specialized AI agents powered by Claude. Target completion: 72 hours from submission to final report.

## Overview

This system uses a hierarchical supervisor pattern where one orchestrator agent manages 6 specialized worker agents that handle different parts of business analysis:

- **Intake Agent**: Structured information gathering and validation
- **Research Agent**: Market analysis and competitive intelligence
- **Analysis Agent**: Business model evaluation using VC/PE frameworks
- **Financial Modeling Agent**: 3-year projections and unit economics
- **Validation Agent**: Quality checks and consistency validation
- **Synthesis Agent**: Final report generation

## Architecture

```
┌─────────────────────────────────────────────────────┐
│              Orchestrator Agent                      │
│    (Workflow Management & Coordination)              │
└─────────────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   ┌────▼────┐     ┌────▼────┐     ┌────▼────┐
   │ Intake  │     │Research │     │Analysis │
   │  Agent  │     │  Agent  │     │  Agent  │
   └─────────┘     └─────────┘     └─────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   ┌────▼────┐     ┌────▼────┐     ┌────▼────┐
   │Financial│     │Validation│    │Synthesis│
   │  Agent  │     │  Agent  │     │  Agent  │
   └─────────┘     └─────────┘     └─────────┘
```

## 7-Phase Workflow

### Phase 1: Intake
- Conducts structured interview to gather business information
- Validates completeness (80%+ required to proceed)
- Outputs: Structured JSON with all business parameters

### Phase 2: Research & Analysis (Parallel)
- **Research**: Market analysis, competitive intelligence, comparable companies
- **Analysis**: VC-style evaluation with scoring across 6 dimensions
- Outputs: Market research brief + business model scorecard

### Phase 3: Financial Modeling
- Builds 3-year P&L projections
- Calculates unit economics (CAC, LTV, payback, margins)
- Creates scenario analysis (optimistic, base, pessimistic)
- Outputs: Excel spreadsheet with formulas + scenario comparison

### Phase 4: Validation
- Cross-checks financial consistency
- Validates assumptions against benchmarks
- Performs reasonableness tests
- Flags low-confidence outputs for human review
- Outputs: Validation report + confidence scores

### Phase 5: Synthesis
- Aggregates all findings into cohesive deliverable
- Generates executive summary with recommendations
- Creates detailed analysis sections
- Outputs: Final report (PDF-ready format)

### Phase 6: Human Review (if needed)
- Triggered if confidence score < threshold or critical issues found
- Reviewer can approve, request modifications, or override

### Phase 7: Delivery
- Final PDF report
- Excel financial model
- Audit trail of sources and assumptions

## Installation

### Prerequisites
- Python 3.10+
- Anthropic API key

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd Business-Models
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

## Usage

### Quick Start

Run an evaluation with the example business:

```bash
python examples/run_evaluation.py
```

### Using the Python API

```python
from src.workflow import BusinessEvaluationWorkflow

# Initialize workflow
workflow = BusinessEvaluationWorkflow()

# Provide business description
business_description = """
We are building CloudSync Pro - a B2B SaaS platform that helps
mid-market companies synchronize their data across multiple cloud
applications in real-time...
"""

# Run evaluation
result = workflow.evaluate_business(business_description)

# Print summary
workflow.print_summary(result)

# Access detailed results
if result.final_report:
    print(result.final_report.executive_summary)
    print(f"Overall Score: {result.final_report.overall_score}/10")
```

### Using the Command Line

```bash
# From a string
python -m src.workflow "Your business description here"

# From a file
python -m src.workflow --file path/to/business_description.txt
```

## Configuration

### Environment Variables

Create a `.env` file with the following:

```env
# Required
ANTHROPIC_API_KEY=your_api_key_here

# Optional (with defaults)
DEFAULT_MODEL=claude-sonnet-4-5-20250929
DEFAULT_MAX_TOKENS=4096
DEFAULT_TEMPERATURE=0.7

LOG_LEVEL=INFO
ENVIRONMENT=development

COMPLETENESS_THRESHOLD=80
CONFIDENCE_THRESHOLD=70
ENABLE_HUMAN_REVIEW=true

OUTPUT_DIR=./outputs
REPORTS_DIR=./reports
MODELS_DIR=./models
```

### Agent Configuration

Customize agent behavior in `configs/agent_config.yaml`:

```yaml
intake:
  model: "claude-sonnet-4-5-20250929"
  temperature: 0.7
  completeness_threshold: 80

research:
  max_tokens: 8000
  min_comparable_companies: 5
```

## Project Structure

```
Business-Models/
├── src/
│   ├── agents/           # Agent implementations
│   │   ├── base.py       # Base agent class
│   │   ├── intake.py     # Intake agent
│   │   ├── research.py   # Research agent
│   │   ├── analysis.py   # Analysis agent
│   │   ├── financial.py  # Financial modeling agent
│   │   ├── validation.py # Validation agent
│   │   ├── synthesis.py  # Synthesis agent
│   │   └── orchestrator.py # Orchestrator
│   ├── models/           # Data models
│   │   └── schemas.py    # Pydantic schemas
│   ├── utils/            # Utilities
│   │   ├── config.py     # Configuration
│   │   └── logger.py     # Logging setup
│   └── workflow.py       # Main workflow runner
├── configs/              # Configuration files
│   └── agent_config.yaml
├── examples/             # Example usage
│   ├── example_submission.txt
│   └── run_evaluation.py
├── tests/                # Test suite
│   ├── test_models.py
│   └── test_agents.py
├── outputs/              # Workflow state outputs (generated)
├── reports/              # Final reports (generated)
├── models/               # Financial models (generated)
├── requirements.txt      # Python dependencies
├── pyproject.toml        # Project metadata
└── README.md             # This file
```

## Output Files

The system generates several output files:

1. **Workflow State** (`outputs/workflow_<id>_<timestamp>.json`)
   - Complete workflow state with all intermediate results
   - JSON format for programmatic access

2. **Financial Model** (`models/<business>_<timestamp>.xlsx`)
   - Excel spreadsheet with projections
   - Multiple sheets: Summary, Scenarios, Unit Economics
   - Formulas intact for easy modification

3. **Final Report** (structured data in workflow state)
   - Executive summary
   - Detailed analysis sections
   - Key findings and recommendations

## Data Models

### BusinessSubmission
Complete business information collected during intake:
- Business overview (name, industry, stage, problem, solution)
- Value proposition and differentiators
- Market information (TAM/SAM/SOM)
- Business model (revenue, pricing, costs)
- Financial projections
- Team composition and traction

### MarketResearch
Market analysis output:
- Market overview and trends
- Competitive landscape
- 5-10 comparable companies with metrics
- Industry benchmarks (CAC, LTV, margins)
- Opportunities and threats

### BusinessAnalysis
VC-style evaluation:
- Scores across 6 dimensions (0-10 scale)
- Overall weighted score
- Unit economics assessment
- Risk matrix with mitigations
- Strategic recommendations

### FinancialModel
Financial projections:
- 3 scenarios (optimistic, base, pessimistic)
- Unit economics (CAC, LTV, payback, margins)
- Key financial drivers
- Sensitivity analysis

### ValidationReport
Quality assurance:
- Overall validation status
- List of issues found
- Confidence scores by section
- Human review flag and reason

### FinalReport
Synthesis output:
- Executive summary
- Recommendation (INVEST/PASS/MONITOR)
- Detailed analysis sections
- Key findings and next steps
- Audit trail

## Testing

Run the test suite:

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/test_models.py

# With verbose output
pytest -v
```

## Development

### Code Style

This project uses:
- **Black** for code formatting
- **Flake8** for linting
- **MyPy** for type checking

Run formatters and linters:

```bash
# Format code
black src/ tests/

# Lint
flake8 src/ tests/

# Type check
mypy src/
```

### Adding New Agents

To add a new specialized agent:

1. Create new file in `src/agents/`
2. Inherit from `BaseAgent`
3. Implement `get_system_prompt()` and `process()` methods
4. Add to orchestrator workflow
5. Update configuration in `configs/agent_config.yaml`

Example:

```python
from .base import BaseAgent
from ..models.schemas import AgentType, AgentResponse

class MyNewAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_type=AgentType.CUSTOM,
            temperature=0.5,
        )

    def get_system_prompt(self) -> str:
        return "You are an expert in..."

    def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        # Implementation
        pass
```

## Performance

Expected performance metrics:
- **Latency**: 5-15 minutes end-to-end (depending on API latency)
- **Cost**: ~$1-3 per evaluation (varies with model and input size)
- **Accuracy**: 70-90% confidence scores typical for quality outputs

## Limitations

- Requires comprehensive initial business description for best results
- Market research limited to Claude's knowledge + available context
- Financial projections are estimates based on industry benchmarks
- Human review recommended for investment decisions

## Roadmap

- [ ] Add real-time web search integration for market research
- [ ] Implement iterative conversation for intake phase
- [ ] Generate PDF reports with visualizations
- [ ] Add support for follow-up questions and refinements
- [ ] Build interactive dashboard for scenario exploration
- [ ] Add Monte Carlo simulation for sensitivity analysis
- [ ] Implement comparison mode for multiple business ideas

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run the test suite
5. Submit a pull request

## License

[Specify your license]

## Support

For issues or questions:
- Open an issue on GitHub
- Check the documentation
- Review example usage in `examples/`

## Acknowledgments

Built with:
- [Anthropic Claude](https://www.anthropic.com/claude) - AI models
- [Pydantic](https://pydantic.dev/) - Data validation
- [FastAPI](https://fastapi.tiangolo.com/) - API framework (optional)
- [OpenPyXL](https://openpyxl.readthedocs.io/) - Excel generation
