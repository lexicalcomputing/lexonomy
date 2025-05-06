import pdfkit
import base64

def html_string_to_pdf():
    options = {
        'encoding': 'UTF-8',
        'disable-smart-shrinking': '',
    }

    try:
        with open("tmp/pdf_export.html") as f:
            string_html = f.read()
    except:
        return ""

    pdf_bytes = pdfkit.from_string(string_html, output_path=None, options=options, css="./css/nvh-formatting-editor.css")
    pdf_string = base64.b64encode(pdf_bytes).decode('utf-8')
    return pdf_string

def clear_html_file():
    try:
        with open("tmp/pdf_export.html", "w") as f:
            pass
    except:
        return False
    return True


def append_to_html_file(html_string):
    try:
        with open("tmp/pdf_export.html", "a") as f:
            f.write(html_string)
    except:
        return False
    return True

def readEntries(db):
    c = db.execute("SELECT id, nvh FROM entries")
    rows = c.fetchall()
    if not rows:
        return []
    result = []
    for row in rows:
        nvh = row["nvh"]
        id = row["id"]
        """
        if configs["subbing"]:
            nvh = addSubentryParentTags(db, id, nvh)
        """
        result.append({"id": id, "nvh": nvh})
    return result