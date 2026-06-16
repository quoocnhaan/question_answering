import numpy as np
from FlagEmbedding import BGEM3FlagModel

# Chạy script này 1 lần ở nhà để tải model về thư mục local
from huggingface_hub import snapshot_download
from sklearn.metrics.pairwise import cosine_similarity

model_path = snapshot_download(repo_id="BAAI/bge-m3", local_dir="./bge-m3-local")
print(f"Model đã được tải về: {model_path}")

# 1. Khởi tạo model từ thư mục local (để chạy offline trong Docker)
# use_fp16=True giúp tiết kiệm VRAM và tăng tốc độ inference
model = BGEM3FlagModel("./bge-m3-local", use_fp16=True)

# 2. Định nghĩa các câu Anchor cho 3 nhóm
anchor_texts = {
    "READING": "Đoạn thông tin chi tiết, văn bản dài, đọc hiểu đoạn văn có sẵn.",
    "MATH": "Tính toán toán học, công thức vật lý, phương trình, giải tích, suy luận logic, con số.",
    "KNOWLEDGE": "Hỏi đáp kiến thức chung, lịch sử, pháp luật, địa lý, định nghĩa khái niệm.",
}

# 3. Tạo Embedding cho các Anchor (Chỉ làm 1 lần khi khởi động hệ thống)
anchor_labels = list(anchor_texts.keys())
anchor_sentences = list(anchor_texts.values())

# Trích xuất vector dense (đặc trưng ngữ nghĩa)
anchor_embeddings = model.encode(anchor_sentences, batch_size=3)["dense_vecs"]


def semantic_router(question_text):
    """
    So sánh câu hỏi với các Anchor để quyết định luồng xử lý.
    """
    # Nhúng câu hỏi đầu vào
    question_emb = model.encode([question_text])["dense_vecs"]

    # Tính độ tương đồng Cosine
    similarities = cosine_similarity(question_emb, anchor_embeddings)[0]

    # Tìm nhóm có độ tương đồng cao nhất
    best_match_idx = np.argmax(similarities)
    best_category = anchor_labels[best_match_idx]
    confidence_score = similarities[best_match_idx]

    return best_category, confidence_score


# --- Test thử nghiệm ---
test_questions = [
    "Một hạt chuyển động dọc theo trục x với vị trí x(t) = t^3 - 3t^2. Vận tốc nhỏ nhất là bao nhiêu?",
    "Ngôi chùa Ba La Mật được khai dựng vào năm nào?",
    "Đoạn thông tin: Thạch hình là một phương pháp tử hình... Câu hỏi: Theo nội dung, tội nào bị ném đá?",
]

for q in test_questions:
    category, score = semantic_router(q)
    print(f"Câu hỏi: {q[:50]}... \n=> Phân loại: {category} (Score: {score:.4f})\n")
