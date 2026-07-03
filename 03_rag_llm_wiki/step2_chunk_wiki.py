"""
[03_rag_llm_wiki] STEP 2 — 위키를 '청크'로 나누기

이 단계가 하는 일:
- 01_rag와 동일한 청킹 방식으로, 이번엔 '위키'를 검색 단위로 나눈다.
- 원본이 아니라 정제된 위키를 청킹한다는 점만 다르다.
- 결과를 build/chunks.jsonl 로 저장한다.

사전 준비:
    python step1_prepare_wiki.py   # 위키가 준비돼 있어야 함

실행:
    python step2_chunk_wiki.py
"""

import os
import json
import rag_core


def main():
    chunks = rag_core.chunk_wiki(rag_core.WIKI_DIR)

    os.makedirs(rag_core.BUILD_DIR, exist_ok=True)
    with open(rag_core.CHUNKS_PATH, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    print(f"생성된 청크 수: {len(chunks)}개")
    print(f"저장 위치: {os.path.relpath(rag_core.CHUNKS_PATH)}\n")

    per_doc = {}
    for c in chunks:
        per_doc[c["source"]] = per_doc.get(c["source"], 0) + 1
    for src, n in per_doc.items():
        print(f"  - {src}: {n}개")

    sample = chunks[0]
    print("\n[샘플 청크 #0]")
    print(f"  출처: {sample['source']}")
    print(f"  섹션: {sample['section']}")
    print("  " + sample["document"].replace("\n", "\n  ")[:400])
    print("\n→ 다음: step3_embed_store.py")


if __name__ == "__main__":
    main()
