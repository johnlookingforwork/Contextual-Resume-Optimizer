import ollama
import json
from models import ResumeSchema 

class ResumeBrain:
    def __init__(self, model_name="llama3.2:3b"):
        self.model_name = model_name

    def structure_resume(self, raw_text: str) -> ResumeSchema:
        """Uses LLM to turn raw text into a structured JSON format."""
        
        prompt = f"""
        You are an expert HR Data Scientist. Convert the following raw resume text into a 
        structured JSON format that exactly matches this schema:
        {ResumeSchema.schema_json()}
        
        Raw Text:
        {raw_text}
        
        Return ONLY the JSON. Do not include any conversational text.
        """

        response = ollama.generate(model=self.model_name, prompt=prompt)
        
        # Parse the string response into a Python dictionary
        data = json.loads(response['response'])
        
        # Validation: This turns the dict into our official Pydantic object
        return ResumeSchema(**data)

if __name__ == "__main__":
    # This is for a quick isolated test
    brain = ResumeBrain()
    print("Brain initialized and ready for inference.")