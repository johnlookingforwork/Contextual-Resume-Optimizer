from extractor import extract_resume_text
from brain import ResumeBrain

def main():
    # 1. Path to your local resume
    resume_path = "data/my_resume.pdf"
    
    print(f"--- Step 1: Extracting text from {resume_path} ---")
    raw_data = extract_resume_text(resume_path)
    
    print("--- Step 2: Initializing the AI Brain (Ollama) ---")
    brain = ResumeBrain(model_name="llama3.2:3b")
    
    print("--- Step 3: Structuring the Resume ---")
    # This calls your brain.py logic to talk to Ollama
    structured_resume = brain.structure_resume(raw_data.raw_text)
    
    print("\n--- Success! Structured Resume Data: ---")
    print(f"Name: {structured_resume.name}")
    print(f"Skills Identified: {', '.join(structured_resume.skills)}")
    
    # You can also print the whole JSON object
    # print(structured_resume.json(indent=2))

if __name__ == "__main__":
    main()