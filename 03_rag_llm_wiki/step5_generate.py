"""
[03_rag_llm_wiki] STEP 5 — 검색된 위키 청크로 답변 생성하기 (RAG + Wiki 완성)

이 단계가 하는 일:
- step4에서 검색한 '위키 청크'를 근거로 LLM 답변을 만든다.
- 01_rag와 파이프라인은 같지만, 근거가 원본이 아니라 정제된 위키다.
  → 검색 대상을 원본에서 위키로 바꾼 것이 'RAG + LLM Wiki'다.

실행:
    python step5_generate.py "수료 기준은 무엇인가요?"
"""

import os
import sys
from openai import OpenAI
import rag_core


def main():
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY 환경변수를 설정하세요(검색 임베딩 + 답변 생성에 사용).")
    question = " ".join(sys.argv[1:]).strip() or "수료 기준은 무엇인가요?"

    collection = rag_core.get_collection()
    client = OpenAI()
    result = rag_core.ask(question, collection, client)

    print(f"질문: {question}\n")
    print("답변:")
    print(result["answer"])
    print("\n근거 (위키):")
    for s in result["sources"]:
        print(f"- {s}")

    print("\n(참고) 검색된 위키 청크의 거리:")
    for i, hit in enumerate(result["hits"], start=1):
        print(f"  [{i}] 거리 {hit['distance']:.4f} | {hit['source']}")


if __name__ == "__main__":
    main()
