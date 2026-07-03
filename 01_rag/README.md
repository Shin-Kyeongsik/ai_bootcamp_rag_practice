# 01_rag — 원본 문서로 RAG 구성하기

원본 안내 문서(`../bootcamp_docs/`)를 **그대로** 청킹·검색해서 답변하는 RAG 파이프라인을,
번호 스텝으로 하나씩 따라가며 만듭니다.

## RAG 파이프라인 한눈에

```
문서 로드 → 청킹 → 임베딩·저장 → (질문) 검색 → 생성
step1      step2   step3         step4      step5
```

## 실행 순서

```bash
# API 키는 ../api_key.txt 에서 자동으로 불러옵니다 (별도 설정 불필요)

python step1_load.py                # ① 원본 문서 확인
python step2_chunk.py               # ② 청크로 분할 → build/chunks.jsonl
python step3_embed_store.py         # ③ 임베딩 → chroma_db/ 저장
python step4_retrieve.py "수료 기준은?"   # ④ 검색만 (거리 확인)
python step5_generate.py "수료 기준은?"   # ⑤ 검색 + 생성 (RAG 완성)
```

## 각 스텝이 보여주는 것

| 스텝 | 하는 일 | 눈으로 확인하는 산출물 |
|------|---------|------------------------|
| step1_load | 원본 문서 읽기 | 문서 목록·글자 수 |
| step2_chunk | 헤더 기준 청킹 | `build/chunks.jsonl`, 청크 수·샘플 |
| step3_embed_store | 임베딩 + 벡터DB 저장 | 임베딩 차원, 저장된 벡터 수 |
| step4_retrieve | 유사 청크 검색 | 각 청크의 **거리**·출처 |
| step5_generate | 근거로 답변 생성 | 답변 + 근거 문서 |

## 완성형 데모 (선택)

스텝을 다 이해했다면, 같은 로직을 묶은 웹 UI로도 볼 수 있습니다.

```bash
python step2_chunk.py && python step3_embed_store.py   # 인덱싱 먼저
streamlit run app.py
```

## 핵심 개념

- **RAG = 검색(Retrieval) + 생성(Generation)**: 답을 지어내지 않고, 먼저 관련 문서를 찾아 그 근거로 답한다.
- 문서에 없는 질문(예: "참가비는?")에는 **"확인할 수 없습니다"**로 답한다 → 일반 LLM의 환각과 대비된다.
- `rag_core.py`에 청킹/임베딩/검색/생성 함수가 모여 있고, 각 step 스크립트가 이를 호출하며 과정을 보여준다.

## 산출물

- `build/chunks.jsonl`, `chroma_db/` 는 실행 중 생성되는 산출물입니다(버전관리 제외 가능).
