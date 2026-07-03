"""
02_llm_wiki 공용 설정 — 경로 / 모델 / 프롬프트 / 주제 매핑.

LLM Wiki 방식:
  원본 문서 → (LLM이 요약·정규화·중복통합) → 주제별 위키 → 위키 전체로 답변.
RAG와 달리 '검색'이 없다. 지식을 미리 위키로 정제해 두고, 그걸 통째로 근거로 쓴다.
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, "..", "bootcamp_docs")
WIKI_DIR = os.path.join(BASE_DIR, "wiki")


def _load_api_key_from_file():
    """수강생 편의: OPENAI_API_KEY 환경변수가 없으면 ../api_key.txt에서 읽어 설정한다.

    (환경변수가 이미 있으면 그대로 존중한다.)
    """
    if os.environ.get("OPENAI_API_KEY"):
        return
    key_path = os.path.join(BASE_DIR, "..", "api_key.txt")
    try:
        with open(key_path, encoding="utf-8") as f:
            key = f.read().strip()
    except FileNotFoundError:
        return
    if key:
        os.environ["OPENAI_API_KEY"] = key


_load_api_key_from_file()

GEN_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")

# 원본 문서 → 위키 페이지 매핑.
# (출력 파일명, 위키 페이지 제목, [원본 파일들])
# 08+09 처럼 여러 원본을 하나로 '통합'하는 경우가 재구성의 핵심을 보여준다.
TOPICS = [
    ("01_개요.md", "부트캠프 개요", ["01_부트캠프_개요.md"]),
    ("02_일정.md", "전체 일정", ["02_전체_일정표.md"]),
    ("03_장소_등록.md", "장소 및 등록 안내", ["03_장소_및_등록_안내.md"]),
    ("04_실습환경.md", "실습 환경 설치 가이드", ["04_실습_환경_설치_가이드.md"]),
    ("05_일차별_실습.md", "일차별 실습 안내", ["05_일차별_실습_안내.md"]),
    ("06_과제.md", "과제 제출 규칙", ["06_과제_제출_규칙.md"]),
    ("07_수료.md", "수료 기준", ["07_수료_기준.md"]),
    ("08_멘토링_FAQ.md", "멘토링 및 자주 묻는 질문(FAQ)",
     ["08_멘토링_및_QA_안내.md", "09_참가자_FAQ.md"]),
]

# 위키를 만들 때 LLM에게 주는 규칙 (환각 금지가 핵심)
WIKI_SYSTEM_PROMPT = """당신은 부트캠프 안내 문서를 정리하는 편집자입니다.
주어진 '원본 문서' 내용만을 사용해, 깔끔한 위키 페이지를 한국어 Markdown으로 작성하세요.

규칙:
1. 원본에 없는 사실을 새로 지어내지 마세요. 오직 원본 내용만 재구성합니다.
2. 날짜/시간/장소/조건 등 구체적 값은 원본 그대로 정확히 유지하세요.
3. 중복되는 내용은 하나로 통합하고, 핵심을 표·목록으로 구조화하세요.
4. 페이지 맨 위에 '# {제목}'과 2~3줄 요약을 두고, 이어서 세부 내용을 정리하세요.
5. 사족(인사말, 메타 설명) 없이 위키 본문만 출력하세요.
"""

# 위키로 답변할 때 LLM에게 주는 규칙
ANSWER_SYSTEM_PROMPT = """당신은 'AI Agent 실무 부트캠프 2026'의 안내 AI입니다.
아래 '위키'는 부트캠프 안내 문서를 정리한 것입니다. 이 위키 내용만을 근거로 한국어로 답하세요.

규칙:
1. 위키에 관련 내용이 있으면 그 근거로 최대한 답하세요(표현이 달라도 됩니다).
2. 위키에 전혀 없는 내용이면 "제공된 위키에서 확인할 수 없습니다"라고 답하고, 지어내지 마세요.
3. 날짜/시간/장소/조건은 위키에 적힌 값을 정확히 인용하세요.
"""
