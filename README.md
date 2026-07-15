# Finpro JobApp

**An AI-powered career navigator application automation platform that streamlines job chatbot, smart search, resume processing (cv analysis)  while giving recommendations for career growth, interview simulation and market demands through intelligent workflow orchestration.**

![Status](https://img.shields.io/badge/status-active-brightgreen)
![Version](https://img.shields.io/badge/version-1.0-blue)
![License](https://img.shields.io/badge/license-Educational%2FPortfolio-blue)

![Frontend](https://img.shields.io/badge/frontend-Streamlit-red)
![Backend](https://img.shields.io/badge/backend-n8n-orange)
![Database](https://img.shields.io/badge/database-Aiven%20MySQL-316192)
![VectorDB](https://img.shields.io/badge/vector%20DB-Qdrant-DC244C)

![AI](https://img.shields.io/badge/AI-OpenAI%20GPT-purple)
![Embeddings](https://img.shields.io/badge/Embeddings-OpenAI-success)
![RAG](https://img.shields.io/badge/RAG-Qdrant-blueviolet)
![Text--to--SQL](https://img.shields.io/badge/Text--to--SQL-LLM-yellowgreen)

![Architecture](https://img.shields.io/badge/Architecture-Microservices-informational)

![Python](https://img.shields.io/badge/Python-3.12-3776AB)
![OpenAI](https://img.shields.io/badge/OpenAI-API-412991)

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Workflow](#workflow)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Installation](#️-installation)
- [Folder Structure](#️-folder-structure)
- [Usage](#-usage)
- [Real-World Problem](#real-world-problem)
- [Security Considerations](#security-considerations)
- [Future Improvements](#future-improvements)
- [Limitations](#limitations)
- [Why This Project?](#why-this-project)
- [License](#license)

---

## Overview

As a freshgraduate, searching for a job and understanding the roadmap for future career chances are tedius work. We made this app with the freshgraduates in mind as we made a chatbot so that the freshers can ask questions about jobs, smart search, roadmap of how they could advanced their career, interview simulation to help them ace their interview and market demands.

**Finpro JobApp** automates this workflow by combining AI, document processing, and workflow orchestration into a single intelligent pipeline.

The platform extracts structured information from resumes, identifies relevant opportunities, give links to a website for career advancement — all with minimal user intervention.

---

## Key Features

- 🧠 AI-powered resume parsing
- 👤 Intelligent candidate profile extraction and career advancement roadmap
- 🔍 Automated job discovery
- 🔄 End-to-end workflow automation using n8n
- 🧩 Modular and extensible architecture

---

## Workflow

```text
Resume Upload
      │
      ▼
Extract Candidate Information
      │
      ▼
Search Relevant Job Advancement
      │
      ▼
Generate Career Pathway
      │
      ▼
Simulate Interview according to their career of choice
      │
      ▼
Resume is not stored anywhere for privacy

```

---

## Technology Stack

| Category | Tools & Services |
|---|---|
| **Dataset** | Kaggle dataset, Self-made learning links dataset |
| **Workflow Automation** | n8n |
| **Artificial Intelligence** | Large Language Models (LLMs), LangChain, OpenAI API |
| **Document Processing** | PDF Parsing, PyPDF2, Resume Information Extraction |
| **Frontend** | Streamlit |
| **Data Processing** | Python, Pandas, Numpy, Jupyter Notebook |
| **Vector Database** | Qdrant |
| **SQL** | Aiven |

---

## Architecture

```text
                        +----------------------+
                        |      Streamlit       |
                        |      Frontend        |
                        +----------+-----------+
                                   |
                                   |
                          REST API / Webhook
                                   |
                        +----------v-----------+
                        |         n8n          |
                        | Workflow Orchestration|
                        +----------+-----------+
                                   |
                         +----------v-----------+
                        |         n8n          |
                        |     Authorization    |
                        +----------+-----------+
                                   |
        -----------------------------------------------------------------
        |                 |                 |                |            |
        |                 |                 |                |            |
   Job Chatbot     Smart Job Search    CV Analysis     AI Interview   Market Demand
       RAG          (Text-to-SQL)    
        |                 |                 |                |            |
        -----------------------------------------------------------------
                                   |
                    +--------------+---------------+
                    |                              |
          +---------v---------+          +---------v---------+
          |    Aiven MySQL    |          |      Qdrant       |
          | Jobs & Learning   |          |  Semantic Search  |
          |    Links          |          |                   |
          +-------------------+          +-------------------+
                    |                              |
                    +--------------+---------------+
                                   |
                           OpenAI GPT APIs
```

---

## ⚙️ Installation

```bash
pip install -r requirements.txt
```

---

## 🗂️ Folder Structure

```text
Finpro-JobApp/
├── dataset/            # Dataset source, data cleaning and preparation, ML model
├── docs/               # Documents
├── models/             # ML model
├── n8n/                # n8n backend files
├── notebooks/          # Data processing, data ingestion, ML model processes
├── pages/              # Streamlit pages
├── app.py              # Main Streamlit page
├── menu.py             # Streamlit sidebar page
├── requirements.txt    # Requirement environments
├── style.css           # Streamlit CSS
├── README.md           # Main project guide
└── utils.py/           # Backend Functions
```

---

## 💻 How to Run

```bash
streamlit run app.py
```

---

## Real-World Problem

### 1. Inefficient Job Search

Traditional job portals rely heavily on keyword matching and predefined filters, making it difficult for users to express complex job preferences.

**Solution**

Natural language search allows users to describe jobs conversationally (e.g., "Find remote backend developer jobs in Indonesia"), which are translated into optimized Vector database for accurate semantic retrieval.

---

### 2. Lack of Personalized Career Guidance

Many candidates are uncertain whether their current skills align with industry demands.

**Solution**

The system analyzes uploaded CVs, compares extracted skills with current job requirements, identifies skill gaps, and generates personalized career roadmaps with recommendation scores.

---

### 3. Limited Interview Preparation

Many applicants have limited access to realistic interview practice and constructive feedback.

**Solution**

The AI interview simulator generates role-specific interview questions, evaluates responses, and provides actionable feedback on communication, technical knowledge, and overall performance.

---

### 4. Limited Visibility into Job Market Trends

Job seekers often lack insights into hiring demand, salary trends, and emerging skills.

**Solution**

SQL-powered analytics provide dashboards highlighting in-demand skills, hiring companies, salary distributions, and job market trends to support informed career decisions.

---

### 5. Fragmented Career Development Tools

Users frequently switch between multiple websites for resume analysis, job searching, interview preparation, and market research.

**Solution**

This platform integrates these capabilities into a single AI-powered workflow, improving usability and reducing friction throughout the job-seeking process.


**Finpro JobApp** automates these repetitive processes while helping candidates submit more targeted applications with tailored resumes.

---

## Security Considerations

The project is designed with security best practices in mind:

- 🔐 Authentication, Authorization and Credentials are managed outside source control
- 🔑 CVs uploaded are not saved for Data Protection
- 🛡️ Restrict Qdrant access using API keys and datas are stored without exposing raw personal documents
- ✅ Uploaded documents are validated before processing

---

## Future Improvements

- [ ] Resume Optimization Generator
- [ ] Personalized Job Alerts
- [ ] Cover letter generation
- [ ] Recruiter Matching
- [ ] Multi-language Support
- [ ] Real-time Job Market Analytics
- [ ] SQL Validator and Read-only databases
- [ ] Recruiter Dashboard

---

## Limitations

While the platform demonstrates an end-to-end AI-powered career assistant, several limitations remain:

- **LLM Hallucinations** – AI-generated recommendations, interview feedback, and career advice may contain inaccuracies and should be treated as guidance rather than professional advice.

- **Text-to-SQL Reliability** – Complex or ambiguous natural language queries may produce incorrect SQL statements, data injection or unauthorized SQL query prompt. A validation layer is required before execution.

- **Recommendation Accuracy** – Career match percentages are heuristic-based and depend on the quality of extracted skills and available job market data.

- **Dataset Dependency** – Job recommendations and market analytics are only as accurate as the underlying job database.

- **Limited Resume Parsing** – Unstructured or poorly formatted CVs may result in incomplete skill extraction.

- **Embedding Quality** – Semantic search performance depends on the selected embedding model and vector indexing strategy.

- **No Real-Time Market Data** – Current analytics rely on stored datasets rather than live recruitment platforms.

- **Scalability** – The current architecture targets prototypes and small-to-medium workloads. High-traffic deployments would require load balancing, caching, asynchronous processing, and distributed services.

- **Privacy Considerations** – Uploaded resumes contain sensitive personal information and require secure storage, encryption, and controlled access.

- **Language Support** – The current implementation primarily targets English-language resumes and job descriptions.

---

## Why This Project?

This project demonstrates the integration of modern AI technologies with structured databases to solve practical recruitment and career development challenges. By combining conversational AI, Text-to-SQL, semantic search, and analytics within a unified platform, it enables users to:

- Search jobs using LLM.
- Receive personalized career recommendations.
- Identify skill gaps and learning pathways.
- Practice interviews with AI-generated feedback.
- Make data-driven career decisions using labor market analytics.

The result is a comprehensive AI-powered career assistant that streamlines the job search process, enhances career planning, and improves job readiness for individuals at different stages of their professional journey.

---

## License

This project is intended for **educational and portfolio purposes**. Please ensure compliance with the terms of service of any third-party APIs or job platforms used within the workflow.
