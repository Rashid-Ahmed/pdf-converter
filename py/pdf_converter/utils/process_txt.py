from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate


def txt_to_pdf(bytes_content: bytes) -> bytes:
    # Parse the txt content
    text = bytes_content.decode("utf-8")
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    paragraphs = text.split("\n")

    # Add content to story
    for para in paragraphs:
        story.append(Paragraph(para, styles["Normal"]))
    # Build the story
    doc.build(story)
    # Get story bytes
    buffer.seek(0)
    return buffer.getvalue()
