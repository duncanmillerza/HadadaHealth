"""
PDF Export Module for Clinical Reports

Provides PDF generation functionality for AI-powered clinical reports
using ReportLab with professional medical document formatting.
"""
import json
from io import BytesIO
from datetime import datetime
from typing import Dict, Any, List, Optional

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from modules.database import get_report_by_id, get_report_templates
from modules.data_aggregation import get_patient_data_summary


class ReportPDFGenerator:
    """Generator for professional medical report PDFs"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom styles for medical reports"""
        # Header style
        self.styles.add(ParagraphStyle(
            name='ReportHeader',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            textColor=colors.HexColor('#2D6356'),  # HadadaHealth brand color
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subheader style
        self.styles.add(ParagraphStyle(
            name='ReportSubHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=15,
            spaceAfter=10,
            textColor=colors.HexColor('#2D6356'),
            fontName='Helvetica-Bold'
        ))
        
        # Body text style
        self.styles.add(ParagraphStyle(
            name='ReportBody',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=14,
            spaceBefore=6,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            fontName='Helvetica'
        ))
        
        # AI-generated content style
        self.styles.add(ParagraphStyle(
            name='AIGeneratedContent',
            parent=self.styles['ReportBody'],
            leftIndent=10,
            rightIndent=10,
            borderWidth=1,
            borderColor=colors.HexColor('#E8F4F1'),
            borderPadding=8,
            backColor=colors.HexColor('#F8FDF9')
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='ReportFooter',
            parent=self.styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER,
            textColor=colors.gray,
            fontName='Helvetica-Oblique'
        ))
    
    def generate_report_pdf(self, report_id: int) -> BytesIO:
        """
        Generate a PDF for a specific report
        
        Args:
            report_id: ID of the report to export
            
        Returns:
            BytesIO buffer containing the PDF
        """
        # Get report data
        report = get_report_by_id(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")
        
        # Get template information
        templates = get_report_templates()
        template = next((t for t in templates if t['id'] == report['template_id']), None)
        
        # Get patient data
        patient_summary = None
        try:
            disciplines = json.loads(report['disciplines']) if isinstance(report['disciplines'], str) else report['disciplines']
            patient_summary = get_patient_data_summary(report['patient_id'], disciplines)
        except Exception as e:
            print(f"Could not load patient summary: {e}")
        
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2.5*cm,
            bottomMargin=2*cm
        )
        
        # Build document content
        story = []
        
        # Header
        self._add_header(story, report, template)
        
        # Patient information
        if patient_summary:
            self._add_patient_info(story, patient_summary)
        
        # Report content
        self._add_report_content(story, report, template)
        
        # AI-generated sections
        if report.get('ai_generated_sections'):
            self._add_ai_generated_content(story, report)
        
        # Footer
        self._add_footer(story, report)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return buffer
    
    def _add_header(self, story: List, report: Dict[str, Any], template: Optional[Dict[str, Any]]):
        """Add report header"""
        # Practice header
        story.append(Paragraph("HadadaHealth Clinical Report", self.styles['ReportHeader']))
        story.append(Spacer(1, 0.3*inch))
        
        # Report title
        story.append(Paragraph(report['title'], self.styles['Heading1']))
        story.append(Spacer(1, 0.2*inch))
        
        # Report metadata table
        metadata = [
            ['Report ID:', str(report['id'])],
            ['Report Type:', report['report_type'].replace('_', ' ').title()],
            ['Status:', report['status'].replace('_', ' ').title()],
            ['Created:', self._format_date(report.get('created_at'))],
            ['Template:', template['name'] if template else 'Unknown'],
        ]
        
        if report.get('deadline_date'):
            metadata.append(['Deadline:', self._format_date(report['deadline_date'])])
        
        metadata_table = Table(metadata, colWidths=[2*inch, 3*inch])
        metadata_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F8F9FA')),
        ]))
        
        story.append(metadata_table)
        story.append(Spacer(1, 0.3*inch))
    
    def _add_patient_info(self, story: List, patient_summary):
        """Add patient information section"""
        story.append(Paragraph("Patient Information", self.styles['ReportSubHeader']))
        
        demographics = patient_summary.demographics
        if demographics:
            patient_info = [
                ['Patient ID:', patient_summary.patient_id],
                ['Name:', demographics.get('name', 'Not available')],
                ['Date of Birth:', demographics.get('date_of_birth', 'Not available')],
                ['Gender:', demographics.get('gender', 'Not available')],
            ]
            
            if demographics.get('medical_aid'):
                patient_info.append(['Medical Aid:', demographics['medical_aid']])
            
            if demographics.get('primary_diagnosis'):
                patient_info.append(['Primary Diagnosis:', demographics['primary_diagnosis']])
            
            patient_table = Table(patient_info, colWidths=[2*inch, 3.5*inch])
            patient_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F8F9FA')),
            ]))
            
            story.append(patient_table)
        
        # Disciplines involved
        if patient_summary.disciplines_involved:
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(
                f"<b>Disciplines Involved:</b> {', '.join(patient_summary.disciplines_involved)}", 
                self.styles['ReportBody']
            ))
        
        story.append(Spacer(1, 0.2*inch))
    
    def _add_report_content(self, story: List, report: Dict[str, Any], template: Optional[Dict[str, Any]]):
        """Add main report content"""
        story.append(Paragraph("Report Content", self.styles['ReportSubHeader']))
        
        # Parse report content
        content = {}
        if report.get('content'):
            try:
                content = json.loads(report['content']) if isinstance(report['content'], str) else report['content']
            except json.JSONDecodeError:
                content = {'raw_content': report['content']}
        
        if content:
            for field_id, field_value in content.items():
                if field_value:
                    # Format field name
                    field_name = field_id.replace('_', ' ').title()
                    story.append(Paragraph(f"<b>{field_name}:</b>", self.styles['ReportSubHeader']))
                    
                    # Add field content
                    if isinstance(field_value, str):
                        story.append(Paragraph(field_value, self.styles['ReportBody']))
                    else:
                        story.append(Paragraph(str(field_value), self.styles['ReportBody']))
                    
                    story.append(Spacer(1, 0.1*inch))
        else:
            story.append(Paragraph("No content available for this report.", self.styles['ReportBody']))
        
        story.append(Spacer(1, 0.2*inch))
    
    def _add_ai_generated_content(self, story: List, report: Dict[str, Any]):
        """Add AI-generated content sections"""
        story.append(Paragraph("AI-Generated Content", self.styles['ReportSubHeader']))
        
        ai_sections = {}
        try:
            ai_sections = json.loads(report['ai_generated_sections']) if isinstance(report['ai_generated_sections'], str) else report['ai_generated_sections']
        except json.JSONDecodeError:
            pass
        
        if ai_sections:
            for section_type, section_data in ai_sections.items():
                # Section header
                section_title = section_type.replace('_', ' ').title()
                story.append(Paragraph(f"<b>{section_title}</b>", self.styles['ReportSubHeader']))
                
                # AI content with special styling
                if isinstance(section_data, dict) and 'content' in section_data:
                    content = section_data['content']
                    story.append(Paragraph(content, self.styles['AIGeneratedContent']))
                    
                    # Add generation metadata
                    if section_data.get('generated_at'):
                        story.append(Paragraph(
                            f"<i>Generated on: {self._format_date(section_data['generated_at'])}</i>",
                            self.styles['ReportFooter']
                        ))
                else:
                    story.append(Paragraph(str(section_data), self.styles['AIGeneratedContent']))
                
                story.append(Spacer(1, 0.15*inch))
        else:
            story.append(Paragraph("No AI-generated content available.", self.styles['ReportBody']))
        
        story.append(Spacer(1, 0.2*inch))
    
    def _add_footer(self, story: List, report: Dict[str, Any]):
        """Add report footer"""
        story.append(Spacer(1, 0.3*inch))
        
        # Assigned therapists
        assigned_therapists = []
        try:
            assigned_therapists = json.loads(report['assigned_therapist_ids']) if isinstance(report['assigned_therapist_ids'], str) else report['assigned_therapist_ids']
        except json.JSONDecodeError:
            pass
        
        if assigned_therapists:
            story.append(Paragraph(
                f"<b>Assigned Therapists:</b> {', '.join(assigned_therapists)}", 
                self.styles['ReportBody']
            ))
        
        # Report generation info
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(
            f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by HadadaHealth AI Report System",
            self.styles['ReportFooter']
        ))
        
        # Compliance disclaimer
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(
            "This report contains confidential patient information protected under POPIA and applicable healthcare privacy laws.",
            self.styles['ReportFooter']
        ))
    
    def _format_date(self, date_string: Optional[str]) -> str:
        """Format date string for display"""
        if not date_string:
            return "Not specified"
        
        try:
            # Try different date formats
            for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S']:
                try:
                    dt = datetime.strptime(date_string.split('.')[0].split('T')[0] if 'T' in date_string else date_string, fmt.split(' ')[0])
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            return date_string  # Return as-is if parsing fails
        except Exception:
            return "Invalid date"


class ReportPDFService:
    """Service for managing PDF export operations"""
    
    def __init__(self):
        self.generator = ReportPDFGenerator()
    
    def export_report_as_pdf(self, report_id: int) -> BytesIO:
        """
        Export a report as PDF
        
        Args:
            report_id: ID of the report to export
            
        Returns:
            BytesIO buffer containing the PDF
        """
        return self.generator.generate_report_pdf(report_id)
    
    def get_pdf_filename(self, report_id: int) -> str:
        """
        Generate appropriate filename for PDF export
        
        Args:
            report_id: Report ID
            
        Returns:
            Suggested filename
        """
        report = get_report_by_id(report_id)
        if not report:
            return f"report_{report_id}.pdf"
        
        # Sanitize title for filename
        safe_title = "".join(c for c in report['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_')[:50]  # Limit length
        
        timestamp = datetime.now().strftime('%Y%m%d')
        return f"{safe_title}_{timestamp}_report_{report_id}.pdf"


# Global service instance
pdf_service = ReportPDFService()


def export_report_pdf(report_id: int) -> BytesIO:
    """
    Convenience function to export report as PDF
    
    Args:
        report_id: Report ID
        
    Returns:
        PDF buffer
    """
    return pdf_service.export_report_as_pdf(report_id)


def get_report_pdf_filename(report_id: int) -> str:
    """
    Convenience function to get PDF filename
    
    Args:
        report_id: Report ID
        
    Returns:
        Filename
    """
    return pdf_service.get_pdf_filename(report_id)