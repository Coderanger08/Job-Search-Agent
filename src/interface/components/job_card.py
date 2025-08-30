import streamlit as st
from typing import Dict, Any, Optional
import json

class JobCard:
    """Reusable job card component for displaying job listings"""
    
    def __init__(self):
        self.css_styles = """
        <style>
        .job-card-container {
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .job-card-container:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            border-color: #667eea;
        }
        
        .job-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 1rem;
        }
        
        .job-title {
            font-size: 1.4rem;
            font-weight: 600;
            color: #2c3e50;
            margin: 0;
            line-height: 1.3;
        }
        
        .company-name {
            font-size: 1.1rem;
            color: #667eea;
            font-weight: 500;
            margin: 0.5rem 0;
        }
        
        .job-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            margin: 1rem 0;
        }
        
        .meta-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.9rem;
            color: #666;
        }
        
        .meta-icon {
            font-size: 1rem;
        }
        
        .job-summary {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            font-size: 0.95rem;
            line-height: 1.5;
            color: #555;
        }
        
        .job-actions {
            display: flex;
            gap: 0.5rem;
            margin-top: 1rem;
            flex-wrap: wrap;
        }
        
        .action-btn {
            padding: 0.5rem 1rem;
            border: none;
            border-radius: 6px;
            font-size: 0.9rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            text-decoration: none;
            display: inline-block;
        }
        
        .btn-primary {
            background: #667eea;
            color: white;
        }
        
        .btn-primary:hover {
            background: #5a6fd8;
            transform: translateY(-1px);
        }
        
        .btn-secondary {
            background: #f8f9fa;
            color: #666;
            border: 1px solid #e0e0e0;
        }
        
        .btn-secondary:hover {
            background: #e9ecef;
            color: #333;
        }
        
        .salary-badge {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
        }
        
        .location-badge {
            background: #e3f2fd;
            color: #1976d2;
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 500;
        }
        
        .experience-badge {
            background: #f3e5f5;
            color: #7b1fa2;
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 500;
        }
        
        .job-type-badge {
            background: #e8f5e8;
            color: #2e7d32;
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 500;
        }
        
        .source-badge {
            position: absolute;
            top: 1rem;
            right: 1rem;
            background: #fff3cd;
            color: #856404;
            padding: 0.2rem 0.6rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        </style>
        """
    
    def render(self, job: Dict[str, Any], card_id: Optional[str] = None) -> None:
        """
        Render a job card with all job information
        
        Args:
            job: Dictionary containing job information
            card_id: Unique identifier for the card (for button keys)
        """
        # Apply CSS styles
        st.markdown(self.css_styles, unsafe_allow_html=True)
        
        # Extract job data with defaults
        title = job.get('title', 'N/A')
        company = job.get('company', 'N/A')
        location = job.get('location', 'N/A')
        salary = job.get('salary', 'N/A')
        summary = job.get('summary', 'N/A')
        application_url = job.get('application_url', '#')
        experience = job.get('experience', 'N/A')
        job_type = job.get('job_type', 'N/A')
        source = job.get('source', 'Unknown')
        
        # Create unique card ID
        if not card_id:
            card_id = f"job_{hash(title + company)}"
        
        # Render the job card
        st.markdown(f"""
        <div class="job-card-container">
            <div class="source-badge">{source}</div>
            
            <div class="job-header">
                <div>
                    <h3 class="job-title">💼 {title}</h3>
                    <p class="company-name">🏢 {company}</p>
                </div>
                <div class="salary-badge">💰 {salary}</div>
            </div>
            
            <div class="job-meta">
                <div class="meta-item">
                    <span class="meta-icon">📍</span>
                    <span class="location-badge">{location}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-icon">👨‍💼</span>
                    <span class="experience-badge">{experience}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-icon">💼</span>
                    <span class="job-type-badge">{job_type}</span>
                </div>
            </div>
            
            <div class="job-summary">
                📝 {summary}
            </div>
            
            <div class="job-actions">
                <a href="{application_url}" target="_blank" class="action-btn btn-primary">
                    🚀 Apply Now
                </a>
                <button class="action-btn btn-secondary" onclick="saveJob('{card_id}')">
                    💾 Save Job
                </button>
                <button class="action-btn btn-secondary" onclick="shareJob('{card_id}')">
                    📤 Share
                </button>
                <button class="action-btn btn-secondary" onclick="showDetails('{card_id}')">
                    📋 Details
                </button>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Add action buttons using Streamlit
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("💾 Save", key=f"save_{card_id}"):
                self._save_job(job)
        
        with col2:
            if st.button("📤 Share", key=f"share_{card_id}"):
                self._share_job(job)
        
        with col3:
            if st.button("📋 Details", key=f"details_{card_id}"):
                self._show_details(job)
        
        with col4:
            if st.button("🔗 Direct Link", key=f"link_{card_id}"):
                st.markdown(f"[Open Job Posting]({application_url})")
    
    def _save_job(self, job: Dict[str, Any]) -> None:
        """Save job to favorites"""
        # Initialize saved jobs in session state
        if 'saved_jobs' not in st.session_state:
            st.session_state.saved_jobs = []
        
        # Check if job is already saved
        job_id = f"{job.get('title', '')}_{job.get('company', '')}"
        existing_jobs = [j for j in st.session_state.saved_jobs if 
                        f"{j.get('title', '')}_{j.get('company', '')}" == job_id]
        
        if not existing_jobs:
            st.session_state.saved_jobs.append(job)
            st.success("✅ Job saved to favorites!")
        else:
            st.warning("⚠️ Job already saved!")
    
    def _share_job(self, job: Dict[str, Any]) -> None:
        """Share job information"""
        share_text = f"""
        💼 {job.get('title', 'N/A')}
        🏢 {job.get('company', 'N/A')}
        📍 {job.get('location', 'N/A')}
        💰 {job.get('salary', 'N/A')}
        🔗 {job.get('application_url', 'N/A')}
        """
        
        st.code(share_text, language=None)
        st.info("📋 Job information copied! Share this with others.")
    
    def _show_details(self, job: Dict[str, Any]) -> None:
        """Show detailed job information"""
        st.subheader("📋 Job Details")
        
        # Display job data in a structured format
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Job Title:**", job.get('title', 'N/A'))
            st.write("**Company:**", job.get('company', 'N/A'))
            st.write("**Location:**", job.get('location', 'N/A'))
            st.write("**Salary:**", job.get('salary', 'N/A'))
        
        with col2:
            st.write("**Experience:**", job.get('experience', 'N/A'))
            st.write("**Job Type:**", job.get('job_type', 'N/A'))
            st.write("**Source:**", job.get('source', 'N/A'))
            st.write("**Posted:**", job.get('posted_date', 'N/A'))
        
        st.write("**Summary:**", job.get('summary', 'N/A'))
        
        # Show raw JSON data
        with st.expander("🔍 Raw Data"):
            st.json(job)
    
    def render_compact(self, job: Dict[str, Any], card_id: Optional[str] = None) -> None:
        """Render a compact version of the job card"""
        title = job.get('title', 'N/A')
        company = job.get('company', 'N/A')
        location = job.get('location', 'N/A')
        salary = job.get('salary', 'N/A')
        
        st.markdown(f"""
        <div class="job-card-container" style="padding: 1rem;">
            <div class="job-header" style="margin-bottom: 0.5rem;">
                <div>
                    <h4 class="job-title" style="font-size: 1.1rem;">💼 {title}</h4>
                    <p class="company-name" style="font-size: 0.9rem;">🏢 {company}</p>
                </div>
                <div class="salary-badge">{salary}</div>
            </div>
            <div class="meta-item">
                <span class="meta-icon">📍</span>
                <span class="location-badge">{location}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
