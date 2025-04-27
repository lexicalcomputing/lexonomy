import pdfkit
import base64

def html_string_to_pdf(html_string):
    options = {
        'encoding': 'UTF-8',
        'disable-smart-shrinking': '',
    }
    pdf_bytes = pdfkit.from_string(html_string, output_path=None, options=options, css="./css/nvh-formatting-editor.css")
    pdf_string = base64.b64encode(pdf_bytes).decode('utf-8')
    return pdf_string
