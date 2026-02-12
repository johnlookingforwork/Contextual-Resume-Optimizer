import os
from extractor import extract_resume_text
from ocr_engine import extract_text_from_image
from brain import ResumeBrain

def main():
    # 1. Path to your local resume
    resume_path = "data/my_resume.pdf"
    job_desc_path = "data/job_screenshot.png"

    print(f"--- Step 1: Extracting text from {resume_path} and {job_desc_path} ---")
    raw_resume = extract_resume_text(resume_path)
    raw_job_text = extract_text_from_image(job_desc_path)

    print("--- Step 2: Initializing the AI Brain (OpenAI) ---")
    brain = ResumeBrain(api_key=os.environ.get("OPENAI_API_KEY"))

    print("--- Step 3: Structuring the Resume ---")
    # This calls your brain.py logic to talk to Ollama
    structured_resume = brain.structure_resume(raw_resume.raw_text)

    print("--- Step 4: Structuring the Job Description ---")
    structured_job_desc = brain.structure_job_description(raw_job_text)

    print("\n--- Success! Structured Resume Data: ---")
    print(f"Name: {structured_resume.name}")
    print("Skills Identified:")
    for category, skill_list in structured_resume.skills.items():
        print(f"  {category}: {', '.join(skill_list)}")

    print("\n--- Success! Structured Job Description Data: ---")
    print(f"Job Title: {structured_job_desc.title}")
    print(f"Required Skills: {', '.join(structured_job_desc.required_skills)}")

    # Phase 2: Semantic Analysis
    print("\n--- Step 5: Running Semantic Analysis ---")
    analysis = brain.analyze_resume(structured_resume, structured_job_desc)

    print("\n" + "="*60)
    print("ANALYSIS RESULTS")
    print("="*60)

    print(f"\n📊 Overall Alignment Score: {analysis.overall_alignment_score:.1%}")

    print(f"\n✅ Top Strengths ({len(analysis.strengths)} found):")
    for i, strength in enumerate(analysis.strengths[:5], 1):
        print(f"  {i}. {strength}")

    print(f"\n🎯 Semantic Matches ({len(analysis.matches)} found):")
    for i, match in enumerate(sorted(analysis.matches, key=lambda x: x.match_score, reverse=True)[:5], 1):
        print(f"  {i}. [{match.match_type.upper()}] '{match.resume_item}' → '{match.job_requirement}'")
        print(f"     Score: {match.match_score:.2f} | {match.reasoning}")

    print(f"\n⚠️  Keyword Gaps ({len(analysis.gaps)} found):")
    for i, gap in enumerate(sorted(analysis.gaps, key=lambda g: {"high": 3, "medium": 2, "low": 1}[g.importance], reverse=True)[:5], 1):
        print(f"  {i}. [{gap.importance.upper()}] {gap.missing_keyword}")
        print(f"     → {gap.integration_suggestion}")

    print(f"\n💡 Recommendations:")
    for i, rec in enumerate(analysis.recommendations, 1):
        print(f"  {i}. {rec}")

    print("\n" + "="*60)

    # Save analysis results to file
    output_path = "cache/latest_analysis.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(analysis.model_dump_json(indent=2))
    print(f"\n💾 Full analysis saved to: {output_path}")

    # Phase 3: Resume Tailoring
    print("\n--- Step 6: Tailoring Resume ---")
    tailored_resume = brain.tailor_resume(structured_resume, analysis, structured_job_desc)

    print("\n" + "="*60)
    print("TAILORED RESUME")
    print("="*60)

    print("\n✨ Updated Skills:")
    for category, skill_list in tailored_resume.updated_skills.items():
        print(f"  {category}: {', '.join(skill_list)}")

    print("\n📝 Tailored Work History:")
    for exp in tailored_resume.tailored_work_history:
        print(f"\n  🏢 {exp.company} - {exp.role} ({exp.duration})")
        for bullet in exp.tailored_bullet_points:
            print(f"    • {bullet}")

    if tailored_resume.tailored_projects:
        print("\n🔧 Tailored Projects:")
        for proj in tailored_resume.tailored_projects:
            print(f"\n  📂 {proj.name} ({', '.join(proj.tech_stack)})")
            if proj.url:
                print(f"     {proj.url}")
            for bullet in proj.tailored_bullet_points:
                print(f"    • {bullet}")

    print("\n" + "="*60)

    # Save tailored resume to file
    output_path = "cache/tailored_resume.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(tailored_resume.model_dump_json(indent=2))
    print(f"\n💾 Full tailored resume saved to: {output_path}")

if __name__ == "__main__":
    main()
