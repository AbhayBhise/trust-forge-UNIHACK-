# Unilog Trust Engine: AI Agent Handover Context

Hello! You are picking up development on the **Unilog Trust Engine**, a hackathon project built to solve AI-driven product catalog enrichment at an enterprise scale.

The user will provide the official hackathon problem statement below, but this document contains the architectural context, our strict "Doc-First" philosophy, and your immediate instructions.

---

## 1. The Core Philosophy (Doc-First Approach)
We are explicitly prioritizing **traceability and truth over hallucination.** 
Most LLM pipelines ingest a CSV and blindly guess the missing data. Our system acts as an "Evidence-Based Trust Engine." 
- **Rule 1:** The system must NEVER generate content from unvalidated information.
- **Rule 2:** If evidence (like a manufacturer PDF) cannot be found, the system must gracefully degrade, mark the product as `needs_review` with 0% confidence, and refuse to hallucinate.
- **Rule 3:** Marketing descriptions (Short, Long, Invoice, etc.) must be generated **deterministically** using *only* the extracted, evidence-backed attributes.

## 2. Current Architecture & State
The project takes a raw `Input.csv` (1000 rows of basic SKUs) and enriches it into a massive 252-column `Delivered Output.csv` matching the client's schema.

**Backend (`files/`):**
* **`pipeline.py` (The Brain):** Processes a single product row through a 5-step journey: Identity Resolution -> Evidence Retrieval -> Attribute Extraction (50 attributes) -> Confidence Scoring -> Deterministic Description Generation.
* **`eval.py` & `CompositeProvider`:** Handles evidence retrieval. It aggregates a `PDFEvidenceProvider` (which extracts specs from real PDFs) and mock providers for the demo.
* **`export_mapper.py`:** Takes the processed Python objects and perfectly flattens them into the massive 252-column CSV required by the schema.
* **`server.py`:** A FastAPI web server hosting the UI and providing a `POST /pipeline/process` endpoint for live CSV uploads.
* **`run_batch.py`:** The offline script used to process the 1000-row batch and generate the pre-computed JSON dataset for the dashboard.

**Frontend (`frontend/`):**
* A pure HTML/JS/CSS dashboard providing explainability to the judges. It features a Batch Dashboard, a detailed Product Journey (showing attribute confidence scores), Enterprise QA metrics, and a Live Demo Upload tool.

---

## 3. Official Problem Statement
*[USER: Paste the exact problem statement from the official hackathon site here]*


---

## 4. Your Immediate Instructions (Research Papers)
The user has added two research papers to the root directory:
1. `paper 1.pdf`
2. `paper 2.pdf`

**Your Tasks:**
1. **Read both papers carefully.** Use your file reading/PDF parsing tools to analyze the contents of `paper 1.pdf` and `paper 2.pdf` located in the root directory.
2. **Extract Methodologies:** Identify the most efficient, impactful, and state-of-the-art concepts from these papers regarding data extraction, RAG (Retrieval-Augmented Generation), entity resolution, or AI confidence scoring.
3. **Apply to the Pipeline:** Propose and implement ways to integrate these methodologies into our existing `pipeline.py` or `pdf_evidence_provider.py` architecture to make our solution faster, more accurate, or highly innovative for the judges. Ensure your proposals strictly adhere to our "Doc-First / Anti-Hallucination" philosophy.
