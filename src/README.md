# AI Dermatology Assistant

An AI-powered dermatology assistant that helps users understand common skin conditions from **text** and **skin images**. The system combines a **Vision Language Model (Qwen2.5-VL)**, **Retrieval-Augmented Generation (RAG)**, and **LangGraph** to generate evidence-based responses grounded in trusted medical documents.

> **Disclaimer:** This project is designed for educational and research purposes only. It does **not** provide medical diagnoses or replace consultation with qualified healthcare professionals.

---

# Features

- 💬 Ask questions about common skin diseases using natural language.
- 📷 Upload skin images for visual analysis.
- 👁️ Generate image descriptions using Qwen2.5-VL.
- 📚 Retrieve relevant medical knowledge using RAG.
- 🤖 Generate grounded responses using retrieved documents.
- 📖 Return supporting references whenever available.

---

# Technology Stack

| Component | Technology |
|-----------|------------|
| Programming Language | Python 3.12+ |
| Agent Framework | LangGraph |
| LLM Provider | OpenRouter |
| Vision Model | Qwen2.5-VL |
| Embedding Model | nomic-embed-text-v1 |
| Vector Database | ChromaDB |

---

# System Architecture

```text
                    User
                      │
          ┌───────────┴───────────┐
          │                       │
        Text                   Image
          │                       │
          └───────────┬───────────┘
                      │
              Qwen2.5-VL
          (Image Description)
                      │
            Combined User Context
                      │
               LangGraph Agent
                      │
                 RAG Pipeline
                      │
                 ChromaDB
                      │
                OpenRouter LLM
                      │
      Evidence-based Response + Citation
```

---

# Project Structure

```text
.
├── app/                # Application entrypoint
├── graph/              # LangGraph workflow
├── nodes/              # Graph nodes
├── prompts/            # Prompt templates
├── rag/                # Retrieval pipeline
├── data/               # Knowledge base
├── docs/
│   ├── architecture.md
│   └── roadmap.md
├── requirements.txt
└── README.md
```

---

# Development Roadmap

| Task | Description |
|------|-------------|
| Task 01 | Build the medical knowledge base |
| Task 02 | Develop the Vision Pipeline |
| Task 03 | Build the Context Builder |
| Task 04 | Implement the RAG pipeline |
| Task 05 | Design the LangGraph workflow |
| Task 06 | Build the user interface |

---

# Demo Workflow

1. User submits a text question or uploads a skin image.
2. Qwen2.5-VL converts the image into a structured description.
3. LangGraph combines the image description with the user's question.
4. The RAG pipeline retrieves relevant medical documents from ChromaDB.
5. The LLM generates a response grounded in the retrieved evidence.
6. The system returns the final answer together with supporting references.


# Future Work

- Support additional skin disease datasets.
- Improve retrieval quality with hybrid search.
- Integrate medical guideline updates.
- Support multilingual conversations.
- Add automatic evaluation for RAG responses.

---

# License

This project is intended for research and educational purposes.

The generated responses should **not** be interpreted as medical diagnoses or treatment recommendations.