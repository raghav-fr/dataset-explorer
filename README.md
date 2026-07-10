# 📊 AI Dataset Explorer

<div align="center">

# Explore, Analyze and Chat with Your Data Using AI

An intelligent dataset analysis platform built with **React**, **FastAPI**, **Gemini AI**, and **Qdrant** that automatically cleans datasets, performs Exploratory Data Analysis (EDA), generates AI-powered insights, and enables Retrieval-Augmented Generation (RAG) based conversations with your uploaded data.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi)
![React](https://img.shields.io/badge/React-Frontend-61DAFB?logo=react)
![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-v4-38B2AC?logo=tailwindcss)
![Gemini AI](https://img.shields.io/badge/Gemini-AI-blueviolet)
![Qdrant](https://img.shields.io/badge/Qdrant-VectorDB-red)

</div>

---

# 📖 Overview

AI Dataset Explorer is a full-stack intelligent data analysis platform that simplifies the process of understanding datasets through automation and Artificial Intelligence.

Users can upload CSV datasets, automatically clean and preprocess them, generate comprehensive exploratory data analysis (EDA), visualize statistical patterns, receive AI-generated insights for every chart, and interact with their data through a conversational interface powered by Retrieval-Augmented Generation (RAG).

Instead of manually writing analysis code, users receive an interactive dashboard containing descriptive statistics, missing value analysis, feature distributions, correlations, outlier detection, AI explanations, and natural language querying capabilities.

The project combines traditional data science with modern Large Language Models to create an intelligent analytics assistant.

---

# ✨ Features

* 📂 Upload CSV datasets
* 🧹 Automatic dataset preprocessing
* 🧠 Intelligent missing value detection
* 📊 Automatic Exploratory Data Analysis
* 📈 Interactive visualizations
* 📉 Correlation heatmaps
* 📦 Distribution analysis
* 🔥 Outlier detection
* 📋 Descriptive statistics
* 🤖 Gemini AI generated insights
* 🧠 AI explanation for every visualization
* 🔎 Automatic feature analysis
* 🗂 Dataset indexing using Qdrant
* 💬 RAG-based conversational chat
* ⚡ FastAPI backend
* 🎨 Modern React + Tailwind interface
* 🚀 High-performance architecture

---

# 🛠 Tech Stack

| Technology          | Purpose             |
| ------------------- | ------------------- |
| React               | Frontend            |
| Tailwind CSS        | UI Styling          |
| FastAPI             | Backend API         |
| Python              | Backend Development |
| Pandas              | Data Processing     |
| NumPy               | Numerical Computing |
| Plotly              | Interactive Charts  |
| Matplotlib          | Visualizations      |
| Seaborn             | Statistical Graphs  |
| Gemini AI           | AI Insights         |
| LangChain           | RAG Pipeline        |
| Qdrant              | Vector Database     |
| Sentence Embeddings | Semantic Search     |

---

# 🏗 System Architecture

```text
                    User
                      │
                      ▼
               React Frontend
                      │
                      ▼
                FastAPI Backend
                      │
      ┌───────────────┼────────────────┐
      │               │                │
      ▼               ▼                ▼
 Data Cleaning   Auto EDA Engine   AI Insight Engine
      │               │                │
      └───────────────┼────────────────┘
                      ▼
            Embedding Generation
                      │
                      ▼
                Qdrant Vector DB
                      │
                      ▼
               Gemini RAG Chat
```

---

# 🚀 Workflow

```text
Upload Dataset
        │
        ▼
Dataset Cleaning
        │
        ▼
Automatic EDA
        │
        ▼
Generate Charts
        │
        ▼
Gemini AI Insights
        │
        ▼
Embedding Generation
        │
        ▼
Qdrant Indexing
        │
        ▼
Conversational RAG Chat
```

---

# 📂 Project Structure

```text
dataset-explorer/

├── frontend/
│   ├── src/
│   ├── public/
│   └── components/
│
├── backend/
│   ├── app/
│   ├── api/
│   ├── services/
│   ├── models/
│   ├── utils/
│   └── main.py
│
├── uploads/
├── vector_db/
├── requirements.txt
├── package.json
└── README.md
```

---

# 🧠 AI Capabilities

The application leverages Google's Gemini model to generate intelligent explanations for every visualization and statistical result.

AI capabilities include:

* Automatic chart interpretation
* Statistical reasoning
* Trend analysis
* Pattern discovery
* Feature importance explanation
* Data quality assessment
* Correlation interpretation
* Natural language dataset exploration

---

# 📊 Automatic Exploratory Data Analysis

The system automatically performs:

* Dataset overview
* Missing value analysis
* Duplicate detection
* Constant feature detection
* High-cardinality feature detection
* Numerical feature analysis
* Categorical feature analysis
* Correlation matrix
* Distribution plots
* Box plots
* Histograms
* Pairwise analysis
* Outlier detection
* Target feature analysis (if available)

---

# 💬 Retrieval-Augmented Generation (RAG)

After analysis, every dataset is converted into semantic embeddings and indexed using **Qdrant**.

Users can ask questions such as:

* Which feature has the strongest correlation?
* What are the missing values?
* Explain the outliers.
* Which category appears most frequently?
* Summarize this dataset.
* What insights can be drawn from the visualizations?

The chatbot retrieves the most relevant context before generating an AI response, ensuring grounded and dataset-specific answers.

---

# 🚀 Getting Started

## Prerequisites

Before running the project, install:

* Python 3.11+
* Node.js
* npm
* Git

---

## Clone Repository

```bash
git clone https://github.com/raghav-fr/dataset-explorer.git
```

Navigate into the project

```bash
cd dataset-explorer
```

---

## Backend Setup

Create virtual environment

```bash
python -m venv venv
```

Activate environment

### Windows

```bash
venv\Scripts\activate
```

### Linux / macOS

```bash
source venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Start backend

```bash
uvicorn app.main:app --reload
```

---

## Frontend Setup

Navigate to frontend

```bash
cd frontend
```

Install dependencies

```bash
npm install
```

Run React application

```bash
npm run dev
```

---

# 📦 Main Technologies

* React
* Tailwind CSS
* FastAPI
* Python
* Pandas
* NumPy
* Plotly
* Matplotlib
* Seaborn
* LangChain
* Gemini AI
* Qdrant
* Sentence Embeddings

---

# 🌟 Highlights

* AI-Powered Data Analysis
* Automatic EDA
* Interactive Dashboard
* AI Insights
* Dataset Chatbot
* Retrieval-Augmented Generation
* Vector Database Integration
* Modern Responsive Interface
* Modular Architecture
* Scalable Backend

---

# 🚀 Future Enhancements

* PDF report generation
* Excel and JSON support
* Dashboard export
* User authentication
* Project management
* Dataset versioning
* Team collaboration
* Multiple LLM support
* Real-time analytics
* Cloud deployment
* AutoML integration
* Predictive analytics

---

# 🤝 Contributing

Contributions are welcome.

1. Fork the repository.

2. Create a feature branch.

```bash
git checkout -b feature-name
```

3. Commit your changes.

```bash
git commit -m "Add new feature"
```

4. Push the branch.

```bash
git push origin feature-name
```

5. Open a Pull Request.

---

# 👨‍💻 Author

**Raghav**

GitHub: https://github.com/raghav-fr

---

# 📄 License

This project is licensed under the **MIT License**.

You are free to use, modify, and distribute this project under the terms of the license.

---

# ⭐ Support

If you found this project useful, consider giving it a ⭐ on GitHub.

Your support helps improve the project and motivates future development.

---

<div align="center">

### Built with ❤️ using React, FastAPI, Gemini AI & Qdrant

**Turning Raw Data into Intelligent Insights 🚀**

</div>
