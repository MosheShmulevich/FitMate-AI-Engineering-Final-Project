import json
import re

from rank_bm25 import BM25Okapi

from rag import (
    KNOWLEDGE_DIR,
    extract_pdf_pages,
    chunk_text,
    retrieve as vector_retrieve,
    openai_client,
)


# ==================================================
# Configuration
# ==================================================

VECTOR_TOP_K = 20
BM25_TOP_K = 20
FUSION_TOP_K = 12
FINAL_TOP_K = 4

RERANK_MODEL = "gpt-4.1-mini"


# ==================================================
# Tokenization
# ==================================================

def tokenize(text: str):
    return re.findall(
        r"\w+",
        text.lower(),
        flags=re.UNICODE,
    )


# ==================================================
# Load Local Knowledge for BM25
# ==================================================

def load_chunks():
    records = []

    pdf_files = list(
        KNOWLEDGE_DIR.glob("*.pdf")
    )

    for pdf_path in pdf_files:

        for page_number, text in extract_pdf_pages(
            pdf_path
        ):

            chunks = chunk_text(text)

            for chunk_number, chunk in enumerate(
                chunks
            ):

                records.append({
                    "text": chunk,
                    "source": pdf_path.name,
                    "page": page_number,
                    "chunk": chunk_number,
                })

    return records


LOCAL_CHUNKS = load_chunks()

TOKENIZED_CORPUS = [
    tokenize(record["text"])
    for record in LOCAL_CHUNKS
]

BM25_INDEX = (
    BM25Okapi(TOKENIZED_CORPUS)
    if TOKENIZED_CORPUS
    else None
)


# ==================================================
# BM25 Search
# ==================================================

def bm25_retrieve(
    query: str,
    top_k: int = BM25_TOP_K
):

    if not BM25_INDEX:
        return []

    query_tokens = tokenize(query)

    scores = BM25_INDEX.get_scores(
        query_tokens
    )

    ranked_indices = sorted(
        range(len(scores)),
        key=lambda index: scores[index],
        reverse=True,
    )

    results = []

    for index in ranked_indices[:top_k]:

        if scores[index] <= 0:
            continue

        record = LOCAL_CHUNKS[index]

        results.append({
            "text": record["text"],
            "source": record["source"],
            "page": record["page"],
            "chunk": record["chunk"],
            "bm25_score": float(
                scores[index]
            ),
        })

    return results


# ==================================================
# Reciprocal Rank Fusion
# ==================================================

def make_key(result):
    return (
        result.get("source"),
        result.get("page"),
        result.get("chunk"),
    )


def reciprocal_rank_fusion(
    vector_results,
    bm25_results,
    top_k=FUSION_TOP_K,
    k=60,
):
    fused = {}

    # Vector results
    for rank, result in enumerate(
        vector_results,
        start=1,
    ):

        key = make_key(result)

        if key not in fused:
            fused[key] = {
                **result,
                "fusion_score": 0.0,
                "retrieval_methods": [],
            }

        fused[key]["fusion_score"] += (
            1 / (k + rank)
        )

        if "vector" not in fused[key][
            "retrieval_methods"
        ]:
            fused[key][
                "retrieval_methods"
            ].append("vector")

    # BM25 results
    for rank, result in enumerate(
        bm25_results,
        start=1,
    ):

        key = make_key(result)

        if key not in fused:
            fused[key] = {
                **result,
                "fusion_score": 0.0,
                "retrieval_methods": [],
            }

        fused[key]["fusion_score"] += (
            1 / (k + rank)
        )

        if "bm25" not in fused[key][
            "retrieval_methods"
        ]:
            fused[key][
                "retrieval_methods"
            ].append("bm25")

    ranked = sorted(
        fused.values(),
        key=lambda item: item[
            "fusion_score"
        ],
        reverse=True,
    )

    return ranked[:top_k]


# ==================================================
# LLM Reranker
# ==================================================

def rerank_candidates(
    query: str,
    candidates,
    top_k=FINAL_TOP_K,
):

    if not candidates:
        return []

    candidate_text = ""

    for index, candidate in enumerate(
        candidates
    ):

        candidate_text += f"""
CANDIDATE {index}

Source: {candidate['source']}
Page: {candidate['page']}

Content:
{candidate['text']}

-------------------------
"""

    prompt = f"""
You are the professional retrieval reranker
for an evidence-grounded fitness assistant.

Your task is to rank retrieved knowledge chunks
according to how useful and trustworthy they are
for answering the user's exact question.

USER QUESTION:
{query}


IMPORTANT RANKING RULES:

1. Prefer chunks that contain:
   - Practical recommendations
   - Clear definitions
   - Research findings
   - Training principles
   - Nutrition principles
   - Practical Application / recommendations
   - Concrete explanations

2. Strongly prefer content that directly answers
   the user's question.

3. A title-only chunk should rank very low.

4. IMPORTANT CONTEXT RULE:
   Do NOT treat every statement appearing in a
   presentation as an endorsed recommendation.

   A chunk may describe:
   - assumptions
   - common beliefs
   - myths
   - questions for discussion
   - claims being challenged
   - examples of incorrect thinking

   Such chunks should rank BELOW actual
   recommendations unless the text clearly
   confirms that the claim is supported.

5. Hebrew headings such as:
   - "הנחות יסוד"
   - "מיתוסים"
   - "שאלות"
   - "נקודה למחשבה"

   can indicate discussion material rather than
   a final professional recommendation.

6. Headings such as:
   - "המלצות יישומיות"
   - "Practical Application"
   - research conclusions
   - explicit professional recommendations

   should generally receive higher priority.

7. Do not infer that quoted text is true merely
   because it appears inside a retrieved chunk.

8. Do NOT answer the user's question.

9. Return ONLY valid JSON.


Required JSON format:

{{
    "ranking": [2, 0, 1, 3]
}}

The numbers are candidate indexes ordered from
most useful to least useful.


CANDIDATES:

{candidate_text}
"""

    try:

        response = (
            openai_client
            .chat
            .completions
            .create(
                model=RERANK_MODEL,
                temperature=0,
                response_format={
                    "type": "json_object"
                },
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a strict retrieval "
                            "reranker. Return valid JSON only."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
            )
        )

        content = (
            response
            .choices[0]
            .message
            .content
        )

        data = json.loads(content)

        ranking = data.get(
            "ranking",
            []
        )

        valid_ranking = []

        for index in ranking:

            if (
                isinstance(index, int)
                and 0 <= index < len(candidates)
                and index not in valid_ranking
            ):
                valid_ranking.append(index)

        # Add any candidates omitted by the model
        for index in range(
            len(candidates)
        ):

            if index not in valid_ranking:
                valid_ranking.append(index)

        reranked = [
            candidates[index]
            for index in valid_ranking
        ]

        return reranked[:top_k]

    except Exception as error:

        print(
            "Reranking failed. "
            "Using Hybrid Search order instead."
        )

        print(error)

        return candidates[:top_k]


# ==================================================
# Advanced Retrieval
# ==================================================

def advanced_retrieve(
    query: str,
    top_k=FINAL_TOP_K,
):

    # 1. Semantic retrieval
    vector_results = vector_retrieve(
        query=query,
        top_k=VECTOR_TOP_K,
    )

    # 2. Keyword retrieval
    keyword_results = bm25_retrieve(
        query=query,
        top_k=BM25_TOP_K,
    )

    # 3. Hybrid fusion
    fused_results = reciprocal_rank_fusion(
        vector_results,
        keyword_results,
        top_k=FUSION_TOP_K,
    )

    # 4. Context-aware reranking
    final_results = rerank_candidates(
        query,
        fused_results,
        top_k=top_k,
    )

    return final_results


# ==================================================
# Comparison Test
# ==================================================

if __name__ == "__main__":

    query = (
        "מהם כמה עקרונות חשובים "
        "בבניית תוכנית אימון?"
    )

    print(
        "================================"
    )

    print(
        "BASIC RAG"
    )

    print(
        "================================"
    )

    basic_results = vector_retrieve(
        query=query,
        top_k=4,
    )

    for index, result in enumerate(
        basic_results,
        start=1,
    ):

        print(
            f"\n--- Result {index} ---"
        )

        print(
            f"Score: "
            f"{result['score']:.4f}"
        )

        print(
            f"Source: {result['source']}"
        )

        print(
            f"Page: {result['page']}"
        )

        print(
            result["text"][:500]
        )

    print(
        "\n\n================================"
    )

    print(
        "ADVANCED RAG"
    )

    print(
        "Hybrid Search + Context-Aware Reranking"
    )

    print(
        "================================"
    )

    advanced_results = advanced_retrieve(
        query=query,
        top_k=4,
    )

    for index, result in enumerate(
        advanced_results,
        start=1,
    ):

        print(
            f"\n--- Result {index} ---"
        )

        print(
            f"Source: {result['source']}"
        )

        print(
            f"Page: {result['page']}"
        )

        print(
            "Methods:",
            result.get(
                "retrieval_methods",
                []
            )
        )

        print(
            result["text"][:500]
        )