import json
import re
import hashlib
import os
from pathlib import Path
from typing import List
from models import (
    ResumeSchema,
    JobDescriptionSchema,
    SemanticMatch,
    KeywordGap,
    AnalysisResult,
    TailoredResume,
    TailoredExperience,
    Experience,
    CoverLetter,
)
from tqdm import tqdm
import time

class ResumeBrain:
    def __init__(self, provider="openai", model_name=None, api_key=None, cache_dir="cache"):
        self.provider = provider
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        if provider == "openai":
            from openai import OpenAI
            self.model_name = model_name or "gpt-4o"
            self.openai_client = OpenAI(api_key=api_key)
        else:
            import ollama
            self.ollama = ollama
            self.model_name = model_name or "llama3.2:3b"

    def _get_cache_key(self, text: str) -> str:
        """Generate a hash-based cache key from input text."""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def _get_cache_path(self, cache_type: str, text: str) -> Path:
        """Get the cache file path for a given input."""
        cache_key = self._get_cache_key(text)
        return self.cache_dir / f"{cache_type}_{cache_key}.json"

    def _load_from_cache(self, cache_path: Path) -> dict | None:
        """Load structured data from cache if it exists."""
        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load cache from {cache_path}: {e}")
                return None
        return None

    def _save_to_cache(self, cache_path: Path, data: dict):
        """Save structured data to cache."""
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to save cache to {cache_path}: {e}")

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
        """Helper function to call LLM and return parsed JSON dict."""

        if self.provider == "openai":
            return self._openai_call(prompt, description)
        else:
            return self._ollama_call(prompt, description)

    def _openai_call(self, prompt: str, description: str) -> dict:
        """Call OpenAI API with JSON mode and return parsed dict."""
        print(f"  [{description}] Calling OpenAI ({self.model_name})...")
        response = self.openai_client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        return json.loads(content)

    def _ollama_call(self, prompt: str, description: str) -> dict:
        """Call Ollama with streaming and return parsed dict."""
        stream = self.ollama.generate(
            model=self.model_name,
            prompt=prompt,
            stream=True,
            format='json'
        )

        response_chunks = []

        with tqdm(desc=description, unit=" B", unit_scale=True, total=0) as pbar:
            for chunk in stream:
                if 'response' in chunk:
                    response_chunks.append(chunk['response'])
                    pbar.update(len(chunk['response'].encode('utf-8')))

                if chunk.get('done'):
                    if 'total_duration' in chunk and 'eval_count' in chunk:
                        duration_seconds = chunk['total_duration'] / 1e9
                        if duration_seconds > 0:
                            tokens_per_second = chunk['eval_count'] / duration_seconds
                            pbar.set_postfix_str(f"{tokens_per_second:.2f} tok/s")
                    if pbar.total == 0:
                        pbar.total = pbar.n
                    pbar.refresh()
                    break

        full_response = "".join(response_chunks)

        try:
            cleaned_response = self._clean_json_response(full_response)
            data = json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            print("Error: LLM response was not valid JSON.")
            print(f"JSON Error: {e}")
            print(f"Error at line {e.lineno}, column {e.colno}: {e.msg}")
            print("\nProblematic section:")
            lines = cleaned_response.split('\n')
            start = max(0, e.lineno - 3)
            end = min(len(lines), e.lineno + 2)
            for i in range(start, end):
                marker = ">>> " if i == e.lineno - 1 else "    "
                print(f"{marker}{i + 1}: {lines[i]}")
            raise ValueError("LLM response could not be parsed as JSON.")

        return data

    def structure_resume(self, raw_text: str) -> ResumeSchema:
        """Uses LLM to turn raw text into a structured JSON format."""

        # Check cache first
        cache_path = self._get_cache_path("resume", raw_text)
        cached_data = self._load_from_cache(cache_path)

        if cached_data is not None:
            print(f"Loading resume from cache: {cache_path}")
            return ResumeSchema(**cached_data)

        print("Cache not found, processing with LLM...")

        example_json = '''{
  "name": "Jane Smith",
  "email": "jane@example.com",
  "phone": "(555) 123-4567",
  "location": "Dallas, TX",
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
        6. Extract the phone number exactly as it appears on the resume. If not found, set "phone" to null
        7. Extract the city and state (e.g. "Dallas, TX") as "location". If not found, set "location" to null

        Here is the resume text to convert:
        ---RESUME START---
        {raw_text}
        ---RESUME END---

        Return the JSON object:
        """

        data = self._stream_and_structure(prompt, "Structuring Resume")

        # Save to cache
        self._save_to_cache(cache_path, data)
        print(f"Saved resume to cache: {cache_path}")

        # Validation: This turns the dict into our official Pydantic object
        return ResumeSchema(**data)

    def structure_job_description(self, raw_text: str) -> JobDescriptionSchema:
        """Uses LLM to turn raw job description text into a structured JSON format."""

        # Check cache first
        cache_path = self._get_cache_path("job_description", raw_text)
        cached_data = self._load_from_cache(cache_path)

        if cached_data is not None:
            print(f"Loading job description from cache: {cache_path}")
            return JobDescriptionSchema(**cached_data)

        print("Cache not found, processing with LLM...")

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

        # Save to cache
        self._save_to_cache(cache_path, data)
        print(f"Saved job description to cache: {cache_path}")

        # Validation: This turns the dict into our official Pydantic object
        return JobDescriptionSchema(**data)

    # ==================== Phase 2: Semantic Analysis Methods ====================

    def analyze_semantic_matches(
        self,
        resume: ResumeSchema,
        job_description: JobDescriptionSchema
    ) -> List[SemanticMatch]:
        """
        Analyzes semantic connections between resume and job requirements.
        Identifies not just exact matches but also transferable skills and semantic similarities.
        """
        # Create a combined cache key from both resume and job description
        cache_key_text = f"{resume.model_dump_json()}|{job_description.model_dump_json()}"
        cache_path = self._get_cache_path("semantic_matches", cache_key_text)
        cached_data = self._load_from_cache(cache_path)

        if cached_data is not None:
            print(f"Loading semantic matches from cache: {cache_path}")
            return [SemanticMatch(**match) for match in cached_data]

        print("Analyzing semantic skill matches...")

        # Prepare resume content for analysis
        resume_skills = resume.skills
        resume_experiences = []
        for exp in resume.work_history:
            resume_experiences.extend(exp.description)

        example_json = '''{
  "matches": [
    {
      "resume_item": "Led team of 5 developers",
      "job_requirement": "Leadership experience",
      "match_score": 0.9,
      "reasoning": "Leading a team of developers directly demonstrates leadership experience",
      "match_type": "semantic"
    },
    {
      "resume_item": "Python",
      "job_requirement": "Python",
      "match_score": 1.0,
      "reasoning": "Exact skill match",
      "match_type": "exact"
    },
    {
      "resume_item": "JavaScript",
      "job_requirement": "Frontend development",
      "match_score": 0.7,
      "reasoning": "JavaScript is commonly used for frontend development",
      "match_type": "transferable"
    }
  ]
}'''

        prompt = f"""
        You are an expert recruiter analyzing semantic connections between a candidate's resume and a job description.

        RESUME SKILLS: {resume_skills}
        RESUME EXPERIENCES (bullet points): {resume_experiences[:20]}

        JOB REQUIRED SKILLS: {job_description.required_skills}
        JOB RESPONSIBILITIES: {job_description.responsibilities}

        Analyze and identify connections between the resume and job requirements. Look for:
        1. EXACT matches (same terminology)
        2. SEMANTIC matches (different words, same concept: "Team Captain" → "Leadership")
        3. TRANSFERABLE skills (related skills: "JavaScript" → "Frontend Development")

        Return a JSON object following this structure:
        {example_json}

        RULES:
        1. Only identify genuine connections - do not fabricate skills
        2. match_score should reflect confidence (1.0 = exact, 0.7-0.9 = semantic, 0.5-0.7 = transferable)
        3. Be thorough but realistic
        4. Focus on the most important/relevant matches

        Return the JSON object:
        """

        data = self._stream_and_structure(prompt, "Analyzing Semantic Matches")

        # Save to cache
        self._save_to_cache(cache_path, data.get("matches", []))

        # Convert to Pydantic models
        matches = [SemanticMatch(**match) for match in data.get("matches", []) if match.get("job_requirement")]
        return matches

    def identify_keyword_gaps(
        self,
        resume: ResumeSchema,
        job_description: JobDescriptionSchema,
        existing_matches: List[SemanticMatch]
    ) -> List[KeywordGap]:
        """
        Identifies important keywords/skills from the job description that are missing from the resume.
        Uses existing matches to avoid suggesting keywords that are already covered semantically.
        """
        # Create cache key
        cache_key_text = f"{resume.model_dump_json()}|{job_description.model_dump_json()}|gaps"
        cache_path = self._get_cache_path("keyword_gaps", cache_key_text)
        cached_data = self._load_from_cache(cache_path)

        if cached_data is not None:
            print(f"Loading keyword gaps from cache: {cache_path}")
            return [KeywordGap(**gap) for gap in cached_data]

        print("Analyzing keyword gaps...")

        # Extract what's already matched to avoid duplicates
        matched_job_requirements = [match.job_requirement for match in existing_matches]

        example_json = '''{
  "gaps": [
    {
      "missing_keyword": "Docker",
      "importance": "high",
      "context_in_job": "Required: Experience with Docker containerization",
      "suggested_section": "skills",
      "integration_suggestion": "Add 'Docker' to the skills list if you have any containerization experience"
    },
    {
      "missing_keyword": "CI/CD",
      "importance": "medium",
      "context_in_job": "Implement and maintain CI/CD pipelines",
      "suggested_section": "work_history",
      "integration_suggestion": "If you've worked with automated deployment, mention 'CI/CD pipeline' in relevant work experience"
    }
  ]
}'''

        prompt = f"""
        You are an ATS (Applicant Tracking System) expert analyzing keyword gaps between a resume and job description.

        RESUME SKILLS: {resume.skills}
        RESUME WORK HISTORY: {[exp.description for exp in resume.work_history][:15]}

        JOB REQUIRED SKILLS: {job_description.required_skills}
        JOB RESPONSIBILITIES: {job_description.responsibilities}

        ALREADY MATCHED (don't suggest these): {matched_job_requirements}

        Identify important keywords, skills, or concepts from the job description that are MISSING from the resume.

        Return JSON following this structure:
        {example_json}

        CRITICAL RULES:
        1. ONLY suggest keywords that appear in the job description
        2. Do NOT suggest keywords already matched (listed above)
        3. Do NOT fabricate or hallucinate keywords
        4. Prioritize by importance: "high" for required skills, "medium" for nice-to-have, "low" for minor mentions
        5. Be specific about WHERE and HOW to add each keyword
        6. Focus on ATS optimization - keywords that will help the resume get past automated screening

        Return the JSON object:
        """

        data = self._stream_and_structure(prompt, "Identifying Keyword Gaps")

        # Save to cache
        gaps_data = data.get("gaps", [])
        self._save_to_cache(cache_path, gaps_data)

        # Convert to Pydantic models
        gaps = [KeywordGap(**gap) for gap in gaps_data]
        return gaps

    def analyze_resume(
        self,
        resume: ResumeSchema,
        job_description: JobDescriptionSchema
    ) -> AnalysisResult:
        """
        Complete semantic analysis of resume against job description.
        Orchestrates all analysis steps and returns comprehensive results.
        """
        print("\n" + "="*60)
        print("STARTING SEMANTIC ANALYSIS")
        print("="*60)

        # Step 1: Find semantic matches
        matches = self.analyze_semantic_matches(resume, job_description)
        print(f"\n✓ Found {len(matches)} semantic matches")

        # Step 2: Identify keyword gaps
        gaps = self.identify_keyword_gaps(resume, job_description, matches)
        print(f"✓ Identified {len(gaps)} keyword gaps")

        # Step 3: Calculate overall alignment score
        # Score based on: (number of matches) / (total job requirements)
        total_requirements = len(job_description.required_skills) + len(job_description.responsibilities)
        alignment_score = min(1.0, len(matches) / max(1, total_requirements)) if total_requirements > 0 else 0.0

        # Step 4: Extract strengths (high-scoring matches)
        strengths = [
            f"{match.resume_item} aligns with {match.job_requirement} (score: {match.match_score:.2f})"
            for match in sorted(matches, key=lambda x: x.match_score, reverse=True)[:5]
        ]

        # Step 5: Generate high-level recommendations
        recommendations = []

        # Add skill recommendations based on high-priority gaps
        high_priority_gaps = [gap for gap in gaps if gap.importance == "high"]
        if high_priority_gaps:
            recommendations.append(
                f"Add {len(high_priority_gaps)} high-priority keywords: {', '.join([g.missing_keyword for g in high_priority_gaps[:3]])}"
            )

        # Add alignment recommendation
        if alignment_score < 0.5:
            recommendations.append("Consider tailoring your experience descriptions to better match job responsibilities")
        elif alignment_score >= 0.75:
            recommendations.append("Strong alignment with job requirements - focus on highlighting relevant projects")

        # Add transferable skills recommendation
        transferable_matches = [m for m in matches if m.match_type == "transferable"]
        if transferable_matches:
            recommendations.append(
                f"Emphasize transferable skills: {', '.join([m.resume_item for m in transferable_matches[:2]])}"
            )

        print(f"✓ Overall alignment score: {alignment_score:.2%}")
        print("="*60 + "\n")

        return AnalysisResult(
            matches=matches,
            gaps=gaps,
            overall_alignment_score=alignment_score,
            strengths=strengths,
            recommendations=recommendations
        )

    # ==================== Phase 3: Resume Tailoring Engine ====================

    def tailor_resume(self, resume: ResumeSchema, analysis: AnalysisResult) -> TailoredResume:
        """
        Rewrites resume content to align with the job description by tailoring each experience individually.
        """
        print("\n" + "="*60)
        print("STARTING RESUME TAILORING")
        print("="*60)

        tailored_work_history = []
        for experience in resume.work_history:
            tailored_experience = self._tailor_experience(experience, analysis)
            tailored_work_history.append(tailored_experience)

        # Update skills based on gaps
        updated_skills = resume.skills.copy()
        for gap in analysis.gaps:
            if gap.suggested_section == "skills" and gap.missing_keyword not in updated_skills:
                updated_skills.append(gap.missing_keyword)

        return TailoredResume(
            tailored_work_history=tailored_work_history,
            updated_skills=updated_skills
        )

    def _tailor_experience(self, experience: Experience, analysis: AnalysisResult) -> TailoredExperience:
        """
        Tailors a single work experience using the LLM.
        """
        cache_key_text = f"{experience.model_dump_json()}|{analysis.model_dump_json()}|tailored_exp"
        cache_path = self._get_cache_path("tailored_experience", cache_key_text)
        cached_data = self._load_from_cache(cache_path)

        if cached_data:
            print(f"Loading tailored experience for {experience.company} from cache: {cache_path}")
            return TailoredExperience(**cached_data)

        print(f"Tailoring experience for {experience.company} with LLM...")

        prompt = f"""
        You are an expert career coach. Rewrite the bullet points for a single work experience to align with the provided analysis.

        **Original Bullet Points for {experience.company}:**
        {self._format_bullet_points(experience.description)}

        **Analysis to Guide You:**
        - **Semantic Matches (Resume Item -> Job Requirement):**
        {self._format_semantic_matches(analysis.matches)}

        - **Keyword Gaps to Fill:**
        {self._format_keyword_gaps(analysis.gaps)}

        CRITICAL RULES:
        1.  Rewrite the bullet points to incorporate the language from the 'job_requirement' and 'missing_keyword' fields.
        2.  Preserve the original meaning and metrics of the bullet points.
        3.  Do NOT invent new experiences.

        **Output Format:**
        Return a single, valid JSON object with a single key "tailored_bullet_points" containing a list of the rewritten bullet points.

        EXAMPLE OUTPUT:
        {{
            "tailored_bullet_points": [
                "Engineered and implemented REST APIs for payment systems, resulting in a 15% increase in transaction speed.",
                "Led a team of 3 developers in a project that designed and implemented a bi-directional integration architecture, improving data consistency by 30%."
            ]
        }}

        Return the JSON object now:
        """

        data = self._stream_and_structure(prompt, f"Tailoring {experience.company}")

        raw_bullets = data.get("tailored_bullet_points", [])
        bullets = [str(b) for b in raw_bullets if str(b).strip()]

        return TailoredExperience(
            company=experience.company,
            role=experience.role,
            duration=experience.duration,
            tailored_bullet_points=bullets,
        )

    # ==================== Phase 4: Cover Letter Generation ====================

    def generate_cover_letter(
        self,
        resume: ResumeSchema,
        job_description: JobDescriptionSchema,
        analysis: AnalysisResult,
    ) -> CoverLetter:
        """Generate a cover letter grounded in the candidate's experience and semantic analysis."""
        cache_key_text = f"{resume.model_dump_json()}|{job_description.model_dump_json()}|cover_letter"
        cache_path = self._get_cache_path("cover_letter", cache_key_text)
        cached_data = self._load_from_cache(cache_path)

        if cached_data is not None:
            print(f"Loading cover letter from cache: {cache_path}")
            return CoverLetter(**cached_data)

        print("Generating cover letter with LLM...")

        example_json = '''{
  "greeting": "Dear Hiring Manager,",
  "opening_paragraph": "I am writing to express my interest in the Software Engineer position...",
  "body_paragraphs": [
    "In my role at Tech Corp, I led...",
    "Additionally, my experience with..."
  ],
  "closing_paragraph": "I am excited about the opportunity to contribute...",
  "sign_off": "Sincerely,"
}'''

        prompt = f"""
        You are an expert career coach. Write a concise, professional cover letter for a candidate applying to the following job.

        CANDIDATE NAME: {resume.name}
        CANDIDATE SKILLS: {resume.skills}
        CANDIDATE WORK HISTORY:
        {self._format_work_history(resume.work_history)}

        JOB TITLE: {job_description.title}
        JOB REQUIRED SKILLS: {job_description.required_skills}
        JOB RESPONSIBILITIES: {job_description.responsibilities}

        TOP STRENGTHS FROM ANALYSIS:
        {analysis.strengths}

        SEMANTIC MATCHES:
        {self._format_semantic_matches(analysis.matches[:5])}

        CRITICAL RULES:
        1. Ground every claim in the candidate's ACTUAL experience — do NOT fabricate achievements
        2. Reference specific skills and experiences from the resume
        3. Keep it concise: 1 opening paragraph, 2 body paragraphs, 1 closing paragraph
        4. Use a professional but personable tone
        5. The body paragraphs should connect the candidate's experience to the job requirements

        Return a JSON object following this structure:
        {example_json}

        Return the JSON object:
        """

        data = self._stream_and_structure(prompt, "Generating Cover Letter")

        self._save_to_cache(cache_path, data)
        print(f"Saved cover letter to cache: {cache_path}")

        return CoverLetter(**data)

    def _format_bullet_points(self, bullet_points: List[str]) -> str:
        return "\n".join([f"- {bp}" for bp in bullet_points])

    def _format_work_history(self, work_history: List) -> str:
        return "\n".join([
            f"- {exp.role} at {exp.company} ({exp.duration}):\n  " + "\n  ".join(exp.description)
            for exp in work_history
        ])

    def _format_semantic_matches(self, matches: List[SemanticMatch]) -> str:
        return "\n".join([
            f"- '{match.resume_item}' can be rephrased to match '{match.job_requirement}'"
            for match in matches
        ])

    def _format_keyword_gaps(self, gaps: List[KeywordGap]) -> str:
        return "\n".join([
            f"- The resume is missing the keyword '{gap.missing_keyword}' which is of {gap.importance} importance."
            for gap in gaps
        ])


if __name__ == "__main__":
    # This is for a quick isolated test
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        brain = ResumeBrain(provider="openai", api_key=api_key)
    else:
        brain = ResumeBrain(provider="ollama")
    print(f"Brain initialized with provider={brain.provider}, model={brain.model_name}")
