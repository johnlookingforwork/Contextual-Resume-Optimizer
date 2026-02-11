import streamlit as st
from extractor import extract_resume_text_from_bytes
from brain import ResumeBrain
from generator import generate_resume_pdf_bytes, generate_cover_letter_pdf_bytes

st.set_page_config(page_title="Resume Optimizer", layout="wide")
st.title("Contextual Resume Optimizer")

# ── API key setup ───────────────────────────────────────────────
try:
    openai_api_key = st.secrets["openai"]["api_key"]
except (KeyError, FileNotFoundError):
    st.error("OpenAI API key not found. Add it to `.streamlit/secrets.toml` "
             "or configure it in Streamlit Cloud's Secrets settings.")
    st.stop()

# ── Sidebar: Inputs ──────────────────────────────────────────────
with st.sidebar:
    st.header("Inputs")
    uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])
    job_text = st.text_area("Paste the job description", height=300)
    run_button = st.button("Optimize Resume", type="primary", use_container_width=True)

# ── Pipeline execution ───────────────────────────────────────────
if run_button:
    if not uploaded_file or not job_text.strip():
        st.warning("Please upload a resume PDF and paste a job description.")
    else:
        brain = ResumeBrain(api_key=openai_api_key)
        pdf_bytes = uploaded_file.read()

        # Step 1 — Extract
        with st.status("Extracting text from PDF...", expanded=False) as s:
            resume_data = extract_resume_text_from_bytes(pdf_bytes)
            s.update(label="Text extracted", state="complete")

        # Step 2 — Structure resume
        with st.status("Structuring resume...", expanded=False) as s:
            structured_resume = brain.structure_resume(resume_data.raw_text)
            s.update(label="Resume structured", state="complete")

        # Step 3 — Structure job description
        with st.status("Structuring job description...", expanded=False) as s:
            structured_job = brain.structure_job_description(job_text)
            s.update(label="Job description structured", state="complete")

        # Step 4 — Semantic analysis
        with st.status("Running semantic analysis...", expanded=False) as s:
            analysis = brain.analyze_resume(structured_resume, structured_job)
            s.update(label="Analysis complete", state="complete")

        # Step 5 — Tailor resume
        with st.status("Tailoring resume...", expanded=False) as s:
            tailored = brain.tailor_resume(structured_resume, analysis)
            s.update(label="Resume tailored", state="complete")

        # Step 6 — Cover letter
        with st.status("Generating cover letter...", expanded=False) as s:
            cover_letter = brain.generate_cover_letter(
                structured_resume, structured_job, analysis
            )
            s.update(label="Cover letter generated", state="complete")

        # Persist results in session state so tab clicks don't re-run pipeline
        st.session_state["analysis"] = analysis
        st.session_state["tailored"] = tailored
        st.session_state["cover_letter"] = cover_letter
        st.session_state["structured_resume"] = structured_resume

# ── Results tabs ─────────────────────────────────────────────────
if "analysis" in st.session_state:
    analysis = st.session_state["analysis"]
    tailored = st.session_state["tailored"]
    cover_letter = st.session_state["cover_letter"]
    structured_resume = st.session_state["structured_resume"]

    tab_analysis, tab_resume, tab_cover, tab_downloads = st.tabs(
        ["Analysis", "Tailored Resume", "Cover Letter", "Downloads"]
    )

    # ── Tab 1: Analysis ──────────────────────────────────────────
    with tab_analysis:
        st.metric("Alignment Score", f"{analysis.overall_alignment_score:.0%}")

        st.subheader("Strengths")
        for s_item in analysis.strengths:
            st.write(f"- {s_item}")

        st.subheader("Semantic Matches")
        for match in sorted(analysis.matches, key=lambda m: m.match_score, reverse=True):
            with st.expander(
                f"[{match.match_type.upper()}] {match.resume_item} -> {match.job_requirement}  ({match.match_score:.0%})"
            ):
                st.write(f"**Reasoning:** {match.reasoning}")
                st.progress(match.match_score)

        st.subheader("Keyword Gaps")
        for gap in sorted(
            analysis.gaps,
            key=lambda g: {"high": 3, "medium": 2, "low": 1}[g.importance],
            reverse=True,
        ):
            with st.expander(f"[{gap.importance.upper()}] {gap.missing_keyword}"):
                if gap.context_in_job:
                    st.write(f"**Context in job:** {gap.context_in_job}")
                st.write(f"**Suggested section:** {gap.suggested_section}")
                st.write(f"**Integration suggestion:** {gap.integration_suggestion}")

        st.subheader("Recommendations")
        for rec in analysis.recommendations:
            st.info(rec)

    # ── Tab 2: Tailored Resume ───────────────────────────────────
    with tab_resume:
        st.subheader("Updated Skills")
        st.write(" | ".join(tailored.updated_skills))

        st.subheader("Tailored Work History")
        for exp in tailored.tailored_work_history:
            st.markdown(f"**{exp.role}** at {exp.company} ({exp.duration})")
            for bullet in exp.tailored_bullet_points:
                st.write(f"- {bullet}")
            st.divider()

    # ── Tab 3: Cover Letter ──────────────────────────────────────
    with tab_cover:
        st.markdown(f"**{cover_letter.greeting}**")
        st.write(cover_letter.opening_paragraph)
        for para in cover_letter.body_paragraphs:
            st.write(para)
        st.write(cover_letter.closing_paragraph)
        st.markdown(f"*{cover_letter.sign_off}*")
        st.markdown(f"*{structured_resume.name}*")

    # ── Tab 4: Downloads ─────────────────────────────────────────
    with tab_downloads:
        base_dict = structured_resume.model_dump()
        tailored_dict = tailored.model_dump()
        cover_dict = cover_letter.model_dump()

        resume_pdf = generate_resume_pdf_bytes(base_dict, tailored_dict)
        cover_pdf = generate_cover_letter_pdf_bytes(cover_dict, structured_resume.name)

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="Download Tailored Resume (PDF)",
                data=resume_pdf,
                file_name="tailored_resume.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        with col2:
            st.download_button(
                label="Download Cover Letter (PDF)",
                data=cover_pdf,
                file_name="cover_letter.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
