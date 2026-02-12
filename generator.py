import json
import glob
import os
from io import BytesIO
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
)
from reportlab.lib.colors import HexColor


CACHE_DIR = Path("cache")
OUTPUT_DIR = Path("output")


def _find_base_resume() -> dict:
    """Find and load the cached base resume JSON (contains name, email, education)."""
    pattern = str(CACHE_DIR / "resume_*.json")
    matches = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    if not matches:
        raise FileNotFoundError(
            "No cached base resume found in cache/. Run main.py first to generate it."
        )
    with open(matches[0], "r", encoding="utf-8") as f:
        return json.load(f)


def _load_tailored_resume() -> dict:
    """Load the tailored resume JSON."""
    path = CACHE_DIR / "tailored_resume.json"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run main.py first to generate the tailored resume."
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_styles() -> dict:
    """Create paragraph styles for the resume PDF."""
    base = getSampleStyleSheet()
    styles = {}

    styles["Name"] = ParagraphStyle(
        "Name",
        parent=base["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        alignment=TA_CENTER,
        spaceAfter=2,
        textColor=HexColor("#1a1a1a"),
    )

    styles["Contact"] = ParagraphStyle(
        "Contact",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
        spaceAfter=6,
        textColor=HexColor("#444444"),
    )

    styles["SectionHeader"] = ParagraphStyle(
        "SectionHeader",
        parent=base["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        spaceBefore=10,
        spaceAfter=4,
        textColor=HexColor("#1a1a1a"),
        borderWidth=0,
    )

    styles["JobTitle"] = ParagraphStyle(
        "JobTitle",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        spaceAfter=1,
        textColor=HexColor("#1a1a1a"),
    )

    styles["JobMeta"] = ParagraphStyle(
        "JobMeta",
        parent=base["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=10,
        leading=13,
        spaceAfter=3,
        textColor=HexColor("#555555"),
    )

    styles["Bullet"] = ParagraphStyle(
        "Bullet",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=13,
        leftIndent=14,
        bulletIndent=0,
        spaceAfter=2,
        textColor=HexColor("#2a2a2a"),
    )

    styles["SkillText"] = ParagraphStyle(
        "SkillText",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        spaceAfter=2,
        textColor=HexColor("#2a2a2a"),
    )

    styles["EduTitle"] = ParagraphStyle(
        "EduTitle",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        spaceAfter=1,
        textColor=HexColor("#1a1a1a"),
    )

    styles["EduMeta"] = ParagraphStyle(
        "EduMeta",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=13,
        spaceAfter=4,
        textColor=HexColor("#555555"),
    )

    styles["ProjectTitle"] = ParagraphStyle(
        "ProjectTitle",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        spaceAfter=1,
        textColor=HexColor("#1a1a1a"),
    )

    styles["ProjectMeta"] = ParagraphStyle(
        "ProjectMeta",
        parent=base["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=10,
        leading=13,
        spaceAfter=3,
        textColor=HexColor("#555555"),
    )

    return styles


def _section_divider():
    """Return a horizontal rule for section separation."""
    return HRFlowable(
        width="100%",
        thickness=0.5,
        color=HexColor("#cccccc"),
        spaceBefore=2,
        spaceAfter=6,
    )


def _build_header(story, styles, base_resume):
    """Build the header section: Name | email | links."""
    name = base_resume.get("name", "")
    email = base_resume.get("email", "")
    links = base_resume.get("links", [])

    story.append(Paragraph(name, styles["Name"]))
    contact_parts = [p for p in [email] + links if p]
    if contact_parts:
        story.append(Paragraph(" | ".join(contact_parts), styles["Contact"]))
    story.append(_section_divider())


def _build_skills(story, styles, tailored):
    """Build the categorized skills section."""
    skills = tailored.get("updated_skills", {})
    if not skills:
        return

    story.append(Paragraph("SKILLS", styles["SectionHeader"]))
    story.append(_section_divider())

    # Handle both dict (categorized) and list (legacy flat) formats
    if isinstance(skills, dict):
        for category, skill_list in skills.items():
            if skill_list:
                text = f"<b>{category}:</b> {', '.join(skill_list)}"
                story.append(Paragraph(text, styles["SkillText"]))
    else:
        story.append(Paragraph(" | ".join(skills), styles["SkillText"]))

    story.append(Spacer(1, 4))


def _build_experience(story, styles, tailored):
    """Build the work experience section."""
    work_history = tailored.get("tailored_work_history", [])
    if not work_history:
        return

    story.append(Paragraph("PROFESSIONAL EXPERIENCE", styles["SectionHeader"]))
    story.append(_section_divider())

    for job in work_history:
        company = job.get("company", "")
        role = job.get("role", "")
        duration = job.get("duration", "")

        story.append(Paragraph(f"{role}", styles["JobTitle"]))
        story.append(Paragraph(f"{company} | {duration}", styles["JobMeta"]))

        for bullet in job.get("tailored_bullet_points", []):
            clean = bullet.lstrip("- ")
            story.append(Paragraph(f"&bull;  {clean}", styles["Bullet"]))
        story.append(Spacer(1, 6))


def _build_projects(story, styles, tailored):
    """Build the projects section."""
    projects = tailored.get("tailored_projects", [])
    if not projects:
        return

    story.append(Paragraph("PROJECTS", styles["SectionHeader"]))
    story.append(_section_divider())

    for proj in projects:
        name = proj.get("name", "")
        url = proj.get("url", "")
        tech_stack = proj.get("tech_stack", [])

        title_parts = [name]
        if url:
            title_parts.append(url)
        story.append(Paragraph(" | ".join(title_parts), styles["ProjectTitle"]))

        if tech_stack:
            story.append(
                Paragraph(
                    f"<b>Tech Stack:</b> {', '.join(tech_stack)}",
                    styles["ProjectMeta"],
                )
            )

        for bullet in proj.get("tailored_bullet_points", []):
            clean = bullet.lstrip("- ")
            story.append(Paragraph(f"&bull;  {clean}", styles["Bullet"]))
        story.append(Spacer(1, 6))


def _build_education(story, styles, tailored, base_resume):
    """Build the education section from tailored_education, falling back to base_resume."""
    education = tailored.get("tailored_education", []) or base_resume.get("education", [])
    if not education:
        return

    story.append(Paragraph("EDUCATION", styles["SectionHeader"]))
    story.append(_section_divider())

    for edu in education:
        degree = edu.get("degree", "")
        institution = edu.get("institution", "")
        grad_date = edu.get("graduation_date", "")

        story.append(Paragraph(degree, styles["EduTitle"]))
        story.append(Paragraph(f"{institution} | {grad_date}", styles["EduMeta"]))


def generate_pdf(output_filename: str = "tailored_resume.pdf") -> Path:
    """
    Generate an ATS-friendly PDF resume by combining:
    - Personal info + education from the cached base resume
    - Tailored work history + updated skills from tailored_resume.json

    Returns the path to the generated PDF.
    """
    base_resume = _find_base_resume()
    tailored = _load_tailored_resume()

    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / output_filename

    styles = _build_styles()

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
    )

    story = []

    # Section order: Header -> Skills -> Experience -> Projects -> Education
    _build_header(story, styles, base_resume)
    _build_skills(story, styles, tailored)
    _build_experience(story, styles, tailored)
    _build_projects(story, styles, tailored)
    _build_education(story, styles, tailored, base_resume)

    doc.build(story)
    return output_path


def generate_resume_pdf_bytes(base_resume: dict, tailored: dict) -> BytesIO:
    """Generate an ATS-friendly PDF resume into an in-memory buffer.

    Same layout as generate_pdf() but accepts data directly and returns
    a BytesIO object suitable for st.download_button.
    """
    buf = BytesIO()
    styles = _build_styles()

    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
    )

    story = []

    # Section order: Header -> Skills -> Experience -> Projects -> Education
    _build_header(story, styles, base_resume)
    _build_skills(story, styles, tailored)
    _build_experience(story, styles, tailored)
    _build_projects(story, styles, tailored)
    _build_education(story, styles, tailored, base_resume)

    doc.build(story)
    buf.seek(0)
    return buf


def generate_cover_letter_pdf_bytes(cover_letter: dict, candidate_name: str) -> BytesIO:
    """Generate a professional cover letter PDF into an in-memory buffer."""
    buf = BytesIO()
    base = getSampleStyleSheet()

    styles = {
        "Name": ParagraphStyle(
            "CLName",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            alignment=TA_CENTER,
            spaceAfter=2,
            textColor=HexColor("#1a1a1a"),
        ),
        "Greeting": ParagraphStyle(
            "CLGreeting",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=16,
            spaceAfter=8,
            textColor=HexColor("#1a1a1a"),
        ),
        "Body": ParagraphStyle(
            "CLBody",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=16,
            spaceAfter=10,
            textColor=HexColor("#2a2a2a"),
        ),
        "SignOff": ParagraphStyle(
            "CLSignOff",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=16,
            spaceBefore=16,
            spaceAfter=4,
            textColor=HexColor("#1a1a1a"),
        ),
    }

    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        topMargin=0.8 * inch,
        bottomMargin=0.8 * inch,
        leftMargin=1.0 * inch,
        rightMargin=1.0 * inch,
    )

    story = []

    # Name header
    story.append(Paragraph(candidate_name, styles["Name"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#cccccc"), spaceBefore=2, spaceAfter=14))

    # Greeting
    story.append(Paragraph(cover_letter.get("greeting", "Dear Hiring Manager,"), styles["Greeting"]))

    # Opening paragraph
    story.append(Paragraph(cover_letter.get("opening_paragraph", ""), styles["Body"]))

    # Body paragraphs
    for para in cover_letter.get("body_paragraphs", []):
        story.append(Paragraph(para, styles["Body"]))

    # Closing paragraph
    story.append(Paragraph(cover_letter.get("closing_paragraph", ""), styles["Body"]))

    # Sign off
    story.append(Paragraph(cover_letter.get("sign_off", "Sincerely,"), styles["SignOff"]))
    story.append(Paragraph(candidate_name, styles["SignOff"]))

    doc.build(story)
    buf.seek(0)
    return buf


if __name__ == "__main__":
    print("Generating ATS-friendly PDF resume...")
    path = generate_pdf()
    print(f"PDF saved to: {path}")
