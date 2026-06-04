# 고객 지원 티켓 데이터 기반 운영 리스크 분석 프로젝트

CS 운영 데이터를 분석하여 반복 문의, 처리 지연, 우선순위 부담을 정량화하고 운영 리스크를 평가하는 시스템입니다.

재오픈율, 처리시간, 우선순위를 통합한 **Risk Score**를 설계하여 데이터 기반으로 개선 우선순위를 도출할 수 있도록 했습니다.

## 프로젝트 개요

- Kaggle Customer Support Tickets Dataset의 **2,800건** 티켓 데이터를 분석했습니다.
- 전체 재오픈율은 **49.54%**로, 반복 문의가 운영 품질을 설명하는 핵심 신호라고 판단했습니다.
- 재오픈율, 처리시간, 우선순위가 서로 다른 위험 신호를 보여 단일 KPI의 한계를 확인했습니다.
- 최종적으로 Risk Score를 설계해 개선 우선순위를 판단하는 기준을 만들었습니다.

| 항목 | 내용 |
| --- | --- |
| 데이터 | Kaggle Customer Support Ticket Satisfaction Analysis |
| 분석 단위 | 고객 지원 티켓 **2,800건** |
| 핵심 목표 | 운영 리스크 정량화 및 개선 우선순위 도출 |
| 주요 지표 | 재오픈율, 처리시간, 우선순위 |
| 결과물 | Streamlit Operational Insight Dashboard |

## 왜 이 프로젝트를 시작했는가?

- CS 운영에서는 문의량만으로 실제 리스크를 판단하기 어렵습니다.
- 재오픈 티켓은 반복 문의, 추가 상담 비용, 고객 경험 저하로 이어질 수 있습니다.
- 처리시간이 긴 영역과 재오픈율이 높은 영역이 다르게 나타나는지도 확인할 필요가 있었습니다.

> 목표: 운영자가 어떤 문제를 먼저 개선해야 하는지 판단할 수 있는 기준 만들기

## 문제 정의

- 문의량이 많다 = 운영 리스크가 높다는 의미는 아니었습니다.
- 재오픈율 기준 위험 영역과 처리시간 기준 위험 영역이 다르게 나타났습니다.
- 여러 KPI를 함께 해석해 개선 우선순위를 정할 기준이 필요했습니다.

> 핵심 질문: 재오픈율, 처리시간, 우선순위를 함께 고려해 어떤 영역을 먼저 개선해야 하는가?

## 분석 흐름

1. **재오픈율을 운영 품질 KPI로 선정**
   - 전체 재오픈율: **49.54%**

2. **EDA 1. 카테고리 기준 재오픈율 분석**
   - Other: **52.44%**

3. **EDA 2. 채널 기준 재오픈율 분석**
   - Phone: **50.27%**

4. **EDA 3. 처리시간 기준 분석**
   - Account: **37.66h**

5. **단일 KPI 한계 발견**
   - 재오픈율 기준 위험 영역과 처리시간 기준 위험 영역이 다르게 나타남

6. **Risk Score 설계**
   - Reopened Rate + Resolution Time + Priority Weight

7. **운영 개선 우선순위 도출**
   - Risk Score 1위: **Other**
   - Risk Score: **0.8536**

분석은 SQL과 Pandas를 중심으로 진행했고, 계산된 KPI와 Risk Score를 Streamlit 대시보드로 시각화했습니다.

## 데이터 개요

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

운영 리스크를 설명할 수 있는 지표를 찾기 위해 문의 유형, 채널, 처리시간 기준으로 데이터를 나누어 확인했습니다.

### EDA 1. Issue Category 기준 재오픈율 분석

<img src="docs/eda-category.png" width="640" alt="Issue Category 기준 재오픈율 분석 화면">

**핵심 수치**
- Other: **52.44%**
- Delivery: **50.98%**
- Technical: **49.44%**

**해석**
- Other 카테고리의 재오픈율이 가장 높게 나타났습니다.
- 여러 문의 유형이 한 카테고리에 섞여 있을 가능성을 운영 리스크로 해석했습니다.

**운영 개선 연결**
- 반복 키워드 기반 세부 카테고리 분리 검토

### EDA 2. Channel 기준 재오픈율 분석

<img src="docs/eda-channel.png" width="640" alt="Channel 기준 재오픈율 분석 화면">

**핵심 수치**
- Phone: **50.27%**
- Email: **49.42%**
- Chat: **48.92%**

**해석**
- Phone 채널의 재오픈율이 가장 높게 나타났습니다.
- 상담 기록, 후속 조치, 에스컬레이션 기준 점검이 필요한 접점으로 해석했습니다.

**운영 개선 연결**
- 상담 가이드 및 QA 샘플링 점검

### EDA 3. 처리시간 기준 분석

<img src="docs/eda-resolution-time.png" width="640" alt="처리시간 기준 분석 화면">

**핵심 수치**
- Account: **37.66h**
- Other: **37.07h**
- Technical: **36.63h**

**해석**
- 처리시간 기준으로는 Account가 가장 높게 나타났습니다.
- 재오픈율 기준 결과와 처리시간 기준 결과가 달라 단일 KPI의 한계를 확인했습니다.

**운영 개선 연결**
- 처리시간 상위 문의 SOP 점검

## Risk Score 설계

**왜 필요했는가?**
- 재오픈율 기준: **Other**, **Phone** 리스크 확인
- 처리시간 기준: **Account** 병목 확인
- 단일 KPI만으로는 개선 우선순위 판단이 어려움

**통합 지표**
- **Reopened Rate**: 반복 문의와 고객 경험 저하 가능성
- **Resolution Time**: 처리 병목과 운영 리소스 부담
- **Priority Weight**: 긴급도에 따른 대응 부담

```text
Risk Score =
0.5 x Normalized Reopened Rate
+ 0.3 x Normalized Resolution Time
+ 0.2 x Normalized Priority Weight
```

**결과**
- Risk Score 1위: **Other**
- Risk Score: **0.8536**

Risk Score는 개별 KPI를 따로 보는 대신, 운영 리소스를 어디에 먼저 투입할지 판단하기 위한 기준입니다.

## Dashboard

대시보드는 KPI 조회를 넘어 운영 문제 판단과 개선 방향 도출까지 이어지도록 구성했습니다.

### 운영 리스크 현황

<img src="docs/ai-insight-risk-summary.png" width="640" alt="운영 리스크 현황 화면">

Risk Score가 높은 카테고리의 추천 근거, 재오픈율, 처리시간, 우선순위 가중치를 함께 제공합니다.

### 개선 권고안

<img src="docs/ai-insight-improvement.png" width="640" alt="개선 권고안 화면">

SQL/Risk Score 결과를 바탕으로 개선 권고안과 예상 효과를 문장형으로 제공합니다.

### 운영 리소스 제안

<img src="docs/ai-insight-resource.png" width="640" alt="운영 리소스 제안 화면">

고위험 영역에 대해 QA 샘플링, 상담 가이드 점검, 운영 리소스 배치를 검토할 수 있도록 정리합니다.

## 분석 결과의 운영 개선 연결

- 분석: SQL + Pandas
- Risk Score 계산: Python
- 시각화: Streamlit
- LLM 역할: 분석 결과를 추천 근거 -> 개선 권고안 -> 예상 효과 문장으로 변환

LLM은 분석을 수행하지 않으며, SQL/Pandas/Risk Score 결과를 운영자가 이해하기 쉬운 문장으로 변환하는 보조 계층입니다.

## 운영 개선 방향

| 영역 | 근거 | 개선 방향 |
| --- | --- | --- |
| 문의 분류 체계 | Other 재오픈율 **52.44%** | 반복 키워드 기반 세부 카테고리 분리 |
| 상담 품질 | Phone 재오픈율 **50.27%** | 상담 가이드 및 QA 샘플링 점검 |
| 처리 프로세스 | Account 처리시간 **37.66h** | 처리시간 상위 문의 SOP 점검 |
| 운영 관리 | Risk Score 1위 **Other** | Risk Score 기반 주간 모니터링 |

## 프로젝트를 통해 얻은 인사이트

- 문의량이 많다 = 운영 리스크가 높다는 의미는 아니었습니다.
- 재오픈율은 운영 품질을 보는 핵심 KPI였지만, 우선순위 판단에는 충분하지 않았습니다.
- 처리시간과 우선순위까지 함께 고려했을 때 개선이 필요한 영역을 더 설득력 있게 판단할 수 있었습니다.
- 이 프로젝트의 핵심은 대시보드 구현이 아니라, 운영 데이터를 분석해 어디를 먼저 개선해야 하는지 판단하는 기준을 설계한 것입니다.

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
