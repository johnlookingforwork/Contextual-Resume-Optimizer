import streamlit as st
import plotly.graph_objects as go
from pyvis.network import Network
from models import AnalysisResult, SemanticMatch, KeywordGap
from typing import List

# Color map for match types
_COLORS = {"exact": "#2ecc71", "semantic": "#3498db", "transferable": "#e67e22"}


def render_xai_dashboard(analysis: AnalysisResult):
    """Main entry point for the XAI Dashboard tab."""
    _build_score_breakdown(analysis.matches, analysis.gaps)
    st.divider()

    st.subheader("Qualification Flow")
    st.caption("How your resume items map to job requirements. Band thickness = match score.")
    fig = _build_sankey(analysis.matches)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No matches to visualize.")

    st.divider()

    st.subheader("Connection Map")
    st.caption("Interactive network graph. Hover over edges for details.")
    html = _build_network_graph(analysis.matches)
    if html:
        st.components.v1.html(html, height=500, scrolling=True)
    else:
        st.info("No matches to visualize.")

    st.divider()

    st.subheader("Line-by-Line Connections")
    _build_connection_table(analysis.matches, analysis.gaps)


def _build_sankey(matches: List[SemanticMatch]):
    """Return a Plotly Sankey figure for resume→JD qualification flow."""
    if not matches:
        return None

    # Deduplicate labels while preserving order
    resume_labels = list(dict.fromkeys(m.resume_item for m in matches))
    jd_labels = list(dict.fromkeys(m.job_requirement for m in matches))

    # Node list: resume items first, then JD items
    node_labels = resume_labels + jd_labels
    resume_offset = 0
    jd_offset = len(resume_labels)

    sources, targets, values, link_colors, hovertexts = [], [], [], [], []

    for m in matches:
        src = resume_offset + resume_labels.index(m.resume_item)
        tgt = jd_offset + jd_labels.index(m.job_requirement)
        sources.append(src)
        targets.append(tgt)
        values.append(m.match_score)
        link_colors.append(_COLORS.get(m.match_type, "#95a5a6"))
        hovertexts.append(
            f"<b>{m.match_type.title()}</b> ({m.match_score:.0%})<br>{m.reasoning}"
        )

    # Truncate long labels for display
    display_labels = [_truncate(l, 45) for l in node_labels]

    # Node colors: green-ish for resume, blue-ish for JD
    node_colors = ["#27ae60"] * len(resume_labels) + ["#2980b9"] * len(jd_labels)

    fig = go.Figure(go.Sankey(
        node=dict(
            pad=20,
            thickness=20,
            label=display_labels,
            color=node_colors,
            hovertemplate="%{label}<extra></extra>",
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=link_colors,
            hovertemplate="%{customdata}<extra></extra>",
            customdata=hovertexts,
        ),
    ))
    fig.update_layout(
        margin=dict(l=10, r=10, t=30, b=10),
        font=dict(size=11),
        height=max(400, len(node_labels) * 28),
    )
    return fig


def _build_network_graph(matches: List[SemanticMatch]):
    """Return an HTML string of a pyvis bipartite network graph."""
    if not matches:
        return None

    net = Network(height="450px", width="100%", directed=False, notebook=False)
    net.barnes_hut(gravity=-3000, spring_length=250, spring_strength=0.001)

    resume_items = list(dict.fromkeys(m.resume_item for m in matches))
    jd_items = list(dict.fromkeys(m.job_requirement for m in matches))

    # Add resume nodes (left column)
    for i, item in enumerate(resume_items):
        net.add_node(
            f"r_{i}",
            label=_truncate(item, 40),
            title=item,
            color="#27ae60",
            x=-300,
            y=i * 100,
            physics=True,
            group="resume",
        )

    # Add JD nodes (right column)
    for i, item in enumerate(jd_items):
        net.add_node(
            f"j_{i}",
            label=_truncate(item, 40),
            title=item,
            color="#2980b9",
            x=300,
            y=i * 100,
            physics=True,
            group="jd",
        )

    # Add edges
    for m in matches:
        src = f"r_{resume_items.index(m.resume_item)}"
        tgt = f"j_{jd_items.index(m.job_requirement)}"
        net.add_edge(
            src,
            tgt,
            value=m.match_score * 5,
            title=f"{m.match_type.title()} ({m.match_score:.0%}): {m.reasoning}",
            color=_COLORS.get(m.match_type, "#95a5a6"),
        )

    net.set_options("""
    {
      "interaction": {
        "hover": true,
        "tooltipDelay": 100
      },
      "edges": {
        "smooth": { "type": "continuous" }
      }
    }
    """)

    return net.generate_html()


def _build_connection_table(matches: List[SemanticMatch], gaps: List[KeywordGap]):
    """Render a filtered connection table with Streamlit controls."""
    col1, col2 = st.columns(2)
    with col1:
        type_filter = st.selectbox(
            "Filter by match type",
            ["All", "exact", "semantic", "transferable"],
            key="xai_type_filter",
        )
    with col2:
        score_threshold = st.slider(
            "Minimum score",
            0.0, 1.0, 0.0, 0.05,
            key="xai_score_slider",
        )

    filtered = [
        m for m in matches
        if m.match_score >= score_threshold
        and (type_filter == "All" or m.match_type == type_filter)
    ]
    filtered.sort(key=lambda m: m.match_score, reverse=True)

    if filtered:
        for m in filtered:
            badge_color = (
                "green" if m.match_score >= 0.8
                else "orange" if m.match_score >= 0.5
                else "red"
            )
            st.markdown(
                f":{badge_color}[**{m.match_score:.0%}**] "
                f"**{m.match_type.upper()}** &mdash; "
                f"{m.resume_item} → {m.job_requirement}"
            )
            st.caption(f"Reasoning: {m.reasoning}")
    else:
        st.info("No matches meet the current filter criteria.")

    # Unmatched JD requirements (gaps)
    if gaps:
        st.markdown("---")
        st.markdown("**Unmatched JD Requirements (Gaps)**")
        for gap in sorted(
            gaps,
            key=lambda g: {"high": 3, "medium": 2, "low": 1}[g.importance],
            reverse=True,
        ):
            st.markdown(
                f":red[**{gap.importance.upper()}**] {gap.missing_keyword} "
                f"— *{gap.integration_suggestion}*"
            )


def _build_score_breakdown(matches: List[SemanticMatch], gaps: List[KeywordGap]):
    """Render metric cards summarizing match types and gap priorities."""
    exact = [m for m in matches if m.match_type == "exact"]
    semantic = [m for m in matches if m.match_type == "semantic"]
    transferable = [m for m in matches if m.match_type == "transferable"]

    def _avg(lst):
        return sum(m.match_score for m in lst) / len(lst) if lst else 0.0

    col1, col2, col3 = st.columns(3)
    col1.metric("Exact Matches", len(exact), f"avg {_avg(exact):.0%}")
    col2.metric("Semantic Matches", len(semantic), f"avg {_avg(semantic):.0%}")
    col3.metric("Transferable Matches", len(transferable), f"avg {_avg(transferable):.0%}")

    high = sum(1 for g in gaps if g.importance == "high")
    med = sum(1 for g in gaps if g.importance == "medium")
    low = sum(1 for g in gaps if g.importance == "low")

    col4, col5, col6 = st.columns(3)
    col4.metric("High-Priority Gaps", high)
    col5.metric("Medium-Priority Gaps", med)
    col6.metric("Low-Priority Gaps", low)


def _truncate(text: str, max_len: int) -> str:
    return text if len(text) <= max_len else text[:max_len - 1] + "…"
