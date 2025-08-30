# 🚀 Bangladesh Job Search Agent

**AI-Powered Job Search with Real-time Data from Multiple Sources**

A sophisticated job search application built with Advanced RAG (Retrieval Augmented Generation) technology, designed specifically for the Bangladesh job market. This system combines multiple data sources, intelligent query processing, and a beautiful user interface to provide comprehensive job search capabilities.

## 🌟 Features

### 🔍 **Advanced Search Capabilities**
- **Multi-Source Job Search**: BDJobs, LinkedIn, Indeed, and web search integration
- **Intelligent Query Processing**: Natural language understanding with advanced query classification
- **Real-time Data Retrieval**: Live job listings from multiple sources
- **Hybrid Data Approach**: API + Web scraping + LLM-powered extraction

### 🤖 **AI-Powered Intelligence**
- **RAG Architecture**: Retrieval Augmented Generation for accurate responses
- **Query Understanding**: Advanced NLP for complex job queries
- **Smart Filtering**: Intelligent job matching and relevance scoring
- **Conversational Interface**: Natural language job search conversations

### 🎨 **Beautiful User Interface**
- **Modern Streamlit Interface**: Clean, responsive design
- **Interactive Job Cards**: Rich job information display
- **Advanced Filtering**: Location, salary, experience, job type filters
- **Analytics Dashboard**: Search insights and performance metrics
- **Real-time Updates**: Live search results and notifications

### 🏗️ **Production-Ready Architecture**
- **Modular Design**: Scalable, maintainable codebase
- **Configuration Management**: Centralized settings and API key management
- **Comprehensive Logging**: Detailed system monitoring and debugging
- **Health Monitoring**: Real-time system health checks
- **Error Handling**: Robust error management and recovery

## 🏆 **System Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                    BANGLADESH JOB SEARCH AGENT              │
├─────────────────────────────────────────────────────────────┤
│  🎨 User Interface Layer                                    │
│  ├── Streamlit Web App                                      │
│  ├── Interactive Job Cards                                  │
│  ├── Search Filters & Analytics                             │
│  └── Real-time Notifications                                │
├─────────────────────────────────────────────────────────────┤
│  🧠 AI Processing Layer                                     │
│  ├── RAG Engine (Retrieval Augmented Generation)            │
│  ├── Query Parser & Classifier                              │
│  ├── LLM Pipeline (Gemini, HuggingFace, Ollama)            │
│  └── Intelligent Source Router                              │
├─────────────────────────────────────────────────────────────┤
│  🔗 Data Source Layer                                       │
│  ├── API Scraper Manager                                    │
│  ├── Web Search Integration                                 │
│  ├── Custom Scrapers (BDJobs, etc.)                         │
│  └── Data Validation & Enrichment                           │
├─────────────────────────────────────────────────────────────┤
│  ⚙️ Infrastructure Layer                                    │
│  ├── Configuration Management                               │
│  ├── Logging & Monitoring                                   │
│  ├── Health Checks & Analytics                              │
│  └── Error Handling & Recovery                              │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.8 or higher
- Internet connection
- API keys (Gemini, HuggingFace)

### **Installation**

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd job-search-rag
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API keys**
   Create a `.env` file in the project root:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   HUGGINGFACE_API_KEY=your_huggingface_api_key_here
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

5. **Access the interface**
   Open your browser and go to: `http://localhost:8501`

## 📋 **Usage Guide**

### **Basic Job Search**
1. **Enter your query** in natural language:
   - "Software Engineer jobs in Dhaka"
   - "Marketing positions with 3+ years experience"
   - "Remote developer jobs"

2. **Apply filters** using the sidebar:
   - Location preferences
   - Salary range
   - Experience level
   - Job type (Full-time, Part-time, etc.)

3. **View results** in the interactive job cards

### **Advanced Features**
- **Save jobs** for later review
- **Share job listings** with others
- **View analytics** and search insights
- **Export results** to CSV format

### **Conversational Search**
- Ask follow-up questions
- Request job comparisons
- Get salary insights
- Find similar positions

## 🔧 **Configuration**

### **Application Settings**
The system uses a centralized configuration management system:

```python
# Configuration files are stored in:
~/.bangladesh_job_search/
├── config.json              # Application settings
├── user_preferences.json    # User preferences
├── api_keys.json           # API key management
└── logs/                   # System logs
```

### **Key Settings**
- **Search Sources**: Configure which job sites to search
- **Performance**: Adjust concurrent searches and timeouts
- **UI Preferences**: Theme, language, default filters
- **API Settings**: Rate limits, fallback options

## 📊 **System Monitoring**

### **Health Checks**
The system continuously monitors:
- **System Resources**: CPU, memory, disk usage
- **API Health**: Response times and availability
- **Application Metrics**: Performance and error rates
- **Network Connectivity**: Internet and service availability

### **Logging**
Comprehensive logging system with:
- **Application Logs**: General system activity
- **Error Logs**: Detailed error tracking
- **Performance Logs**: Response times and metrics
- **Analytics Logs**: User behavior and search patterns

### **Analytics Dashboard**
Real-time insights including:
- Search performance metrics
- Popular job categories
- User interaction patterns
- System health status

## 🛠️ **Development**

### **Project Structure**
```
job-search-rag/
├── main.py                          # Main application entry point
├── requirements.txt                 # Python dependencies
├── README.md                       # This file
├── .env                           # Environment variables
├── src/
│   ├── core/                      # Core system components
│   │   ├── config_manager.py      # Configuration management
│   │   ├── logging_manager.py     # Logging system
│   │   ├── health_monitor.py      # Health monitoring
│   │   ├── system_validator.py    # System validation
│   │   ├── rag_engine.py          # RAG processing engine
│   │   ├── query_parser.py        # Query understanding
│   │   ├── api_scraper_manager.py # API and scraping management
│   │   └── enhanced_llm_pipeline.py # LLM processing
│   ├── interface/                 # User interface
│   │   ├── streamlit_app.py       # Main Streamlit application
│   │   └── components/            # UI components
│   │       ├── job_card.py        # Job display component
│   │       ├── search_filters.py  # Search filter component
│   │       └── analytics_dashboard.py # Analytics component
│   └── scrapers/                  # Custom scrapers
│       └── bdjobs_scraper.py      # BDJobs scraper
└── logs/                          # System logs
```

### **Adding New Features**
1. **New Data Sources**: Extend `api_scraper_manager.py`
2. **UI Components**: Add to `src/interface/components/`
3. **LLM Models**: Integrate in `enhanced_llm_pipeline.py`
4. **Configuration**: Update `config_manager.py`

## 🔒 **Security & Privacy**

### **Data Protection**
- **API Key Security**: Encrypted storage and secure transmission
- **User Privacy**: No personal data collection or storage
- **Secure Communication**: HTTPS for all external API calls
- **Input Validation**: Comprehensive input sanitization

### **Rate Limiting**
- **API Protection**: Intelligent rate limiting for external APIs
- **Resource Management**: Memory and CPU usage optimization
- **Error Recovery**: Graceful handling of service failures

## 🚀 **Deployment**

### **Local Development**
```bash
python main.py --debug
```

### **Production Deployment**
```bash
python main.py --port 8501
```

### **Docker Deployment** (Coming Soon)
```bash
docker build -t bangladesh-job-search .
docker run -p 8501:8501 bangladesh-job-search
```

## 📈 **Performance**

### **Optimization Features**
- **Parallel Processing**: Concurrent searches across multiple sources
- **Caching**: Intelligent result caching for faster responses
- **Compression**: Data compression for reduced bandwidth usage
- **Memory Management**: Efficient memory usage and cleanup

### **Scalability**
- **Modular Architecture**: Easy to scale individual components
- **Load Balancing**: Support for multiple instances
- **Database Integration**: Ready for persistent storage
- **API Versioning**: Backward compatibility support

## 🤝 **Contributing**

We welcome contributions! Please see our contributing guidelines:

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Add tests**
5. **Submit a pull request**

### **Development Setup**
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Run linting
flake8 src/
```

## 📞 **Support**

### **Documentation**
- **API Documentation**: Detailed API reference
- **User Guide**: Step-by-step usage instructions
- **Developer Guide**: Technical implementation details
- **Troubleshooting**: Common issues and solutions

### **Contact**
- **Issues**: Report bugs and feature requests
- **Discussions**: Community discussions and Q&A
- **Email**: Support email for urgent issues

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- **Google Gemini**: For providing the primary LLM capabilities
- **Hugging Face**: For transformer models and NLP tools
- **Streamlit**: For the beautiful web interface framework
- **Open Source Community**: For the amazing tools and libraries

---

**Built with ❤️ for the Bangladesh job market**

*Empowering job seekers with AI-powered search technology*
