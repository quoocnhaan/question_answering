from itertools import groupby

import pdfplumber


def extract_headings(pdf_path):
    headings = []

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[2]

        # Trích xuất từ kèm font, size và tọa độ 'top' (khoảng cách từ mép trên xuống)
        words = page.extract_words(extra_attrs=["fontname", "size"])

        # BƯỚC 1: Lọc ra chỉ những từ in đậm hoặc cỡ chữ to
        bold_words = [
            w for w in words if "Bold" in w.get("fontname", "") or w.get("size", 0) > 13
        ]

        # BƯỚC 2: Sắp xếp các từ theo tọa độ Y (từ trên xuống dưới trang)
        # Làm tròn tọa độ top (round 0 hoặc 1) vì các chữ cùng dòng có thể chênh nhau 0.x pixel
        bold_words.sort(key=lambda w: round(w["top"]))

        # BƯỚC 3: Gom nhóm các từ nằm trên cùng một dòng
        for y_coord, group in groupby(bold_words, key=lambda w: round(w["top"])):
            line_words = list(group)

            # Sắp xếp lại các từ trên cùng 1 dòng theo tọa độ X (từ trái sang phải)
            line_words.sort(key=lambda w: w["x0"])

            # Nối text lại với nhau (có thể bỏ khoảng trắng nếu là các mảnh của 1 từ)
            # Ở đây dùng logic đơn giản là nối bằng khoảng trắng, bạn có thể tinh chỉnh thêm x_tolerance
            # Sắp xếp lại các mảnh chữ trên cùng 1 dòng theo tọa độ X (từ trái sang phải)
            line_words.sort(key=lambda w: w["x0"])

            full_line_text = ""
            for i, w in enumerate(line_words):
                if i > 0:
                    # Tính khoảng cách: mép trái của từ hiện tại (x0) trừ đi mép phải của từ trước đó (x1)
                    space_dist = w["x0"] - line_words[i - 1]["x1"]

                    # Nếu khoảng cách lớn hơn 1.5 pixel, chèn thêm khoảng trắng
                    # (Bạn có thể tinh chỉnh con số 1.5 này lên 2.0 nếu chữ vẫn bị dính)
                    if space_dist > 1.5:
                        full_line_text += " "

                full_line_text += w["text"]

            # Có thể clean thêm khoảng trắng thừa nếu có
            full_line_text = full_line_text.strip()
            # Lấy size lớn nhất trong dòng làm đại diện
            max_size = max([w["size"] for w in line_words])

            headings.append(
                {
                    "text": full_line_text,
                    "size": round(max_size, 1),
                    "y_position": y_coord,
                }
            )

    return headings


# Kết quả kỳ vọng sẽ trả về một chuỗi nguyên vẹn: "Bộgiáodụcvàđàotạo"


# Test hàm với một file PDF
pdf_path = "data/Giao Trinh TTHCM.pdf"
headings = extract_headings(pdf_path)
print("Headings found in the PDF:")
for heading in headings:
    print(
        f"Text: {heading['text']}, Size: {heading['size']}, Y Position: {heading['y_position']}"
    )
