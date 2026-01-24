# 🏥 NeoMed AI – Healthcare Document Summarization & Clinical Insights

NeoMed AI is a **full-stack healthcare AI application** that accepts unstructured patient data (text or medical documents) and generates a **clear clinical summary and AI-assisted diagnostic considerations** using Large Language Models (LLMs).

> ⚠️ **Disclaimer**: This system is for **educational and assistive purposes only** and does **not replace professional medical diagnosis**.

---

## 🚀 Features

- 📝 Accepts **clinical text input**
- 📄 Supports **medical documents** (PDF, TXT, Images)
- 🧠 AI-generated **medical summaries**
- 🩺 AI-assisted **clinical considerations (not diagnosis)**
- ⚡ Modern, responsive **medical-grade UI**
- 🔐 Secure backend orchestration of LLMs

---

## 🧠 Architecture Overview

```
User (Browser)
↓
React Frontend (Vite + TypeScript)
↓
FastAPI Backend
↓
Medical LLM (Hugging Face / Gemini)
↓
Structured Summary + Clinical Insights
```


## 🛠 Tech Stack

### Frontend
- React
- TypeScript
- Vite
- Tailwind CSS
- Lucide Icons
- Axios

### Backend
- FastAPI
- Python
- Hugging Face Inference API (MedLLaMA / BioGPT)
- Google Gemini (optional)
- Medical NLP utilities

---

## 📁 Project Structure

```text
Neomed/
├── backend/
│   ├── app.py              # FastAPI entry point
│   ├── summarizer.py       # LLM-based summarization
│   ├── entity_extract.py   # Medical entity extraction
│   ├── smart_parser.py     # File/text parsing
│   └── kq_query.py         # Knowledge queries
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── Dashboard.tsx
│   │   └── LandingPage.tsx
│   └── index.html
│
└── README.md
```

## ⚙️ Environment Variables

Create a `.env` file inside the **backend** folder and add:

```env
HF_API_KEY=your_huggingface_api_key
GEMINI_API_KEY=your_gemini_api_key
```

## ▶️ Running the Project Locally

### 1️⃣ Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```
```bash
cd frontend
npm install
npm run dev
```

Backend runs at:

http://localhost:8000

---

### 2️⃣ Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

http://localhost:5173


### 🔌 API Endpoints

```http
POST /analyze
```

```text
Form Data:
text = Patient clinical notes
```

### 🔐 Safety & Medical Disclaimer

 This application provides **AI-assisted summaries and clinical considerations only**  
and does **not provide medical diagnosis or treatment**.

All outputs must be reviewed by a **qualified healthcare professional**.



🔌 API Endpoints
Analyze Medical Text

POST /analyze

Form Data:

text: Patient clinical notes
## Safety & Medical Disclaimer

⚠️ This application provides AI-assisted summaries and clinical considerations only
and does not provide medical diagnosis or treatment.

All outputs must be reviewed by a qualified healthcare professional.

