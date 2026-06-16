from collections import Counter, defaultdict

import pdfplumber

PDF_PATH = r"data/triet-hocc.pdf"


def get_main_font_size(page):
    sizes = [round(c["size"], 1) for c in page.chars]

    if not sizes:
        return None

    return Counter(sizes).most_common(1)[0][0]


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


def avg_font_size(chars):
    if not chars:
        return 0

    return round(
        sum(c["size"] for c in chars) / len(chars),
        2,
    )


def min_font_size(chars):
    if not chars:
        return 0

    return round(
        min(c["size"] for c in chars),
        2,
    )


def max_font_size(chars):
    if not chars:
        return 0

    return round(
        max(c["size"] for c in chars),
        2,
    )


def extract_lines(page):
    main_size = get_main_font_size(page)

    if not main_size:
        return []

    rows = defaultdict(list)

    for char in page.chars:
        # bỏ footnote/chữ nhỏ
        if char["size"] < main_size - 1:
            continue

        y = round(char["top"])
        rows[y].append(char)

    lines = []

    for y in sorted(rows.keys()):
        chars = sorted(rows[y], key=lambda x: x["x0"])

        text = "".join(c["text"] for c in chars).strip()

        if not text:
            continue

        lines.append(
            {
                "text": text,
                "chars": chars,
            }
        )

    return lines


def print_page_debug(page, page_num):
    print("\n")
    print("=" * 120)
    print(f"PAGE {page_num}")
    print("=" * 120)

    lines = extract_lines(page)

    for row in lines:
        text = row["text"]
        chars = row["chars"]

        if text.isdigit():
            continue

        avg_size = avg_font_size(chars)
        min_size = min_font_size(chars)
        max_size = max_font_size(chars)

        bold = is_bold(chars)

        fonts = Counter(c["fontname"] for c in chars)

        print(
            f"[avg={avg_size:>5}] "
            f"[min={min_size:>5}] "
            f"[max={max_size:>5}] "
            f"[bold={str(bold):<5}] "
            f"[fonts={dict(fonts)}]"
        )

        print(text)
        print("-" * 120)


def main():
    with pdfplumber.open(PDF_PATH) as pdf:
        print(f"\nTotal pages: {len(pdf.pages)}")

        for page_idx, page in enumerate(pdf.pages):
            # Bỏ 2 trang đầu giống parser của bạn
            if page_idx < 2:
                continue

            if page_idx > 7:
                break
            print_page_debug(
                page,
                page_idx + 1,
            )


if __name__ == "__main__":
    main()
