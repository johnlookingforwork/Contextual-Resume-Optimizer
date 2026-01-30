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

    print("--- Step 2: Initializing the AI Brain (Ollama) ---")
    brain = ResumeBrain(model_name="llama3.2:3b")
    
    print("--- Step 3: Structuring the Resume ---")
    # This calls your brain.py logic to talk to Ollama
    structured_resume = brain.structure_resume(raw_resume.raw_text)
    
    print("--- Step 4: Structuring the Job Description ---")
    structured_job_desc = brain.structure_job_description(raw_job_text)

    print("\n--- Success! Structured Resume Data: ---")
    print(f"Name: {structured_resume.name}")
    print(f"Skills Identified: {', '.join(structured_resume.skills)}")

    print("\n--- Success! Structured Job Description Data: ---")
    print(f"Job Title: {structured_job_desc.title}")
    print(f"Required Skills: {', '.join(structured_job_desc.required_skills)}")
    
    # You can also print the whole JSON object
    # print(structured_resume.json(indent=2))
    # print(structured_job_desc.json(indent=2))

if __name__ == "__main__":
    main()