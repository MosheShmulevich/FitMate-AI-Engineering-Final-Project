import streamlit as st

from rag import retrieve as basic_retrieve
from advanced_rag import advanced_retrieve


# ==================================================
# Page Configuration
# ==================================================

st.set_page_config(
    page_title="FitMate RAG Comparison",
    page_icon="🧠",
    layout="wide",
)


# ==================================================
# RTL + Styling
# ==================================================

st.markdown(
    """
    <style>
        html, body, [class*="css"] {
            direction: rtl;
            text-align: right;
        }

        .stTextInput input {
            direction: rtl;
            text-align: right;
        }

        .rag-card {
            border: 1px solid rgba(128, 128, 128, 0.25);
            border-radius: 14px;
            padding: 16px;
            margin-bottom: 14px;
            background: rgba(255, 255, 255, 0.03);
        }

        .rag-title {
            font-size: 1.05rem;
            font-weight: 700;
            margin-bottom: 8px;
        }

        .rag-meta {
            font-size: 0.9rem;
            opacity: 0.75;
            margin-bottom: 10px;
        }

        .rag-text {
            line-height: 1.7;
            white-space: pre-wrap;
        }

        .small-note {
            font-size: 0.9rem;
            opacity: 0.8;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==================================================
# Helpers
# ==================================================

def safe_text(text):
    if not text:
        return "לא נמצא תוכן."
    return str(text)


def render_result_card(result, index, advanced=False):
    source = result.get("source", "Unknown")
    page = result.get("page", "-")
    text = safe_text(result.get("text", ""))

    if advanced:
        methods = result.get("retrieval_methods", [])
        methods_text = ", ".join(methods) if methods else "—"

        meta = (
            f"מקור: {source} | "
            f"עמוד: {page} | "
            f"שיטות אחזור: {methods_text}"
        )
    else:
        score = result.get("score")
        score_text = (
            f"{score:.4f}"
            if isinstance(score, (int, float))
            else "—"
        )

        meta = (
            f"מקור: {source} | "
            f"עמוד: {page} | "
            f"Semantic Score: {score_text}"
        )

    st.markdown(
        f"""
        <div class="rag-card">
            <div class="rag-title">תוצאה {index}</div>
            <div class="rag-meta">{meta}</div>
            <div class="rag-text">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==================================================
# Header
# ==================================================

st.title("🧠 FitMate — Basic RAG vs Advanced RAG")

st.markdown(
    """
    השוואה ישירה בין מנגנון האחזור הבסיסי של FitMate
    לבין מנגנון ה־Advanced RAG.
    """
)

st.markdown(
    """
    **Basic RAG:** Semantic Vector Search  
    **Advanced RAG:** Vector Search + BM25 + Reciprocal Rank Fusion + Context-Aware Reranking
    """
)


# ==================================================
# Query
# ==================================================

default_query = "מהם כמה עקרונות חשובים בבניית תוכנית אימון?"

query = st.text_input(
    "שאלה לבדיקה",
    value=default_query,
)

compare_button = st.button(
    "🔍 השווה Basic מול Advanced",
    use_container_width=True,
)


# ==================================================
# Comparison
# ==================================================

if compare_button:

    if not query.strip():
        st.warning("יש להזין שאלה.")
        st.stop()

    with st.spinner("מריץ את שני מנגנוני האחזור..."):

        try:
            basic_results = basic_retrieve(
                query=query,
                top_k=4,
            )

            advanced_results = advanced_retrieve(
                query=query,
                top_k=4,
            )

        except Exception as error:
            st.error(
                f"שגיאה בהרצת ההשוואה: {error}"
            )
            st.stop()

    basic_column, advanced_column = st.columns(2)

    # ==================================================
    # Basic RAG
    # ==================================================

    with basic_column:
        st.subheader("🔹 Basic RAG")

        st.caption(
            "Semantic Vector Search בלבד"
        )

        if not basic_results:
            st.info("לא נמצאו תוצאות.")
        else:
            for index, result in enumerate(
                basic_results,
                start=1,
            ):
                render_result_card(
                    result,
                    index,
                    advanced=False,
                )

    # ==================================================
    # Advanced RAG
    # ==================================================

    with advanced_column:
        st.subheader("🚀 Advanced RAG")

        st.caption(
            "Hybrid Search + RRF + Context-Aware Reranking"
        )

        if not advanced_results:
            st.info("לא נמצאו תוצאות.")
        else:
            for index, result in enumerate(
                advanced_results,
                start=1,
            ):
                render_result_card(
                    result,
                    index,
                    advanced=True,
                )


# ==================================================
# Presentation Note
# ==================================================

st.divider()

st.markdown(
    """
    <div class="small-note">
    מטרת המסך: להמחיש כיצד Advanced RAG משפר את איכות האחזור
    על ידי שילוב חיפוש סמנטי, BM25, איחוד דירוגים ו־reranking לפי הקשר.
    </div>
    """,
    unsafe_allow_html=True,
)
