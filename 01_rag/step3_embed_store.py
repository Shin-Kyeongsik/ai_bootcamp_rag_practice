"""
[01_rag] STEP 3 — 청크를 벡터로 변환해 저장하기 (임베딩 + 벡터DB)

이 단계가 하는 일:
- build/chunks.jsonl 의 각 청크를 OpenAI 임베딩으로 '벡터(숫자 배열)'로 변환한다.
  → 의미가 비슷한 문장은 벡터 공간에서 가까이 위치한다.
- 변환한 벡터를 Chroma 벡터DB(chroma_db/)에 저장한다. 이제 '의미로 검색'할 수 있다.

사전 준비:
    export OPENAI_API_KEY=sk-...   # 임베딩 호출에 사용
    python step2_chunk.py          # 청크가 먼저 있어야 함

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
        raise SystemExit("청크 파일이 없습니다. 먼저 step2_chunk.py를 실행하세요.")

    # 1) 청크 로드
    chunks = []
    with open(rag_core.CHUNKS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            chunks.append(json.loads(line))
    print(f"불러온 청크: {len(chunks)}개")

    # 2) 임베딩 함수 준비 (이 함수가 청크를 벡터로 바꿔줌)
    ef = rag_core.get_embedding_function()
    sample_vec = ef([chunks[0]["document"]])[0]
    print(f"임베딩 모델: {rag_core.EMBEDDING_MODEL}")
    print(f"임베딩 차원(벡터 길이): {len(sample_vec)}")

    # 3) Chroma 컬렉션 새로 만들기 (재실행 시 기존 것 삭제)
    client = chromadb.PersistentClient(path=rag_core.DB_DIR)
    try:
        client.delete_collection(rag_core.COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(rag_core.COLLECTION_NAME, embedding_function=ef)

    # 4) 저장 (Chroma가 각 문서를 임베딩해서 벡터와 함께 보관)
    collection.add(
        ids=[c["id"] for c in chunks],
        documents=[c["document"] for c in chunks],
        metadatas=[{"source": c["source"], "section": c["section"]} for c in chunks],
    )

    print(f"\n벡터DB에 저장된 청크 수: {collection.count()}개")
    print(f"저장 위치: {os.path.relpath(rag_core.DB_DIR)}")
    print("→ 다음: step4_retrieve.py (질문으로 관련 청크를 검색해 봅니다)")


if __name__ == "__main__":
    main()
