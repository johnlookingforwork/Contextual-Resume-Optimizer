# Project Roadmap & Validation Criteria

## Phase 1: Data Ingestion & Normalization

**Goal:** Transform unstructured PDFs and visual screenshots into structured, type-safe data.

- **Status:** ✅ Completed
- **Validation Criteria:**
  - [x] **Extraction Accuracy:** PDF text extraction handles multi-column layouts without merging text incorrectly.
  - [x] **Schema Enforcement:** All extracted data must pass Pydantic validation (No missing required fields).
  - [x] **Privacy Check:** `.gitignore` successfully prevents PII (Personally Identifiable Information) from being committed.

## Phase 2: Semantic Alignment (Gap Analysis)

**Goal:** Identify the relationship between candidate skills and job requirements.

- **Status:** 🚧 In Progress

### Phase 2.1: Data Model Design
- **Status:** ✅ Completed
- **Tasks:**
  - [x] Create `SemanticMatch` model for skill/requirement mappings
  - [x] Create `KeywordGap` model for missing keyword analysis
  - [x] Create `AnalysisResult` model to hold all analysis outputs
  - [x] Update models.py with new schemas

### Phase 2.2: Semantic Skill Matcher
- **Status:** ✅ Completed
- **Tasks:**
  - [x] Implement `analyze_semantic_matches()` in ResumeBrain
  - [x] Use LLM to identify semantic connections (e.g., "Team Captain" → "Leadership")
  - [x] Generate match scores and reasoning for each connection
  - [x] Add caching for analysis results

### Phase 2.3: Keyword Gap Analyzer
- **Status:** ✅ Completed
- **Tasks:**
  - [x] Implement `identify_keyword_gaps()` in ResumeBrain
  - [x] Extract keywords from job description that are missing from resume
  - [x] Prioritize gaps by importance (high/medium/low)
  - [x] Suggest which resume sections should incorporate each keyword

### Phase 2.4: Integration & Testing
- **Status:** ✅ Completed
- **Tasks:**
  - [x] Create `analyze_resume()` method that orchestrates all analysis
  - [x] Update main.py to run semantic analysis
  - [x] Display analysis results with formatting
  - [x] Save analysis results to JSON file

### Validation Criteria:
  - [ ] **Semantic Mapping:** The system must recognize "Java" and "C#" as transferable skills for an Object-Oriented Programming role.
  - [ ] **Zero-Hallucination:** The "Missing Skills" list must only include items found in the Job Description, not fabricated ones.
  - [ ] **Inference Speed:** Local LLM response time for analysis must stay under 30 seconds on Intel hardware.

## Phase 3: The Tailoring Engine

**Goal:** Rewrite resume bullet points to optimize for the target Job Description.

- **Status:** 📅 Planned
- **Validation Criteria:**
  - [ ] **Fact Grounding:** Every rewritten bullet point must be traceable back to an original fact in the base resume.
  - [ ] **STAR Method Adherence:** Rewritten bullets must follow the Situation-Task-Action-Result format.
  - [ ] **Similarity Score:** The post-tailored resume should show a >20% increase in Cosine Similarity to the Job Description.

## Phase 3.5: PDF Resume Generation

**Goal:** Convert tailored resume JSON into an ATS-friendly PDF for direct upload to job application portals.

- **Status:** ✅ Completed

### Tasks:
- [x] Select PDF library (`reportlab`) for ATS-compatible text-based output
- [x] Create `generator.py` that merges base resume (name, email, education) with tailored data (work history, skills)
- [x] Generate single-column, text-selectable PDF using standard fonts (Helvetica)
- [x] Output saved to `output/tailored_resume.pdf`

### Validation Criteria:
- [x] **ATS Parsability:** PDF uses real text (not images), standard fonts, and single-column layout for reliable ATS parsing.
- [x] **Data Integrity:** All sections from base resume (contact, education) and tailored resume (skills, work history) are present.
- [x] **Standalone Execution:** `python generator.py` produces a PDF without requiring Ollama or any LLM call.

## Phase 4: UI & Deployment

**Goal:** Provide a usable Streamlit interface with explainable AI reasoning and downloadable outputs.

- **Status:** ✅ Completed

### Tasks:
- [x] Add `CoverLetter` Pydantic model to `models.py`
- [x] Add `extract_resume_text_from_bytes()` to `extractor.py` for in-memory PDF uploads
- [x] Add `generate_cover_letter()` method to `ResumeBrain` in `brain.py`
- [x] Add `generate_resume_pdf_bytes()` and `generate_cover_letter_pdf_bytes()` to `generator.py`
- [x] Create `app.py` Streamlit entry point with sidebar inputs and 4-tab results layout
- [x] Implement `st.status()` progress indicators for each pipeline step
- [x] Implement `st.expander` for explainable AI reasoning on semantic matches and keyword gaps
- [x] Implement `st.session_state` to persist results across Streamlit reruns
- [x] Add PDF download buttons for tailored resume and cover letter

### Validation Criteria:
- [x] **User Experience:** System provides expandable "Reasoning" tooltips for each semantic match and keyword gap (XAI).
- [x] **End-to-End Flow:** Upload PDF, paste job description, click button -> all 4 tabs render correctly.
- [x] **Downloadable Outputs:** Both tailored resume and cover letter are downloadable as PDFs.
- [x] **CLI Backward Compatibility:** Existing `python main.py` and `python generator.py` paths still work.
- [ ] **Reproducibility:** A fresh `pip install` on a separate machine successfully runs the full pipeline.
