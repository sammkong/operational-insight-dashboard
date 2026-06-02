import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.analysis import build_analysis_summary, run_query
from src.llm_insight import (
    generate_improvement_plan,
    generate_resource_plan,
    generate_risk_summary,
)


st.set_page_config(
    page_title="Operational Insight Dashboard",
    page_icon="",
    layout="wide",
)


@st.cache_data(ttl=300)
def load_query(query_name: str) -> pd.DataFrame:
    return run_query(query_name)


@st.cache_data(ttl=300)
def load_compact_ai_context() -> dict[str, pd.DataFrame]:
    return {
        "overview_kpis": run_query("overview_kpis"),
        "reopened_rate_by_issue_category": run_query("reopened_rate_by_issue_category"),
        "risk_ranking": run_query("risk_ranking"),
    }


def render_kpi(label: str, value: object, suffix: str = "") -> None:
    if value is None or pd.isna(value):
        st.metric(label, "-")
    else:
        st.metric(label, f"{value}{suffix}")


def safe_load(query_name: str) -> pd.DataFrame:
    try:
        return load_query(query_name)
    except Exception as exc:
        st.error(
            "PostgreSQL 데이터를 불러오지 못했습니다. "
            "데이터베이스 설정, 테이블 생성, CSV 적재 여부를 확인하세요."
        )
        st.exception(exc)
        return pd.DataFrame()


def bar_chart(df: pd.DataFrame, x: str, y: str, title: str) -> None:
    if df.empty:
        st.info("표시할 데이터가 없습니다.")
        return
    fig = px.bar(df, x=x, y=y, title=title, text_auto=True)
    fig.update_layout(margin=dict(l=20, r=20, t=60, b=20))
    st.plotly_chart(fig, use_container_width=True)


def line_chart(df: pd.DataFrame, x: str, y: str, title: str) -> None:
    if df.empty:
        st.info("표시할 데이터가 없습니다.")
        return
    fig = px.line(df, x=x, y=y, title=title, markers=True)
    fig.update_layout(margin=dict(l=20, r=20, t=60, b=20))
    st.plotly_chart(fig, use_container_width=True)


def render_ollama_result(action):
    try:
        st.markdown(action())
    except requests.exceptions.Timeout:
        st.error("모델 응답 시간이 초과되었습니다. 다시 시도하거나 더 작은 모델을 사용하세요.")
    except requests.exceptions.ConnectionError:
        st.error("Ollama 서버에 연결할 수 없습니다. `ollama serve` 실행 여부를 확인하세요.")
    except requests.exceptions.HTTPError as exc:
        st.error("Ollama API 호출 중 오류가 발생했습니다. 모델 설치 여부를 확인하세요.")
        st.exception(exc)
    except requests.exceptions.RequestException as exc:
        st.error("Ollama 요청이 실패했습니다. 서버 상태와 모델명을 확인하세요.")
        st.exception(exc)


st.title("Operational Insight Dashboard")
st.caption("고객 지원 티켓 데이터 기반 운영 리스크 분석 및 LLM 기반 운영 인사이트 생성 플랫폼")

page = st.sidebar.radio(
    "Page",
    [
        "Operational Overview",
        "Risk Analytics",
        "AI Insight",
    ],
)

if page == "Operational Overview":
    st.subheader("Operational Overview")
    st.write("운영 현황을 한 화면에서 파악하기 위한 요약 페이지입니다.")

    kpis = safe_load("overview_kpis")
    issue_distribution = safe_load("issue_category_counts")
    channel_distribution = safe_load("channel_counts")
    avg_resolution_by_issue = safe_load("avg_resolution_by_issue_category")
    avg_resolution_by_priority = safe_load("avg_resolution_by_priority")

    if not kpis.empty:
        row = kpis.iloc[0]
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            render_kpi("Total Tickets", row.get("total_tickets"))
        with col2:
            render_kpi("Average Resolution Time", row.get("avg_resolution_time_hours"), " h")
        with col3:
            render_kpi("Average First Response Time", row.get("avg_first_response_minutes"), " min")
        with col4:
            render_kpi("Reopened Rate", row.get("reopened_rate"), "%")

    col1, col2 = st.columns(2)
    with col1:
        bar_chart(issue_distribution, "issue_category", "ticket_count", "Issue Category Distribution")
    with col2:
        bar_chart(channel_distribution, "channel", "ticket_count", "Channel Distribution")

    col3, col4 = st.columns(2)
    with col3:
        bar_chart(
            avg_resolution_by_issue,
            "issue_category",
            "avg_resolution_time_hours",
            "Average Resolution Time by Issue Category",
        )
    with col4:
        bar_chart(
            avg_resolution_by_priority,
            "priority",
            "avg_resolution_time_hours",
            "Average Resolution Time by Priority",
        )

    st.subheader("Detailed Tables")
    tab1, tab2, tab3, tab4 = st.tabs(
        ["Issue Category", "Channel", "Issue Resolution", "Priority Resolution"]
    )
    with tab1:
        st.dataframe(issue_distribution, use_container_width=True)
    with tab2:
        st.dataframe(channel_distribution, use_container_width=True)
    with tab3:
        st.dataframe(avg_resolution_by_issue, use_container_width=True)
    with tab4:
        st.dataframe(avg_resolution_by_priority, use_container_width=True)

elif page == "Risk Analytics":
    st.subheader("Risk Analytics")
    st.write("재오픈율, 상담 담당자 경험 연차, Risk Score를 기준으로 운영 우선순위를 분석합니다.")

    reopened_overall = safe_load("reopened_rate_overall")
    reopened_by_issue = safe_load("reopened_rate_by_issue_category")
    reopened_by_channel = safe_load("reopened_rate_by_channel")
    reopened_by_priority = safe_load("reopened_rate_by_priority")
    agent_resolution = safe_load("agent_experience_resolution")
    agent_reopened = safe_load("agent_experience_reopened")
    risk_ranking = safe_load("risk_ranking")

    st.markdown("### Reopened Analysis")
    if not reopened_overall.empty:
        render_kpi("Overall Reopened Rate", reopened_overall.iloc[0]["reopened_rate"], "%")

    col1, col2, col3 = st.columns(3)
    with col1:
        bar_chart(reopened_by_issue, "issue_category", "reopened_rate", "Reopened Rate by Issue Category")
    with col2:
        bar_chart(reopened_by_channel, "channel", "reopened_rate", "Reopened Rate by Channel")
    with col3:
        bar_chart(reopened_by_priority, "priority", "reopened_rate", "Reopened Rate by Priority")

    tab1, tab2, tab3 = st.tabs(["Issue Category", "Channel", "Priority"])
    with tab1:
        st.dataframe(reopened_by_issue, use_container_width=True)
    with tab2:
        st.dataframe(reopened_by_channel, use_container_width=True)
    with tab3:
        st.dataframe(reopened_by_priority, use_container_width=True)

    st.markdown("### Agent Analysis")
    col4, col5 = st.columns(2)
    with col4:
        line_chart(
            agent_resolution,
            "agent_experience_years",
            "avg_resolution_time_hours",
            "Agent Experience vs Resolution Time",
        )
        st.dataframe(agent_resolution, use_container_width=True)
    with col5:
        line_chart(
            agent_reopened,
            "agent_experience_years",
            "reopened_rate",
            "Agent Experience vs Reopened Rate",
        )
        st.dataframe(agent_reopened, use_container_width=True)

    st.markdown("### Risk Score")
    st.caption(
        "Risk Score = 0.5 × Normalized Reopened Rate + "
        "0.3 × Normalized Resolution Time + 0.2 × Priority Weight"
    )
    bar_chart(risk_ranking, "issue_category", "risk_score", "Risk Score TOP 5")
    st.dataframe(risk_ranking, use_container_width=True)

elif page == "AI Insight":
    st.subheader("AI Insight")
    st.write(
        "Operational Overview 및 Risk Analytics 결과 요약만 Ollama Qwen 모델에 전달합니다. "
        "LLM은 SQL 분석 결과를 해석하는 역할만 수행하며, 새 숫자를 만들지 않도록 제한합니다."
    )

    try:
        results = load_compact_ai_context()
        summary = build_analysis_summary(results)
    except Exception as exc:
        st.error("분석 결과를 생성하지 못했습니다. PostgreSQL 연결과 적재 상태를 확인하세요.")
        st.exception(exc)
        st.stop()

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("운영 리스크 요약 생성"):
            render_ollama_result(lambda: generate_risk_summary(summary))
    with col2:
        if st.button("운영 개선안 생성"):
            render_ollama_result(lambda: generate_improvement_plan(summary))
    with col3:
        if st.button("운영 리소스 제안"):
            render_ollama_result(lambda: generate_resource_plan(summary))

    st.divider()
    st.header("AI Insight")
    st.subheader("LLM 기반 운영 인사이트")
    st.write("현재 분석 결과를 기반으로 생성된 운영 인사이트")

    st.markdown("### 섹션 1. 운영 리스크 요약")
    st.markdown(
        """
전체 재오픈율은 49.54%로 나타났다.

문의 유형별 분석 결과, Other 카테고리가 가장 높은 Risk Score(0.8536)를 기록했다.

이는 특정 문제 유형보다는 현재 문의 분류 체계가 충분히 세분화되지 않았을 가능성을 시사한다.
"""
    )

    st.markdown("### 섹션 2. 우선 대응 영역")
    st.markdown(
        """
1순위: Other  
2순위: Delivery  
3순위: Technical

위 세 영역은 재오픈율과 처리시간이 상대적으로 높아 운영 개선 효과가 클 것으로 판단된다.
"""
    )

    st.markdown("### 섹션 3. 운영 개선 제안")
    st.markdown(
        """
- Other 문의를 재분류하여 신규 카테고리 정의
- Delivery 문의 처리 가이드 표준화
- Technical 문의 FAQ 및 자동응답 보강
- Phone 채널 상담 품질 점검
"""
    )
