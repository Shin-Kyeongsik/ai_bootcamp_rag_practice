"""
통합 데모 — 사이드바에서 방식을 골라 비교하는 Streamlit 앱.

세 가지 방식을 한 앱에서 전환하며 사용한다:
  ① 01 · RAG (원본 문서)      — 원본 청크를 검색해 답변
  ② 02 · LLM Wiki (위키 전체) — 정제된 위키 전체를 컨텍스트에 넣어 답변 (검색 없음)
  ③ 03 · RAG + Wiki (위키 검색) — 정제된 위키 청크를 검색해 답변

각 방식은 해당 모듈이 만들어 둔 산출물을 사용한다:
  - 01: 01_rag/chroma_db          (step3_embed_store.py 로 생성)
  - 02: 02_llm_wiki/wiki/*.md      (step2_build_wiki.py 로 생성)
  - 03: 03_rag_llm_wiki/chroma_db  (step3_embed_store.py 로 생성)

실행:
    streamlit run app.py
"""

import os
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI
import streamlit as st

# ── 경로/상수 ────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAG_DB = os.path.join(BASE_DIR, "01_rag", "chroma_db")
RAG_COLLECTION = "bootcamp_docs"
WIKI_DIR = os.path.join(BASE_DIR, "02_llm_wiki", "wiki")
WIKI_RAG_DB = os.path.join(BASE_DIR, "03_rag_llm_wiki", "chroma_db")
WIKI_RAG_COLLECTION = "bootcamp_wiki"

EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")

# 검색(RAG) 방식 답변 규칙
RAG_SYSTEM_PROMPT = """당신은 'AI Agent 실무 부트캠프 2026'의 안내 AI입니다.
반드시 아래 '참고 자료' 내용만을 근거로 한국어로 답변하세요.

규칙:
1. 표현이 달라도 참고 자료에 관련 내용이 있으면 그 근거로 최대한 답하세요.
2. 참고 자료에 전혀 없으면 "제공된 자료에서 확인할 수 없습니다"라고 답하고 지어내지 마세요.
3. 날짜/시간/장소/조건은 자료에 적힌 값을 정확히 인용하세요.
"""


def load_api_key_from_file():
    """OPENAI_API_KEY가 없으면 api_key.txt에서 읽어 설정한다."""
    if os.environ.get("OPENAI_API_KEY"):
        return
    try:
        with open(os.path.join(BASE_DIR, "api_key.txt"), encoding="utf-8") as f:
            key = f.read().strip()
        if key:
            os.environ["OPENAI_API_KEY"] = key
    except FileNotFoundError:
        pass


load_api_key_from_file()


# ── 방식 정의 ────────────────────────────────────────────────
METHODS = {
    "① 01 · RAG (원본 문서)": "rag",
    "② 02 · LLM Wiki (위키 전체)": "wiki",
    "③ 03 · RAG + Wiki (위키 검색)": "rag_wiki",
}

METHOD_DESC = {
    "rag": "원본 안내 문서(`bootcamp_docs`)를 청킹·검색해서 관련 조각만 근거로 답합니다.",
    "wiki": "LLM이 정제한 위키 **전체**를 컨텍스트에 넣어 답합니다. (검색 없음)",
    "rag_wiki": "정제한 위키를 청킹·검색해서 관련 **위키 조각**만 근거로 답합니다.",
}


def get_embedding_function(api_key):
    return embedding_functions.OpenAIEmbeddingFunction(api_key=api_key, model_name=EMBEDDING_MODEL)


@st.cache_resource(show_spinner=False)
def get_collection(db_dir, collection_name, api_key):
    client = chromadb.PersistentClient(path=db_dir)
    return client.get_collection(collection_name, embedding_function=get_embedding_function(api_key))


def retrieve(collection, question, top_k):
    result = collection.query(
        query_texts=[question], n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    hits = []
    for doc, meta, dist in zip(result["documents"][0], result["metadatas"][0], result["distances"][0]):
        hits.append({
            "document": doc,
            "source": meta.get("source", "unknown"),
            "section": meta.get("section", ""),
            "distance": dist,
        })
    return hits


def generate(question, context, client, model):
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": RAG_SYSTEM_PROMPT},
            {"role": "user", "content": f"참고 자료:\n{context}\n\n질문: {question}"},
        ],
        temperature=0,
    )
    return completion.choices[0].message.content.strip()


def load_wiki_text():
    """02가 만든 위키 전체를 (파일명과 함께) 하나의 문자열로 합친다."""
    files = sorted(f for f in os.listdir(WIKI_DIR) if f.endswith(".md"))
    blocks, names = [], []
    for name in files:
        with open(os.path.join(WIKI_DIR, name), encoding="utf-8") as f:
            blocks.append(f"===== 위키 페이지: {name} =====\n{f.read()}")
        names.append(name)
    return "\n\n".join(blocks), names


# ── UI ───────────────────────────────────────────────────────
st.set_page_config(page_title="부트캠프 안내 AI — 통합 데모", page_icon="🎓")

st.sidebar.header("⚙️ 설정")
method_label = st.sidebar.radio("방식 선택", list(METHODS.keys()))
method = METHODS[method_label]
st.sidebar.info(METHOD_DESC[method])

api_key = os.environ.get("OPENAI_API_KEY") or st.sidebar.text_input(
    "OpenAI API Key", type="password", help="api_key.txt 또는 환경변수가 있으면 자동 사용됩니다."
)
top_k = st.sidebar.slider("검색할 조각 수 (top-k)", 1, 8, 4,
                          help="RAG 방식(①③)에만 적용됩니다.")
model = st.sidebar.text_input("생성 모델", DEFAULT_MODEL)

st.title("🎓 AI Agent 실무 부트캠프 2026 안내 AI")
st.caption("사이드바에서 방식을 골라, 같은 질문을 세 가지 방식으로 비교해 보세요.")

st.markdown("**예시 질문**")
examples = [
    "등록은 몇 시부터 어디서 하나요?",
    "Docker 설치가 안 되어 있으면 언제 도움을 받나요?",
    "수료 기준은 무엇인가요?",
    "일일 과제는 어떻게 출제돼?",
]
cols = st.columns(len(examples))
clicked_example = None
for col, ex in zip(cols, examples):
    if col.button(ex, use_container_width=True):
        clicked_example = ex

question = st.text_input("질문을 입력하세요", value=clicked_example or "")
run = st.button("질문하기", type="primary") or bool(clicked_example)


def render_hits(hits):
    st.markdown("### 🔎 실제로 검색된 조각")
    st.caption("질문과 가장 가깝다고 판단된 조각들. **거리가 작을수록 유사**합니다.")
    for i, hit in enumerate(hits, start=1):
        title = f"**[{i}] `{hit['source']}`**"
        if hit["section"]:
            title += f" — {hit['section']}"
        st.markdown(title)
        st.caption(f"거리 {hit['distance']:.4f} (작을수록 유사)")
        st.code(hit["document"], language="markdown")


if run and question.strip():
    if not api_key:
        st.error("OpenAI API Key가 필요합니다. api_key.txt를 두거나 사이드바에 입력하세요.")
        st.stop()
    client = OpenAI(api_key=api_key)
    q = question.strip()

    try:
        # ── ② LLM Wiki: 위키 전체를 컨텍스트로 (검색 없음) ──
        if method == "wiki":
            if not os.path.isdir(WIKI_DIR) or not os.listdir(WIKI_DIR):
                st.error("위키가 없습니다. 먼저 `02_llm_wiki/step2_build_wiki.py`를 실행하세요.")
                st.stop()
            with st.spinner("위키 전체를 근거로 답변 생성 중..."):
                wiki_text, names = load_wiki_text()
                answer = generate(q, wiki_text, client, model)
            st.markdown("### 답변")
            st.write(answer)
            st.markdown("### 근거")
            st.caption("검색 없이 **위키 전체**를 컨텍스트로 사용했습니다.")
            for n in names:
                st.markdown(f"- `02_llm_wiki/wiki/{n}`")

        # ── ①/③ RAG: 검색 후 생성 ──
        else:
            if method == "rag":
                db_dir, coll = RAG_DB, RAG_COLLECTION
                missing_hint = "먼저 `01_rag/step2_chunk.py` → `step3_embed_store.py`를 실행하세요."
            else:  # rag_wiki
                db_dir, coll = WIKI_RAG_DB, WIKI_RAG_COLLECTION
                missing_hint = ("먼저 `02_llm_wiki/step2_build_wiki.py` 후 "
                                "`03_rag_llm_wiki/step2_chunk_wiki.py` → `step3_embed_store.py`를 실행하세요.")
            if not os.path.isdir(db_dir):
                st.error(f"벡터 저장소가 없습니다. {missing_hint}")
                st.stop()

            with st.spinner("검색하고 답변 생성 중..."):
                collection = get_collection(db_dir, coll, api_key)
                hits = retrieve(collection, q, top_k)
                context = "\n\n---\n\n".join(
                    f"[{i}] 출처: {h['source']}"
                    + (f" ({h['section']})" if h["section"] else "")
                    + f"\n{h['document']}"
                    for i, h in enumerate(hits, start=1)
                )
                answer = generate(q, context, client, model)

            st.markdown("### 답변")
            st.write(answer)
            st.markdown("### 근거 문서")
            seen = []
            for h in hits:
                if h["source"] not in seen:
                    seen.append(h["source"])
            for s in seen:
                st.markdown(f"- `{s}`")
            render_hits(hits)
    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
elif run:
    st.info("질문을 입력해 주세요.")
