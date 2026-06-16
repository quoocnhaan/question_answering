import os
import re
from collections import Counter, defaultdict

import pandas as pd
import pdfplumber


def avg_font_size(chars):
    if not chars:
        return 0
    return round(sum(c["size"] for c in chars) / len(chars), 1)


def get_style(chars):
    return (avg_font_size(chars), is_bold(chars))


def get_main_font_size(page):
    sizes = [round(c["size"], 1) for c in page.chars]
    if not sizes:
        return None
    return Counter(sizes).most_common(1)[0][0]


def extract_lines_without_footnotes(page):
    rows = defaultdict(list)

    for char in page.chars:
        y = round(char["top"])

        # Bỏ chữ nhỏ hơn font 11 (Dùng round để tránh sai số thập phân VD: 10.96)
        if round(char["size"]) < 11:
            continue

        rows[y].append(char)

    lines = []

    for y in sorted(rows.keys()):
        chars = sorted(rows[y], key=lambda x: x["x0"])
        text = "".join(c["text"] for c in chars).strip()

        if text:
            lines.append(
                {
                    "text": text,
                    "chars": chars,
                }
            )

    return lines


# ==========================================
# STRUCTURE DETECTORS
# ==========================================
def is_chapter(line: str) -> bool:
    line = line.strip()
    match = re.match(r"^(Chương|CHƯƠNG|chương|Phần|PHẦN|phần)\s+([IVXLC]+|\d+)\b", line)
    if not match:
        return False
    if len(line) <= 25:
        return True
    if re.match(
        r"^(Chương|CHƯƠNG|chương|Phần|PHẦN|phần)\s+([IVXLC]+|\d+)\s*[:\-\.]", line
    ):
        return True
    if line.isupper():
        return True
    return False


def is_roman(line: str) -> bool:
    line = line.strip()
    # Chống nhiễu các tên riêng thường gặp trong sách Chính trị
    if (
        line.startswith("V.I.")
        or line.startswith("V. I.")
        or line.startswith("C. Mác")
        or line.startswith("Ph. Ăngghen")
    ):
        return False

    # Thu hẹp phạm vi: Các mục La Mã trong sách hiếm khi vượt quá 39 (XXXIX).
    # Chỉ quét ký tự I, V, X và bắt buộc VIẾT HOA.
    return bool(re.match(r"^[IVX]+(?:\s*[\-\.])(?:\s|$)", line))


def is_bold(chars):
    if not chars:
        return False
    bold_count = sum(
        1
        for c in chars
        if any(
            k in c["fontname"].lower() for k in ["bold", "black", "demi", "semibold"]
        )
    )
    return bold_count / len(chars) > 0.6


def is_number(line_text: str, line_chars: list) -> bool:
    pattern = r"^\d+\s*\.\s+([A-ZÀ-Ỹa-zá-ỹ]|\d)"
    if not re.match(pattern, line_text.strip()):
        return False
    return is_bold(line_chars)


def is_letter(line_text: str, line_chars: list) -> bool:
    pattern = r"^[a-zđ]\s*\)\s+"
    if not re.match(pattern, line_text.strip()):
        return False
    return is_bold(line_chars)


# ==========================================
# LỌC TIÊU ĐỀ BỊ RỚT DÒNG (Đã nâng cấp)
# ==========================================
def is_title_continuation(
    line: str, current_title: str, current_style: tuple, last_title_style: tuple
) -> bool:
    line = line.strip()
    current_title = current_title.strip()

    # 1. Câu quá dài hoặc kết thúc bằng dấu chấm câu -> CHẮC CHẮN là nội dung
    if len(line) > 90 or line.endswith((".", ":", ";")):
        return False

    # 2. Dòng trước đang nối dở bằng dấu gạch ngang
    if current_title.endswith("-"):
        return True

    # 3. Dòng đang xét IN HOA TOÀN BỘ -> Tiêu đề rớt dòng
    if line.isupper():
        return True

    # 4. Dòng bắt đầu bằng chữ thường -> Khả năng rất cao là nối dòng của câu trước
    if line and line[0].islower():
        return True

    # 5. Cùng style (size, độ đậm)
    if last_title_style is not None and current_style == last_title_style:
        # KHỐNG CHẾ CHẶT: Nếu tiêu đề đang IN HOA TOÀN BỘ, nhưng dòng hiện tại
        # lại là chữ thường (chỉ viết hoa chữ đầu) -> Đây là đoạn văn nội dung, không gộp!
        if current_title.isupper() and not line.isupper() and line[0].isupper():
            return False

        # Nếu dòng đủ ngắn và không vi phạm luật trên, chấp nhận nối
        if len(line) < 80:
            return True

    return False


# ==========================================
# PDF → LINES
# ==========================================
def get_document_lines(pdf_path):
    lines = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                if i < 2:
                    continue

                filtered_lines = extract_lines_without_footnotes(page)
                if not filtered_lines:
                    continue

                for row in filtered_lines:
                    text = row["text"].strip()
                    if not text or text.isdigit():
                        continue

                    lines.append(
                        {
                            "text": text,
                            "chars": row["chars"],
                            "page": i + 1,
                        }
                    )
    except Exception as e:
        print(f"Lỗi đọc file {pdf_path}: {e}")

    return lines


# ==========================================
# SMART MERGE
# ==========================================
def merge_lines(lines):
    merged = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if not merged:
            merged = line
            continue

        if re.match(r"^(\d+|[a-zA-Z])\.\s", line):
            merged += "\n" + line
        elif re.match(r"^[\:\,\.\)]", line):
            merged += line
        elif merged.endswith((".", ":", ";")):
            merged += "\n" + line
        else:
            merged += " " + line

    return re.sub(r"[ \t]+", " ", merged).strip()


# ==========================================
# MAIN PARSER
# ==========================================
def parse_pdf(pdf_path):
    lines = get_document_lines(pdf_path)
    if not lines:
        return []

    sections = []
    current_chapter = ""
    current_roman = ""
    current_number = ""
    current_letter = ""

    buffer = []
    start_page = None
    last_updated_level = None
    last_title_style = None

    def flush():
        if not buffer:
            return

        title_parts = [current_chapter, current_roman, current_number, current_letter]
        full_title = " > ".join([t for t in title_parts if t])
        if not full_title:
            full_title = "Phần mở đầu"

        content = merge_lines(buffer)
        if not content:
            return

        sections.append(
            {
                "title": full_title,
                "content": content,
                "page": start_page,
                "source": os.path.basename(pdf_path),
            }
        )

    for item in lines:
        line = item["text"]
        chars = item["chars"]
        page = item["page"]

        if is_chapter(line):
            flush()
            current_chapter = line
            current_roman = current_number = current_letter = ""
            buffer = []
            start_page = page
            last_updated_level = 1
            last_title_style = get_style(chars)

        elif is_roman(line):
            flush()
            current_roman = line
            current_number = current_letter = ""
            buffer = []
            start_page = page
            last_updated_level = 2
            last_title_style = get_style(chars)

        elif is_number(line, chars):
            flush()
            current_number = line
            current_letter = ""
            buffer = []
            start_page = page
            last_updated_level = 3
            last_title_style = get_style(chars)

        elif is_letter(line, chars):
            flush()
            current_letter = line
            buffer = []
            start_page = page
            last_updated_level = 4
            last_title_style = get_style(chars)

        else:
            current_style = get_style(chars)
            is_continuation = False

            if last_updated_level is not None:
                title_to_check = ""
                if last_updated_level == 1:
                    title_to_check = current_chapter
                elif last_updated_level == 2:
                    title_to_check = current_roman
                elif last_updated_level == 3:
                    title_to_check = current_number
                elif last_updated_level == 4:
                    title_to_check = current_letter

                is_continuation = is_title_continuation(
                    line, title_to_check, current_style, last_title_style
                )

            if is_continuation:
                if last_updated_level == 1:
                    current_chapter += " " + line
                elif last_updated_level == 2:
                    current_roman += " " + line
                elif last_updated_level == 3:
                    current_number += " " + line
                elif last_updated_level == 4:
                    current_letter += " " + line
            else:
                last_updated_level = None
                if start_page is None:
                    start_page = page
                buffer.append(line)

    flush()
    return sections


if __name__ == "__main__":
    pdf_path = r"data/kinh-te-chinh-tri.pdf"
    output_csv = r"data/kinh-te-chinh-tri.csv"

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    print(f"Processing: {pdf_path}")

    sections = parse_pdf(pdf_path)

    if sections:
        df = pd.DataFrame(sections)
        df.to_csv(output_csv, index=False, encoding="utf-8-sig")

        print(f"✅ Saved → {output_csv}")
        print(f"✅ Total sections: {len(df)}")
        print(df[["title", "page"]].head(10))
    else:
        print("⚠️ Không tìm thấy nội dung")
