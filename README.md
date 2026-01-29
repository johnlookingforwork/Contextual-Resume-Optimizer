# Contextual-Resume-Optimizer
This app helps job applicants tailor their resume to a specific job description using NLP and RAG. 

## 📌 Project Overview
A NLP-driven pipeline designed to bridge the semantic gap between a candidate's resume and a professional job description. This project utilizes Retrieval-Augmented Generation (RAG) and Large Language Models (LLMs) to perform context-aware resume tailoring, ensuring alignment with specific industry taxonomies.

## 🔬 Research Goals & Motivation
The primary objective is to investigate how LLMs can be used to improve the accuracy of recruitment systems while maintaining high levels of **explainability (XAI)**. 
* **Key Challenge:** Moving beyond keyword matching to semantic alignment (e.g., recognizing that "Led a team of 5" maps to "People Management" requirements).
* **Social Impact:** Reducing bias by implementing a modular "De-biasing Layer" that focuses on skill-based metrics rather than demographic indicators.

## 🏗️ System Architecture
The system is built on a modular microservices architecture:
1. **Extraction Engine:** Utilizes Python-based OCR to digitize PDF inputs into structured JSON.
2. **Contextual Analysis:** Employs RAG to retrieve relevant professional experience from the user's history that specifically addresses the job description.
3. **Verification Layer:** A logic-based check to ensure generated content remains grounded in the user's original facts.

## 🛠️ Technical Stack
* **Language:** Python
* **LLM Orchestration:** LangChain / LlamaIndex
* **Validation:** Pydantic (Strict data typing)
* **Frontend:** Streamlit

## 📈 Evaluation Metrics
To validate the system's effectiveness, the project measures:
* **Cosine Similarity:** Pre- and post-tailoring comparison.
* **Prompt Faithfulness:** Ensuring no "hallucinated" skills are added.

## 🚀 Local Setup
1. Clone the repo: `git clone https://github.com/johnlookingforwork/Contextual-Resume-Optimizer.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `streamlit run app.py`
