"""
03_rag_llm_wiki 공용 로직 — 청킹 / 임베딩 / 검색 / 생성.

01_rag와 구조는 같지만, 검색 대상이 '원본 문서'가 아니라
02_llm_wiki가 만든 '정제된 위키'다. (source = ../02_llm_wiki/wiki)

즉 RAG의 파이프라인은 동일하고, 입력 소스만 위키로 바뀐다.
"""

import os
import re
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 검색 대상: 02_llm_wiki가 생성한 위키
WIKI_DIR = os.path.join(BASE_DIR, "..", "02_llm_wiki", "wiki")
BUILD_DIR = os.path.join(BASE_DIR, "build")
CHUNKS_PATH = os.path.join(BUILD_DIR, "chunks.jsonl")
DB_DIR = os.path.join(BASE_DIR, "chroma_db")
COLLECTION_NAME = "bootcamp_wiki"


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
MAX_CHARS = 1200

SYSTEM_PROMPT = """당신은 'AI Agent 실무 부트캠프 2026'의 안내 AI입니다.
반드시 아래에 제공되는 '참고 위키' 내용만을 근거로 한국어로 답변하세요.

규칙:
1. 질문의 표현이 참고 위키와 다르더라도, 관련 내용이 있으면 그 근거로 최대한 답하세요.
2. 참고 위키에 관련 내용이 전혀 없을 때만 "제공된 위키에서 확인할 수 없습니다"라고
   답하세요. 이 경우 절대 지어내지 마세요.
3. 날짜/시간/장소/조건은 위키에 적힌 값을 정확히 그대로 인용하세요.
"""


# ── 청킹 ────────────────────────────────────────────────────
def split_markdown_by_headers(text: str):
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


def chunk_wiki(wiki_dir: str = WIKI_DIR):
    """위키 폴더의 모든 .md를 청킹해 [dict] 리스트로 반환한다."""
    chunks = []
    md_files = sorted(f for f in os.listdir(wiki_dir) if f.endswith(".md"))
    for filename in md_files:
        with open(os.path.join(wiki_dir, filename), "r", encoding="utf-8") as f:
            text = f.read()
        idx = 0
        for header_path, body in split_markdown_by_headers(text):
            for hp, chunk in enforce_max_chars(header_path, body):
                chunks.append({
                    "id": f"{filename}::{idx}",
                    "document": chunk,
                    "source": f"02_llm_wiki/wiki/{filename}",
                    "section": hp,
                })
                idx += 1
    return chunks


# ── 임베딩 / 컬렉션 ──────────────────────────────────────────
def get_embedding_function(api_key: str = None):
    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY가 필요합니다(임베딩에도 사용됩니다).")
    return embedding_functions.OpenAIEmbeddingFunction(api_key=key, model_name=EMBEDDING_MODEL)


def get_collection(api_key: str = None):
    if not os.path.isdir(DB_DIR):
        raise RuntimeError("벡터 저장소가 없습니다. 먼저 step3_embed_store.py를 실행하세요.")
    client = chromadb.PersistentClient(path=DB_DIR)
    return client.get_collection(COLLECTION_NAME, embedding_function=get_embedding_function(api_key))


# ── 검색 / 생성 ─────────────────────────────────────────────
def retrieve(collection, question: str, top_k: int = DEFAULT_TOP_K):
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
        header = f"[위키 {i}] 출처: {hit['source']}"
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
    user_prompt = f"참고 위키:\n{context}\n\n질문: {question}\n\n위 참고 위키만을 근거로 답변하세요."
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
