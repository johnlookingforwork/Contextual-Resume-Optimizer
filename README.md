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
- **LLM Orchestration:** LangChain / LlamaIndex
- **Validation:** Pydantic (Strict data typing)
- **Frontend:** Streamlit

## 📈 Evaluation Metrics

To validate the system's effectiveness, the project measures:

- **Cosine Similarity:** Pre- and post-tailoring comparison.
- **Prompt Faithfulness:** Ensuring no "hallucinated" skills are added.

## ✅ Project Impact

While the practical application assists candidates in navigating modern recruitment pipelines, the underlying research goal is to investigate how Context-Aware Systems can more accurately represent human experience in a machine-readable format without losing nuance or introducing bias.

## 🚀 Local Setup

1. Clone the repo: `git clone https://github.com/johnlookingforwork/Contextual-Resume-Optimizer.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `streamlit run app.py`# 🚀 Getting Started

### 1. Prerequisites

Ensure you have Python 3.10+ installed on your system.

### 2. Install Ollama (Local LLM Server)

This project uses **Ollama** to handle local inference, ensuring your resume data never leaves your machine.

- **macOS/Windows:** Download the installer from [ollama.com](https://ollama.com/download).
- **Linux:** Run the following command:
  ```bash
  curl -fsSL [https://ollama.com/install.sh](https://ollama.com/install.sh) | sh
  ```

### 3. Model Setup

Once Ollama is installed and running, pull the lightweight model used for this project:

```bash
ollama pull llama3.2:3b
```

### 4. Install Tesseract OCR

This project uses Tesseract for Optical Character Recognition (OCR) to extract text from PDF resumes.

- **macOS:**
  ```bash
  brew install tesseract
  ```

- **Windows:**
  1. Download the Tesseract installer from the [UB-Mannheim repository](https://github.com/UB-Mannheim/tesseract/wiki).
  2. Run the installer and be sure to note the installation path.
  3. Add the Tesseract installation directory (e.g., `C:\Program Files\Tesseract-OCR`) to your system's `PATH` environment variable.

- **Linux (Debian/Ubuntu):**
  ```bash
  sudo apt update
  sudo apt install tesseract-ocr
  ```
