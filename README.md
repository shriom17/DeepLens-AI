# NoticeSense AI

> Intelligent notice analysis powered by Azure AI and OpenAI

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square)
![Flask](https://img.shields.io/badge/Flask-Latest-green?style=flat-square)
![Azure](https://img.shields.io/badge/Azure-AI%20Services-0078D4?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

## Overview

**NoticeSense AI** is an intelligent document processing platform that automatically extracts, analyzes, and generates insights from notices and announcements. Powered by Azure AI Document Intelligence and OpenAI's language models, it transforms unstructured notice documents into structured, actionable information.

## ✨ Key Features

- **📄 Intelligent Document Extraction** – Automatically extracts structured data from notices (title, type, organization, dates, etc.)
- **🤖 AI-Powered Analysis** – Uses Azure OpenAI to generate summaries, identify action items, and answer questions
- **📊 Text Analytics** – Advanced NLP capabilities for deeper content understanding
- **🎯 Classification** – Automatically classifies notice types (exams, internships, events, fees, holidays, etc.)
- **💾 Data Management** – Process and store notice data with organized file management
- **🖥️ Modern Web Interface** – Clean, responsive UI built with modern HTML/CSS/JavaScript

## 🛠️ Tech Stack

### Backend
- **Python 3.8+** – Core language
- **Flask** – Web framework
- **Azure AI Services** – Document Intelligence & Text Analytics
- **OpenAI API** – Generative AI for content generation
- **python-dotenv** – Environment configuration management

### Frontend
- HTML5 / CSS3 / JavaScript
- Modern responsive design with custom styling

## 📋 Prerequisites

- Python 3.8 or higher
- Azure Account with:
  - Azure AI Document Intelligence resource
  - Azure OpenAI resource
- OpenAI API credentials or Azure OpenAI deployment
- pip (Python package manager)

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/NoticeSnense-AI.git
cd NoticeSnense-AI
```

### 2. Create a Virtual Environment
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirement.txt
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Azure AI Document Intelligence
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://<your-region>.api.cognitive.microsoft.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=<your-key>

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_KEY=<your-key>
AZURE_OPENAI_DEPLOYMENT=<deployment-name>

# Azure Text Analytics
AZURE_TEXT_ANALYTICS_ENDPOINT=https://<your-region>.api.cognitive.microsoft.com/
AZURE_TEXT_ANALYTICS_KEY=<your-key>
```

## 📖 Usage

### Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

### Processing a Notice

1. Open the web interface
2. Upload a notice document (PDF, image, or document format)
3. Click "Analyze" to extract structured data
4. View results including:
   - Extracted fields (title, type, organization, etc.)
   - AI-generated summary
   - Identified action items
   - Custom Q&A interface

## 📁 Project Structure

```
NoticeSnense-AI/
├── app.py                      # Main Flask application
├── requirement.txt             # Python dependencies
├── config/
│   └── notice-schema.json      # Notice field schema definition
├── services/
│   ├── azure_content.py        # Azure Document Intelligence integration
│   ├── generative_ai.py        # Azure OpenAI integration
│   ├── notice_processor.py     # Notice data processing logic
│   └── text_analysis.py        # Text analytics functionality
├── utils/
│   ├── helpers.py              # Utility functions
│   └── prompts.py              # AI prompt templates
├── data/
│   ├── uploads/                # User-uploaded documents
│   └── processed/              # Processed notice data
└── README.md                   # This file
```

## 🔄 How It Works

1. **Document Upload** – User submits a notice document through the web interface
2. **Content Extraction** – Azure Document Intelligence analyzes the document using the pre-built analyzer
3. **Data Processing** – Extracted fields are structured and normalized
4. **AI Analysis** – Azure OpenAI generates summaries, action items, and insights
5. **Display Results** – Results are presented in the web interface

## 📊 Notice Schema

Supported notice fields (defined in `config/notice-schema.json`):

- **Title** – Notice heading
- **NoticeType** – Classification (exam, internship, event, fee, holiday, etc.)
- **Organization** – Issuing organization
- **Date** – Notice publication date
- **Deadline** – Action deadline (if applicable)
- **Content** – Full notice text
- **Contact** – Contact information
- Additional fields as per your schema

## 🔐 Security

- Store sensitive credentials in `.env` file (never commit to version control)
- Use Azure Managed Identity for production deployments
- Implement proper authentication for API endpoints
- Add `.env` to `.gitignore`

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License – see the LICENSE file for details.

## 🆘 Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review Azure AI services documentation

## 🎯 Roadmap

- [ ] Database integration (replace in-memory storage)
- [ ] Batch processing capabilities
- [ ] Advanced filtering and search
- [ ] Export to multiple formats (PDF, Excel, etc.)
- [ ] Multi-language support
- [ ] API documentation (Swagger/OpenAPI)
- [ ] Unit and integration tests

## 📚 Resources

- [Azure AI Document Intelligence Docs](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/)
- [Azure OpenAI Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Azure Text Analytics](https://learn.microsoft.com/en-us/azure/ai-services/language-service/text-analytics/overview)

---

**Made with ❤️ using Azure AI Services**