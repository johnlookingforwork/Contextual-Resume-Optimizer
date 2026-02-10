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

    # --- Header: Name & Contact ---
    name = base_resume.get("name", "")
    email = base_resume.get("email", "")
    phone = base_resume.get("phone", "")
    location = base_resume.get("location", "")

    story.append(Paragraph(name, styles["Name"]))
    contact_parts = [p for p in [email, phone, location] if p]
    if contact_parts:
        story.append(Paragraph(" | ".join(contact_parts), styles["Contact"]))
    story.append(_section_divider())

    # --- Skills ---
    skills = tailored.get("updated_skills", [])
    if skills:
        story.append(Paragraph("SKILLS", styles["SectionHeader"]))
        story.append(_section_divider())
        skills_text = " | ".join(skills)
        story.append(Paragraph(skills_text, styles["SkillText"]))
        story.append(Spacer(1, 4))

    # --- Work Experience ---
    work_history = tailored.get("tailored_work_history", [])
    if work_history:
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
                story.append(
                    Paragraph(
                        f"&bull;  {clean}",
                        styles["Bullet"],
                    )
                )
            story.append(Spacer(1, 6))

    # --- Education ---
    education = base_resume.get("education", [])
    if education:
        story.append(Paragraph("EDUCATION", styles["SectionHeader"]))
        story.append(_section_divider())

        for edu in education:
            degree = edu.get("degree", "")
            institution = edu.get("institution", "")
            grad_date = edu.get("graduation_date", "")

            story.append(Paragraph(degree, styles["EduTitle"]))
            story.append(
                Paragraph(f"{institution} | {grad_date}", styles["EduMeta"])
            )

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

    # --- Header ---
    name = base_resume.get("name", "")
    email = base_resume.get("email", "")
    phone = base_resume.get("phone", "")
    location = base_resume.get("location", "")

    story.append(Paragraph(name, styles["Name"]))
    contact_parts = [p for p in [email, phone, location] if p]
    if contact_parts:
        story.append(Paragraph(" | ".join(contact_parts), styles["Contact"]))
    story.append(_section_divider())

    # --- Skills ---
    skills = tailored.get("updated_skills", [])
    if skills:
        story.append(Paragraph("SKILLS", styles["SectionHeader"]))
        story.append(_section_divider())
        story.append(Paragraph(" | ".join(skills), styles["SkillText"]))
        story.append(Spacer(1, 4))

    # --- Work Experience ---
    work_history = tailored.get("tailored_work_history", [])
    if work_history:
        story.append(Paragraph("PROFESSIONAL EXPERIENCE", styles["SectionHeader"]))
        story.append(_section_divider())
        for job in work_history:
            story.append(Paragraph(job.get("role", ""), styles["JobTitle"]))
            story.append(
                Paragraph(
                    f"{job.get('company', '')} | {job.get('duration', '')}",
                    styles["JobMeta"],
                )
            )
            for bullet in job.get("tailored_bullet_points", []):
                clean = bullet.lstrip("- ")
                story.append(Paragraph(f"&bull;  {clean}", styles["Bullet"]))
            story.append(Spacer(1, 6))

    # --- Education ---
    education = base_resume.get("education", [])
    if education:
        story.append(Paragraph("EDUCATION", styles["SectionHeader"]))
        story.append(_section_divider())
        for edu in education:
            story.append(Paragraph(edu.get("degree", ""), styles["EduTitle"]))
            story.append(
                Paragraph(
                    f"{edu.get('institution', '')} | {edu.get('graduation_date', '')}",
                    styles["EduMeta"],
                )
            )

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
