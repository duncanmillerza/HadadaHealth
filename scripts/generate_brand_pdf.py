from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib import colors
from reportlab.lib.units import inch
import os


def build_brand_pdf(output_path: str):
    doc = SimpleDocTemplate(output_path, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=42, bottomMargin=42)
    styles = getSampleStyleSheet()

    title = ParagraphStyle('Title', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=20, leading=24, spaceAfter=12)
    h1 = ParagraphStyle('H1', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=14, leading=18, spaceBefore=12, spaceAfter=6)
    h2 = ParagraphStyle('H2', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, leading=16, spaceBefore=10, spaceAfter=4)
    body = ParagraphStyle('Body', parent=styles['BodyText'], fontName='Helvetica', fontSize=10.5, leading=14, alignment=TA_LEFT, spaceAfter=6)
    small = ParagraphStyle('Small', parent=styles['BodyText'], fontName='Helvetica-Oblique', fontSize=9, leading=12, textColor=colors.grey)

    story = []

    # Logo if available
    logo_path_png = os.path.join('static', 'logo_small_green.png')
    if os.path.exists(logo_path_png):
        story.append(Image(logo_path_png, width=96, height=96))
        story.append(Spacer(1, 12))

    story.append(Paragraph('HadadaHealth Brand Style Guide', title))
    story.append(Paragraph('Version: 2025-08-30', small))

    # Brand Overview
    story.append(Paragraph('Brand Overview', h1))
    story.append(Paragraph('HadadaHealth is a healthcare management platform for therapists. It streamlines clinical operations and documentation (appointments, treatment notes, AI report writing, billing) with a focus on trust, efficiency, and POPIA-compliant workflows for multi-disciplinary practices.', body))

    # Core Values
    story.append(Paragraph('Core Values', h1))
    values = [
        'Clinical accuracy: evidence‑based, clear, editable AI assistance for reports',
        'Efficiency: reduce admin overhead, fast flows, sensible defaults',
        'Trust & privacy: POPIA compliance, audit trails, role‑based permissions',
        'Collaboration: multi‑disciplinary workflows and therapist coordination',
    ]
    for v in values:
        story.append(Paragraph(f'• {v}', body))

    # Voice & Tone
    story.append(Paragraph('Voice & Tone', h1))
    tone = [
        'Professional and clinical, precise, no slang',
        'Empathetic and patient‑centered where relevant',
        'Clear and action‑oriented; scannable structure',
        'Compliance‑aware: avoid absolute medical claims; include review/approval prompts for AI outputs',
        'No emojis in UI; neutral, supportive microcopy',
    ]
    for t in tone:
        story.append(Paragraph(f'• {t}', body))

    # Colors
    story.append(Paragraph('Color System', h1))
    color_rows = [
        ['Role', 'Hex', 'Usage'],
        ['Hadada Green', '#2D6356', 'Primary CTAs, focus, highlights'],
        ['Deep Blue', '#32517A', 'Headers, secondary CTAs, links on dark'],
        ['Success', '#059669', 'Positive states and notifications'],
        ['Info', '#0ea5e9', 'Informational states'],
        ['Warning', '#f59e0b', 'Cautions and non-blocking issues'],
        ['Error', '#dc3545', 'Errors and destructive actions'],
        ['Neutral Ink', '#1f2937', 'Primary text'],
        ['Muted', '#6b7280', 'Secondary text'],
        ['Divider', '#e5e7eb', 'Borders and separators'],
        ['Surface', '#f9fafb / #F9F8F8', 'Backgrounds'],
    ]
    table = Table(color_rows, hAlign='LEFT', colWidths=[120, 80, 280])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#111827')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#e5e7eb')),
        ('BOX', (0, 0), (-1, -1), 0.25, colors.HexColor('#e5e7eb')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fcfcfc')]),
    ]))
    story.append(table)
    story.append(Spacer(1, 12))

    # Typography
    story.append(Paragraph('Typography', h1))
    story.append(Paragraph('Base UI: System UI Sans (e.g., -apple-system, Segoe UI, Roboto). Serif (Georgia/Times) for clinical previews/print. Material Icons for iconography.', body))

    # UI Components
    story.append(Paragraph('UI Components', h1))
    comps = [
        'Buttons: 6–8px radius, brand fills, hover darken 10–15%',
        'Headers/Nav: gradient (#2D6356 → #32517A) with white text',
        'Cards/Sections: white surfaces, soft shadows',
        'Forms: clear labels, green focus outline; accessible sizes',
        'Notifications: color-coded backgrounds with left border emphasis',
        'Wizard: progress steps, clear Next/Back, responsive summary sidebar',
    ]
    for c in comps:
        story.append(Paragraph(f'• {c}', body))

    # Accessibility
    story.append(Paragraph('Accessibility', h1))
    acc = [
        'Maintain WCAG AA contrast',
        'Always visible focus states (2px outline, offset 2px)',
        'Icon fonts with aria-labels; do not rely on color alone',
    ]
    for a in acc:
        story.append(Paragraph(f'• {a}', body))

    # Data Privacy
    story.append(Paragraph('Data Privacy & Compliance', h1))
    story.append(Paragraph('POPIA-aligned workflows with audit trails, role-based permissions, and explicit review of AI-generated content prior to finalization. Avoid PHI in non-secured logs.', body))

    # Messaging
    story.append(Paragraph('Messaging Guidelines', h1))
    msg = [
        'Headlines: concise, benefit‑led (e.g., “Generate clinical reports in minutes”)',
        'Microcopy: instructional and neutral (“Select patient”, “Add therapist”)',
        'AI content: hedge confidently; include brief source references',
        'Avoid emojis, slang, and alarmist wording',
    ]
    for m in msg:
        story.append(Paragraph(f'• {m}', body))

    # For AI Tools
    story.append(Paragraph('For AI Tools (Guardrails)', h1))
    ai = [
        'Tone: professional, clinical, concise; no emojis',
        'Safety: no diagnosis; suggest clinician review; cite sources for summaries',
        'Privacy: exclude identifying details unless explicitly provided',
        'Style: use brand palette for UI mocks; headings sans-serif; clinical previews in serif',
    ]
    for x in ai:
        story.append(Paragraph(f'• {x}', body))

    # Open Questions
    story.append(Paragraph('Open Questions', h1))
    oq = [
        'Primary web font standardization (Inter/Source Sans vs system UI)?',
        'Logo rules: clear-space, min sizes, monochrome variants?',
        'Tagline: define one (e.g., “Care, documented.”)?',
        'Imagery: photography/illustration policy (Hadada motif)?',
        'Accent usage: when to use #2563eb vs #32517A?',
        'PDF print styling: preferred typeface/margins in ReportLab exports?',
        'Accessibility targets beyond WCAG AA?',
        'Localization roadmap beyond English/Afrikaans?',
    ]
    for q in oq:
        story.append(Paragraph(f'• {q}', body))

    doc.build(story)


if __name__ == '__main__':
    os.makedirs('docs', exist_ok=True)
    build_brand_pdf(os.path.join('docs', 'brand-style-guide.pdf'))
    print('Generated docs/brand-style-guide.pdf')

