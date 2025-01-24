import fitz
from PIL import Image
import io


def extract_page_image(pdf_file, page_number):
    print("[get_image_page] Extrayendo imagen de la página", page_number)
    print("[get_image_page] Archivo PDF:", pdf_file)
    doc = fitz.open(pdf_file)
    page = doc.load_page(page_number - 1)  # PyMuPDF usa indexación 0
    pix = page.get_pixmap(dpi=300)  # type: ignore
    img = Image.open(io.BytesIO(pix.tobytes()))
    return img
