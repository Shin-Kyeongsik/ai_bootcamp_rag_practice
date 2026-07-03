"""
[01_rag] STEP 2 — 문서를 '청크'로 나누기 (청킹)

이 단계가 하는 일:
- 긴 문서를 그대로 검색하면 정확도가 떨어지므로, 마크다운 헤더(#, ##, ###)
  기준으로 의미 단위(섹션)로 잘게 나눈다. → 이 조각을 '청크(chunk)'라고 한다.
- 각 청크에 출처 파일명과 헤더 경로(섹션)를 메타데이터로 붙인다.
- 결과를 build/chunks.jsonl 로 저장해 다음 단계가 사용하고, 우리도 파일로 확인할 수 있다.

청킹 로직 자체는 rag_core.split_markdown_by_headers / enforce_max_chars 에 있다.

실행:
    python step2_chunk.py
"""

import os
import json
import rag_core


def main():
    chunks = rag_core.chunk_documents(rag_core.DOCS_DIR)

    os.makedirs(rag_core.BUILD_DIR, exist_ok=True)
    with open(rag_core.CHUNKS_PATH, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    print(f"생성된 청크 수: {len(chunks)}개")
    print(f"저장 위치: {os.path.relpath(rag_core.CHUNKS_PATH)}\n")

    # 문서별 청크 개수
    per_doc = {}
    for c in chunks:
        per_doc[c["source"]] = per_doc.get(c["source"], 0) + 1
    for src, n in per_doc.items():
        print(f"  - {src}: {n}개")

    # 샘플 청크 1개를 눈으로 확인
    sample = chunks[0]
    print("\n[샘플 청크 #0]")
    print(f"  출처: {sample['source']}")
    print(f"  섹션: {sample['section']}")
    print("  ── 본문 ──")
    print("  " + sample["document"].replace("\n", "\n  ")[:400])
    print("\n→ 다음: step3_embed_store.py (청크를 벡터로 변환해 저장합니다)")


if __name__ == "__main__":
    main()
