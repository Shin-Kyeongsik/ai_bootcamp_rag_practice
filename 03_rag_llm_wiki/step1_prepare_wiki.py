"""
[03_rag_llm_wiki] STEP 1 — 위키 준비 확인

이 단계가 하는 일:
- 검색 대상인 위키(../02_llm_wiki/wiki/*.md)가 준비돼 있는지 확인한다.
- 이 모듈은 원본이 아니라 '02에서 만든 정제된 위키'를 검색 대상으로 삼는다.
- 위키가 없으면 02_llm_wiki를 먼저 실행하도록 안내한다.

실행:
    python step1_prepare_wiki.py
"""

import os
import rag_core


def main():
    if not os.path.isdir(rag_core.WIKI_DIR):
        raise SystemExit(
            "위키가 없습니다. 먼저 02_llm_wiki를 실행하세요:\n"
            "    cd ../02_llm_wiki && python step2_build_wiki.py"
        )

    wiki_files = sorted(f for f in os.listdir(rag_core.WIKI_DIR) if f.endswith(".md"))
    if not wiki_files:
        raise SystemExit("위키 폴더가 비어 있습니다. 02_llm_wiki/step2_build_wiki.py를 실행하세요.")

    print(f"검색 대상 위키: {len(wiki_files)}개 ({os.path.relpath(rag_core.WIKI_DIR)})")
    total = 0
    for name in wiki_files:
        with open(os.path.join(rag_core.WIKI_DIR, name), "r", encoding="utf-8") as f:
            n = len(f.read())
        total += n
        print(f"  - {name}: {n:,}자")
    print(f"\n위키 총 글자 수: {total:,}자")
    print("→ 다음: step2_chunk_wiki.py (위키를 청크로 나눕니다)")


if __name__ == "__main__":
    main()
