import glob
import os
import re

import pandas as pd


def clean_wiki_text(text):
    """Hàm làm sạch các thẻ HTML và Wiki markups rác"""
    if not isinstance(text, str):
        return ""
    # Bỏ các thẻ HTML như <templatestyles ... />
    text = re.sub(r"<[^>]+>", "", text)
    # Bỏ khoảng trắng thừa
    text = re.sub(r"\s+", " ", text).strip()
    return text


def process_wikipedia_parquet(data_dir):
    print("Đang đọc các file parquet...")
    # Đọc tất cả các file parquet trong thư mục
    files = glob.glob(os.path.join(data_dir, "*.parquet"))

    dfs = []
    for f in files:
        dfs.append(pd.read_parquet(f))

    df = pd.concat(dfs, ignore_index=True)
    print(f"Tổng số bài viết ban đầu: {len(df)}")

    # --- BƯỚC LỌC CHI TIẾT ---

    # 1. Bỏ các trang hệ thống, trang định hướng (Không có giá trị RAG)
    print("Đang lọc các trang rác...")
    df = df[~df["title"].str.contains("định hướng", case=False, na=False)]
    df = df[
        ~df["title"].str.startswith(("Wikipedia:", "Tập tin:", "Bản mẫu:", "Thể loại:"))
    ]
    df = df[df["title"] != "Trang Chính"]

    # 2. Lọc độ dài (Chỉ lấy các bài viết có nội dung tương đối dài, chứa nhiều kiến thức)
    # Loại bỏ các bài viết quá ngắn (stubs) dưới 800 ký tự
    print("Đang lọc theo độ dài...")
    df = df[df["text"].str.len() > 800]

    # 3. Làm sạch Text
    print("Đang làm sạch văn bản (Xóa HTML)...")
    df["text"] = df["text"].apply(clean_wiki_text)

    print(f"Tổng số bài viết CHẤT LƯỢNG giữ lại: {len(df)}")

    # 4. Xuất ra file mới để chuẩn bị cho bước Chunking & FAISS
    output_path = "cleaned_wiki_data.parquet"
    df.to_parquet(output_path, index=False)
    print(f"Đã lưu dữ liệu sạch vào: {output_path}")


if __name__ == "__main__":
    # Thay đường dẫn tới thư mục chứa 3 file parquet của bạn
    dataset_path = r"E:\ProjectAI\Agent\viwiki_data\data"
    process_wikipedia_parquet(dataset_path)
