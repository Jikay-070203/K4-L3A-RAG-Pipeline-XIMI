import streamlit as st
from dotenv import load_dotenv

from src.task10_generation import generate_with_citation


load_dotenv()

st.set_page_config(
    page_title="IELTS Writing RAG",
    page_icon="📚",
    layout="wide",
)

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("IELTS Writing RAG")
    st.caption("Hỏi đáp dựa trên tài liệu IELTS đã lập chỉ mục")
    top_k = st.slider("Số chunks", 3, 10, 5)

    if st.button("Xóa cuộc trò chuyện"):
        st.session_state.messages = []
        st.rerun()

st.title("IELTS Writing Assistant")
st.caption("Câu trả lời chỉ dựa trên nguồn đã truy hồi và hiển thị kèm citation.")


def show_sources(sources: list[dict]) -> None:
    """Hiển thị nguồn, phương thức truy hồi và điểm số."""
    if not sources:
        return

    st.markdown("**Nguồn đã sử dụng**")
    for index, source in enumerate(sources, 1):
        metadata = source["metadata"]
        title = metadata["title"]
        source_name = metadata["source"]
        method = source["retrieval_method"]
        score = source["score"]
        url = metadata.get("url")
        label = f"[{index}] {title} — {method} — score={score:.4f}"
        with st.expander(label):
            st.write(f"**Source:** {source_name}")
            if url:
                st.write(f"**URL:** {url}")
            st.write(source["content"])

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            show_sources(message.get("sources", []))

query = st.chat_input("Nhập câu hỏi...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Đang truy hồi tài liệu và tạo câu trả lời..."):
            result = generate_with_citation(query, top_k=top_k)

        answer = result["answer"]
        sources = result["sources"]
        st.markdown(answer)
        st.caption(f"retrieval_source: {result['retrieval_source']}")
        show_sources(sources)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "sources": sources,
        }
    )
