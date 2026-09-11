from io import BytesIO

from pypdf import PdfReader


def extract_text_from_pdf(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))

    pages = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages.append(text)

    return "\n\n".join(pages)
