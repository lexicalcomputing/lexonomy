import pdfkit
import base64

def html_string_to_pdf(user):
    options = {
        'encoding': 'UTF-8',
        'disable-smart-shrinking': '',
    }

    try:
        with open(f"tmp/pdf_export_{user['email']}.html") as f:
            string_html = f.read()
    except:
        return ""

    pdf_bytes = pdfkit.from_string(string_html, output_path=None, options=options, css="./css/nvh-formatting-editor.css")
    pdf_string = base64.b64encode(pdf_bytes).decode('utf-8')
    clear_html_file(user)
    return pdf_string

def clear_html_file(user):
    try:
        with open(f"tmp/pdf_export_{user['email']}.html", "w") as f:
            pass
    except:
        return False
    return True


def append_to_html_file(user, html_string):
    try:
        with open(f"tmp/pdf_export_{user['email']}.html", "a") as f:
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