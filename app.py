import streamlit as st
from src.config import Config, fetch_latest_models, MODEL_FAMILIES
from src.orchestrator import Orchestrator
from src.github_client import fetch_pr_for_review, detect_language_from_filename

# ── 페이지 설정 ──
st.set_page_config(page_title="AI Code Review Pipeline", layout="wide")
st.title("AI Code Review Pipeline")
st.caption("Multi-Agent 코드 리뷰 자동화 시스템")

# ── severity 색상 ──
SEVERITY_COLOR = {
    "critical": "#FF4B4B",
    "warning": "#FFA726",
    "info": "#42A5F5",
}
SEVERITY_EMOJI = {
    "critical": "\u2757",  # ❗
    "warning": "\u26A0\uFE0F",  # ⚠️
    "info": "\u2139\uFE0F",  # ℹ️
}
AGENT_STATUS = {
    "start": "\U0001F504",   # 🔄
    "done": "\u2705",        # ✅
    "error": "\u274C",       # ❌
    "waiting": "\u2B1C",     # ⬜
}

LANGUAGES = ["자동 감지", "Python", "JavaScript", "TypeScript", "Java", "Go"]

# ── 모델 목록 자동 조회 (API에서 최신 버전을 가져옴, 실패 시 기본값 사용) ──
@st.cache_data(ttl=3600, show_spinner=False)
def get_model_options() -> dict[str, str]:
    """패밀리별 최신 모델을 조회하여 {표시명: 모델ID} 딕셔너리를 반환."""
    api_key = Config().api_key
    latest = fetch_latest_models(api_key)
    return {
        f"{MODEL_FAMILIES[family]} — {latest[family]}": latest[family]
        for family in ["sonnet", "haiku", "opus"]
    }


MODEL_OPTIONS = get_model_options()


# ── 마크다운 리포트 생성 ──
def generate_markdown_report(result: dict) -> str:
    summary = result["findings"].get("summary", {})
    lines = [
        "# AI Code Review Report\n",
        f"**언어**: {result['language']}",
        f"**점수**: {summary.get('overall_score', '-')}/100",
        f"**등급**: {summary.get('grade', '-')}\n",
    ]

    total = summary.get("total_issues", {})
    lines.append("## 이슈 통계\n")
    lines.append("| Critical | Warning | Info |")
    lines.append("|---|---|---|")
    lines.append(f"| {total.get('critical', 0)} | {total.get('warning', 0)} | {total.get('info', 0)} |\n")

    top3 = summary.get("top_3_actions", [])
    if top3:
        lines.append("## 수정 우선순위 Top 3\n")
        for item in top3:
            lines.append(f"{item['priority']}. **{item['issue']}** (예상: {item['effort']})")
        lines.append("")

    conflicts = summary.get("cross_review_conflicts", [])
    if conflicts:
        lines.append("## 교차 반론 충돌\n")
        for c in conflicts:
            lines.append(f"- **{c['issue']}**")
            lines.append(f"  - 충돌: {c['conflict']}")
            lines.append(f"  - 해결: {c['resolution']}")
        lines.append("")

    all_issues = summary.get("all_issues", [])
    if all_issues:
        lines.append("## 전체 이슈 목록\n")
        lines.append("| Agent | Severity | Line | Issue | Suggestion |")
        lines.append("|---|---|---|---|---|")
        for iss in all_issues:
            lines.append(
                f"| {iss.get('agent', '')} | {iss.get('severity', '')} "
                f"| {iss.get('line', '')} | {iss.get('issue', '')} "
                f"| {iss.get('suggestion', '')} |"
            )
        lines.append("")

    comment = summary.get("comment", "")
    if comment:
        lines.append(f"## 종합 코멘트\n\n{comment}\n")

    if result.get("errors"):
        lines.append("## 에러\n")
        for err in result["errors"]:
            lines.append(f"- **{err['agent']}**: {err['error']}")

    return "\n".join(lines)


# ── Agent별 이슈 테이블 렌더링 ──
def render_issues(issues: list):
    if not issues:
        st.success("이슈가 발견되지 않았습니다.")
        return

    for iss in issues:
        sev = iss.get("severity", "info")
        emoji = SEVERITY_EMOJI.get(sev, "")
        color = SEVERITY_COLOR.get(sev, "#888")

        st.markdown(
            f"<span style='color:{color};font-weight:bold'>{emoji} [{sev.upper()}]</span> "
            f"Line {iss.get('line', '?')}",
            unsafe_allow_html=True,
        )
        st.markdown(f"**문제**: {iss.get('issue', '')}")
        if iss.get("code_snippet"):
            st.code(iss["code_snippet"], language="python")
        st.markdown(f"**수정 제안**: {iss.get('suggestion', '')}")
        st.divider()


def render_cross_review(cross_review: list):
    if not cross_review:
        return

    st.markdown("#### 교차 반론")
    for cr in cross_review:
        opinion = cr.get("opinion", "")
        icon = {"agree": "\u2705", "caution": "\u26A0\uFE0F", "disagree": "\u274C"}.get(opinion, "")
        st.markdown(
            f"{icon} **{cr.get('target_agent', '')}** — {cr.get('target_issue', '')}"
        )
        st.markdown(f"> {cr.get('comment', '')}")


def render_result(result: dict, col):
    """리뷰 결과를 우측 컬럼에 렌더링."""
    findings = result.get("findings", {})
    summary = findings.get("summary", {})
    errors = result.get("errors", [])

    with col:
        tab_overview, tab_security, tab_perf, tab_quality = st.tabs(
            ["Overview", "Security", "Performance", "Quality"]
        )

        with tab_overview:
            score = summary.get("overall_score", "-")
            grade = summary.get("grade", "-")
            total = summary.get("total_issues", {})

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("점수", f"{score}/100")
            m2.metric("등급", grade)
            m3.metric("Critical", total.get("critical", 0))
            m4.metric("Warning", total.get("warning", 0))
            m5.metric("Info", total.get("info", 0))

            top3 = summary.get("top_3_actions", [])
            if top3:
                st.markdown("#### 수정 우선순위 Top 3")
                for item in top3:
                    st.markdown(
                        f"**{item['priority']}.** {item['issue']} "
                        f"(예상: {item['effort']})"
                    )

            conflicts = summary.get("cross_review_conflicts", [])
            if conflicts:
                st.markdown("#### 교차 반론 충돌")
                for c in conflicts:
                    with st.expander(c.get("issue", "")):
                        st.markdown(f"**충돌**: {c.get('conflict', '')}")
                        st.markdown(f"**해결**: {c.get('resolution', '')}")

            comment = summary.get("comment", "")
            if comment:
                st.info(comment)

            if errors:
                st.markdown("#### 에러")
                for err in errors:
                    st.error(f"**{err['agent']}**: {err['error']}")

        with tab_security:
            sec = findings.get("security", {})
            st.markdown(f"**요약**: {sec.get('summary', '결과 없음')}")
            render_issues(sec.get("issues", []))

        with tab_perf:
            perf = findings.get("performance", {})
            st.markdown(f"**요약**: {perf.get('summary', '결과 없음')}")
            render_issues(perf.get("issues", []))
            render_cross_review(perf.get("cross_review", []))

        with tab_quality:
            qual = findings.get("quality", {})
            st.markdown(f"**요약**: {qual.get('summary', '결과 없음')}")
            render_issues(qual.get("issues", []))
            render_cross_review(qual.get("cross_review", []))


def run_pipeline(code: str, language: str = None, model: str = None) -> dict:
    """파이프라인 실행 + 진행 상태 표시."""
    config = Config()
    if model:
        config.model = model
    config.validate()
    orchestrator = Orchestrator(config)

    status_container = st.container()
    agent_names = ["security", "performance", "quality", "summary"]
    agent_status = {name: "waiting" for name in agent_names}

    def update_status_display():
        parts = []
        for name in agent_names:
            s = agent_status[name]
            parts.append(f"{AGENT_STATUS[s]} {name.capitalize()}")
        status_container.markdown(" \u2192 ".join(parts))

    update_status_display()

    def on_progress(agent_name: str, status: str):
        agent_status[agent_name] = status
        update_status_display()

    with st.spinner("리뷰 진행 중..."):
        result = orchestrator.run(code, language=language, on_progress=on_progress)

    return result


# ══════════════════════════════════════
# 메인 레이아웃
# ══════════════════════════════════════
col_input, col_result = st.columns([1, 1.5])

with col_input:
    selected_model_label = st.selectbox("모델 선택", list(MODEL_OPTIONS.keys()))
    selected_model = MODEL_OPTIONS[selected_model_label]

    input_mode = st.radio(
        "입력 방식",
        ["코드 직접 입력", "GitHub PR URL", "파일 업로드"],
        horizontal=True,
    )

    # ── 코드 직접 입력 ──
    if input_mode == "코드 직접 입력":
        code = st.text_area("리뷰할 코드를 붙여넣으세요", height=420, label_visibility="collapsed")
        lang_col, btn_col = st.columns([1, 1])
        with lang_col:
            language = st.selectbox("언어", LANGUAGES)
        with btn_col:
            st.write("")
            run_button = st.button("리뷰 시작", type="primary", use_container_width=True)

        if run_button:
            if not code.strip():
                st.warning("코드를 입력해주세요.")
                st.stop()
            lang_arg = None if language == "자동 감지" else language.lower()

            # 자동 감지 시 confidence가 낮으면 경고
            if lang_arg is None:
                from src.review_state import detect_language, ReviewState
                detected, confidence = detect_language(code)
                if detected == "unknown":
                    st.warning("언어를 감지할 수 없습니다. 위 드롭다운에서 직접 선택해주세요.")
                    st.stop()
                if confidence < ReviewState.LOW_CONFIDENCE_THRESHOLD:
                    st.warning(
                        f"언어가 **{detected}**(으)로 감지되었지만 확신도가 낮습니다 "
                        f"(confidence: {confidence:.0%}). "
                        f"정확한 리뷰를 위해 위 드롭다운에서 직접 선택하는 것을 권장합니다."
                    )

            try:
                result = run_pipeline(code, lang_arg, model=selected_model)
                st.session_state["result"] = result
            except ValueError as e:
                st.error(str(e))

    # ── GitHub PR URL ──
    elif input_mode == "GitHub PR URL":
        pr_url = st.text_input("PR URL", placeholder="https://github.com/owner/repo/pull/123")

        if st.button("PR 분석", type="secondary", use_container_width=True):
            if not pr_url.strip():
                st.warning("PR URL을 입력해주세요.")
                st.stop()
            config = Config()
            with st.spinner("PR 파일 목록 가져오는 중..."):
                try:
                    pr_files = fetch_pr_for_review(pr_url, token=config.github_token)
                except Exception as e:
                    st.error(f"PR 분석 실패: {e}")
                    st.stop()

            if not pr_files:
                st.warning("리뷰할 코드 파일이 없습니다.")
                st.stop()

            st.session_state["pr_files"] = pr_files

        if "pr_files" in st.session_state:
            pr_files = st.session_state["pr_files"]
            st.markdown(f"**변경된 파일 ({len(pr_files)}개)**")

            selected = []
            for i, f in enumerate(pr_files):
                checked = st.checkbox(
                    f"{f['filename']} (+{f['additions']}, -{f['deletions']})",
                    value=True,
                    key=f"pr_file_{i}",
                )
                if checked:
                    selected.append(f)

            if st.button("선택 파일 리뷰 시작", type="primary", use_container_width=True):
                if not selected:
                    st.warning("리뷰할 파일을 선택해주세요.")
                    st.stop()

                all_results = []
                for f in selected:
                    st.markdown(f"---\n**{f['filename']}** 리뷰 중...")
                    try:
                        result = run_pipeline(f["code"], f["language"], model=selected_model)
                        result["_filename"] = f["filename"]
                        all_results.append(result)
                    except ValueError as e:
                        st.error(f"{f['filename']}: {e}")

                if all_results:
                    st.session_state["result"] = all_results[0]
                    if len(all_results) > 1:
                        st.session_state["all_pr_results"] = all_results

    # ── 파일 업로드 ──
    elif input_mode == "파일 업로드":
        uploaded = st.file_uploader(
            "파일 업로드",
            type=["py", "js", "jsx", "ts", "tsx", "java", "go"],
            accept_multiple_files=True,
        )

        if uploaded and st.button("리뷰 시작", type="primary", use_container_width=True):
            all_results = []
            for f in uploaded:
                code = f.read().decode("utf-8")
                lang = detect_language_from_filename(f.name)
                st.markdown(f"---\n**{f.name}** 리뷰 중...")
                try:
                    result = run_pipeline(code, lang, model=selected_model)
                    result["_filename"] = f.name
                    all_results.append(result)
                except ValueError as e:
                    st.error(f"{f.name}: {e}")

            if all_results:
                st.session_state["result"] = all_results[0]
                if len(all_results) > 1:
                    st.session_state["all_pr_results"] = all_results

# ── 다중 파일 결과 선택 ──
if "all_pr_results" in st.session_state:
    results = st.session_state["all_pr_results"]
    filenames = [r.get("_filename", f"파일 {i+1}") for i, r in enumerate(results)]
    selected_file = st.selectbox("파일별 결과 보기", filenames)
    idx = filenames.index(selected_file)
    st.session_state["result"] = results[idx]

# ── 결과 표시 ──
if "result" in st.session_state:
    result = st.session_state["result"]
    render_result(result, col_result)

    md_report = generate_markdown_report(result)
    st.download_button(
        "Markdown 리포트 다운로드",
        md_report,
        file_name="review_report.md",
        mime="text/markdown",
    )
