"""
[03_rag_llm_wiki] STEP 3 — 위키 청크를 벡터로 변환해 저장하기

이 단계가 하는 일:
- build/chunks.jsonl(위키 청크)을 OpenAI 임베딩으로 벡터화해 Chroma에 저장한다.
- 01_rag와 완전히 같은 과정. 저장되는 내용이 원본 청크가 아니라 '위키 청크'일 뿐이다.

사전 준비:
    export OPENAI_API_KEY=sk-...
    python step2_chunk_wiki.py

실행:
    python step3_embed_store.py
"""

import os
import json
import chromadb
import rag_core


def main():
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY 환경변수를 설정하세요(임베딩에 사용).")
    if not os.path.exists(rag_core.CHUNKS_PATH):
        raise SystemExit("청크 파일이 없습니다. 먼저 step2_chunk_wiki.py를 실행하세요.")

    chunks = []
    with open(rag_core.CHUNKS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            chunks.append(json.loads(line))
    print(f"불러온 위키 청크: {len(chunks)}개")

    ef = rag_core.get_embedding_function()
    sample_vec = ef([chunks[0]["document"]])[0]
    print(f"임베딩 모델: {rag_core.EMBEDDING_MODEL}")
    print(f"임베딩 차원(벡터 길이): {len(sample_vec)}")

    client = chromadb.PersistentClient(path=rag_core.DB_DIR)
    try:
        client.delete_collection(rag_core.COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(rag_core.COLLECTION_NAME, embedding_function=ef)

    collection.add(
        ids=[c["id"] for c in chunks],
        documents=[c["document"] for c in chunks],
        metadatas=[{"source": c["source"], "section": c["section"]} for c in chunks],
    )

    print(f"\n벡터DB에 저장된 위키 청크 수: {collection.count()}개")
    print(f"저장 위치: {os.path.relpath(rag_core.DB_DIR)}")
    print("→ 다음: step4_retrieve.py")


if __name__ == "__main__":
    main()
