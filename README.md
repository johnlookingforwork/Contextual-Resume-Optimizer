# Contextual-Resume-Optimizer

This app helps job applicants tailor their resume to a specific job description using NLP and RAG.

## 📌 Project Overview

A NLP-driven pipeline designed to bridge the semantic gap between a candidate's resume and a professional job description. This project utilizes Retrieval-Augmented Generation (RAG) and Large Language Models (LLMs) to perform context-aware resume tailoring, ensuring alignment with specific industry taxonomies. The objective is to optimize the information exchange between job seekers and automated screening systems by maximizing semantic relevance.

## 🔬 Research Goals & Motivation

The primary objective is to investigate how LLMs can be used to improve the accuracy of recruitment systems while maintaining high levels of **explainability (XAI)**.

- **Key Challenge:** Moving beyond keyword matching to semantic alignment (e.g., recognizing that "Led a team of 5" maps to "People Management" requirements).
- **Social Impact:** Reducing bias by implementing a modular "De-biasing Layer" that focuses on skill-based metrics rather than demographic indicators.

## 🏗️ System Architecture

The system is built on a modular microservices architecture:

1. **Extraction Engine:** Utilizes Python-based OCR to digitize PDF inputs into structured JSON.
2. **Contextual Analysis:** Employs RAG to retrieve relevant professional experience from the user's history that specifically addresses the job description.
3. **Verification Layer:** A logic-based check to ensure generated content remains grounded in the user's original facts.

## 🛠️ Technical Stack

- **Language:** Python
- **LLM Providers:** OpenAI (GPT-4o, primary) / Ollama (local/free fallback)
- **LLM Orchestration:** LangChain / LlamaIndex
- **Validation:** Pydantic (Strict data typing)
- **PDF Generation:** ReportLab (ATS-friendly output)
- **Frontend:** Streamlit

## 📈 Evaluation Metrics

To validate the system's effectiveness, the project measures:

- **Cosine Similarity:** Pre- and post-tailoring comparison.
- **Prompt Faithfulness:** Ensuring no "hallucinated" skills are added.

## ✅ Project Impact

While the practical application assists candidates in navigating modern recruitment pipelines, the underlying research goal is to investigate how Context-Aware Systems can more accurately represent human experience in a machine-readable format without losing nuance or introducing bias.

# 🚀 Getting Started

### 1. Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Python 3.10+**
- **Ollama:** Download and install from [ollama.com](https://ollama.com/download).
- **Tesseract OCR:**
    - **macOS:** `brew install tesseract`
    - **Windows:** Follow the instructions on the [Tesseract Wiki](https://github.com/UB-Mannheim/tesseract/wiki).
    - **Linux (Debian/Ubuntu):** `sudo apt update && sudo apt install tesseract-ocr`

### 2. Setup & Installation

Follow these steps to set up your project environment:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/Contextual-Resume-Optimizer.git
    cd Contextual-Resume-Optimizer
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # Create a virtual environment named 'venv'
    python3 -m venv venv

    # Activate the environment
    source venv/bin/activate
    # On Windows, use: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    # Ensure you are inside the activated virtual environment
    pip install -r requirements.txt
    ```

### 3. LLM Provider Setup

The app supports two LLM providers. Choose one (or both):

#### Option A: OpenAI (Recommended)

**For the web app (Streamlit):** Create `.streamlit/secrets.toml` in the project root:
```toml
[openai]
api_key = "sk-your-actual-key-here"
```
This file is gitignored. On Streamlit Community Cloud, add the same key via the Secrets UI in app settings.

**For the CLI:** Set the `OPENAI_API_KEY` environment variable:
```bash
export OPENAI_API_KEY="sk-your-actual-key-here"
python main.py
```

#### Option B: Ollama (Local / Free)

Install Ollama from [ollama.com](https://ollama.com/download), then pull the model:
```bash
ollama pull llama3.2:3b
```
The app falls back to Ollama automatically when no OpenAI key is configured.

### 4. Run the Web App (Streamlit)
Launch the Streamlit UI to upload a resume, paste a job description, and get a tailored resume + cover letter:
```bash
streamlit run app.py
```

### 5. Run the CLI Pipeline
Alternatively, run the full pipeline from the command line:
```bash
python main.py
```

### 6. Generate ATS-Friendly PDF (CLI)
After running the CLI pipeline, generate a PDF resume ready for job applications:
```bash
python generator.py
```
The PDF will be saved to `output/tailored_resume.pdf`.

