"""
[01_rag] STEP 5 — 검색된 청크로 답변 생성하기 (RAG 완성)

이 단계가 하는 일:
- step4의 검색 결과(관련 청크)를 프롬프트의 '참고 문서'로 넣고,
  LLM에게 "이 문서만 근거로 답하라"고 지시해 최종 답변을 만든다.
- 이렇게 검색(Retrieval) + 생성(Generation)을 합친 것이 RAG다.
- 답변과 함께 근거 문서를 표시한다. 문서에 없으면 지어내지 않고 '확인 불가'로 답한다.

실행:
    python step5_generate.py "수료 기준은 무엇인가요?"
"""

import sys
import os
from openai import OpenAI
import rag_core


def main():
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY 환경변수를 설정하세요(검색 임베딩 + 답변 생성에 사용).")
    question = " ".join(sys.argv[1:]).strip() or "수료 기준은 무엇인가요?"

    collection = rag_core.get_collection()
    client = OpenAI()

    # 검색 → 생성 (rag_core.ask 가 두 단계를 함께 수행)
    result = rag_core.ask(question, collection, client)

    print(f"질문: {question}\n")
    print("답변:")
    print(result["answer"])
    print("\n근거 문서:")
    for s in result["sources"]:
        print(f"- {s}")

    print("\n(참고) 검색된 청크의 거리:")
    for i, hit in enumerate(result["hits"], start=1):
        print(f"  [{i}] 거리 {hit['distance']:.4f} | {hit['source']}")


if __name__ == "__main__":
    main()
