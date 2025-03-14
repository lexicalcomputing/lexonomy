import pdfkit
import base64

def html_string_to_pdf(html_string):
    options = {
        'encoding': 'UTF-8'
    }
    pdf_bytes = pdfkit.from_string(html_string, options=options)
    pdf_string = base64.b64encode(pdf_bytes).decode('utf-8')
    return pdf_string
