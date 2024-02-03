from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate


def txt_to_pdf(bytes_content):
    text = bytes_content.decode("utf-8")
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    paragraphs = text.split("\n")

    for para in paragraphs:
        story.append(Paragraph(para, styles["Normal"]))
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
