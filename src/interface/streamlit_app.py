import streamlit as st
import sys
import os
from datetime import datetime
import pandas as pd
import json
from typing import List, Dict, Any

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.core.rag_engine import RAGEngine
from src.core.query_parser import QueryParser
from config import Config

# Page configuration
st.set_page_config(
    page_title="Bangladesh Job Search Agent",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .job-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    
    .job-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        max-width: 80%;
    }
    
    .user-message {
        background: #667eea;
        color: white;
        margin-left: auto;
    }
    
    .bot-message {
        background: #f8f9fa;
        border: 1px solid #e0e0e0;
    }
    
    .stats-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
    }
    
    .filter-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class JobSearchInterface:
    def __init__(self):
        self.rag_engine = None
        self.query_parser = None
        self.initialize_components()
        
    def initialize_components(self):
        """Initialize RAG engine and query parser"""
        try:
            self.rag_engine = RAGEngine()
            self.query_parser = QueryParser()
            st.success("✅ Job Search Agent initialized successfully!")
        except Exception as e:
            st.error(f"❌ Failed to initialize: {e}")
            st.info("Please check your API keys in the .env file")
    
    def display_header(self):
        """Display the main header"""
        st.markdown("""
        <div class="main-header">
            <h1>💼 Bangladesh Job Search Agent</h1>
            <p>AI-Powered Job Search with Real-time Data from Multiple Sources</p>
        </div>
        """, unsafe_allow_html=True)
    
    def display_sidebar(self):
        """Display sidebar with filters and settings"""
        with st.sidebar:
            st.header("🔍 Search Filters")
            
            # Location filter
            st.subheader("📍 Location")
            locations = ["All Locations", "Dhaka", "Chittagong", "Sylhet", "Rajshahi", "Khulna", "Barisal", "Rangpur", "Mymensingh"]
            selected_location = st.selectbox("Select Location", locations)
            
            # Experience level
            st.subheader("👨‍💼 Experience Level")
            experience_levels = ["Any", "Entry Level", "Mid Level", "Senior Level", "Executive"]
            selected_experience = st.selectbox("Select Experience", experience_levels)
            
            # Job type
            st.subheader("💼 Job Type")
            job_types = ["Any", "Full-time", "Part-time", "Contract", "Remote", "Hybrid"]
            selected_job_type = st.selectbox("Select Job Type", job_types)
            
            # Salary range
            st.subheader("💰 Salary Range (BDT)")
            salary_range = st.slider("Monthly Salary", 0, 200000, (0, 200000), 5000)
            
            # Data sources
            st.subheader("🌐 Data Sources")
            sources = {
                "BDJobs": st.checkbox("BDJobs", value=True),
                "LinkedIn": st.checkbox("LinkedIn", value=True),
                "Indeed": st.checkbox("Indeed", value=True),
                "Web Search": st.checkbox("Web Search", value=True)
            }
            
            # Search settings
            st.header("⚙️ Settings")
            max_results = st.slider("Max Results", 5, 50, 20)
            search_timeout = st.slider("Search Timeout (seconds)", 10, 60, 30)
            
            # Developer options
            st.header("🔧 Developer Options")
            debug_mode = st.checkbox("Debug Mode", value=False, help="Show detailed logs and metrics")
            show_metrics = st.checkbox("Show Performance Metrics", value=False, help="Display system performance during search")
            
            if debug_mode:
                st.info("🔧 Debug mode enabled - You'll see detailed logs and system information")
            
            return {
                "location": selected_location,
                "experience": selected_experience,
                "job_type": selected_job_type,
                "salary_range": salary_range,
                "sources": sources,
                "max_results": max_results,
                "timeout": search_timeout
            }
    
    def display_chat_interface(self):
        """Display the main chat interface"""
        st.header("💬 Chat with Job Agent")
        
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask me about jobs in Bangladesh..."):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Display assistant response
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                message_placeholder.markdown("🔍 Searching for jobs...")
                
                try:
                    # Get search filters from sidebar
                    filters = self.get_current_filters()
                    
                    # Search for jobs
                    results = self.search_jobs(prompt, filters)
                    
                    # Display results
                    if results and results.get('jobs'):
                        message_placeholder.markdown("✅ Found jobs! Here are the results:")
                        self.display_job_results(results['jobs'])
                        
                        # Add assistant response to chat history
                        response_text = f"Found {len(results['jobs'])} jobs matching your query. Check the results below!"
                        st.session_state.messages.append({"role": "assistant", "content": response_text})
                    else:
                        message_placeholder.markdown("❌ No jobs found. Try adjusting your search criteria.")
                        st.session_state.messages.append({"role": "assistant", "content": "No jobs found. Try adjusting your search criteria."})
                        
                except Exception as e:
                    message_placeholder.markdown(f"❌ Error: {str(e)}")
                    st.session_state.messages.append({"role": "assistant", "content": f"Error: {str(e)}"})
    
    def get_current_filters(self):
        """Get current filter values from sidebar"""
        # This would integrate with the sidebar filters
        return {
            "location": "All Locations",
            "experience": "Any",
            "job_type": "Any",
            "salary_range": (0, 200000),
            "sources": {"BDJobs": True, "LinkedIn": True, "Indeed": True, "Web Search": True},
            "max_results": 20,
            "timeout": 30
        }
    
    def search_jobs(self, query: str, filters: Dict[str, Any]):
        """Search for jobs using the RAG engine"""
        if not self.rag_engine:
            raise Exception("RAG engine not initialized")
        
        # Parse the query
        parsed_query = self.query_parser.parse_query(query)
        
        # Add filters to parsed query
        parsed_query.update(filters)
        
        # Search using RAG engine
        results = self.rag_engine.search(parsed_query)
        return results
    
    def display_job_results(self, jobs: List[Dict[str, Any]]):
        """Display job results in beautiful cards"""
        if not jobs:
            st.info("No jobs found matching your criteria.")
            return
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(jobs)
        
        # Display job cards
        for idx, job in enumerate(jobs):
            with st.container():
                st.markdown(f"""
                <div class="job-card">
                    <h3>💼 {job.get('title', 'N/A')}</h3>
                    <p><strong>🏢 Company:</strong> {job.get('company', 'N/A')}</p>
                    <p><strong>📍 Location:</strong> {job.get('location', 'N/A')}</p>
                    <p><strong>💰 Salary:</strong> {job.get('salary', 'N/A')}</p>
                    <p><strong>📝 Summary:</strong> {job.get('summary', 'N/A')}</p>
                    <p><strong>🔗 <a href="{job.get('application_url', '#')}" target="_blank">Apply Now</a></strong></p>
                </div>
                """, unsafe_allow_html=True)
                
                # Add action buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"Save Job {idx+1}", key=f"save_{idx}"):
                        st.success("Job saved to favorites!")
                with col2:
                    if st.button(f"Share {idx+1}", key=f"share_{idx}"):
                        st.info("Share link copied to clipboard!")
                with col3:
                    if st.button(f"Details {idx+1}", key=f"details_{idx}"):
                        st.json(job)
    
    def display_analytics(self):
        """Display search analytics and statistics"""
        st.header("📊 Search Analytics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="stats-card">
                <h3>Total Searches</h3>
                <h2>24</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="stats-card">
                <h3>Jobs Found</h3>
                <h2>156</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="stats-card">
                <h3>Avg Response Time</h3>
                <h2>2.3s</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div class="stats-card">
                <h3>Success Rate</h3>
                <h2>94%</h2>
            </div>
            """, unsafe_allow_html=True)
    
    def display_search_history(self):
        """Display search history"""
        st.header("📚 Search History")
        
        # Sample search history
        history = [
            {"query": "Software Engineer jobs in Dhaka", "date": "2024-01-15", "results": 12},
            {"query": "Marketing Manager positions", "date": "2024-01-14", "results": 8},
            {"query": "Remote developer jobs", "date": "2024-01-13", "results": 15},
        ]
        
        for item in history:
            with st.expander(f"🔍 {item['query']} - {item['date']} ({item['results']} results)"):
                st.write(f"**Query:** {item['query']}")
                st.write(f"**Date:** {item['date']}")
                st.write(f"**Results:** {item['results']} jobs found")
                if st.button("Rerun Search", key=f"rerun_{item['query']}"):
                    st.info("Searching...")
    
    def run(self):
        """Main application runner"""
        # Display header
        self.display_header()
        
        # Create tabs for different sections
        tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "📊 Analytics", "📚 History", "⚙️ Settings"])
        
        with tab1:
            # Display sidebar filters
            filters = self.display_sidebar()
            
            # Display chat interface
            self.display_chat_interface()
        
        with tab2:
            self.display_analytics()
        
        with tab3:
            self.display_search_history()
        
        with tab4:
            st.header("⚙️ Application Settings")
            st.write("Configure your job search preferences here.")
            
            # API Configuration
            st.subheader("🔑 API Configuration")
            st.text_input("Gemini API Key", type="password", help="Enter your Gemini API key")
            st.text_input("Hugging Face API Key", type="password", help="Enter your Hugging Face API key")
            
            # Search Preferences
            st.subheader("🔍 Search Preferences")
            st.checkbox("Enable advanced search", value=True)
            st.checkbox("Include remote jobs", value=True)
            st.checkbox("Show salary information", value=True)
            
            # Notification Settings
            st.subheader("🔔 Notifications")
            st.checkbox("Email notifications for new jobs", value=False)
            st.checkbox("Browser notifications", value=True)

def main():
    """Main entry point"""
    # Initialize the interface
    interface = JobSearchInterface()
    
    # Run the application
    interface.run()

if __name__ == "__main__":
    main()
