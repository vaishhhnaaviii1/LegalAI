# app/services/similarity_service.py
import numpy as np
from sentence_transformers import SentenceTransformer, util

# 🧠 Model ko globally load kar rahe hain taaki memory save ho
try:
    print("⏳ Loading LegalAI Embedding Model...")
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    print("✅ Model Loaded Successfully!")
except Exception as e:
    print(f"❌ Error loading embedding model: {str(e)}")
    embedding_model = None


def compute_similarity_percentage(current_case_text: str, precedent_case_text: str) -> int:
    """
    Takes two text blocks, converts them to embeddings, 
    and returns a rounded similarity percentage (0-100).
    """
    if not embedding_model:
        return 0 # Fallback agar model load nahi hua
        
    if not current_case_text.strip() or not precedent_case_text.strip():
        return 0

    # 1. Text ko multi-dimensional vectors mein badlo
    embedding_current = embedding_model.encode(current_case_text, convert_to_tensor=True)
    embedding_precedent = embedding_model.encode(precedent_case_text, convert_to_tensor=True)

    # 2. Cosine Similarity calculate karo (Result ranges from -1 to 1)
    cosine_score = util.cos_sim(embedding_current, embedding_precedent)

    # 3. Score ko extract karo aur negative values ko handle karne ke liye clamp karo
    score_val = cosine_score.item()
    if score_val < 0:
        score_val = 0.0

    # 4. Percentage mein convert karke absolute round integer return karo
    return int(round(score_val * 100))