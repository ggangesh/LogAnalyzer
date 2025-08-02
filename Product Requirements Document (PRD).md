# 📄 Product Requirements Document (PRD) – LogSage AI (Local Deployment)

## 1. Overview

- **Product Name**: LogSage AI  
- **Version**: MVP (v1, Local-Only)  
- **Description**:  
  LogSage AI is a local-first, AI-powered log analysis tool that ingests logs from flat files, parses them, and provides actionable insights using a Retrieval-Augmented Generation (RAG) pipeline and GPT-style models. It is designed for privacy-sensitive environments, entirely self-hosted with no cloud dependencies.

---

## 2. Goals & Objectives

- Enable fast log ingestion and parsing from uploaded files  
- Use AI to detect anomalies and generate summaries  
- Support natural language Q&A over logs via a local RAG pipeline  
- Provide UI for browsing logs, summaries, and queries  
- Fully functional offline (when OpenAI is not used)  

---

## 3. Target Users

- Site Reliability Engineers (SREs)  
- DevOps Engineers  
- Backend Developers  
- IT Ops / Support Teams  
- QA/Automation Engineers  

---

## 4. Deployment Type

- Local, on-prem installation  
- Linux or containerized environment  
- Optional GPU support for local LLMs  

---

## 5. Features

### ✅ MVP Features

- Log Upload (UI + REST API)  
- Log Parsing (regex, structured)  
- Time-Based Filtering (1h, 24h, custom)  
- Anomaly Detection (latency spikes, errors)  
- Natural Language Questions (e.g., “Why 500 errors yesterday?”)  
- Daily/weekly summaries  
- Downloadable reports (PDF/JSON)  

### 🤖 AI Features

- GPT-4/4o integration (optional if online)  
- LangChain-based RAG pipeline  
- Embedding + chunk retrieval from vector DB  
- Summarization, root cause hints, Q&A  
- Predefined prompt templates  

### 🔒 Privacy Features

- Entirely local vector and file storage  
- No external cloud logging or telemetry  
- Logs and metadata stay on the machine  

---

## 6. Tech Stack

| Layer            | Technology                              |
|------------------|------------------------------------------|
| Frontend         | Flask (Python web framework with Jinja2 templates) |
| Backend API      | FastAPI (Python)                        |
| Log Parsing      | Regex, JSON, Pandas                     |
| Database         | Sqllite (local)            |
| Vector Storage   | FAISS (on disk) or Qdrant (self-hosted) |
| Embedding Model  | OpenAI (text-embedding-3-small) or all-MiniLM-L6-v2 (offline) |
| LLM Inference    | GPT-4/4o (via API) or LLaMA/Mistral (offline via Ollama / llama.cpp) |
| File Storage     | Local filesystem                        |
| Security         | JWT / Basic Auth                        |

---

## 7. Non-Functional Requirements

- **Latency**: GPT insights returned within 15 seconds  
- **File Size**: Supports logs up to 100 MB/file  
- **Scalability**: Designed for up to 10 GB/day (local disk)  
- **Security**: Logs stored locally 

---

## 8. UI/UX Requirements

### Frontend Architecture
- **Framework**: Flask with Jinja2 templates
- **Styling**: Tailwind CSS for responsive design  
- **JavaScript**: Vanilla JS/AJAX for dynamic interactions
- **Communication**: HTTP requests to FastAPI backend

### UI Components
- **Dashboard**: log volume, error rate, anomaly timeline, frequency
- **Log Viewer**: filter/search logs by time/type/source  
- **AI Query Panel**: chat-style NLP questions with AJAX  
- **Insight Panel**: shows summaries, anomalies, root cause hints  
- **File Upload Panel**: Flask file upload with progress indicators
- **Settings**: model, embedding, and retention configuration  
---

## 10. Success Metrics (KPIs)

- % logs successfully parsed  
- GPT insight response time  
- Anomaly detection precision/recall  
- AI query volume per user  
- % use offline vs cloud GPT  
- User feedback from QA/Beta  

---

## 11. Future Enhancements (Post-MVP)

- Live log stream ingestion (local syslog/UDP)  
- Role-based access control (RBAC)  
- Log correlation across microservices  
- Support for multiple language logs (non-English)  
- Voice-based log querying (Whisper or Vosk)  
- Local UI deployment via Electron or native app  
