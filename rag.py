"""Small FAISS retrieval-augmented maintenance guide."""

from pathlib import Path
import sys

import numpy as np

from llm import ask_llm

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_GUIDE = BASE_DIR / "data" / "maintenance_guide.md"


def chunk_markdown(text: str, words_per_chunk: int = 90) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    for paragraph in paragraphs:
        words = paragraph.split()
        for i in range(0, len(words), words_per_chunk):
            chunks.append(" ".join(words[i:i + words_per_chunk]))
    return chunks


class GuideRAG:
    def __init__(self, guide_path: str | Path = DEFAULT_GUIDE, model_name: str = "all-MiniLM-L6-v2"):
        self.guide_path = Path(guide_path)
        self.chunks = chunk_markdown(self.guide_path.read_text(encoding="utf-8"))
        try:
            import faiss
            from sentence_transformers import SentenceTransformer
            self.encoder = SentenceTransformer(model_name)
            embeddings = self.encoder.encode(self.chunks, normalize_embeddings=True)
            self.embeddings = np.asarray(embeddings, dtype="float32")
            self.index = faiss.IndexFlatIP(self.embeddings.shape[1])
            self.index.add(self.embeddings)
            self.backend = "sentence-transformer"
        except Exception as exc:
            from sklearn.feature_extraction.text import TfidfVectorizer

            self.backend = "tfidf-fallback"
            self.encoder = TfidfVectorizer(stop_words="english").fit(self.chunks)
            embeddings = self.encoder.transform(self.chunks).toarray()
            norms = np.maximum(np.linalg.norm(embeddings, axis=1, keepdims=True), 1e-12)
            self.embeddings = np.asarray(embeddings / norms, dtype="float32")
            try:
                import faiss
                self.index = faiss.IndexFlatIP(self.embeddings.shape[1])
                self.index.add(self.embeddings)
                self.use_faiss = True
            except Exception:
                self.index = None
                self.use_faiss = False

    def retrieve(self, query: str, top_k: int = 3) -> list[str]:
        if self.backend == "sentence-transformer":
            vector = np.asarray(
                self.encoder.encode([query], normalize_embeddings=True), dtype="float32"
            )
            _, indexes = self.index.search(vector, min(top_k, len(self.chunks)))
            return [self.chunks[int(i)] for i in indexes[0] if i >= 0]

        vector = self.encoder.transform([query]).toarray().astype("float32")
        norm = max(float(np.linalg.norm(vector)), 1e-12)
        vector = vector / norm
        scores = self.embeddings @ vector[0]
        indexes = np.argsort(scores)[::-1][:min(top_k, len(self.chunks))]
        return [self.chunks[int(i)] for i in indexes]

    def answer(self, query: str) -> dict:
        chunks = self.retrieve(query)
        context = "\n\n".join(chunks)
        prompt = (
            "Answer the question using only the retrieved guide excerpts below. "
            "If the excerpts do not contain an answer, say so. Do not add facts from outside "
            "the excerpts.\n\nExcerpts:\n" + context + "\n\nQuestion: " + query
        )
        try:
            answer = ask_llm(prompt)
        except RuntimeError:
            answer = "Retrieved maintenance guidance:\n" + context
        return {"answer": answer, "sources": chunks}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    rag = GuideRAG()
    print(rag.answer("How should I make a lathe safe before repair?"))
