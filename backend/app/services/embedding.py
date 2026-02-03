from typing import List
import os
from app.config import settings

_model = None


def get_embedding_model():
    """Lazy import to avoid PyTorch DLL issues on Windows."""
    global _model
    if _model is None:
        try:
            # Import here to avoid loading PyTorch at module import time
            from sentence_transformers import SentenceTransformer
            model_path = settings.embedding_model
            _model = SentenceTransformer(model_path)
        except OSError as e:
            if "DLL" in str(e) or "WinError" in str(e):
                raise RuntimeError(
                    "PyTorch DLL loading failed. This is a common Windows issue.\n"
                    "To fix:\n"
                    "1. Run: .\\fix-pytorch-windows.ps1\n"
                    "2. Install Visual C++ Redistributable: https://aka.ms/vs/17/release/vc_redist.x64.exe\n"
                    "3. Restart your terminal/IDE\n"
                    f"Original error: {e}"
                ) from e
            raise
    return _model


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for a list of texts."""
    model = get_embedding_model()
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    return embeddings.tolist()


def generate_embedding(text: str) -> List[float]:
    """Generate embedding for a single text."""
    return generate_embeddings([text])[0]

