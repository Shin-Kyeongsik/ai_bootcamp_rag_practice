"""
[02_llm_wiki] STEP 3 — 생성된 위키 살펴보기 (선택)

이 단계가 하는 일:
- step2가 만든 wiki/*.md 목록과 각 페이지의 첫 부분(요약)을 출력한다.
- 원본 대비 얼마나 압축·정리됐는지 글자 수로 비교해 '재구성 효과'를 눈으로 본다.

실행:
    python step3_inspect_wiki.py
"""

import os
import config


def main():
    if not os.path.isdir(config.WIKI_DIR):
        raise SystemExit("위키가 없습니다. 먼저 step2_build_wiki.py를 실행하세요.")

    # 원본 총 글자 수
    docs_chars = 0
    for out_name, title, sources in config.TOPICS:
        for name in sources:
            with open(os.path.join(config.DOCS_DIR, name), "r", encoding="utf-8") as f:
                docs_chars += len(f.read())

    wiki_files = sorted(f for f in os.listdir(config.WIKI_DIR) if f.endswith(".md"))
    wiki_chars = 0
    print(f"생성된 위키 페이지: {len(wiki_files)}개\n")
    for name in wiki_files:
        with open(os.path.join(config.WIKI_DIR, name), "r", encoding="utf-8") as f:
            text = f.read()
        wiki_chars += len(text)
        # 첫 5줄(제목 + 요약)만 미리보기
        preview = "\n    ".join(text.splitlines()[:5])
        print(f"[{name}] {len(text):,}자")
        print(f"    {preview}\n")

    print("── 재구성 효과 ──")
    print(f"원본 총합: {docs_chars:,}자  →  위키 총합: {wiki_chars:,}자")
    if docs_chars:
        print(f"압축률: 위키가 원본의 약 {wiki_chars / docs_chars * 100:.0f}%")
    print("\n→ 다음: step4_answer_from_wiki.py (위키로 질문에 답합니다)")


if __name__ == "__main__":
    main()
