# 03_rag_llm_wiki — 위키에 RAG 붙이기

02_llm_wiki가 만든 **정제된 위키**를 검색 대상으로 삼아 RAG(검색+생성)를 수행합니다.
01_rag와 파이프라인은 같고, **검색 대상이 원본 → 위키로 바뀐** 것이 핵심입니다.

> ⚠️ **선행 조건**: 먼저 `02_llm_wiki/step2_build_wiki.py`를 실행해 위키를 생성해야 합니다.
> 이 모듈은 `../02_llm_wiki/wiki/*.md` 를 입력으로 사용합니다.

## 파이프라인 한눈에

```
위키 준비 → 청킹 → 임베딩·저장 → (질문) 검색 → 생성
step1       step2   step3         step4      step5
```

## 실행 순서

```bash
# API 키는 ../api_key.txt 에서 자동으로 불러옵니다 (별도 설정 불필요)

# (선행) cd ../02_llm_wiki && python step2_build_wiki.py

python step1_prepare_wiki.py               # ① 위키 준비 확인
python step2_chunk_wiki.py                 # ② 위키를 청킹 → build/chunks.jsonl
python step3_embed_store.py                # ③ 임베딩 → chroma_db/ 저장
python step4_retrieve.py "수료 기준은?"      # ④ 위키에서 검색 (거리 확인)
python step5_generate.py "수료 기준은?"      # ⑤ 검색 + 생성
```

## 세 방식 비교로 마무리

| | 01_rag | 02_llm_wiki | 03_rag_llm_wiki |
|---|---|---|---|
| 검색 대상 | 원본 청크 | (검색 없음) | **위키 청크** |
| 지식 정제 | ✕ | ✅ | ✅ |
| 검색 | ✅ | ✕ | ✅ |
| 대규모 확장 | 원본이 커도 검색으로 대응 | 컨텍스트 한계 | **정제 + 검색**으로 가장 유리 |

**RAG + LLM Wiki**는 "지식을 미리 정리(위키)해서 검색 품질을 높이고, 검색으로 규모 문제도 푼다"는 두 장점을 합친 방식입니다.

## 산출물

- `build/chunks.jsonl`, `chroma_db/` 는 실행 중 생성되는 산출물입니다.
