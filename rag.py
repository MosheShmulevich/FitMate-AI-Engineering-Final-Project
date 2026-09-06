import os
import time
import hashlib
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from pinecone.errors.exceptions import NotFoundError
from pypdf import PdfReader


# =========================
# Configuration
# =========================

load_dotenv()

KNOWLEDGE_DIR = Path("knowledge")

INDEX_NAME = "fitmate-knowledge"
NAMESPACE = "fitness-knowledge"

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is missing from .env")

if not PINECONE_API_KEY:
    raise RuntimeError("PINECONE_API_KEY is missing from .env")


# =========================
# Clients
# =========================

openai_client = OpenAI(
    api_key=OPENAI_API_KEY
)

pc = Pinecone(
    api_key=PINECONE_API_KEY
)


# =========================
# Pinecone
# =========================

def ensure_index():
    existing_indexes = pc.list_indexes().names()

    if INDEX_NAME not in existing_indexes:
        pc.create_index(
            name=INDEX_NAME,
            dimension=EMBEDDING_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )

        print("Creating Pinecone index...")

        while True:
            description = pc.describe_index(INDEX_NAME)

            if description.status["ready"]:
                break

            time.sleep(1)

    return pc.Index(INDEX_NAME)


def clear_namespace(index):
    try:
        index.delete(
            delete_all=True,
            namespace=NAMESPACE
        )
        time.sleep(1)

    except NotFoundError:
        pass


# =========================
# PDF Processing
# =========================

def extract_pdf_pages(pdf_path: Path):
    reader = PdfReader(pdf_path)

    for page_number, page in enumerate(
        reader.pages,
        start=1
    ):
        text = page.extract_text()

        if text and text.strip():
            yield page_number, text.strip()


def chunk_text(
    text: str,
    chunk_size: int = 1400,
    overlap: int = 200
):
    chunks = []

    start = 0

    while start < len(text):
        end = start + chunk_size

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


# =========================
# Embeddings
# =========================

def create_embeddings(texts):
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts
    )

    return [
        item.embedding
        for item in response.data
    ]


# =========================
# Safe Vector ID
# =========================

def create_vector_id(
    source: str,
    page: int,
    chunk: int
):
    raw_id = f"{source}|{page}|{chunk}"

    return hashlib.sha1(
        raw_id.encode("utf-8")
    ).hexdigest()


# =========================
# Build Knowledge Base
# =========================

def build_knowledge_base():
    index = ensure_index()

    clear_namespace(index)

    pdf_files = list(
        KNOWLEDGE_DIR.glob("*.pdf")
    )

    if not pdf_files:
        print(
            "No PDF files found in knowledge/"
        )
        return

    records = []

    for pdf_path in pdf_files:
        print(
            f"Processing: {pdf_path.name}"
        )

        for page_number, text in extract_pdf_pages(
            pdf_path
        ):
            chunks = chunk_text(text)

            for chunk_number, chunk in enumerate(
                chunks
            ):
                vector_id = create_vector_id(
                    pdf_path.name,
                    page_number,
                    chunk_number
                )

                records.append({
                    "id": vector_id,
                    "text": chunk,
                    "source": pdf_path.name,
                    "page": page_number,
                    "chunk": chunk_number
                })

    if not records:
        print(
            "No readable text found in PDFs."
        )
        return

    print(
        f"Created {len(records)} chunks."
    )

    batch_size = 50

    for start in range(
        0,
        len(records),
        batch_size
    ):
        batch = records[
            start:start + batch_size
        ]

        texts = [
            record["text"]
            for record in batch
        ]

        embeddings = create_embeddings(texts)

        vectors = []

        for record, embedding in zip(
            batch,
            embeddings
        ):
            vectors.append({
                "id": record["id"],
                "values": embedding,
                "metadata": {
                    "text": record["text"],
                    "source": record["source"],
                    "page": record["page"],
                    "chunk": record["chunk"]
                }
            })

        index.upsert(
            vectors=vectors,
            namespace=NAMESPACE
        )

        uploaded = min(
            start + batch_size,
            len(records)
        )

        print(
            f"Uploaded {uploaded}/{len(records)} chunks"
        )

    print(
        "\nFitMate knowledge base built successfully."
    )


# =========================
# Retrieval
# =========================

def retrieve(
    query: str,
    top_k: int = 4
):
    index = ensure_index()

    query_embedding = create_embeddings(
        [query]
    )[0]

    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        namespace=NAMESPACE,
        include_metadata=True
    )

    retrieved = []

    for match in results.matches:
        metadata = match.metadata or {}

        retrieved.append({
            "score": match.score,
            "text": metadata.get(
                "text",
                ""
            ),
            "source": metadata.get(
                "source",
                "Unknown"
            ),
            "page": metadata.get(
                "page"
            ),
            "chunk": metadata.get(
                "chunk"
            )
        })

    return retrieved


# =========================
# Test
# =========================

if __name__ == "__main__":
    print(
        "=== FitMate RAG Setup ==="
    )

    build_knowledge_base()

    print(
        "\n=== Retrieval Test ==="
    )

    query = (
        "מהם העקרונות לבניית תוכנית אימון?"
    )

    print(
        f"\nQuery: {query}"
    )

    results = retrieve(
        query,
        top_k=4
    )

    if not results:
        print(
            "No retrieval results found."
        )

    else:
        for i, result in enumerate(
            results,
            start=1
        ):
            print(
                f"\n--- Result {i} ---"
            )

            print(
                f"Score: {result['score']:.4f}"
            )

            print(
                f"Source: {result['source']}"
            )

            print(
                f"Page: {result['page']}"
            )

            print(
                f"Chunk: {result['chunk']}"
            )

            print("\nText:")

            print(
                result["text"][:700]
            )