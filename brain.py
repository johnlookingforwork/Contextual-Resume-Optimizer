import json
import hashlib
from pathlib import Path
from typing import List, Optional
from models import (
    ResumeSchema,
    JobDescriptionSchema,
    SemanticMatch,
    KeywordGap,
    AnalysisResult,
    TailoredResume,
    TailoredExperience,
    TailoredProject,
    Experience,
    Project,
    CoverLetter,
)

class ResumeBrain:
    def __init__(self, model_name="gpt-4o", api_key=None, cache_dir="cache"):
        from openai import OpenAI
        self.model_name = model_name
        self.client = OpenAI(api_key=api_key)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

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

    def _stream_and_structure(self, prompt: str, description: str) -> dict:
        """Call OpenAI with JSON mode and return parsed dict."""
        print(f"  [{description}] Calling OpenAI ({self.model_name})...")
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        return json.loads(content)

    def _flatten_skills(self, skills: dict) -> list:
        """Flatten a categorized skills dict into a single list for prompt injection."""
        return [s for cat in skills.values() for s in cat]

    def structure_resume(self, raw_text: str) -> ResumeSchema:
        """Uses LLM to turn raw text into a structured JSON format."""

        # Check cache first
        cache_path = self._get_cache_path("resume", raw_text)
        cached_data = self._load_from_cache(cache_path)

        if cached_data is not None:
            print(f"Loading resume from cache: {cache_path}")
            # Fallback: if cached skills is a flat list, wrap it
            if isinstance(cached_data.get("skills"), list):
                cached_data["skills"] = {"General": cached_data["skills"]}
            return ResumeSchema(**cached_data)

        print("Cache not found, processing with LLM...")

        example_json = '''{
  "name": "Jane Smith",
  "email": "jane@example.com",
  "phone": "(555) 123-4567",
  "location": "Dallas, TX",
  "links": ["github.com/janesmith", "linkedin.com/in/janesmith"],
  "skills": {
    "Languages": ["Python", "JavaScript", "SQL"],
    "Frameworks": ["React", "Django", "Flask"],
    "Tools": ["Docker", "Git", "AWS", "PostgreSQL"]
  },
  "work_history": [
    {
      "company": "Tech Corp",
      "role": "Software Engineer",
      "duration": "2020-2023",
      "description": [
        "Built scalable web applications serving 10K+ users",
        "Improved system performance by 40% through query optimization"
      ]
    }
  ],
  "projects": [
    {
      "name": "E-Commerce Platform",
      "description": [
        "Built a full-stack e-commerce platform with payment integration",
        "Implemented real-time inventory tracking with WebSockets"
      ],
      "tech_stack": ["React", "Node.js", "PostgreSQL", "Stripe"],
      "url": "github.com/janesmith/ecommerce"
    }
  ],
  "education": [
    {
      "institution": "University of Texas",
      "degree": "B.S. Computer Science",
      "graduation_date": "2020",
      "entry_type": "degree"
    }
  ]
}'''

        prompt = f"""
        You are an expert HR Data Scientist specializing in Software Engineering resumes.
        Convert the resume text into a valid JSON object.

        REQUIRED JSON STRUCTURE (follow this exact format):
        {example_json}

        CRITICAL RULES:
        1. The "description" field MUST be an array of strings, NOT a stringified array
        2. Return ONLY the JSON object - no extra text, markdown, or explanations
        3. Ensure all arrays and objects are properly formatted
        4. Do not include any JSON Schema keywords like "type", "properties", "additionalProperties"
        5. Extract the phone number exactly as it appears on the resume. If not found, set "phone" to null
        6. Extract the city and state (e.g. "Dallas, TX") as "location". If not found, set "location" to null
        7. Do NOT extract any Summary or Objective section content
        8. "skills" MUST be a dictionary grouped by category (e.g. "Languages", "Frameworks", "Tools", "Cloud", "Databases").
           Filter out fluff skills like Microsoft Office, Communication, Teamwork, Leadership, Detail-oriented, etc.
           Only include technical skills relevant to software engineering.
        9. If the resume has a Projects section, extract each project with name, description (bullet points), tech_stack, and url (if present).
           If no Projects section exists, set "projects" to an empty array [].
        10. Each education entry must include "entry_type" classified as "degree", "certification", or "bootcamp".
        11. Extract links: GitHub, LinkedIn, portfolio URLs, or personal website URLs into the "links" array.
            If none found, set "links" to an empty array [].

        Here is the resume text to convert:
        ---RESUME START---
        {raw_text}
        ---RESUME END---

        Return the JSON object:
        """

        data = self._stream_and_structure(prompt, "Structuring Resume")

        # Fallback: if LLM returns skills as a flat list, wrap it
        if isinstance(data.get("skills"), list):
            data["skills"] = {"General": data["skills"]}

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

        # Flatten categorized skills for prompt
        resume_skills = self._flatten_skills(resume.skills)
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

        # Flatten categorized skills for prompt
        flat_skills = self._flatten_skills(resume.skills)

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

        RESUME SKILLS: {flat_skills}
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

    def tailor_resume(
        self,
        resume: ResumeSchema,
        analysis: AnalysisResult,
        job_description: JobDescriptionSchema,
    ) -> TailoredResume:
        """
        Rewrites resume content to align with the job description using SWE best practices.
        """
        print("\n" + "="*60)
        print("STARTING RESUME TAILORING")
        print("="*60)

        # --- Tailor experiences (filter irrelevant ones) ---
        tailored_work_history = []
        for experience in resume.work_history:
            result = self._tailor_experience(experience, analysis, job_description)
            if result is not None:
                tailored_work_history.append(result)

        # Safety check: if ALL experiences were filtered, keep the 2 most recent
        if not tailored_work_history and resume.work_history:
            for experience in resume.work_history[:2]:
                result = self._tailor_experience(experience, analysis, job_description, force_keep=True)
                if result is not None:
                    tailored_work_history.append(result)

        # --- Tailor skills via LLM: filter to job-relevant + integrate gaps ---
        gap_keywords = [g.missing_keyword for g in analysis.gaps if g.suggested_section == "skills"]
        updated_skills = self._tailor_skills(resume.skills, job_description, gap_keywords)

        # --- Filter education to degrees only ---
        tailored_education = [
            edu for edu in resume.education
            if edu.entry_type == "degree"
        ]
        # Fallback: if nothing passes filter, keep all
        if not tailored_education:
            tailored_education = list(resume.education)

        # --- Tailor projects ---
        tailored_projects = []
        for project in resume.projects:
            result = self._tailor_project(project, job_description)
            if result is not None:
                tailored_projects.append(result)

        return TailoredResume(
            tailored_work_history=tailored_work_history,
            updated_skills=updated_skills,
            tailored_projects=tailored_projects,
            tailored_education=tailored_education,
        )

    def _tailor_experience(
        self,
        experience: Experience,
        analysis: AnalysisResult,
        job_description: JobDescriptionSchema,
        force_keep: bool = False,
    ) -> Optional[TailoredExperience]:
        """
        Tailors a single work experience using the LLM with XYZ/STAR format.
        Returns None if the experience is completely irrelevant.
        """
        cache_key_text = f"{experience.model_dump_json()}|{job_description.model_dump_json()}|tailored_exp_v2"
        cache_path = self._get_cache_path("tailored_experience", cache_key_text)
        cached_data = self._load_from_cache(cache_path)

        if cached_data:
            print(f"Loading tailored experience for {experience.company} from cache: {cache_path}")
            if not cached_data.get("relevant", True) and not force_keep:
                return None
            if cached_data.get("tailored_bullet_points"):
                return TailoredExperience(
                    company=experience.company,
                    role=experience.role,
                    duration=experience.duration,
                    tailored_bullet_points=cached_data["tailored_bullet_points"],
                )
            return None

        print(f"Tailoring experience for {experience.company} with LLM...")

        job_keywords = ", ".join(job_description.required_skills[:15])
        job_responsibilities = "\n".join([f"- {r}" for r in job_description.responsibilities[:10]])

        prompt = f"""
        You are an elite SWE resume coach. Rewrite the bullet points for a single work experience
        following strict Software Engineering resume best practices.

        **Role:** {experience.role} at {experience.company} ({experience.duration})

        **Original Bullet Points:**
        {self._format_bullet_points(experience.description)}

        **Target Job Keywords:** {job_keywords}
        **Target Job Responsibilities:**
        {job_responsibilities}

        **Analysis Guidance:**
        - **Semantic Matches:**
        {self._format_semantic_matches(analysis.matches)}
        - **Keyword Gaps to Fill:**
        {self._format_keyword_gaps(analysis.gaps)}

        CRITICAL RULES:
        1. RELEVANCE CHECK: If this experience is completely irrelevant to the target job,
           return {{"relevant": false, "tailored_bullet_points": []}}.
           If partially relevant, keep 1-2 bullets only.
        2. XYZ FORMAT: Every bullet MUST follow "Accomplished [X] as measured by [Y], by doing [Z]".
           Example: "Reduced API latency by 40% (from 200ms to 120ms) by implementing Redis caching layer for frequently accessed endpoints"
        3. MANDATORY METRICS: Every bullet must include %, $, time saved, users impacted, or similar.
           If the original lacks metrics, insert a realistic placeholder in brackets like [reduced by ~30%] or [serving ~5K users].
        4. STRONG ACTION VERBS ONLY: Use verbs like Engineered, Architected, Optimized, Spearheaded,
           Implemented, Automated, Deployed, Designed, Scaled, Migrated. Never use "Helped", "Assisted", "Worked on".
        5. NO FLUFF: No soft skills, no "team player", no "detail-oriented", no "excellent communicator".
        6. KEYWORD INTEGRATION: Naturally weave in job description keywords where truthful.
        7. Do NOT invent entirely new experiences. You may reframe and quantify existing ones.

        **Output Format:**
        Return a JSON object:
        {{
            "relevant": true,
            "tailored_bullet_points": [
                "Engineered a real-time data pipeline processing 10K+ events/sec by leveraging Apache Kafka and Python, reducing data latency by 60%",
                "Architected microservices migration from monolith, improving deployment frequency by 300% [~4x per week] using Docker and Kubernetes"
            ]
        }}

        Return the JSON object now:
        """

        data = self._stream_and_structure(prompt, f"Tailoring {experience.company}")

        # Save to cache
        self._save_to_cache(cache_path, data)

        is_relevant = data.get("relevant", True)
        if not is_relevant and not force_keep:
            print(f"  → Filtered out {experience.company} (irrelevant)")
            return None

        raw_bullets = data.get("tailored_bullet_points", [])
        bullets = [str(b) for b in raw_bullets if str(b).strip()]

        if not bullets:
            return None

        return TailoredExperience(
            company=experience.company,
            role=experience.role,
            duration=experience.duration,
            tailored_bullet_points=bullets,
        )

    def _tailor_project(
        self,
        project: Project,
        job_description: JobDescriptionSchema,
    ) -> Optional[TailoredProject]:
        """
        Tailors a single project using the LLM with XYZ/STAR format.
        Returns None if the project is completely irrelevant.
        """
        cache_key_text = f"{project.model_dump_json()}|{job_description.model_dump_json()}|tailored_proj"
        cache_path = self._get_cache_path("tailored_project", cache_key_text)
        cached_data = self._load_from_cache(cache_path)

        if cached_data:
            print(f"Loading tailored project for {project.name} from cache: {cache_path}")
            if not cached_data.get("relevant", True):
                return None
            if cached_data.get("tailored_bullet_points"):
                return TailoredProject(
                    name=project.name,
                    tailored_bullet_points=cached_data["tailored_bullet_points"],
                    tech_stack=cached_data.get("tech_stack", project.tech_stack),
                    url=project.url,
                )
            return None

        print(f"Tailoring project {project.name} with LLM...")

        job_keywords = ", ".join(job_description.required_skills[:15])

        prompt = f"""
        You are an elite SWE resume coach. Rewrite the bullet points for a personal/side project
        following strict Software Engineering resume best practices.

        **Project:** {project.name}
        **Tech Stack:** {', '.join(project.tech_stack)}
        **URL:** {project.url or 'N/A'}

        **Original Bullet Points:**
        {self._format_bullet_points(project.description)}

        **Target Job Keywords:** {job_keywords}

        CRITICAL RULES:
        1. RELEVANCE CHECK: If this project is completely irrelevant to the target job,
           return {{"relevant": false, "tailored_bullet_points": [], "tech_stack": []}}.
        2. XYZ FORMAT: Every bullet MUST follow "Accomplished [X] as measured by [Y], by doing [Z]".
        3. Highlight the tech stack used — especially technologies that overlap with the target job.
        4. STRONG ACTION VERBS ONLY: Engineered, Architected, Designed, Implemented, Built, Deployed, etc.
        5. Include metrics where possible (users, performance, data volume). Use bracketed placeholders if needed.
        6. Do NOT invent entirely new project details.

        **Output Format:**
        Return a JSON object:
        {{
            "relevant": true,
            "tailored_bullet_points": [
                "Engineered a full-stack e-commerce platform handling [~500 daily transactions] using React, Node.js, and PostgreSQL",
                "Implemented real-time inventory tracking with WebSockets, reducing stock discrepancies by [~25%]"
            ],
            "tech_stack": ["React", "Node.js", "PostgreSQL", "WebSockets"]
        }}

        Return the JSON object now:
        """

        data = self._stream_and_structure(prompt, f"Tailoring Project {project.name}")

        # Save to cache
        self._save_to_cache(cache_path, data)

        if not data.get("relevant", True):
            print(f"  → Filtered out project {project.name} (irrelevant)")
            return None

        raw_bullets = data.get("tailored_bullet_points", [])
        bullets = [str(b) for b in raw_bullets if str(b).strip()]

        if not bullets:
            return None

        return TailoredProject(
            name=project.name,
            tailored_bullet_points=bullets,
            tech_stack=data.get("tech_stack", project.tech_stack),
            url=project.url,
        )

    def _tailor_skills(
        self,
        skills: dict,
        job_description: JobDescriptionSchema,
        gap_keywords: List[str],
    ) -> dict:
        """
        Uses LLM to curate skills to only those relevant to the target job,
        integrating gap keywords into appropriate categories.
        """
        cache_key_text = f"{json.dumps(skills)}|{job_description.model_dump_json()}|{gap_keywords}|tailored_skills"
        cache_path = self._get_cache_path("tailored_skills", cache_key_text)
        cached_data = self._load_from_cache(cache_path)

        if cached_data is not None:
            print(f"Loading tailored skills from cache: {cache_path}")
            if isinstance(cached_data, dict) and cached_data:
                return cached_data
            return skills

        print("Tailoring skills with LLM...")

        prompt = f"""
        You are an elite SWE resume coach. Curate the candidate's skills section to be laser-focused
        on the target job. Remove anything irrelevant and integrate missing keywords.

        **Candidate's Current Skills (by category):**
        {json.dumps(skills, indent=2)}

        **Gap Keywords to Integrate (add these to the appropriate category):**
        {gap_keywords}

        **Target Job Required Skills:** {job_description.required_skills}
        **Target Job Responsibilities:** {', '.join(job_description.responsibilities[:8])}

        CRITICAL RULES:
        1. ONLY keep skills that are relevant to the target job or closely related.
           Remove skills that have no connection to the job requirements.
        2. Integrate the gap keywords into the most appropriate existing category.
        3. Keep categories clean: "Languages", "Frameworks", "Tools", "Cloud/DevOps", "Databases", etc.
           You may rename or merge categories if it makes sense. Remove empty categories.
        4. Order skills within each category by relevance to the job (most relevant first).
        5. Do NOT invent skills the candidate doesn't have (except for the provided gap keywords).
        6. Aim for a focused, specialized look — not a kitchen-sink dump.

        Return a JSON object where keys are category names and values are arrays of skills:
        {{
            "Languages": ["Python", "TypeScript", "SQL"],
            "Frameworks": ["React", "Django"],
            "Tools & Cloud": ["Docker", "AWS", "Terraform", "Git"]
        }}

        Return the JSON object now:
        """

        data = self._stream_and_structure(prompt, "Tailoring Skills")

        # Validate we got a non-empty dict back
        if isinstance(data, dict) and data:
            self._save_to_cache(cache_path, data)
            return data

        # Fallback: return original skills unchanged
        return skills

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

        # Flatten skills for prompt
        flat_skills = self._flatten_skills(resume.skills)

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
        CANDIDATE SKILLS: {flat_skills}
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
    brain = ResumeBrain()
    print(f"Brain initialized with model={brain.model_name}")
