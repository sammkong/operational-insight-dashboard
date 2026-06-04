import requests

from src.config import OLLAMA_BASE_URL, OLLAMA_MODEL


SYSTEM_RULES = """당신은 운영 데이터 분석가입니다.

규칙:
1. 반드시 한국어로만 답변하세요.
2. 분석 결과에 없는 숫자를 만들어내지 마세요.
3. 제공된 데이터만 기반으로 판단하세요.
4. 답변은 운영 담당자가 읽는 보고서 형태로 작성하세요.
5. 불필요한 추론 과정을 출력하지 마세요.
6. Thinking 과정은 출력하지 마세요.
7. 최종 답변만 출력하세요.
8. 추론 과정은 출력하지 마세요.
9. 800자 이내로 답변하세요.

출력 형식:

[운영 리스크]

...

[원인 분석]

...

[개선안]

...
"""


DEFAULT_RECOMMENDED_ACTIONS = [
    "반복 키워드 분석",
    "신규 카테고리 정의",
    "FAQ 분리",
    "운영 가이드 보강",
]

DEFAULT_EXPECTED_IMPACTS = [
    "재오픈율 감소",
    "분류 정확도 향상",
    "운영 리소스 절감",
    "FAQ 활용률 증가",
]

INSIGHT_FALLBACKS = {
    "risk_summary": (
        "Other 카테고리는 재오픈율이 높고 분류 범위가 넓어, "
        "현재 카테고리 체계가 운영 리스크를 충분히 설명하지 못할 가능성이 있습니다."
    ),
    "improvement_plan": (
        "Other 카테고리 세분화, Phone 채널 상담 가이드 정비, "
        "Account SOP 보강을 우선 개선안으로 제안합니다."
    ),
    "resource_plan": (
        "Risk Score가 높은 Other, Delivery, Technical 문의 유형에 "
        "운영 리소스를 우선 배치하는 것이 효과적입니다."
    ),
}


def clean_llm_response(response: str, max_sentences: int = 5) -> str:
    text = " ".join((response or "").split())
    if not text:
        return ""

    sentences = []
    sentence = ""
    for char in text:
        sentence += char
        if char in ".!?。！？":
            sentences.append(sentence.strip())
            sentence = ""
        if len(sentences) >= max_sentences:
            break
    if sentence and len(sentences) < max_sentences:
        sentences.append(sentence.strip())

    return " ".join(sentences[:max_sentences])


def extract_recommended_actions(response: str) -> list[str]:
    actions = []
    for line in (response or "").splitlines():
        item = line.strip().lstrip("-*0123456789. ").strip()
        if item and any(keyword in item for keyword in ("분석", "정의", "FAQ", "가이드", "개선", "보강")):
            actions.append(item)
        if len(actions) >= 4:
            break
    return actions or DEFAULT_RECOMMENDED_ACTIONS


def fallback_insight(top_risk=None, insight_type: str = "risk_summary") -> str:
    if insight_type in INSIGHT_FALLBACKS:
        return INSIGHT_FALLBACKS[insight_type]

    category = "Other"
    if top_risk is not None:
        category = top_risk.get("issue_category", category)
    return (
        f"{category} 카테고리는 재오픈율이 높고 분류 범위가 넓어, "
        "현재 카테고리 체계가 운영 리스크를 충분히 설명하지 못할 가능성이 있습니다. "
        "반복 키워드 분석을 통해 신규 카테고리 분리가 필요합니다."
    )


def _call_ollama(prompt: str) -> str:
    url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 500,
            "num_ctx": 4096,
        },
    }
    response = requests.post(url, json=payload, timeout=15)
    response.raise_for_status()
    return response.json().get("response", "").strip()


def generate_risk_summary(analysis_summary: str) -> str:
    prompt = f"""{SYSTEM_RULES}

분석 결과:
{analysis_summary}

질문: 이번 데이터에서 가장 중요한 운영 리스크는 무엇인가?
"""
    return _call_ollama(prompt)


def generate_improvement_plan(analysis_summary: str) -> str:
    prompt = f"""{SYSTEM_RULES}

분석 결과:
{analysis_summary}

질문: 재오픈율이 높은 유형에 대해 어떤 운영 개선이 필요한가?
"""
    return _call_ollama(prompt)


def generate_resource_plan(analysis_summary: str) -> str:
    prompt = f"""{SYSTEM_RULES}

분석 결과:
{analysis_summary}

질문: 운영 리소스를 어디에 우선 배치해야 하는가?
"""
    return _call_ollama(prompt)
