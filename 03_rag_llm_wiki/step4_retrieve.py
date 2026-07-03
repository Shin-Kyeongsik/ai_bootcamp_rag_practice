"""
[03_rag_llm_wiki] STEP 4 — 질문으로 위키 청크 검색하기 (검색만)

이 단계가 하는 일:
- 질문을 벡터로 바꿔, 위키 벡터DB에서 가장 가까운 청크 top-k를 찾는다.
- 01_rag의 검색과 동일하지만, 검색 결과가 '원본 청크'가 아니라 '위키 청크'다.
- 각 청크의 거리(작을수록 유사)와 출처(위키 페이지)를 출력한다.

실행:
    python step4_retrieve.py "수료 기준은 무엇인가요?"
"""

import os
import sys
import rag_core


def main():
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY 환경변수를 설정하세요(질문 임베딩에 사용).")
    question = " ".join(sys.argv[1:]).strip() or "수료 기준은 무엇인가요?"

    collection = rag_core.get_collection()
    hits = rag_core.retrieve(collection, question, top_k=rag_core.DEFAULT_TOP_K)

    print(f"질문: {question}")
    print(f"검색된 위키 청크 {len(hits)}개 (거리가 작을수록 유사):\n")
    for i, hit in enumerate(hits, start=1):
        print(f"[{i}] 거리 {hit['distance']:.4f} | {hit['source']}"
              + (f" | {hit['section']}" if hit["section"] else ""))
        snippet = hit["document"].replace("\n", " ")[:120]
        print(f"    {snippet}...\n")

    print("→ 다음: step5_generate.py")


if __name__ == "__main__":
    main()
