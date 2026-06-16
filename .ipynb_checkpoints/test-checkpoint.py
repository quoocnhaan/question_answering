import json
import re

import pandas as pd


def categorize_question(question_text):
    """
    Phân loại câu hỏi thành:
    READING | MATH | KNOWLEDGE
    """

    # Đọc hiểu
    if (
        "Đoạn thông tin:" in question_text
        or "Title:" in question_text
        or "-- Đoạn văn" in question_text
    ):
        return "READING"

    # Toán có LaTeX
    if re.search(r"\$.+?\$", question_text) or re.search(r"\$\$.+?\$\$", question_text):
        return "MATH"

    # Từ khóa suy luận
    reasoning_keywords = [
        "hàm số",
        "đạo hàm",
        "phương trình",
        "tích phân",
        "đồ thị",
        "điện trở",
        "vận tốc",
        "gia tốc",
        "chiều cao",
        "chi phí",
        "doanh thu",
        "thị trường cạnh tranh",
        "tỷ suất",
        "nồng độ",
        "phản ứng hóa học",
    ]

    question_lower = question_text.lower()

    if any(
        keyword in question_lower for keyword in reasoning_keywords
    ) or question_lower.endswith("là bao nhiêu?"):
        return "MATH"

    return "KNOWLEDGE"


def process_dataset(json_file_path, output_csv_path):
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    labels = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]

    rows = []

    for item in data:
        qid = item["qid"]
        question = item["question"]
        choices = item["choices"]

        formatted_choices = "\n".join(
            f"{labels[i]}. {choice}" for i, choice in enumerate(choices)
        )

        category = categorize_question(question)

        rows.append(
            {
                "qid": qid,
                "category": category,
                "question": question,
                "choices": formatted_choices,
            }
        )

    df = pd.DataFrame(rows)

    df.to_csv(output_csv_path, index=False, encoding="utf-8-sig")

    print(f"Saved {len(df)} records to {output_csv_path}")


# Example
process_dataset("public-test.json", "classified_questions.csv")
