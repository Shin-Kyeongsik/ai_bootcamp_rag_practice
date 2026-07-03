"""
[01_rag] 완성형 데모 — Streamlit 웹 UI

step1~step5로 배운 RAG 파이프라인을 하나의 화면으로 묶은 완성형 데모다.
질문을 입력하면 검색 → 답변 + 근거 문서 + 실제로 추출된 청크(거리)를 보여준다.

사전 준비:
    export OPENAI_API_KEY=sk-...   # (또는 사이드바에 입력)
    python step2_chunk.py && python step3_embed_store.py   # 먼저 인덱싱
    streamlit run app.py
"""

import os
import streamlit as st
from openai import OpenAI

import rag_core

st.set_page_config(page_title="부트캠프 안내 AI (RAG)", page_icon="🎓")


@st.cache_resource(show_spinner=False)
def load_collection(api_key: str):
    return rag_core.get_collection(api_key)


# ── 사이드바 ────────────────────────────────────────────────
st.sidebar.header("⚙️ 설정")
api_key = os.environ.get("OPENAI_API_KEY") or st.sidebar.text_input(
    "OpenAI API Key", type="password", help="환경변수 OPENAI_API_KEY가 있으면 자동 사용됩니다."
)
top_k = st.sidebar.slider("검색할 문서 조각 수 (top-k)", 1, 8, rag_core.DEFAULT_TOP_K)
model = st.sidebar.text_input("생성 모델", rag_core.GEN_MODEL)
st.sidebar.markdown(
    "---\n검색 대상: `bootcamp_docs/`의 원본 안내 문서\n\n"
    "답변은 **검색된 문서 근거**로만 생성됩니다."
)

# ── 본문 ────────────────────────────────────────────────────
st.title("🎓 AI Agent 실무 부트캠프 2026 안내 AI")
st.caption("원본 문서를 검색해 근거와 함께 답변하는 RAG 데모 (01_rag)")

st.markdown("**예시 질문**")
examples = [
    "등록은 몇 시부터 어디서 하나요?",
    "Docker 설치가 안 되어 있으면 언제 도움을 받나요?",
    "수료 기준은 무엇인가요?",
    "최종 발표는 언제 진행되나요?",
]
cols = st.columns(len(examples))
clicked_example = None
for col, ex in zip(cols, examples):
    if col.button(ex, use_container_width=True):
        clicked_example = ex

question = st.text_input("질문을 입력하세요", value=clicked_example or "")
run = st.button("질문하기", type="primary") or bool(clicked_example)

if run and question.strip():
    if not api_key:
        st.error("OpenAI API Key가 필요합니다. 사이드바에 입력하거나 OPENAI_API_KEY 환경변수를 설정하세요.")
        st.stop()
    try:
        collection = load_collection(api_key)
    except Exception as e:
        st.error(f"벡터 저장소를 불러올 수 없습니다: {e}\n\n먼저 step2_chunk.py → step3_embed_store.py를 실행하세요.")
        st.stop()

    client = OpenAI(api_key=api_key)
    with st.spinner("문서를 검색하고 답변을 생성하는 중..."):
        result = rag_core.ask(question.strip(), collection, client, top_k=top_k, model=model)

    if result["answer"] is None:
        st.warning("검색된 문서가 없습니다. 인덱싱 상태를 확인하세요.")
    else:
        st.markdown("### 답변")
        st.write(result["answer"])

        st.markdown("### 근거 문서")
        for s in result["sources"]:
            st.markdown(f"- `{s}`")

        st.markdown("### 🔎 실제로 추출된 문서 조각 (검색 결과)")
        st.caption(
            "아래 조각들이 질문과 가장 가깝다고 판단돼 LLM에 근거로 전달되었습니다. "
            "**거리가 작을수록 질문과 유사**합니다."
        )
        for i, hit in enumerate(result["hits"], start=1):
            title = f"**[{i}] `{hit['source']}`**"
            if hit["section"]:
                title += f" — {hit['section']}"
            st.markdown(title)
            if hit.get("distance") is not None:
                st.caption(f"거리 {hit['distance']:.4f} (작을수록 유사)")
            st.code(hit["document"], language="markdown")
elif run:
    st.info("질문을 입력해 주세요.")
