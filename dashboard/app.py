import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.analysis import run_query


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
        "recommendation_kpis": run_query("recommendation_kpis"),
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


def format_card_value(value: object, suffix: str = "", digits: int = 2) -> str:
    if value is None or pd.isna(value):
        return "-"
    if isinstance(value, float):
        return f"{value:.{digits}f}{suffix}"
    return f"{value}{suffix}"


def get_top_risk_row(risk_ranking: pd.DataFrame) -> pd.Series | None:
    if risk_ranking.empty or "risk_score" not in risk_ranking.columns:
        return None
    return risk_ranking.sort_values("risk_score", ascending=False).iloc[0]


def get_recommendation_kpi_row(
    recommendation_kpis: pd.DataFrame,
    top_risk: pd.Series | None,
) -> pd.Series | None:
    if top_risk is None or recommendation_kpis.empty:
        return None
    category = top_risk.get("issue_category")
    matches = recommendation_kpis[recommendation_kpis["issue_category"] == category]
    if matches.empty:
        return None
    return matches.iloc[0]


def render_card(title: str, body) -> None:
    with st.container(border=True):
        st.markdown(f"#### {title}")
        body()


def render_risk_alert_card(top_risk: pd.Series | None) -> None:
    def body() -> None:
        if top_risk is None:
            st.info("리스크 순위 데이터가 없어 운영 리스크 현황을 표시할 수 없습니다.")
            return

        st.markdown(f"**카테고리:** {top_risk.get('issue_category', '-')}")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("리스크 점수", format_card_value(top_risk.get("risk_score"), digits=4))
        with col2:
            st.metric("재오픈율", format_card_value(top_risk.get("reopened_rate"), "%"))
        with col3:
            st.metric(
                "평균 처리시간",
                format_card_value(top_risk.get("avg_resolution_time_hours"), "시간"),
            )
        with col4:
            st.metric("우선순위 가중치", format_card_value(top_risk.get("avg_priority_weight")))

    render_card("운영 리스크 현황", body)


def render_actions(items: list[str]) -> None:
    for item in items:
        st.markdown(f"- {item}")


def get_report_context(
    top_risk: pd.Series | None,
    kpi_row: pd.Series | None,
) -> dict[str, str]:
    category = "-"
    if top_risk is not None:
        category = str(top_risk.get("issue_category", "-"))

    return {
        "category": category,
        "reopened_rate": format_card_value(
            kpi_row.get("reopened_rate") if kpi_row is not None else None,
            "%",
        ),
        "resolution_time": format_card_value(
            kpi_row.get("avg_resolution_time_hours") if kpi_row is not None else None,
            "시간",
        ),
        "category_share": format_card_value(
            kpi_row.get("category_share") if kpi_row is not None else None,
            "%",
        ),
        "priority_weight": format_card_value(
            kpi_row.get("avg_priority_weight") if kpi_row is not None else None,
        ),
    }


def build_recommended_actions(
    selected_type: str,
    top_risk: pd.Series | None,
    kpi_row: pd.Series | None,
) -> list[str]:
    context = get_report_context(top_risk, kpi_row)
    category = context["category"]

    if selected_type == "risk_summary":
        return [
            (
                f"{category} 카테고리의 재오픈율({context['reopened_rate']})과 "
                f"평균 처리시간({context['resolution_time']})이 우선 관리 KPI로 확인되므로, "
                "반복 발생 사유를 기준으로 문의 유형을 재분류할 필요가 있습니다."
            ),
            (
                f"{category} 문의의 카테고리 비중({context['category_share']})과 "
                f"우선순위 가중치({context['priority_weight']})를 기준으로 FAQ와 상담 가이드를 "
                "정비하여 초기 해결 가능성을 높이는 것을 권장합니다."
            ),
        ]

    if selected_type == "improvement_plan":
        return [
            (
                f"{category} 카테고리에서 재오픈율({context['reopened_rate']})이 관리 대상 KPI로 "
                "확인되므로, 반복 재문의 원인을 기준으로 상담 스크립트와 분류 기준을 보강할 필요가 있습니다."
            ),
            (
                f"평균 처리시간({context['resolution_time']})과 문의 비중({context['category_share']})을 "
                "함께 고려하여 고빈도 처리 케이스의 SOP를 표준화하는 것을 권장합니다."
            ),
        ]

    if selected_type == "resource_plan":
        return [
            (
                f"{category} 카테고리의 우선순위 가중치({context['priority_weight']})와 "
                f"문의 비중({context['category_share']})을 기준으로 숙련 상담 인력을 우선 배치할 필요가 있습니다."
            ),
            (
                f"재오픈율({context['reopened_rate']})과 평균 처리시간({context['resolution_time']})을 "
                "주간 운영 KPI로 모니터링하고, 임계치 초과 시 QA 샘플링을 확대하는 것을 권장합니다."
            ),
        ]

    return []


def build_expected_impacts(selected_type: str, top_risk: pd.Series | None) -> list[str]:
    category = "-"
    if top_risk is not None:
        category = str(top_risk.get("issue_category", "-"))

    if selected_type == "risk_summary":
        return [
            f"문의 유형이 KPI 기준으로 명확하게 분류되어 {category} 카테고리의 반복 문의와 오분류 사례를 줄일 수 있습니다.",
            "초기 응답 기준이 정비되면 재오픈율과 평균 처리시간을 함께 관리할 수 있어 운영 리스크가 조기에 완화될 것으로 기대됩니다.",
        ]

    if selected_type == "improvement_plan":
        return [
            f"{category} 문의의 재문의 원인이 상담 단계에서 더 빨리 식별되어 재오픈율 개선에 직접 기여할 수 있습니다.",
            "SOP 표준화를 통해 상담 처리 편차가 줄어들고 평균 처리시간과 재오픈율을 함께 개선할 수 있을 것으로 기대됩니다.",
        ]

    if selected_type == "resource_plan":
        return [
            f"리스크가 높은 {category} 문의에 숙련 인력이 집중되어 처리 지연과 재오픈 가능성을 줄일 수 있습니다.",
            "주간 KPI 모니터링과 QA 확대를 통해 리소스 부족 신호를 조기에 파악하고 운영 우선순위를 더 명확하게 조정할 수 있습니다.",
        ]

    return []


def format_signed_value(value: object, suffix: str = "", digits: int = 2) -> str:
    if value is None or pd.isna(value):
        return "-"
    number = float(value)
    sign = "+" if number > 0 else ""
    return f"{sign}{number:.{digits}f}{suffix}"


def render_why_recommendation_card(kpi_row: pd.Series | None) -> None:
    def body() -> None:
        if kpi_row is None:
            st.info("추천 근거 KPI를 표시할 수 없습니다.")
            return

        st.markdown(
            "- 재오픈율: "
            f"{format_card_value(kpi_row.get('reopened_rate'), '%')} "
            f"(전체 평균 {format_card_value(kpi_row.get('overall_reopened_rate'), '%')}, "
            f"{format_signed_value(kpi_row.get('reopened_rate_delta'), '%p')})"
        )
        st.markdown(
            "- 평균 처리시간: "
            f"{format_card_value(kpi_row.get('avg_resolution_time_hours'), '시간')} "
            f"(전체 평균 {format_card_value(kpi_row.get('overall_resolution_time_hours'), '시간')}, "
            f"{format_signed_value(kpi_row.get('resolution_time_delta'), '시간')})"
        )
        st.markdown(
            "- 카테고리 비중: "
            f"전체 문의의 {format_card_value(kpi_row.get('category_share'), '%')}"
        )
        st.markdown(
            "- 우선순위 가중치: "
            f"{format_card_value(kpi_row.get('avg_priority_weight'))} "
            f"({format_card_value(kpi_row.get('category_count'), digits=0)}개 카테고리 중 "
            f"{format_card_value(kpi_row.get('priority_weight_rank'), digits=0)}위)"
        )

        reopened_delta = kpi_row.get("reopened_rate_delta")
        resolution_delta = kpi_row.get("resolution_time_delta")
        if (
            reopened_delta is not None
            and resolution_delta is not None
            and not pd.isna(reopened_delta)
            and not pd.isna(resolution_delta)
            and reopened_delta > 0
            and resolution_delta > 0
        ):
            st.caption(
                "재오픈율과 처리시간이 전체 평균보다 높아 반복 문의와 운영 병목 가능성이 있는 "
                "카테고리로 판단했습니다."
            )
        elif reopened_delta is not None and not pd.isna(reopened_delta) and reopened_delta > 0:
            st.caption("재오픈율이 전체 평균보다 높아 반복 문의 가능성이 있는 카테고리로 판단했습니다.")
        elif resolution_delta is not None and not pd.isna(resolution_delta) and resolution_delta > 0:
            st.caption("처리시간이 전체 평균보다 길어 운영 병목 가능성이 있는 카테고리로 판단했습니다.")
        else:
            st.caption("리스크 점수 구성 지표를 기준으로 운영 우선순위 검토가 필요한 카테고리로 판단했습니다.")

    render_card("추천 근거", body)


def render_operational_insight_dashboard(
    top_risk: pd.Series | None,
    kpi_row: pd.Series | None,
    recommended_actions: list[str],
    expected_impacts: list[str],
) -> None:
    render_risk_alert_card(top_risk)
    render_why_recommendation_card(kpi_row)
    render_card("개선 권고안", lambda: render_actions(recommended_actions))
    render_card("예상 효과", lambda: render_actions(expected_impacts))


def render_insight_dashboard(
    selected_type: str,
    top_risk: pd.Series | None = None,
    kpi_row: pd.Series | None = None,
) -> None:
    if selected_type not in {"risk_summary", "improvement_plan", "resource_plan"}:
        return

    actions = build_recommended_actions(selected_type, top_risk, kpi_row)
    impacts = build_expected_impacts(selected_type, top_risk)
    render_operational_insight_dashboard(top_risk, kpi_row, actions, impacts)


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
    st.write("SQL 기반 KPI 분석 결과를 운영 리스크 판단과 개선안으로 연결합니다.")

    try:
        results = load_compact_ai_context()
    except Exception as exc:
        st.error("분석 결과를 생성하지 못했습니다. PostgreSQL 연결과 적재 상태를 확인하세요.")
        st.exception(exc)
        st.stop()

    top_risk = get_top_risk_row(results.get("risk_ranking", pd.DataFrame()))
    kpi_row = get_recommendation_kpi_row(
        results.get("recommendation_kpis", pd.DataFrame()),
        top_risk,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("운영 리스크 요약 생성"):
            st.session_state["selected_insight_type"] = "risk_summary"
    with col2:
        if st.button("운영 개선안 생성"):
            st.session_state["selected_insight_type"] = "improvement_plan"
    with col3:
        if st.button("운영 리소스 제안"):
            st.session_state["selected_insight_type"] = "resource_plan"

    selected_type = st.session_state.get("selected_insight_type")
    if selected_type:
        render_insight_dashboard(selected_type, top_risk, kpi_row)
