"""
[01_rag] STEP 1 — 원본 문서 불러오기

이 단계가 하는 일:
- RAG의 검색 대상인 ../bootcamp_docs/*.md 문서들을 읽어온다.
- 어떤 문서가 몇 글자인지 출력해, 우리가 무엇을 다루는지 눈으로 확인한다.
- (아직 청킹/임베딩은 하지 않는다. 이 단계는 '재료 확인'이다.)

실행:
    python step1_load.py
"""

import os
import rag_core


def main():
    docs_dir = rag_core.DOCS_DIR
    if not os.path.isdir(docs_dir):
        raise SystemExit(f"문서 폴더를 찾을 수 없습니다: {docs_dir}")

    md_files = sorted(f for f in os.listdir(docs_dir) if f.endswith(".md"))
    print(f"원본 문서 폴더: {os.path.relpath(docs_dir)}")
    print(f"문서 개수: {len(md_files)}개\n")

    total_chars = 0
    for filename in md_files:
        with open(os.path.join(docs_dir, filename), "r", encoding="utf-8") as f:
            text = f.read()
        total_chars += len(text)
        print(f"  - {filename}: {len(text):,}자")

    print(f"\n전체 글자 수: {total_chars:,}자")
    print("→ 다음: step2_chunk.py (문서를 검색 단위인 '청크'로 나눕니다)")


if __name__ == "__main__":
    main()
