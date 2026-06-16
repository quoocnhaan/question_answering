import json
import re

from datasets import load_dataset


def get_law_data():
    print("🚀 Chuyển hướng kết nối tới Hugging Face (Kho luật chuẩn Underthesea)...")
    try:
        # Tải bộ dữ liệu Luật Việt Nam cấp cao nhất đã được làm sạch lỗi
        dataset = load_dataset("undertheseanlp/UTS_VLC", split="2026")
    except Exception as e:
        print(f"Đang thử cấu hình khác do lỗi: {e}")
        dataset = load_dataset("undertheseanlp/UTS_VLC", split="train")

    print(f"✅ Đã tải thành công {len(dataset)} văn bản Luật cấp cao!")

    chunks = []
    print("✂️ Đang tiến hành thuật toán bóc tách thành từng Điều luật (Chunking)...")

    for row in dataset:
        # Xử lý các key phổ biến trong kho dữ liệu NLP
        text = row.get("text", row.get("content", ""))
        title = row.get("so_hieu", row.get("title", "Văn bản Luật"))

        if not text:
            continue

        # Chia văn bản theo từng Điều (Hỗ trợ cả định dạng Markdown)
        dieu_list = re.split(
            r"(?=\n\s*(?:Điều|ĐIỀU)\s+\d+[\.:])|(?=\*\*(?:Điều|ĐIỀU)\s+\d+)", text
        )
        for dieu in dieu_list:
            dieu = dieu.strip()
            if len(dieu) > 50:  # Lọc bỏ các đoạn rác quá ngắn
                chunks.append({"source": title, "content": f"[{title}] {dieu}"})

    with open("law_chunks_for_rag.json", "w", encoding="utf-8") as out_f:
        json.dump(chunks, out_f, ensure_ascii=False, indent=4)

    print(f"🎉 QUÁ ĐỈNH! Đã ép ra {len(chunks)} chunks Điều luật nguyên chất.")
    print("📁 File dữ liệu RAG đã sẵn sàng tại: law_chunks_for_rag.json")


if __name__ == "__main__":
    get_law_data()
