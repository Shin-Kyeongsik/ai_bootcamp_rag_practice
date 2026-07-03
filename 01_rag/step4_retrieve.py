"""
[01_rag] STEP 4 — 질문으로 관련 청크 검색하기 (검색만, 생성 없음)

이 단계가 하는 일:
- 질문을 같은 임베딩으로 벡터로 바꾼 뒤, 벡터DB에서 '가장 가까운' 청크 top-k를 찾는다.
- LLM 답변 생성은 아직 하지 않는다. RAG의 핵심인 '검색' 단계만 눈으로 확인한다.
- 각 청크의 거리(작을수록 질문과 유사)와 출처/본문을 출력한다.

실행:
    python step4_retrieve.py "일일 과제는 어떻게 출제돼?"
"""

import sys
import os
import rag_core


def main():
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY 환경변수를 설정하세요(질문 임베딩에 사용).")
    question = " ".join(sys.argv[1:]).strip() or "수료 기준은 무엇인가요?"

    collection = rag_core.get_collection()
    hits = rag_core.retrieve(collection, question, top_k=rag_core.DEFAULT_TOP_K)

    print(f"질문: {question}")
    print(f"검색된 청크 {len(hits)}개 (거리가 작을수록 질문과 유사):\n")
    for i, hit in enumerate(hits, start=1):
        print(f"[{i}] 거리 {hit['distance']:.4f} | {hit['source']}"
              + (f" | {hit['section']}" if hit["section"] else ""))
        snippet = hit["document"].replace("\n", " ")[:120]
        print(f"    {snippet}...\n")

    print("→ 다음: step5_generate.py (검색된 청크를 근거로 LLM 답변을 만듭니다)")


if __name__ == "__main__":
    main()
