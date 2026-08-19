# 🔍 DeepLens AI

> **AI Document Intelligence — Turn complex documents, research papers, and web content into clear, actionable insights.**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=flat-square)
![Azure AI](https://img.shields.io/badge/Azure-AI%20Services-0078D4?style=flat-square)
![Gemini](https://img.shields.io/badge/Google-Gemini-4285F4?style=flat-square)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

---

## 📌 Overview

**DeepLens AI** is an AI-powered document intelligence platform designed to transform long and unstructured content into concise, structured, and meaningful insights.

Instead of simply summarizing a document, DeepLens AI analyzes its content and extracts the information that matters most.

It can process:

- 📄 Research papers and technical documents
- 🎓 IEEE and other publicly accessible research papers
- 🌐 Public web pages and articles
- 🐙 Public GitHub profiles and repositories
- 📑 Long PDF documents
- 🖼️ Scanned and multimodal documents
- 📚 Other publicly accessible long-form content

The system combines **Azure AI services** with **Google Gemini as an alternative AI provider**, allowing the application to continue operating even when Azure-based services are unavailable during development.

---

# ✨ Key Features

### 📄 Intelligent Document Analysis

Extract and understand information from long PDF documents and research papers.

### 🔬 Research Paper Analysis

For research papers, DeepLens AI can identify:

- Research Problem
- Abstract
- Methodology
- Key Findings
- Results
- Limitations
- Future Work
- Important Technical Terms

### 🌐 URL Analysis

Analyze publicly accessible URLs and automatically identify their content type.

Supported sources include:

- PDF URLs
- Web articles
- Research paper pages
- IEEE pages with publicly accessible content
- arXiv pages
- GitHub profiles
- GitHub repositories

> DeepLens AI does not bypass authentication, paywalls, or access restrictions.

### 🐙 GitHub Analysis

Analyze publicly accessible GitHub repositories and profiles.

The system can extract information such as:

- Repository name
- Description
- README
- Programming languages
- Topics
- Stars and forks
- Public repositories
- Profile information

### 🤖 AI-Powered Insights

Generate concise and structured insights instead of returning the entire extracted document.

The output can include:

- Executive Summary
- Key Points
- Important Information
- Action Items
- Technical Insights
- Research Findings
- Limitations
- Future Work
- Custom Q&A

### 🔄 Multiple AI Providers

DeepLens AI supports multiple AI providers.

#### Azure Mode

```text
Azure Content Understanding
        ↓
Azure AI Language
        ↓
Azure OpenAI