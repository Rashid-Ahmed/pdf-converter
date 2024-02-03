import email
from email.header import decode_header
from io import BytesIO
from typing import Tuple, Union

from PIL import Image
from PyPDF4 import PdfFileReader, PdfFileWriter
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate


def decode_payload(payload: email.message.Message, email_encoding: str) -> Union[str, None]:
    # List of encodings to try in priority order
    encodings_to_try = ["utf-8", "windows-1252", "latin-1", "utf-16", "ISO-8859-15"]
    if email_encoding is not None:
        if email_encoding in encodings_to_try:
            encodings_to_try.remove(email_encoding)
        encodings_to_try.insert(0, email_encoding)

    for encoding in encodings_to_try:
        try:
            decoded_text = payload.get_payload(decode=True).decode(encoding)
            return decoded_text
        except UnicodeDecodeError:
            continue  # Try the next encoding if decoding fails

    # If all attempts fail
    return None  # Or handle the failure as needed


def decode_headers(header: str) -> Tuple[str, Union[str, None]]:
    decoded_parts = decode_header(header)
    decoded_text = ""
    body_encoding = None
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            # Decode bytes using the specified encoding or 'utf-8' as default
            decoded_text += part.decode(encoding or "utf-8")
            body_encoding = encoding
        else:
            # If the part is already a string, add it to the decoded text
            decoded_text += part

    # Display the decoded text
    return decoded_text, body_encoding


def parse_body(eml_message: email.message.Message, email_encoding: str, styles):
    # Get the email body content
    body = ""
    if eml_message.is_multipart():
        for part in eml_message.walk():
            if part.get_content_type() == "text/plain":
                decoded_body = decode_payload(part, email_encoding)
                if decoded_body is not None:
                    body += decoded_body

    else:
        decoded_body = decode_payload(eml_message, email_encoding)
        if decoded_body is not None:
            body = decoded_body

    body_paragraphs = [Paragraph(line, styles["Normal"]) for line in body.split("\n")]

    return body_paragraphs


def parse_headers(eml_message: email.message.Message, styles):
    encodings = []
    field_paragraphs = []
    header_fields = ["Subject", "From", "To", "Date"]
    for field in header_fields:
        parsed_field, encoding = decode_headers(eml_message[field])
        if encoding is not None:
            encodings.append(encoding)

        if (field == "From" or field == "To") and all(char in parsed_field for char in ["<", ">", "@"]):
            parsed_field = "".join(char for char in parsed_field if char not in ["<", ">"])

        field_paragraphs.append(Paragraph(field + ": " + parsed_field, styles["Normal"]))
    story = field_paragraphs
    encodings = list(set(encodings))
    if len(encodings) == 1:
        return story, encodings[0]
    # If each header has a different encoding, we dont use their encodings
    return story, None


def create_pdf(output_stream: BytesIO):
    content_bytes = output_stream.getvalue()
    pdf_buffer = BytesIO(content_bytes)
    pdf_reader = PdfFileReader(pdf_buffer)
    pdf_writer = PdfFileWriter()
    for page in pdf_reader.pages:
        pdf_writer.addPage(page)

    return pdf_writer


def add_attachment(part: email.message.Message, pdf_writer: PdfFileWriter):
    attachment_data = part.get_payload(decode=True)
    attachment_reader = PdfFileReader(BytesIO(attachment_data))
    num_pages = attachment_reader.getNumPages()
    for page_num in range(num_pages):
        pdf_writer.addPage(attachment_reader.getPage(page_num))


def add_images(part: email.message.Message, pdf_writer: PdfFileWriter, page_width: int, page_height: int):
    image_data = part.get_payload(decode=True)
    img = Image.open(BytesIO(image_data))
    img_bytes = BytesIO()
    img.save(img_bytes, "PDF")

    img_width, img_height = img.size
    x_offset = (page_width - img_width) / 2
    y_offset = (page_height - img_height) / 2

    # Add the resized image to the PDF writer
    img_bytes.seek(0)

    # Merge the image PDF with the existing PDF
    image_reader = PdfFileReader(img_bytes)
    new_page = pdf_writer.addBlankPage(width=page_width, height=page_height)
    new_page.mergeTranslatedPage(image_reader.getPage(0), x_offset, y_offset)


def eml_to_pdf(eml_content: bytes) -> bytes:
    # Parse the EML content
    eml_message = email.message_from_bytes(eml_content)
    output_stream = BytesIO()
    doc = SimpleDocTemplate(output_stream, pagesize=letter)
    styles = getSampleStyleSheet()
    # Add email header
    story, email_encoding = parse_headers(eml_message, styles)
    # Add body content to the PDF
    body_paragraphs = parse_body(eml_message, email_encoding, styles)

    story.extend(body_paragraphs)
    # Build the PDF
    doc.build(story)

    # Get the content PDF as bytes
    pdf_writer = create_pdf(output_stream)

    first_page = pdf_writer.getPage(0)
    media_box = first_page.mediaBox
    page_width = media_box.getWidth()
    page_height = media_box.getHeight()

    for part in eml_message.walk():
        if part.get_content_maintype() != "multipart" and part.get("Content-Disposition") is not None:
            content_type = part.get_content_type()
            if content_type == "application/pdf":
                # Process PDF attachment
                add_attachment(part, pdf_writer)

            elif content_type in ["image/jpeg", "image/jpg", "image/png"]:
                # Process image (JPEG/JPG/PNG) attachment
                add_images(part, pdf_writer, page_width, page_height)

    output_pdf = BytesIO()
    pdf_writer.write(output_pdf)

    # Reset the buffer to prepare for reading
    output_pdf.seek(0)
    return output_pdf.getvalue()
