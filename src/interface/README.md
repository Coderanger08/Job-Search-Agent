# 🎨 Streamlit Interface for Bangladesh Job Search Agent

## 📋 Overview

This directory contains the modern, interactive Streamlit interface for the Bangladesh Job Search RAG system. The interface provides a beautiful, user-friendly way to interact with our AI-powered job search agent.

## 🚀 Features

### 💬 Chat Interface
- **Natural Language Queries**: Ask for jobs in plain English
- **Real-time Responses**: Get instant job search results
- **Conversation History**: View your search history
- **Interactive Chat**: Type and get responses like a real conversation

### 🔍 Advanced Search Filters
- **Location Filter**: Search by specific cities or remote work
- **Experience Level**: Filter by entry, mid, senior, or executive level
- **Job Type**: Full-time, part-time, contract, remote, hybrid
- **Salary Range**: Custom or predefined salary ranges
- **Data Sources**: Choose which job sites to search
- **Advanced Filters**: Skills, company names, posting dates

### 📊 Analytics Dashboard
- **Search Statistics**: Total searches, jobs found, success rates
- **Performance Metrics**: Response times, source performance
- **Market Insights**: Top locations, job types, salary distributions
- **Real-time Activity**: Live search activity and user patterns
- **Interactive Charts**: Beautiful visualizations with Plotly

### 💼 Job Display
- **Beautiful Job Cards**: Modern, responsive job listings
- **Rich Information**: Title, company, location, salary, summary
- **Action Buttons**: Save, share, view details, apply directly
- **Source Badges**: See which site each job came from
- **Compact View**: Alternative compact display option

## 🏗️ Architecture

```
src/interface/
├── streamlit_app.py          # Main Streamlit application
├── components/               # Reusable UI components
│   ├── job_card.py          # Job display component
│   ├── search_filters.py    # Search filters component
│   └── analytics_dashboard.py # Analytics dashboard component
└── README.md                # This file
```

## 🛠️ Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Environment Variables**:
   Create a `.env` file with your API keys:
   ```
   GEMINI_API_KEY=your_gemini_api_key
   HUGGINGFACE_API_KEY=your_huggingface_api_key
   ```

## 🚀 Running the Application

### Method 1: Direct Streamlit Run
```bash
streamlit run src/interface/streamlit_app.py
```

### Method 2: From Project Root
```bash
cd "Job search RAG"
streamlit run src/interface/streamlit_app.py
```

### Method 3: With Custom Port
```bash
streamlit run src/interface/streamlit_app.py --server.port 8501
```

## 🎯 Usage Guide

### 1. Starting a Search
- Type your job query in the chat input
- Examples:
  - "Software Engineer jobs in Dhaka"
  - "Remote marketing positions"
  - "Python developer with 3 years experience"
  - "Jobs at Google or Microsoft"

### 2. Using Filters
- Use the sidebar to refine your search
- Set location, experience level, job type
- Adjust salary range and data sources
- Save filter presets for future use

### 3. Viewing Results
- Jobs appear as beautiful cards
- Click "Apply Now" to go directly to the job posting
- Save interesting jobs to your favorites
- Share jobs with others

### 4. Analytics
- Switch to the Analytics tab to see statistics
- View search trends and performance metrics
- Export data as CSV or JSON

## 🎨 Customization

### Styling
The interface uses custom CSS for modern styling. Key style classes:
- `.job-card-container`: Main job card styling
- `.metric-card`: Analytics metric cards
- `.main-header`: Application header
- `.chat-message`: Chat message styling

### Components
Each component is modular and can be customized:
- `JobCard`: Modify job display format
- `SearchFilters`: Add new filter types
- `AnalyticsDashboard`: Add new chart types

## 🔧 Configuration

### Streamlit Configuration
The app uses these Streamlit settings:
- **Page Title**: "Bangladesh Job Search Agent"
- **Page Icon**: 💼
- **Layout**: Wide layout for better job display
- **Sidebar**: Expanded by default

### API Integration
The interface integrates with:
- **RAG Engine**: Main search functionality
- **Query Parser**: Natural language understanding
- **Data Sources**: BDJobs, LinkedIn, Indeed, Web Search

## 📱 Responsive Design

The interface is designed to work on:
- **Desktop**: Full feature set with sidebar
- **Tablet**: Responsive layout with collapsible sidebar
- **Mobile**: Optimized for touch interaction

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**:
   ```bash
   pip install -r requirements.txt
   ```

2. **API Key Issues**:
   - Check your `.env` file
   - Verify API keys are valid
   - Ensure services are enabled

3. **Streamlit Warnings**:
   - Warnings about ScriptRunContext are normal in test mode
   - Ignore when running outside Streamlit context

4. **Chart Display Issues**:
   - Ensure Plotly is installed: `pip install plotly`
   - Check browser compatibility

### Debug Mode
Run with debug information:
```bash
streamlit run src/interface/streamlit_app.py --logger.level debug
```

## 🔮 Future Enhancements

- [ ] **Dark Mode**: Toggle between light and dark themes
- [ ] **Job Alerts**: Email notifications for new jobs
- [ ] **Resume Upload**: Upload resume for better matching
- [ ] **Company Profiles**: Detailed company information
- [ ] **Salary Insights**: Market salary analysis
- [ ] **Mobile App**: Native mobile application
- [ ] **Multi-language**: Support for Bengali language

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review the main project README
3. Check API documentation for external services

---

**🎉 Enjoy your AI-powered job search experience!**
