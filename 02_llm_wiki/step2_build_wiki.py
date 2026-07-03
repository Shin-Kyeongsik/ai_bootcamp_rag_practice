"""
[02_llm_wiki] STEP 2 — LLM으로 원본을 '위키'로 재구성하기 (핵심 단계)

이 단계가 하는 일:
- config.TOPICS 매핑에 따라, 원본 문서를 LLM에게 주고 '위키 페이지'로 재구성시킨다.
  (요약·정규화·중복 통합·표 정리. 단, 원본에 없는 사실은 지어내지 않도록 지시.)
- 결과를 wiki/*.md 로 저장한다. → 생성된 위키를 파일로 열어 눈으로 확인할 수 있다.

이것이 RAG와의 가장 큰 차이: RAG는 원본을 그대로 두지만, LLM Wiki는 '미리' 지식을 정제한다.

사전 준비:
    export OPENAI_API_KEY=sk-...

실행:
    python step2_build_wiki.py
"""

import os
from openai import OpenAI
import config


def read_sources(source_files):
    parts = []
    for name in source_files:
        with open(os.path.join(config.DOCS_DIR, name), "r", encoding="utf-8") as f:
            parts.append(f"===== 원본 파일: {name} =====\n{f.read()}")
    return "\n\n".join(parts)


def main():
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY 환경변수를 설정하세요(위키 생성에 사용).")

    os.makedirs(config.WIKI_DIR, exist_ok=True)
    client = OpenAI()

    print(f"LLM({config.GEN_MODEL})으로 위키 {len(config.TOPICS)}개 페이지를 생성합니다...\n")
    for out_name, title, sources in config.TOPICS:
        source_text = read_sources(sources)
        user_prompt = (
            f"원본 문서:\n{source_text}\n\n"
            f"위 내용을 '{title}' 위키 페이지로 정리해 주세요. "
            f"'# {title}' 제목으로 시작하세요."
        )
        completion = client.chat.completions.create(
            model=config.GEN_MODEL,
            messages=[
                {"role": "system", "content": config.WIKI_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
        )
        wiki_md = completion.choices[0].message.content.strip()
        out_path = os.path.join(config.WIKI_DIR, out_name)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(wiki_md + "\n")
        print(f"  ✓ {out_name}  ←  {', '.join(sources)}   ({len(wiki_md):,}자)")

    print(f"\n위키 저장 위치: {os.path.relpath(config.WIKI_DIR)}")
    print("→ 다음: step3_inspect_wiki.py (생성된 위키를 확인) 또는 step4_answer_from_wiki.py")


if __name__ == "__main__":
    main()
