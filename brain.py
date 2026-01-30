import ollama
import json
import re
from models import ResumeSchema, JobDescriptionSchema
from tqdm import tqdm
import time

class ResumeBrain:
    def __init__(self, model_name="llama3.2:3b"):
        self.model_name = model_name

    def _fix_stringified_arrays(self, json_str: str) -> str:
        """Fix description fields that are stringified arrays instead of actual arrays."""
        # Pattern: "description": "[\"item1\", \"item2\"]"
        # Should be: "description": ["item1", "item2"]

        # Fix stringified arrays in description fields
        pattern = r'"description":\s*"\[(.*?)\]"'

        def replace_func(match):
            # Extract the stringified array content
            array_content = match.group(1)
            # Remove the outer quotes and return as an actual array
            return f'"description": [{array_content}]'

        fixed = re.sub(pattern, replace_func, json_str)
        return fixed

    def _clean_json_response(self, response: str) -> str:
        """Clean and fix common JSON formatting issues from LLM responses."""
        # Remove markdown code blocks
        cleaned = response.strip()

        # Remove markdown JSON code blocks
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        cleaned = cleaned.strip()

        # Replace control characters that are invalid in JSON strings
        # We need to be careful to only replace them in string contexts
        # A simpler approach: replace common problematic characters globally
        # JSON strings should have these escaped
        control_char_map = {
            '\n': '\\n',
            '\r': '\\r',
            '\t': '\\t',
            '\b': '\\b',
            '\f': '\\f',
        }

        for char, escaped in control_char_map.items():
            # Only replace if not already escaped
            cleaned = re.sub(f'(?<!\\\\){re.escape(char)}', escaped, cleaned)

        # Fix stringified arrays (common LLM mistake)
        cleaned = self._fix_stringified_arrays(cleaned)

        return cleaned

    def _stream_and_structure(self, prompt: str, description: str):
        """Helper function to stream responses and show progress."""

        # Use format='json' to force valid JSON output
        stream = ollama.generate(
            model=self.model_name,
            prompt=prompt,
            stream=True,
            format='json'
        )
        
        response_chunks = []
        
        # Using a large number for total because we don't know the response size
        with tqdm(desc=description, unit=" B", unit_scale=True, total=0) as pbar:
            for chunk in stream:
                if 'response' in chunk:
                    response_chunks.append(chunk['response'])
                    pbar.update(len(chunk['response'].encode('utf-8')))
                
                if chunk.get('done'):
                    if 'total_duration' in chunk and 'eval_count' in chunk:
                        duration_seconds = chunk['total_duration'] / 1e9  # nanoseconds to seconds
                        if duration_seconds > 0:
                            tokens_per_second = chunk['eval_count'] / duration_seconds
                            pbar.set_postfix_str(f"{tokens_per_second:.2f} tok/s")
                    # Set pbar to 100% on completion
                    if pbar.total == 0:
                        pbar.total = pbar.n
                    pbar.refresh()
                    break

        full_response = "".join(response_chunks)

        try:
            # Clean the response to ensure it's valid JSON
            cleaned_response = self._clean_json_response(full_response)
            data = json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            # Handle cases where the response is not valid JSON
            print("Error: LLM response was not valid JSON.")
            print(f"JSON Error: {e}")
            print(f"Error at line {e.lineno}, column {e.colno}: {e.msg}")
            print("\nProblematic section:")
            # Show context around the error
            lines = cleaned_response.split('\n')
            start = max(0, e.lineno - 3)
            end = min(len(lines), e.lineno + 2)
            for i in range(start, end):
                marker = ">>> " if i == e.lineno - 1 else "    "
                print(f"{marker}{i + 1}: {lines[i]}")

            print("\n--- Attempting to save response to file for debugging ---")
            try:
                debug_file = "/private/tmp/claude-501/-Users-jaoewn-Projects-Contextual-Resume-Optimizer/ba9613f2-b7bf-47a8-a966-91a2b24cbba6/scratchpad/failed_json_response.txt"
                with open(debug_file, 'w') as f:
                    f.write("=== ORIGINAL RESPONSE ===\n")
                    f.write(full_response)
                    f.write("\n\n=== CLEANED RESPONSE ===\n")
                    f.write(cleaned_response)
                print(f"Debug info saved to: {debug_file}")
            except Exception as write_err:
                print(f"Could not save debug file: {write_err}")

            raise ValueError("LLM response could not be parsed as JSON.")

        return data

    def structure_resume(self, raw_text: str) -> ResumeSchema:
        """Uses LLM to turn raw text into a structured JSON format."""

        example_json = '''{
  "name": "Jane Smith",
  "email": "jane@example.com",
  "skills": ["Python", "JavaScript", "SQL"],
  "work_history": [
    {
      "company": "Tech Corp",
      "role": "Software Engineer",
      "duration": "2020-2023",
      "description": [
        "Built scalable web applications",
        "Improved system performance by 40%"
      ]
    }
  ],
  "education": [
    {
      "institution": "University Name",
      "degree": "B.S. Computer Science",
      "graduation_date": "2020"
    }
  ]
}'''

        prompt = f"""
        You are an expert HR Data Scientist. Convert the resume text into a valid JSON object.

        REQUIRED JSON STRUCTURE (follow this exact format):
        {example_json}

        CRITICAL RULES:
        1. The "description" field MUST be an array of strings, NOT a stringified array
        2. Each education entry should be a simple object with keys like "institution", "degree", "graduation_date"
        3. Return ONLY the JSON object - no extra text, markdown, or explanations
        4. Ensure all arrays and objects are properly formatted
        5. Do not include any JSON Schema keywords like "type", "properties", "additionalProperties"

        Here is the resume text to convert:
        ---RESUME START---
        {raw_text}
        ---RESUME END---

        Return the JSON object:
        """

        data = self._stream_and_structure(prompt, "Structuring Resume")
        
        # Validation: This turns the dict into our official Pydantic object
        return ResumeSchema(**data)

    def structure_job_description(self, raw_text: str) -> JobDescriptionSchema:
        """Uses LLM to turn raw job description text into a structured JSON format."""

        example_json = '''{
  "title": "Senior Software Engineer",
  "required_skills": ["Python", "AWS", "Docker"],
  "responsibilities": [
    "Design and implement backend services",
    "Collaborate with cross-functional teams"
  ]
}'''

        prompt = f"""
        You are an expert HR Data Scientist. Convert the job description into a valid JSON object.

        REQUIRED JSON STRUCTURE (follow this exact format):
        {example_json}

        CRITICAL RULES:
        1. All arrays MUST be actual arrays, NOT stringified arrays
        2. Return ONLY the JSON object - no extra text, markdown, or explanations
        3. Ensure all arrays and objects are properly formatted

        Here is the job description to convert:
        ---JOB DESCRIPTION START---
        {raw_text}
        ---JOB DESCRIPTION END---

        Return the JSON object:
        """

        data = self._stream_and_structure(prompt, "Structuring Job Description")
        
        # Validation: This turns the dict into our official Pydantic object
        return JobDescriptionSchema(**data)

if __name__ == "__main__":
    # This is for a quick isolated test
    brain = ResumeBrain()
    print("Brain initialized and ready for inference.")
