import io

import fitz


def extract_pdf_text(content: bytes) -> str:
    document = fitz.open(stream=io.BytesIO(content), filetype="pdf")
    pages = [page.get_text("text") for page in document]
    document.close()
    return "\n".join(pages).strip()
