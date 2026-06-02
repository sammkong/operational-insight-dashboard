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
    response = requests.post(url, json=payload, timeout=300)
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
