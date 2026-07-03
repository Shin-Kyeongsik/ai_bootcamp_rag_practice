"""
01_rag 공용 로직 — 청킹 / 임베딩 / 검색 / 생성.

step 스크립트들과 완성형 app.py가 이 모듈을 함께 사용한다.
각 step 스크립트는 이 함수들을 호출하면서 '무슨 일이 일어나는지'를 출력으로 보여준다.

- 검색 대상: ../bootcamp_docs/*.md (원본 안내 문서)
- 임베딩: OpenAI text-embedding-3-small
- 생성: OpenAI gpt-4o
"""

import os
import re
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI

# ── 경로/상수 ────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, "..", "bootcamp_docs")
BUILD_DIR = os.path.join(BASE_DIR, "build")
CHUNKS_PATH = os.path.join(BUILD_DIR, "chunks.jsonl")
DB_DIR = os.path.join(BASE_DIR, "chroma_db")
COLLECTION_NAME = "bootcamp_docs"


def _load_api_key_from_file():
    """수강생 편의: OPENAI_API_KEY 환경변수가 없으면 ../api_key.txt에서 읽어 설정한다.

    (환경변수가 이미 있으면 그대로 존중한다.)
    """
    if os.environ.get("OPENAI_API_KEY"):
        return
    key_path = os.path.join(BASE_DIR, "..", "api_key.txt")
    try:
        with open(key_path, encoding="utf-8") as f:
            key = f.read().strip()
    except FileNotFoundError:
        return
    if key:
        os.environ["OPENAI_API_KEY"] = key


_load_api_key_from_file()

EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
GEN_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
DEFAULT_TOP_K = 4
MAX_CHARS = 1200  # 청크가 이보다 길면 문단 단위로 재분할

SYSTEM_PROMPT = """당신은 'AI Agent 실무 부트캠프 2026'의 안내 AI입니다.
반드시 아래에 제공되는 '참고 문서' 내용만을 근거로 한국어로 답변하세요.

규칙:
1. 질문의 표현이나 단어가 참고 문서와 다르더라도, 문서에 관련 내용이 있으면
   그 내용을 근거로 최대한 답변하세요.
2. 부분적으로라도 답할 수 있으면 답하고, 문서에 없는 부분은 "그 부분은 문서에서
   확인할 수 없습니다"라고 덧붙이세요.
3. 참고 문서에 관련 내용이 전혀 없을 때만 "제공된 문서에서 확인할 수 없습니다"라고
   답하세요. 이 경우 절대 지어내지 마세요.
4. 날짜/시간/장소/조건은 문서에 적힌 값을 정확히 그대로 인용하세요.
5. 문서에 없는 일반 상식이나 추측으로 새로운 사실을 만들지 마세요.
"""


# ── 청킹 (step2에서 사용) ────────────────────────────────────
def split_markdown_by_headers(text: str):
    """마크다운을 헤더(#, ##, ###) 기준으로 섹션 단위로 분할한다.

    각 섹션은 (헤더 경로, 본문) 튜플. 상위 헤더를 이어붙여
    검색된 청크가 문서의 어느 부분인지 알 수 있게 한다.
    """
    lines = text.splitlines()
    sections = []
    header_stack = {}
    current_lines = []
    current_path = ""

    def flush():
        body = "\n".join(current_lines).strip()
        if body:
            sections.append((current_path, body))

    header_re = re.compile(r"^(#{1,6})\s+(.*)$")
    for line in lines:
        m = header_re.match(line)
        if m:
            flush()
            level = len(m.group(1))
            title = m.group(2).strip()
            for lv in list(header_stack.keys()):
                if lv >= level:
                    del header_stack[lv]
            header_stack[level] = title
            current_path = " > ".join(header_stack[lv] for lv in sorted(header_stack.keys()))
            current_lines = [line]
        else:
            current_lines.append(line)
    flush()
    return sections


def enforce_max_chars(path: str, body: str):
    """청크가 MAX_CHARS를 넘으면 문단 단위로 재분할한다."""
    if len(body) <= MAX_CHARS:
        return [(path, body)]
    parts, buf, length = [], [], 0
    for para in body.split("\n\n"):
        if length + len(para) > MAX_CHARS and buf:
            parts.append((path, "\n\n".join(buf).strip()))
            buf, length = [], 0
        buf.append(para)
        length += len(para) + 2
    if buf:
        parts.append((path, "\n\n".join(buf).strip()))
    return parts


def chunk_documents(docs_dir: str = DOCS_DIR):
    """docs_dir의 모든 .md를 청킹해 [dict] 리스트로 반환한다."""
    chunks = []
    md_files = sorted(f for f in os.listdir(docs_dir) if f.endswith(".md"))
    for filename in md_files:
        with open(os.path.join(docs_dir, filename), "r", encoding="utf-8") as f:
            text = f.read()
        idx = 0
        for header_path, body in split_markdown_by_headers(text):
            for hp, chunk in enforce_max_chars(header_path, body):
                chunks.append(
                    {
                        "id": f"{filename}::{idx}",
                        "document": chunk,
                        "source": f"bootcamp_docs/{filename}",
                        "section": hp,
                    }
                )
                idx += 1
    return chunks


# ── 임베딩 / 컬렉션 ──────────────────────────────────────────
def get_embedding_function(api_key: str = None):
    """OpenAI 임베딩 함수. 인덱싱과 검색이 같은 함수를 써야 한다."""
    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY가 필요합니다(임베딩에도 사용됩니다).")
    return embedding_functions.OpenAIEmbeddingFunction(api_key=key, model_name=EMBEDDING_MODEL)


def get_collection(api_key: str = None):
    """저장된 Chroma 컬렉션을 반환한다(인덱싱된 뒤에만 가능)."""
    if not os.path.isdir(DB_DIR):
        raise RuntimeError("벡터 저장소가 없습니다. 먼저 step3_embed_store.py를 실행하세요.")
    client = chromadb.PersistentClient(path=DB_DIR)
    return client.get_collection(COLLECTION_NAME, embedding_function=get_embedding_function(api_key))


# ── 검색 / 생성 ─────────────────────────────────────────────
def retrieve(collection, question: str, top_k: int = DEFAULT_TOP_K):
    """질문과 유사한 청크 top-k를 거리와 함께 반환한다(거리 작을수록 유사)."""
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


def build_context(hits) -> str:
    blocks = []
    for i, hit in enumerate(hits, start=1):
        header = f"[문서 {i}] 출처: {hit['source']}"
        if hit["section"]:
            header += f" (섹션: {hit['section']})"
        blocks.append(f"{header}\n{hit['document']}")
    return "\n\n---\n\n".join(blocks)


def unique_sources(hits):
    sources = []
    for hit in hits:
        if hit["source"] not in sources:
            sources.append(hit["source"])
    return sources


def generate_answer(question: str, hits, client: OpenAI, model: str = GEN_MODEL) -> str:
    context = build_context(hits)
    user_prompt = (
        f"참고 문서:\n{context}\n\n질문: {question}\n\n위 참고 문서만을 근거로 답변하세요."
    )
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
    )
    return completion.choices[0].message.content.strip()


def ask(question: str, collection, client: OpenAI, top_k: int = DEFAULT_TOP_K, model: str = GEN_MODEL):
    hits = retrieve(collection, question, top_k)
    if not hits:
        return {"answer": None, "sources": [], "hits": []}
    return {
        "answer": generate_answer(question, hits, client, model),
        "sources": unique_sources(hits),
        "hits": hits,
    }
