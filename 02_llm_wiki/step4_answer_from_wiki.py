"""
[02_llm_wiki] STEP 4 — 위키로 질문에 답하기 (검색 없음, full-context)

이 단계가 하는 일:
- step2가 만든 wiki/*.md '전체'를 프롬프트의 컨텍스트로 넣고 답변을 생성한다.
- RAG처럼 '검색'하지 않는다. 이미 정제된 위키를 통째로 근거로 사용한다.
  (문서가 작아 전체가 컨텍스트에 들어가기 때문에 가능한 방식이다.)
- 위키에 없는 질문에는 지어내지 않고 '확인 불가'로 답한다.

사전 준비:
    export OPENAI_API_KEY=sk-...
    python step2_build_wiki.py    # 위키가 먼저 있어야 함

실행:
    python step4_answer_from_wiki.py "수료 기준은 무엇인가요?"
"""

import os
import sys
from openai import OpenAI
import config


def load_wiki():
    """wiki/*.md 를 모두 읽어 (출처 표시와 함께) 하나의 컨텍스트 문자열로 만든다."""
    files = sorted(f for f in os.listdir(config.WIKI_DIR) if f.endswith(".md"))
    blocks, names = [], []
    for name in files:
        with open(os.path.join(config.WIKI_DIR, name), "r", encoding="utf-8") as f:
            blocks.append(f"===== 위키 페이지: {name} =====\n{f.read()}")
        names.append(name)
    return "\n\n".join(blocks), names


def main():
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY 환경변수를 설정하세요(답변 생성에 사용).")
    if not os.path.isdir(config.WIKI_DIR):
        raise SystemExit("위키가 없습니다. 먼저 step2_build_wiki.py를 실행하세요.")

    question = " ".join(sys.argv[1:]).strip() or "수료 기준은 무엇인가요?"
    wiki_text, names = load_wiki()

    client = OpenAI()
    completion = client.chat.completions.create(
        model=config.GEN_MODEL,
        messages=[
            {"role": "system", "content": config.ANSWER_SYSTEM_PROMPT},
            {"role": "user", "content": f"위키:\n{wiki_text}\n\n질문: {question}"},
        ],
        temperature=0,
    )
    answer = completion.choices[0].message.content.strip()

    print(f"질문: {question}\n")
    print("답변:")
    print(answer)
    print(f"\n근거: 위키 {len(names)}개 페이지 전체를 컨텍스트로 사용")
    print("  (" + ", ".join(names) + ")")
    print("\n※ RAG(01)와 달리 검색 없이 위키 전체를 넣었습니다.")


if __name__ == "__main__":
    main()
