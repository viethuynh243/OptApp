"""
md_to_pdf.py - Chuyển file Markdown sang PDF, giữ nguyên tiếng Việt + emoji + bảng.

Cách làm: Markdown -> HTML (kèm CSS in ấn đẹp) -> in ra PDF bằng trình duyệt
headless (Microsoft Edge hoặc Chrome). Không cần LaTeX/pandoc. Khối ```mermaid```
đơn giản (flowchart) được vẽ lại thành sơ đồ HTML/CSS (hộp + mũi tên) để hiển thị
trong PDF mà không cần chạy JavaScript.

Dùng:
    python packaging/md_to_pdf.py <input.md> [output.pdf]
"""

import os
import re
import sys
import html
import subprocess

import markdown


# ---------------------------------------------------------------------------
# Tìm trình duyệt headless (Edge ưu tiên, rồi Chrome)
# ---------------------------------------------------------------------------
def find_browser():
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    raise FileNotFoundError("Khong tim thay Microsoft Edge hoac Chrome de in PDF.")


# ---------------------------------------------------------------------------
# Vẽ lại khối mermaid (flowchart) thành sơ đồ HTML đơn giản
# ---------------------------------------------------------------------------
def mermaid_to_html(code):
    """Bọc mã mermaid để mermaid.js vẽ thật. HTML-escape để textContent giữ
    nguyên định nghĩa (kể cả <br/> và &amp;) cho mermaid đọc đúng."""
    return '<pre class="mermaid">' + html.escape(code.strip()) + "</pre>"


def extract_mermaid(md_text):
    """Thay mọi khối ```mermaid ... ``` bằng placeholder, trả về (text, blocks)."""
    blocks = []

    def repl(m):
        blocks.append(mermaid_to_html(m.group(1)))
        return f"\n@@MERMAID{len(blocks) - 1}@@\n"

    pattern = re.compile(r"```mermaid\s*\n(.*?)```", re.S)
    return pattern.sub(repl, md_text), blocks


CSS = """
@page { size: A4; margin: 14mm 15mm; }
* { box-sizing: border-box; }
body {
  font-family: "Segoe UI", "Segoe UI Emoji", Arial, sans-serif;
  font-size: 11pt; line-height: 1.5; color: #1c2330; margin: 0;
}
h1 { font-size: 21pt; color: #0f4c81; border-bottom: 3px solid #0f4c81;
     padding-bottom: 6px; margin: 0 0 14px; }
h2 { font-size: 15pt; color: #0f4c81; margin: 22px 0 8px;
     border-bottom: 1px solid #d7e1ea; padding-bottom: 4px; }
h3 { font-size: 12.5pt; color: #15406b; margin: 16px 0 6px; }
p { margin: 7px 0; }
a { color: #0f4c81; text-decoration: none; }
code { font-family: Consolas, "Courier New", monospace; font-size: 9.7pt;
       background: #eef2f6; padding: 1px 5px; border-radius: 4px; color: #b03050; }
pre { background: #1e2733; color: #e6edf3; padding: 11px 14px; border-radius: 7px;
      overflow-x: auto; font-size: 9.5pt; line-height: 1.45; }
pre code { background: none; color: inherit; padding: 0; }
blockquote { border-left: 4px solid #f0ad4e; background: #fff8ec; margin: 10px 0;
             padding: 7px 14px; color: #5a4a2a; border-radius: 0 6px 6px 0; }
blockquote p { margin: 3px 0; }
table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 10pt; }
th, td { border: 1px solid #c9d4de; padding: 6px 9px; text-align: left;
         vertical-align: top; }
th { background: #0f4c81; color: #fff; font-weight: 600; }
tr:nth-child(even) td { background: #f4f8fb; }
hr { border: none; border-top: 1px solid #dde5ec; margin: 18px 0; }
ul, ol { margin: 7px 0 7px 4px; padding-left: 22px; }
li { margin: 3px 0; }
/* Không để tiêu đề "mồ côi" cuối trang (tách rời nội dung ngay dưới) */
h1, h2, h3, h4, h5 { break-after: avoid; page-break-after: avoid; break-inside: avoid; }
/* Giữ tiêu đề / dòng dẫn ngay trước sơ đồ dính cùng sơ đồ (không cho ngắt trang) */
:is(h1,h2,h3,h4,h5,p):has(+ pre.mermaid) { break-after: avoid; page-break-after: avoid; }

/* Sơ đồ mermaid (vẽ thật) — canh giữa, nền trong, co vừa 1 trang, không tách ngang */
pre.mermaid { background: transparent; color: inherit; padding: 0; text-align: center;
              break-inside: avoid; page-break-inside: avoid; margin: 12px 0; }
pre.mermaid svg {
  display: block; margin: 0 auto;
  /* Ép co theo trang: rộng tối đa = khổ in, cao tối đa = gần 1 trang A4 */
  max-width: 100% !important; width: auto !important;
  max-height: 232mm !important; height: auto !important;
}
"""

# mermaid.js + cấu hình; in ra PDF sau khi vẽ xong (nhờ --virtual-time-budget).
# useMaxWidth:false -> mermaid xuất SVG kích thước thật (px) để CSS co theo cả
# chiều rộng LẪN chiều cao, nhờ vậy sơ đồ dọc cao vẫn lọt gọn trong 1 trang.
MERMAID_JS = (
    '<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>'
    '<script>mermaid.initialize({startOnLoad:true, theme:"default", '
    'flowchart:{useMaxWidth:false, htmlLabels:true}});</script>'
)


def convert(md_path, pdf_path):
    # Dùng đường dẫn tuyệt đối: Edge headless chạy ở thư mục riêng nên đường dẫn
    # tương đối (cả PDF output lẫn URL file://) sẽ sai chỗ.
    md_path = os.path.abspath(md_path)
    pdf_path = os.path.abspath(pdf_path)
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    md_text, mermaid_blocks = extract_mermaid(md_text)

    html_body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "sane_lists", "attr_list"],
    )
    # Khôi phục các sơ đồ flow (placeholder có thể bị bọc trong <p>)
    for i, block in enumerate(mermaid_blocks):
        html_body = html_body.replace(f"<p>@@MERMAID{i}@@</p>", block)
        html_body = html_body.replace(f"@@MERMAID{i}@@", block)

    has_mermaid = bool(mermaid_blocks)
    head_extra = MERMAID_JS if has_mermaid else ""
    html_doc = (f"<!DOCTYPE html><html lang='vi'><head><meta charset='utf-8'>"
                f"<style>{CSS}</style></head><body>{html_body}{head_extra}"
                f"</body></html>")

    html_path = os.path.splitext(pdf_path)[0] + "_tmp.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_doc)

    browser = find_browser()
    args = [browser, "--headless", "--disable-gpu", "--no-sandbox",
            "--no-pdf-header-footer"]
    # Khi có mermaid: chờ tải CDN + vẽ SVG xong rồi mới in (virtual time)
    if has_mermaid:
        args.append("--virtual-time-budget=15000")
    args += [f"--print-to-pdf={pdf_path}",
             "file:///" + html_path.replace("\\", "/")]
    subprocess.run(args, check=True, timeout=180)

    os.remove(html_path)
    print("Da tao PDF:", pdf_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(src)[0] + ".pdf"
    convert(src, dst)
