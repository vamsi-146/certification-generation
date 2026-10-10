import os
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics

CERT_DIR = "certificates"
os.makedirs(CERT_DIR, exist_ok=True)


def generate_certificate(certificate_id: str, recipient_name: str, event_name: str, issuer: str, date: str) -> str:
    filepath = os.path.join(CERT_DIR, f"{certificate_id}.pdf")
    c = canvas.Canvas(filepath, pagesize=landscape(A4))
    width, height = landscape(A4)
    cx, max_w = width / 2, width - 3 * inch

    navy, gold = HexColor("#1e3a5f"), HexColor("#d4af37")
    dark, grey = HexColor("#333333"), HexColor("#666666")

    def text(y, s, font, size, color):
        """Draw centred text, shrinking the font if it is too wide. Returns drawn width."""
        while size > 18 and pdfmetrics.stringWidth(s, font, size) > max_w:
            size -= 1
        c.setFillColor(color)
        c.setFont(font, size)
        c.drawCentredString(cx, y, s)
        return pdfmetrics.stringWidth(s, font, size)

    # Background
    c.setFillColor(HexColor("#faf8f0"))
    c.rect(0, 0, width, height, fill=1, stroke=0)

    # Borders
    for off, lw, col in [(0.3, 4, navy), (0.4, 2, gold), (0.45, 1, navy)]:
        c.setLineWidth(lw)
        c.setStrokeColor(col)
        c.rect(off * inch, off * inch, width - 2 * off * inch, height - 2 * off * inch)

    # Corner ornaments
    L = 1.0 * inch
    c.setStrokeColor(gold)
    c.setLineWidth(3)
    for x, sx in [(0.4 * inch, 1), (width - 0.4 * inch, -1)]:
        for y, sy in [(0.4 * inch, 1), (height - 0.4 * inch, -1)]:
            c.line(x, y + sy * L, x, y)
            c.line(x, y, x + sx * L, y)
            c.line(x + sx * 0.2 * inch, y + sy * 0.2 * inch, x + sx * 0.4 * inch, y + sy * 0.4 * inch)

    # Top and bottom ornament rows
    c.setStrokeColor(navy)
    c.setLineWidth(1)
    for y in (height - 1.0 * inch, 2.1 * inch):
        c.line(1.2 * inch, y, width - 1.2 * inch, y)
        c.setFillColor(gold)
        for i in range(7):
            c.circle(cx - 3 * inch + i * inch, y, 0.12 * inch, fill=1, stroke=1)

    # Main text (evenly spaced, top to bottom)
    text(height - 1.75 * inch, "Certificate of Achievement", "Times-Bold", 38, navy)
    text(height - 2.50 * inch, "This is to certify that", "Times-Italic", 18, dark)
    nw = text(height - 3.30 * inch, recipient_name, "Times-Bold", 48, navy)
    half = max(2.5 * inch, nw / 2 + 0.2 * inch)
    c.setStrokeColor(gold)
    c.setLineWidth(2)
    c.line(cx - half, height - 3.5 * inch, cx + half, height - 3.5 * inch)
    text(height - 4.10 * inch, "has successfully completed", "Times-Roman", 18, dark)
    text(height - 4.70 * inch, event_name, "Times-Bold", 28, navy)
    text(height - 5.20 * inch, "on", "Times-Italic", 16, dark)
    text(height - 5.60 * inch, date, "Times-Bold", 20, navy)

    # Issuer block
    c.setStrokeColor(navy)
    c.setLineWidth(1.5)
    c.line(cx - 2 * inch, 1.65 * inch, cx + 2 * inch, 1.65 * inch)
    text(1.40 * inch, issuer, "Times-Bold", 18, navy)
    text(1.15 * inch, "Issuing Authority", "Times-Italic", 12, grey)
    text(0.70 * inch, f"Certificate ID: {certificate_id}", "Times-Roman", 10, grey)

    c.save()
    return filepath