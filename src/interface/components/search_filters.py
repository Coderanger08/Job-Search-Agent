import streamlit as st
from typing import Dict, Any, List, Tuple
import json

class SearchFilters:
    """Reusable search filters component with clean, modern design"""
    
    def __init__(self):
        self.locations = [
            "All Locations", "Dhaka", "Chittagong", "Sylhet", "Rajshahi", 
            "Khulna", "Barisal", "Rangpur", "Mymensingh", "Remote"
        ]
        
        self.experience_levels = [
            "Any", "Entry Level (0-2 years)", "Mid Level (3-5 years)", 
            "Senior Level (6-10 years)", "Executive (10+ years)"
        ]
        
        self.job_types = [
            "Any", "Full-time", "Part-time", "Contract", "Remote", "Hybrid", "Internship"
        ]
        
        self.data_sources = {
            "BDJobs": "BDJobs",
            "LinkedIn": "LinkedIn", 
            "Indeed": "Indeed",
            "Web Search": "Web Search"
        }
    
    def render_filters(self) -> Dict[str, Any]:
        """
        Render all search filters in the sidebar with clean, modern design
        
        Returns:
            Dictionary containing all filter values
        """
        # Custom CSS for the clean design
        st.markdown("""
        <style>
        .filter-section {
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            border-left: 3px solid #dc3545;
        }
        .filter-title {
            font-weight: 600;
            color: #495057;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .stSlider > div > div > div > div {
            background-color: #dc3545 !important;
        }
        .stSlider > div > div > div > div > div {
            background-color: #dc3545 !important;
        }
        .stCheckbox > div > div > div {
            color: #dc3545 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        with st.sidebar:
            # Location Filter
            with st.container():
                st.markdown("""
                <div class="filter-section">
                    <div class="filter-title">
                        📍 Location
                    </div>
                </div>
                """, unsafe_allow_html=True)
                location_filter = st.selectbox(
                    "Select Location",
                    self.locations,
                    index=0,
                    label_visibility="collapsed"
                )
            
            # Experience Level Filter
            with st.container():
                st.markdown("""
                <div class="filter-section">
                    <div class="filter-title">
                        👤 Experience Level
                    </div>
                </div>
                """, unsafe_allow_html=True)
                experience_filter = st.selectbox(
                    "Select Experience",
                    self.experience_levels,
                    index=0,
                    label_visibility="collapsed"
                )
            
            # Job Type Filter
            with st.container():
                st.markdown("""
                <div class="filter-section">
                    <div class="filter-title">
                        💼 Job Type
                    </div>
                </div>
                """, unsafe_allow_html=True)
                job_type_filter = st.selectbox(
                    "Select Job Type",
                    self.job_types,
                    index=0,
                    label_visibility="collapsed"
                )
            
            # Salary Range Filter
            with st.container():
                st.markdown("""
                <div class="filter-section">
                    <div class="filter-title">
                        💰 Salary Range (BDT)
                    </div>
                </div>
                """, unsafe_allow_html=True)
                salary_filter = st.slider(
                    "Monthly Salary",
                    min_value=0,
                    max_value=200000,
                    value=(0, 200000),
                    step=5000,
                    label_visibility="collapsed"
                )
            
            # Data Sources Filter
            with st.container():
                st.markdown("""
                <div class="filter-section">
                    <div class="filter-title">
                        🌐 Data Sources
                    </div>
                </div>
                """, unsafe_allow_html=True)
                sources_filter = {}
                for source_name, source_label in self.data_sources.items():
                    sources_filter[source_name] = st.checkbox(
                        source_label,
                        value=True,
                        label_visibility="collapsed"
                    )
            
            # Settings Filter
            with st.container():
                st.markdown("""
                <div class="filter-section">
                    <div class="filter-title">
                        ⚙️ Settings
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Max Results
                max_results = st.slider(
                    "Max Results",
                    min_value=5,
                    max_value=50,
                    value=20,
                    step=5,
                    label_visibility="collapsed"
                )
                
                # Search Timeout
                search_timeout = st.slider(
                    "Search Timeout (seconds)",
                    min_value=10,
                    max_value=60,
                    value=30,
                    step=5,
                    label_visibility="collapsed"
                )
            
            # Combine all filters
            filters = {
                "location": location_filter,
                "experience": experience_filter,
                "job_type": job_type_filter,
                "salary_range": salary_filter,
                "sources": sources_filter,
                "max_results": max_results,
                "search_timeout": search_timeout
            }
            
            return filters
    
    def _render_location_filter(self) -> str:
        """Render location filter"""
        st.subheader("📍 Location")
        selected_location = st.selectbox(
            "Select Location",
            self.locations,
            index=0,
            help="Choose your preferred job location"
        )
        return selected_location
    
    def _render_experience_filter(self) -> str:
        """Render experience level filter"""
        st.subheader("👨‍💼 Experience Level")
        selected_experience = st.selectbox(
            "Select Experience",
            self.experience_levels,
            index=0,
            help="Choose your experience level"
        )
        return selected_experience
    
    def _render_job_type_filter(self) -> str:
        """Render job type filter"""
        st.subheader("💼 Job Type")
        selected_job_type = st.selectbox(
            "Select Job Type",
            self.job_types,
            index=0,
            help="Choose your preferred job type"
        )
        return selected_job_type
    
    def _render_salary_filter(self) -> Tuple[int, int]:
        """Render salary range filter"""
        st.subheader("💰 Salary Range (BDT)")
        
        # Custom salary range
        use_custom_range = st.checkbox("Use Custom Range", value=False)
        
        if use_custom_range:
            min_salary = st.number_input("Minimum Salary", 0, 1000000, 0, 5000)
            max_salary = st.number_input("Maximum Salary", 0, 1000000, 200000, 5000)
            return (min_salary, max_salary)
        else:
            # Predefined ranges
            salary_options = [f"{range_name}" for _, _, range_name in self.salary_ranges]
            selected_range = st.selectbox("Select Salary Range", salary_options)
            
            # Find the corresponding range values
            for min_val, max_val, range_name in self.salary_ranges:
                if range_name == selected_range:
                    return (min_val, max_val)
            
            return (0, 200000)  # Default
    
    def _render_sources_filter(self) -> Dict[str, bool]:
        """Render data sources filter"""
        st.subheader("🌐 Data Sources")
        
        sources = {}
        for source_key, source_name in self.data_sources.items():
            sources[source_key] = st.checkbox(
                source_name, 
                value=True,
                help=f"Search jobs from {source_name}"
            )
        
        return sources
    
    def _render_advanced_filters(self) -> Dict[str, Any]:
        """Render advanced filters"""
        st.subheader("⚙️ Advanced Filters")
        
        # Skills filter
        skills_input = st.text_input(
            "Required Skills",
            placeholder="e.g., Python, Django, React",
            help="Enter required skills (comma-separated)"
        )
        
        # Company filter
        company_filter = st.text_input(
            "Company Name",
            placeholder="e.g., Google, Microsoft",
            help="Search for specific companies"
        )
        
        # Date posted filter
        date_posted = st.selectbox(
            "Posted Within",
            ["Any Time", "Last 24 hours", "Last 3 days", "Last week", "Last month"],
            index=0
        )
        
        # Remote work preference
        remote_preference = st.selectbox(
            "Remote Work",
            ["Any", "Remote Only", "On-site Only", "Hybrid Preferred"],
            index=0
        )
        
        return {
            "skills": skills_input,
            "company": company_filter,
            "date_posted": date_posted,
            "remote_preference": remote_preference
        }
    
    def _render_search_settings(self) -> Dict[str, Any]:
        """Render search settings"""
        st.header("⚙️ Search Settings")
        
        # Max results
        max_results = st.slider(
            "Max Results",
            min_value=5,
            max_value=100,
            value=20,
            step=5,
            help="Maximum number of jobs to display"
        )
        
        # Search timeout
        search_timeout = st.slider(
            "Search Timeout (seconds)",
            min_value=10,
            max_value=120,
            value=30,
            step=5,
            help="Maximum time to wait for search results"
        )
        
        # Sort by
        sort_by = st.selectbox(
            "Sort By",
            ["Relevance", "Date Posted", "Salary (High to Low)", "Salary (Low to High)", "Company Name"],
            index=0
        )
        
        # Enable deduplication
        enable_dedup = st.checkbox(
            "Remove Duplicates",
            value=True,
            help="Remove duplicate job postings"
        )
        
        return {
            "max_results": max_results,
            "timeout": search_timeout,
            "sort_by": sort_by,
            "deduplicate": enable_dedup
        }
    
    def get_filter_summary(self, filters: Dict[str, Any]) -> str:
        """Generate a summary of applied filters"""
        summary_parts = []
        
        if filters["location"] != "All Locations":
            summary_parts.append(f"📍 {filters['location']}")
        
        if filters["experience"] != "Any":
            summary_parts.append(f"👨‍💼 {filters['experience']}")
        
        if filters["job_type"] != "Any":
            summary_parts.append(f"💼 {filters['job_type']}")
        
        if filters["salary_range"] != (0, 200000):
            min_sal, max_sal = filters["salary_range"]
            if max_sal == float('inf'):
                summary_parts.append(f"💰 {min_sal:,}+ BDT")
            else:
                summary_parts.append(f"💰 {min_sal:,} - {max_sal:,} BDT")
        
        active_sources = [name for key, name in self.data_sources.items() 
                         if filters["sources"].get(key, False)]
        if active_sources:
            summary_parts.append(f"🌐 {', '.join(active_sources)}")
        
        if filters["advanced"]["skills"]:
            summary_parts.append(f"🔧 Skills: {filters['advanced']['skills']}")
        
        if filters["advanced"]["company"]:
            summary_parts.append(f"🏢 Company: {filters['advanced']['company']}")
        
        return " | ".join(summary_parts) if summary_parts else "All filters applied"
    
    def save_filters(self, filters: Dict[str, Any], name: str) -> None:
        """Save current filters as a preset"""
        if 'saved_filters' not in st.session_state:
            st.session_state.saved_filters = {}
        
        st.session_state.saved_filters[name] = filters
        st.success(f"✅ Filters saved as '{name}'")
    
    def load_filters(self, name: str) -> Dict[str, Any]:
        """Load saved filters"""
        if 'saved_filters' in st.session_state and name in st.session_state.saved_filters:
            return st.session_state.saved_filters[name]
        return {}
    
    def get_saved_filter_names(self) -> List[str]:
        """Get list of saved filter names"""
        if 'saved_filters' in st.session_state:
            return list(st.session_state.saved_filters.keys())
        return []
    
    def render_filter_presets(self) -> None:
        """Render filter presets section"""
        st.subheader("💾 Saved Filters")
        
        saved_names = self.get_saved_filter_names()
        
        if saved_names:
            selected_preset = st.selectbox("Load Saved Filter", saved_names)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📂 Load"):
                    filters = self.load_filters(selected_preset)
                    st.success(f"✅ Loaded '{selected_preset}'")
            
            with col2:
                if st.button("🗑️ Delete"):
                    if selected_preset in st.session_state.saved_filters:
                        del st.session_state.saved_filters[selected_preset]
                        st.success(f"✅ Deleted '{selected_preset}'")
        else:
            st.info("No saved filters yet. Save your current filters to create presets.")
        
        # Save current filters
        st.markdown("---")
        preset_name = st.text_input("Save Current Filters As:", placeholder="e.g., Software Engineer Dhaka")
        if st.button("💾 Save Filters") and preset_name:
            # This would need to be called with current filters
            st.info("Use the 'Apply Filters' button first, then save.")
