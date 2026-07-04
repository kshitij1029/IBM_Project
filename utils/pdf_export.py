"""
utils/pdf_export.py
────────────────────
Generate a PDF itinerary using ReportLab.
"""

import logging
import io
import re
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, KeepTogether,
    )
    from reportlab.platypus.flowables import HRFlowable
    _REPORTLAB_AVAILABLE = True
except ImportError:
    _REPORTLAB_AVAILABLE = False
    logger.warning("reportlab not installed; PDF export disabled.")


# ── Page-number canvas callback ───────────────────────────────────────────────

def _draw_page_number(canvas, doc):
    """Draw page number at the bottom-centre of every page."""
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#57606a"))
    page_text = f"Page {doc.page}"
    canvas.drawCentredString(A4[0] / 2, 1.2 * cm, page_text)
    canvas.restoreState()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _strip_markdown(text: str) -> str:
    """Remove markdown symbols unsuitable for ReportLab plain text."""
    # Bold / italic markers
    text = re.sub(r'\*{1,3}(.+?)\*{1,3}', r'\1', text)
    # Heading markers
    text = re.sub(r'^#{1,4}\s+', '', text, flags=re.MULTILINE)
    return text.strip()


def _sanitize_para(text: str) -> str:
    """
    Convert minimal markdown to ReportLab XML-safe markup:
      **bold** → <b>bold</b>   *italic* → <i>italic</i>
    Also escapes bare ampersands and angle brackets.
    """
    # Escape XML-special chars first (before adding tags)
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    # ***bold-italic***
    text = re.sub(r'\*{3}(.+?)\*{3}', r'<b><i>\1</i></b>', text)
    # **bold**
    text = re.sub(r'\*{2}(.+?)\*{2}', r'<b>\1</b>', text)
    # *italic*
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    return text


def generate_itinerary_pdf(trip_data: dict) -> bytes | None:
    """
    Build a PDF from *trip_data* dict and return raw bytes.
    Returns None when reportlab is unavailable.
    """
    if not _REPORTLAB_AVAILABLE:
        return None

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2.5 * cm,   # extra room for page numbers
        title=f"AI Trip Planner Report – {trip_data.get('destination', 'Trip')}",
        author="Voyager AI",
    )

    styles = getSampleStyleSheet()

    # ── Custom styles ─────────────────────────────────────────────────────────
    report_title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=22,
        leading=28,
        textColor=colors.HexColor("#1a56db"),
        spaceAfter=4,
        fontName="Helvetica-Bold",
    )
    sub_title_style = ParagraphStyle(
        "SubTitle",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#57606a"),
        spaceAfter=10,
        fontName="Helvetica",
    )
    section_heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading1"],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#1a56db"),
        fontName="Helvetica-Bold",
        spaceBefore=14,
        spaceAfter=6,
    )
    sub_heading_style = ParagraphStyle(
        "SubHeading",
        parent=styles["Heading2"],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#3b82d4"),
        fontName="Helvetica-Bold",
        spaceBefore=10,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#1f2328"),
        spaceAfter=3,
        fontName="Helvetica",
    )
    bullet_style = ParagraphStyle(
        "Bullet",
        parent=body_style,
        leftIndent=14,
        bulletIndent=4,
        spaceBefore=1,
        spaceAfter=2,
    )

    story = []

    # ── Cover block ───────────────────────────────────────────────────────────
    now = datetime.now()
    story.append(Paragraph("AI Trip Planner Report", report_title_style))
    story.append(Paragraph(
        f"Destination: <b>{trip_data.get('destination', 'Trip')}</b> &nbsp;|&nbsp; "
        f"Generated: {now.strftime('%d %B %Y at %H:%M')}",
        sub_title_style,
    ))
    story.append(HRFlowable(
        width="100%", thickness=1.5,
        color=colors.HexColor("#1a56db"), spaceAfter=10,
    ))

    # ── Trip Summary table ────────────────────────────────────────────────────
    def fmt_val(v):
        return str(v) if v else "—"

    summary_rows = [
        ["Destination",   fmt_val(trip_data.get("destination"))],
        ["Duration",       f"{fmt_val(trip_data.get('duration_days'))} days"],
        ["Travelers",      fmt_val(trip_data.get("travelers", 1))],
        ["Start Date",     fmt_val(trip_data.get("start_date"))],
        ["End Date",       fmt_val(trip_data.get("end_date"))],
        ["Travel Style",   fmt_val(trip_data.get("travel_style", "")).title()],
        ["Traveler Type",  fmt_val(trip_data.get("traveler_type", "")).title()],
        ["Total Budget",   f"INR {trip_data.get('budget_inr', 0):,.0f}"],
    ]

    interests = trip_data.get("interests")
    if interests:
        summary_rows.append(["Interests", ", ".join(interests)])

    tbl = Table(summary_rows, colWidths=[4.5 * cm, 11.5 * cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, -1), colors.HexColor("#e8f0fe")),
        ("TEXTCOLOR",     (0, 0), (0, -1), colors.HexColor("#1a56db")),
        ("FONTNAME",      (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",      (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS",(0, 0), (-1, -1), [colors.white, colors.HexColor("#f7f8fa")]),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
    ]))
    story.append(KeepTogether([
        Paragraph("Trip Summary", section_heading_style),
        tbl,
        Spacer(1, 0.5 * cm),
    ]))

    # ── Day-by-Day Itinerary ──────────────────────────────────────────────────
    itinerary_text = trip_data.get("itinerary_text", "")
    if itinerary_text:
        story.append(Paragraph("Day-by-Day Itinerary", section_heading_style))

        for raw_line in itinerary_text.split("\n"):
            line = raw_line.rstrip()
            if not line:
                story.append(Spacer(1, 0.15 * cm))
                continue

            # Heading levels
            if re.match(r'^###\s+', line):
                text = _sanitize_para(re.sub(r'^###\s+', '', line))
                story.append(Paragraph(text, sub_heading_style))
            elif re.match(r'^##\s+', line):
                text = _sanitize_para(re.sub(r'^##\s+', '', line))
                story.append(Paragraph(text, section_heading_style))
            elif re.match(r'^#\s+', line):
                text = _sanitize_para(re.sub(r'^#\s+', '', line))
                story.append(Paragraph(text, section_heading_style))
            # Bullet points
            elif re.match(r'^[-•*]\s+', line):
                text = _sanitize_para(re.sub(r'^[-•*]\s+', '', line))
                story.append(Paragraph(f"• {text}", bullet_style))
            # Numbered list
            elif re.match(r'^\d+\.\s+', line):
                text = _sanitize_para(re.sub(r'^\d+\.\s+', '', line))
                story.append(Paragraph(f"• {text}", bullet_style))
            # Horizontal rule
            elif re.match(r'^-{3,}$', line):
                story.append(HRFlowable(
                    width="100%", thickness=0.5,
                    color=colors.HexColor("#e5e7eb"), spaceAfter=4,
                ))
            else:
                text = _sanitize_para(line)
                if text:
                    story.append(Paragraph(text, body_style))

        story.append(Spacer(1, 0.5 * cm))

    # ── Budget Breakdown ──────────────────────────────────────────────────────
    budget = trip_data.get("budget_breakdown")
    if budget:
        budget_header = [Paragraph("Budget Breakdown (INR)", section_heading_style)]

        budget_rows = [
            [Paragraph("<b>Category</b>", body_style), Paragraph("<b>Amount (INR)</b>", body_style)],
            ["Accommodation",  f"INR {budget.get('accommodation', 0):,.0f}"],
            ["Transport",      f"INR {budget.get('transport', 0):,.0f}"],
            ["Food & Dining",  f"INR {budget.get('food', 0):,.0f}"],
            ["Sightseeing",    f"INR {budget.get('sightseeing', 0):,.0f}"],
            ["Shopping",       f"INR {budget.get('shopping', 0):,.0f}"],
            ["Miscellaneous",  f"INR {budget.get('miscellaneous', 0):,.0f}"],
            [Paragraph("<b>TOTAL</b>", body_style),
             Paragraph(f"<b>INR {budget.get('total', 0):,.0f}</b>", body_style)],
        ]

        btbl = Table(budget_rows, colWidths=[9 * cm, 7 * cm])
        btbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), colors.HexColor("#1a56db")),
            ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND",    (0, -1), (-1, -1), colors.HexColor("#fef3c7")),
            ("TEXTCOLOR",     (0, -1), (-1, -1), colors.HexColor("#92400e")),
            ("FONTNAME",      (0, -1), (-1, -1), "Helvetica-Bold"),
            ("ROWBACKGROUNDS",(0, 1), (-1, -2), [colors.white, colors.HexColor("#f7f8fa")]),
            ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
            ("FONTSIZE",      (0, 0), (-1, -1), 10),
            ("ALIGN",         (1, 0), (1, -1), "RIGHT"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ]))

        story.append(KeepTogether(budget_header + [btbl, Spacer(1, 0.5 * cm)]))

    # ── Footer note ───────────────────────────────────────────────────────────
    story.append(HRFlowable(
        width="100%", thickness=0.5,
        color=colors.HexColor("#e5e7eb"), spaceBefore=10, spaceAfter=6,
    ))
    story.append(Paragraph(
        f"Report generated by Voyager AI on {now.strftime('%d %B %Y at %H:%M:%S')}. "
        "Powered by IBM Granite.",
        ParagraphStyle(
            "Footer",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#57606a"),
            alignment=1,   # centred
        ),
    ))

    # Build with page-number callback
    try:
        doc.build(story, onFirstPage=_draw_page_number, onLaterPages=_draw_page_number)
    except Exception as exc:
        logger.exception("ReportLab build failed: %s", exc)
        return None

    return buffer.getvalue()
