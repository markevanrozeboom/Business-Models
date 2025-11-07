#!/bin/bash

# Robust evaluation runner
cd /Users/markrozeboom/Business-Models
source venv/bin/activate

echo "🚀 Starting California Sports Academies Evaluation..."
echo "This will take 10-15 minutes to complete."
echo "=================================================="
echo ""

# Run the evaluation
python examples/run_evaluation.py

echo ""
echo "=================================================="
echo "✅ Evaluation Complete!"
echo ""
echo "Check the following directories for results:"
echo "  - outputs/    (workflow state JSON files)"
echo "  - models/     (Excel financial models)"
echo "  - reports/    (evaluation reports)"
