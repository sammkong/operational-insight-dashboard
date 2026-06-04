# Operational Insight Dashboard

> CS 운영 데이터를 분석해 운영 리스크를 정량화하고, Risk Score를 기반으로 개선 우선순위를 도출한 포트폴리오 프로젝트

## 프로젝트 개요

Kaggle Customer Support Tickets Dataset을 활용해 고객 지원 티켓 데이터를 분석했습니다.

처음에는 문의 유형별 건수와 처리시간을 확인하는 일반적인 운영 대시보드로 접근했습니다. 하지만 데이터를 분석해보니 **문의량만으로는 운영 리스크를 설명하기 어렵다**는 점이 드러났습니다.

재오픈율은 반복 문의와 고객 경험 저하 가능성을 보여주고, 처리시간은 운영 병목 가능성을 보여줍니다. 여기에 티켓 우선순위까지 함께 보면 각 지표가 서로 다른 위험 신호를 보여준다는 것을 확인할 수 있었습니다.

그래서 이 프로젝트에서는 단일 KPI를 보여주는 데서 멈추지 않고, **Reopened Rate, Resolution Time, Priority Weight를 통합한 Risk Score**를 설계했습니다. 목표는 운영자가 어떤 영역을 먼저 개선해야 하는지 판단할 수 있는 기준을 만드는 것이었습니다.

| 항목 | 내용 |
| --- | --- |
| 데이터 | Kaggle Customer Support Ticket Satisfaction Analysis |
| 분석 단위 | 고객 지원 티켓 2,800건 |
| 핵심 목표 | 운영 리스크 정량화 및 개선 우선순위 도출 |
| 주요 지표 | 재오픈율, 처리시간, 우선순위 |
| 결과물 | Streamlit Operational Insight Dashboard |

## 왜 이 프로젝트를 시작했는가?

CS 운영에서는 문의가 많이 들어오는 영역만 보는 것으로는 충분하지 않습니다.

데이터를 분석하면서 특히 재오픈된 티켓에 주목했습니다. 재오픈은 한 번 해결된 것처럼 보였던 문제가 다시 돌아온다는 의미이기 때문에, 운영 비용 증가와 고객 경험 저하로 이어질 수 있습니다.

하지만 재오픈율만 봐도 한계가 있었습니다. 어떤 카테고리는 재오픈율이 높고, 어떤 카테고리는 처리시간이 길었습니다. 즉, 운영 리스크는 하나의 숫자로 쉽게 설명되지 않았습니다.

이 지점에서 프로젝트의 방향이 명확해졌습니다.

> 단순히 데이터를 보여주는 대시보드가 아니라, 운영자가 개선 우선순위를 판단할 수 있는 기준을 만들어야 한다.

## 문제 정의

분석 과정에서 확인한 문제는 세 가지였습니다.

- 문의량이 많은 영역이 반드시 운영 리스크가 높은 것은 아니었습니다.
- 재오픈율이 높은 영역과 처리시간이 긴 영역이 서로 달랐습니다.
- 운영 개선 우선순위를 정하려면 여러 KPI를 함께 해석할 기준이 필요했습니다.

따라서 이 프로젝트의 핵심 문제는 다음과 같이 정의했습니다.

> CS 운영 데이터에서 재오픈율, 처리시간, 우선순위를 함께 고려해 어떤 영역을 먼저 개선해야 하는지 판단할 수 있는가?

## 분석 과정

분석은 아래 흐름으로 진행했습니다.

```text
STEP 1
재오픈율을 운영 품질 KPI로 선정

↓

EDA 1
Issue Category 기준 재오픈율 분석
결과: Other 카테고리 재오픈율 최고

↓

EDA 2
Channel 기준 재오픈율 분석
결과: Phone 채널 재오픈율 최고

↓

EDA 3
처리시간 기준 분석
결과: Account 카테고리 처리시간 최고

↓

문제 발견
재오픈율 기준 위험 영역과 처리시간 기준 위험 영역이 다름

↓

단일 KPI 한계 발견

↓

Risk Score 설계
Reopened Rate + Resolution Time + Priority Weight 통합 평가

↓

운영 개선 우선순위 도출

↓

Dashboard
```

분석은 SQL과 Pandas를 중심으로 진행했고, 계산된 KPI와 Risk Score를 Streamlit 대시보드로 시각화했습니다.

## 데이터 개요

데이터는 고객 지원 티켓 단위로 구성되어 있으며, 주요 분석 컬럼은 다음과 같습니다.

| 컬럼 | 설명 |
| --- | --- |
| `issue_category` | 문의 유형 |
| `channel` | 문의 채널 |
| `priority` | 티켓 우선순위 |
| `resolution_time_hours` | 해결까지 걸린 시간 |
| `reopened` | 재오픈 여부 |
| `agent_experience_years` | 상담 담당자 경험 연차 |
| `customer_satisfaction` | 고객 만족도 참고 지표 |

## 탐색적 데이터 분석 (EDA)

EDA는 데이터를 다각도로 관찰하며 주요 특성과 패턴을 파악하는 초기 분석 단계입니다.

이 프로젝트에서는 운영 리스크를 설명할 수 있는 지표를 찾기 위해 문의 유형, 채널, 처리시간 기준으로 데이터를 나누어 확인했습니다.

### EDA 1. Issue Category 기준 재오픈율 분석

<img src="docs/eda-category.png" width="820" alt="Issue Category 기준 재오픈율 분석 화면">

문의 유형별 재오픈율을 확인한 결과, **Other 카테고리의 재오픈율이 52.44%로 가장 높게 나타났습니다.**

Other가 높다는 것은 단순히 특정 문의 유형이 위험하다는 의미라기보다, 여러 유형의 문의가 하나의 카테고리에 섞여 있을 가능성을 보여줍니다. 분류가 충분히 세분화되지 않으면 반복 이슈를 찾기 어렵고, 상담 가이드나 FAQ 개선도 정교하게 설계하기 어렵습니다.

### EDA 2. Channel 기준 재오픈율 분석

<img src="docs/eda-channel.png" width="820" alt="Channel 기준 재오픈율 분석 화면">

채널별 재오픈율을 확인한 결과, **Phone 채널의 재오픈율이 50.27%로 가장 높게 나타났습니다.**

Phone 채널은 실시간 상담 특성상 상담 내용 기록, 후속 조치, 에스컬레이션 기준이 충분히 정리되지 않으면 같은 문제가 다시 열릴 가능성이 있습니다. 따라서 Phone 채널은 상담 품질 점검과 운영 가이드 표준화가 필요한 영역으로 볼 수 있습니다.

### EDA 3. 처리시간 기준 분석

<img src="docs/eda-resolution-time.png" width="820" alt="처리시간 기준 분석 화면">

문의 유형별 평균 처리시간을 확인한 결과, **Account 카테고리의 평균 처리시간이 가장 길게 나타났습니다.**

여기서 중요한 점은 재오픈율 기준 결과와 처리시간 기준 결과가 달랐다는 것입니다. 재오픈율 기준으로는 Other가 가장 위험해 보였지만, 처리시간 기준으로는 Account가 더 큰 병목 신호를 보였습니다.

이 결과를 통해 단일 KPI만으로는 운영 리스크를 설명하기 어렵다는 한계를 확인했습니다.

## Risk Score 설계

재오픈율 기준으로는 Other와 Phone이 높게 나타났고, 처리시간 기준으로는 Account가 높게 나타났습니다.

각 KPI가 서로 다른 위험 신호를 보여주었기 때문에 단일 KPI만으로는 운영 개선 우선순위를 결정하기 어려웠습니다. 그래서 재오픈율, 처리시간, 우선순위를 함께 반영하는 Risk Score를 설계했습니다.

Risk Score는 다음 세 지표를 통합 평가합니다.

- **Reopened Rate**: 반복 문의와 고객 경험 저하 가능성
- **Resolution Time**: 처리 병목과 운영 리소스 부담
- **Priority Weight**: 업무 중요도와 긴급도

```text
Risk Score =
0.5 x Normalized Reopened Rate
+ 0.3 x Normalized Resolution Time
+ 0.2 x Normalized Priority Weight
```

Priority Weight는 티켓 우선순위를 숫자로 변환해 반영했습니다.

```text
Low = 1
Medium = 2
High = 3
Urgent = 4
```

Risk Score를 통해 단순히 “어떤 지표가 높은가”가 아니라, **운영 리소스를 어디에 먼저 투입해야 하는가**를 판단할 수 있도록 했습니다.

## Dashboard

대시보드는 KPI 조회 화면이 아니라, 분석 결과를 운영 판단으로 연결하는 화면으로 구성했습니다.

### 운영 리스크 현황

<img src="docs/ai-insight-risk-summary.png" width="820" alt="운영 리스크 현황 화면">

Risk Score가 높은 카테고리를 중심으로 카테고리, 리스크 점수, 재오픈율, 평균 처리시간, 우선순위 가중치를 한 화면에서 확인할 수 있도록 구성했습니다.

### 개선 권고안

<img src="docs/ai-insight-improvement.png" width="820" alt="개선 권고안 화면">

추천 근거와 KPI 차이를 함께 보여주고, 해당 영역에 대해 어떤 운영 개선을 먼저 검토해야 하는지 제안합니다.

### 운영 리소스 제안

<img src="docs/ai-insight-resource.png" width="820" alt="운영 리소스 제안 화면">

리스크가 높은 영역에 숙련 상담 인력, QA 샘플링, 상담 가이드 정비 같은 운영 리소스를 어떻게 배치할지 판단할 수 있도록 구성했습니다.

## LLM 사용 방식

이 프로젝트에서 LLM은 분석 주체가 아닙니다.

- EDA 수행: SQL + Pandas
- Risk Score 계산: Python
- Dashboard 시각화: Streamlit
- LLM 역할: EDA 결과와 Risk Score 결과를 운영자가 이해하기 쉬운 자연어 개선안으로 변환

즉, 분석과 판단 기준은 SQL, Pandas, Python 계산 결과에서 나오며, LLM은 그 결과를 운영 커뮤니케이션에 적합한 문장으로 바꾸는 보조 역할만 수행합니다.

## 운영 개선 방향

분석 결과를 바탕으로 다음과 같은 운영 개선 방향을 도출했습니다.

### 1. Other 카테고리 재분류

Other는 재오픈율과 Risk Score가 높게 나타난 영역입니다. 여러 유형의 문의가 섞여 있을 가능성이 있으므로, 반복 키워드와 상담 로그를 기준으로 세부 카테고리를 재정의할 필요가 있습니다.

### 2. Phone 채널 상담 품질 점검

Phone은 채널 기준 재오픈율이 가장 높았습니다. 상담 기록, 후속 조치, 에스컬레이션 기준을 점검해 같은 문제가 다시 열리는 상황을 줄여야 합니다.

### 3. Account 처리 프로세스 점검

처리시간 기준으로는 Account 카테고리가 가장 긴 병목 신호를 보였습니다. 인증, 계정 변경, 권한 확인처럼 단계가 많은 프로세스에서 지연이 발생하는지 확인할 필요가 있습니다.

### 4. Risk Score 기반 우선순위 관리

개별 KPI를 따로 보는 대신 Risk Score를 기준으로 개선 후보를 정렬하면, 운영 리소스를 어디에 먼저 투입해야 하는지 더 명확하게 판단할 수 있습니다.

## 프로젝트를 통해 얻은 인사이트

문의량이 많다고 운영 리스크가 높은 것은 아니었습니다.

재오픈율만으로도 운영 리스크를 충분히 설명할 수 없었습니다.

재오픈율, 처리시간, 우선순위를 함께 고려했을 때 실제 개선이 필요한 영역이 달라질 수 있었습니다.

이 프로젝트의 핵심은 대시보드를 만든 것이 아니라, **운영 데이터를 분석해 어떤 영역을 먼저 개선해야 하는지 판단 기준을 만든 것**입니다.

## 실행 방법

```bash
pip install -r requirements.txt
streamlit run dashboard/app.py
```

## 기술 스택

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-000000?style=for-the-badge&logoColor=white)
![Qwen](https://img.shields.io/badge/Qwen-6B46C1?style=for-the-badge&logoColor=white)
![Git](https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white)
