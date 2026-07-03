"""
[02_llm_wiki] STEP 1 — 원본 문서 불러오기

이 단계가 하는 일:
- 위키로 재구성할 재료인 ../bootcamp_docs/*.md 를 읽어온다.
- 어떤 원본이 어떤 위키 페이지로 묶일지(주제 매핑)를 미리 보여준다.

실행:
    python step1_load.py
"""

import os
import config


def main():
    if not os.path.isdir(config.DOCS_DIR):
        raise SystemExit(f"문서 폴더를 찾을 수 없습니다: {config.DOCS_DIR}")

    md_files = sorted(f for f in os.listdir(config.DOCS_DIR) if f.endswith(".md"))
    print(f"원본 문서: {len(md_files)}개 ({os.path.relpath(config.DOCS_DIR)})")
    for filename in md_files:
        with open(os.path.join(config.DOCS_DIR, filename), "r", encoding="utf-8") as f:
            n = len(f.read())
        print(f"  - {filename}: {n:,}자")

    print("\n원본 → 위키 페이지 매핑(step2에서 이렇게 재구성):")
    for out_name, title, sources in config.TOPICS:
        print(f"  - {out_name}  ←  {', '.join(sources)}   ({title})")

    print("\n→ 다음: step2_build_wiki.py (LLM이 원본을 위키로 재구성합니다)")


if __name__ == "__main__":
    main()
