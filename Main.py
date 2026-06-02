"""
fill_it_form v5 — แก้วงเล็บหายโดย Redraw ( ) หลัง white-out
"""

import io
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT_FILE = "THSarabun.ttf"
pdfmetrics.registerFont(TTFont("Thai", FONT_FILE))

PAGE_W = 612.0
PAGE_H = 792.0
BLUE   = (0.0, 0.0, 1.0)
BLACK  = (0.0, 0.0, 0.0)
WHITE  = (1.0, 1.0, 1.0)

# ── พิกัด text fields ────────────────────────────────────────
FIELDS = {
    "doc_no":       (441.7, 118.0, 536.3, 133.0, 11, BLUE),
    "fullname_th":  (185.0, 137.0, 370.0, 152.0, 11, BLUE),
    "date":         (450.0, 137.0, 536.3, 152.0, 11, BLUE),
    "fullname_en":  (202.4, 171.0, 350.0, 186.0, 11, BLUE),
    "emp_id":       (450.0, 171.0, 536.3, 186.0, 11, BLUE),
    "workplace":    (183.4, 199.0, 536.3, 214.0, 11, BLUE),
    "department":   (197.5, 226.0, 536.3, 241.0, 11, BLUE),
    "position":     (183.4, 254.0, 536.3, 269.0, 11, BLUE),
    "req_type":     (183.4, 281.0, 536.3, 296.0, 11, BLUE),
    "program":      (197.5, 309.0, 536.3, 324.0, 11, BLUE),
    "detail":       (183.2, 364.0, 536.3, 382.0, 11, BLUE),
    "detail2":      ( 57.0, 382.0, 536.3, 400.0, 11, BLUE),
    "note":         (114.1, 505.0, 536.3, 523.0, 11, BLACK),

    # ── ลายเซ็น: white-out เต็มพื้นที่ระหว่าง ( ) ──────────────
    # white-out ครอบ ) ได้ เพราะจะ redraw ) ทีหลัง
    "sign_requester":  (122.5, 607.0, 234.6, 632.0, 11, BLACK),
    "sign_date":       (126.0, 626.0, 234.0, 641.0, 10, BLACK),
    "sign_approver":   (383.6, 607.0, 483.8, 632.0, 11, BLACK),
    "sign_supervisor": (120.4, 687.0, 228.5, 712.0, 11, BLACK),
    "sign_recorder":   (384.6, 685.0, 485.9, 710.0, 11, BLACK),
}

# ── พิกัดวงเล็บทั้งหมดในส่วนลายเซ็น (จากการวิเคราะห์ template) ──
# จะ redraw หลัง white-out
PARENS = [
    # Row 1 (top=615)
    ("(", 122.5, 615.0),
    (")", 231.8, 615.0),
    ("(", 383.6, 615.0),
    (")", 481.0, 615.0),
    # Row 2 (top=694-696)
    ("(", 120.4, 696.0),
    (")", 225.7, 696.0),
    ("(", 384.6, 694.0),
    (")", 483.1, 694.0),
]

def top_to_rl(top, font_size=11):
    return PAGE_H - top - font_size + 2


def fill_pdf(data: dict, template_bytes: bytes) -> bytes:
    buf = io.BytesIO()
    c   = canvas.Canvas(buf, pagesize=(PAGE_W, PAGE_H))

    # ── 1. White-out + เขียน text ───────────────────────────────
    for field, (x0, top, x1, bot, fsize, color) in FIELDS.items():
        value = str(data.get(field, "") or "")

        c.setFillColorRGB(*WHITE)
        c.setStrokeColorRGB(*WHITE)
        rl_bot = PAGE_H - bot
        c.rect(x0, rl_bot, x1 - x0, bot - top, fill=1, stroke=0)

        if not value:
            continue

        c.setFillColorRGB(*color)
        c.setFont("Thai", fsize)
        c.drawString(x0 + 3, top_to_rl(top, fsize), value)

    # ── 2. Redraw วงเล็บทุกตัวในส่วนลายเซ็น ──────────────────────
    c.setFillColorRGB(*BLACK)
    c.setFont("Thai", 11)
    for char, px, py in PARENS:
        c.drawString(px, top_to_rl(py, 11), char)

    c.save()
    buf.seek(0)

    template = PdfReader(io.BytesIO(template_bytes))
    overlay  = PdfReader(buf)
    writer   = PdfWriter()
    page     = template.pages[0]
    page.merge_page(overlay.pages[0])
    writer.add_page(page)

    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


if __name__ == "__main__":
    with open("template.pdf", "rb") as f:
        tmpl = f.read()

    sample = {
        "doc_no":           "IT-TEST-001",
        "fullname_th":      "ปวรวรรณ สิทธิวุฒิ",
        "date":             "1/6/2569",
        "fullname_en":      "Paworawan Sittiwut",
        "emp_id":           "SPCO23",
        "workplace":        "S.P. Auto Corporation Co.,Ltd. (Head Office)",
        "department":       "Accounting",
        "position":         "ผู้จัดการแผนก",
        "req_type":         "ขอใช้สิทธิ์ผู้ดูแลระบบ (Super User / Administrator)",
        "program":          "AccCloud ระบบจัดการคำสั่งซื้อ และการบริการ",
        "detail":           "กำหนดสิทธิ์การใช้งานพนักงานใหม่",
        "detail2":          "",
        "note":             "ภรภัทร ดวงแก้ว / SPCO41 / ขอเปิดสิทธิ์ SPCO SP SPM",
        "sign_requester":   "ปวรวรรณ สิทธิวุฒิ",
        "sign_date":        "1/6/2569",
        "sign_approver":    "ภาณุ ธีรภานุ",
        "sign_supervisor":  "กนกกาญจน คณารัตนดิลก",
        "sign_recorder":    "ภรภัทร ดวงแก้ว",
    }

    result = fill_pdf(sample, tmpl)
    with open("filled_v5.pdf", "wb") as f:
        f.write(result)
    print("✅ filled_v5.pdf")
