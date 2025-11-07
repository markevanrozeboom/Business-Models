"""PDF report generation utility."""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from ..models.schemas import FinalReport
from ..utils.config import settings
from ..utils.logger import get_logger

logger = get_logger("pdf_generator")


def generate_pdf_report(final_report: FinalReport, output_path: Optional[str] = None) -> str:
    """
    Generate a PDF report from FinalReport data.
    
    Args:
        final_report: FinalReport object with all report data
        output_path: Optional custom output path
        
    Returns:
        Path to generated PDF file
    """
    try:
        # Try to use reportlab if available
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
            HAS_REPORTLAB = True
        except ImportError:
            HAS_REPORTLAB = False
            logger.warning("reportlab_not_available", message="Using text-based fallback")
        
        if not HAS_REPORTLAB:
            # Fallback: create a formatted text file
            return _generate_text_report(final_report, output_path)
        
        # Generate PDF using reportlab
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Business_Evaluation_Report_{timestamp}.pdf"
            output_path = os.path.join(settings.reports_dir, filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Create PDF document
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        story = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor='#1a1a1a',
            spaceAfter=30,
            alignment=TA_CENTER,
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor='#2c3e50',
            spaceAfter=12,
            spaceBefore=20,
        )
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=10,
            textColor='#333333',
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            leading=14,
        )
        
        # Title
        story.append(Paragraph("Business Evaluation Report", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", heading_style))
        story.append(Paragraph(final_report.executive_summary.replace('\n', '<br/>'), body_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Recommendation
        story.append(Paragraph("Recommendation", heading_style))
        story.append(Paragraph(final_report.recommendation.replace('\n', '<br/>'), body_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Market Analysis
        if final_report.market_analysis:
            story.append(PageBreak())
            story.append(Paragraph("Market Analysis", heading_style))
            story.append(Paragraph(final_report.market_analysis.replace('\n', '<br/>'), body_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Business Evaluation
        if final_report.business_evaluation:
            story.append(PageBreak())
            story.append(Paragraph("Business Evaluation", heading_style))
            story.append(Paragraph(final_report.business_evaluation.replace('\n', '<br/>'), body_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Financial Analysis
        if final_report.financial_analysis:
            story.append(PageBreak())
            story.append(Paragraph("Financial Analysis", heading_style))
            story.append(Paragraph(final_report.financial_analysis.replace('\n', '<br/>'), body_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Risk Assessment
        if final_report.risk_assessment:
            story.append(PageBreak())
            story.append(Paragraph("Risk Assessment", heading_style))
            story.append(Paragraph(final_report.risk_assessment.replace('\n', '<br/>'), body_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Key Findings
        if final_report.key_findings:
            story.append(PageBreak())
            story.append(Paragraph("Key Findings", heading_style))
            for i, finding in enumerate(final_report.key_findings, 1):
                story.append(Paragraph(f"{i}. {finding}", body_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Build PDF
        doc.build(story)
        
        logger.info(
            "pdf_report_generated",
            filepath=output_path,
            submission_id=final_report.submission_id,
        )
        
        return output_path
        
    except Exception as e:
        logger.error("pdf_generation_failed", error=str(e))
        # Fallback to text report
        return _generate_text_report(final_report, output_path)


def _generate_text_report(final_report: FinalReport, output_path: Optional[str] = None) -> str:
    """Generate a formatted text report as fallback."""
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Business_Evaluation_Report_{timestamp}.txt"
        output_path = os.path.join(settings.reports_dir, filename)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("BUSINESS EVALUATION REPORT\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Submission ID: {final_report.submission_id}\n")
        f.write(f"Generated: {final_report.generated_at}\n")
        f.write(f"Overall Score: {final_report.overall_score}/10\n\n")
        f.write("=" * 80 + "\n")
        f.write("EXECUTIVE SUMMARY\n")
        f.write("=" * 80 + "\n\n")
        f.write(final_report.executive_summary + "\n\n")
        f.write("=" * 80 + "\n")
        f.write("RECOMMENDATION\n")
        f.write("=" * 80 + "\n\n")
        f.write(final_report.recommendation + "\n\n")
        
        if final_report.market_analysis:
            f.write("=" * 80 + "\n")
            f.write("MARKET ANALYSIS\n")
            f.write("=" * 80 + "\n\n")
            f.write(final_report.market_analysis + "\n\n")
        
        if final_report.business_evaluation:
            f.write("=" * 80 + "\n")
            f.write("BUSINESS EVALUATION\n")
            f.write("=" * 80 + "\n\n")
            f.write(final_report.business_evaluation + "\n\n")
        
        if final_report.financial_analysis:
            f.write("=" * 80 + "\n")
            f.write("FINANCIAL ANALYSIS\n")
            f.write("=" * 80 + "\n\n")
            f.write(final_report.financial_analysis + "\n\n")
        
        if final_report.risk_assessment:
            f.write("=" * 80 + "\n")
            f.write("RISK ASSESSMENT\n")
            f.write("=" * 80 + "\n\n")
            f.write(final_report.risk_assessment + "\n\n")
        
        if final_report.key_findings:
            f.write("=" * 80 + "\n")
            f.write("KEY FINDINGS\n")
            f.write("=" * 80 + "\n\n")
            for i, finding in enumerate(final_report.key_findings, 1):
                f.write(f"{i}. {finding}\n")
            f.write("\n")
    
    logger.info(
        "text_report_generated",
        filepath=output_path,
        submission_id=final_report.submission_id,
    )
    
    return output_path

