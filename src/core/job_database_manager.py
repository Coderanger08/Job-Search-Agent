#!/usr/bin/env python3
"""
Job Database Manager
Handles loading, indexing, and searching the LinkedIn job dataset
"""

import pandas as pd
import numpy as np
import re
import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config import Config

@dataclass
class JobData:
    """Standardized job data structure"""
    title: str
    company: str
    location: str
    description: str
    url: str
    salary: Optional[str] = None
    experience_level: Optional[str] = None
    skills: Optional[List[str]] = None
    posted_date: Optional[str] = None
    source: str = "linkedin_dataset"
    source_site: str = "linkedin"
    # Additional fields from LinkedIn dataset
    job_posting_id: Optional[str] = None
    company_url: Optional[str] = None
    company_logo: Optional[str] = None
    country_code: Optional[str] = None
    job_employment_type: Optional[str] = None
    job_industries: Optional[str] = None
    job_function: Optional[str] = None
    job_num_applicants: Optional[int] = None
    application_availability: Optional[bool] = None
    apply_link: Optional[str] = None
    base_salary: Optional[Dict] = None
    job_base_pay_range: Optional[str] = None
    job_posted_time: Optional[str] = None

class JobDatabaseManager:
    """Manages the LinkedIn job dataset with search and filter capabilities"""
    
    def __init__(self, csv_path: str = "Linkedin job listings information.csv"):
        self.config = Config()
        self.csv_path = csv_path
        self.logger = logging.getLogger(__name__)
        self.df = None
        self.jobs_cache = []
        self.search_index = {}
        
        # Load the dataset
        self._load_dataset()
        self._create_search_index()
    
    def _load_dataset(self):
        """Load and preprocess the LinkedIn CSV dataset"""
        try:
            self.logger.info(f"Loading LinkedIn job dataset from {self.csv_path}")
            
            # Load CSV with proper encoding
            self.df = pd.read_csv(self.csv_path, encoding='utf-8')
            
            # Clean and preprocess data
            self._clean_data()
            
            # Convert to standardized format
            self._convert_to_standard_format()
            
            self.logger.info(f"✅ Loaded {len(self.jobs_cache)} jobs from dataset")
            
        except Exception as e:
            self.logger.error(f"❌ Error loading dataset: {e}")
            raise
    
    def _clean_data(self):
        """Clean and preprocess the raw data"""
        # Remove rows with missing essential data
        essential_columns = ['job_title', 'company_name', 'job_location', 'job_summary']
        self.df = self.df.dropna(subset=essential_columns)
        
        # Clean text fields
        text_columns = ['job_title', 'company_name', 'job_location', 'job_summary']
        for col in text_columns:
            if col in self.df.columns:
                self.df[col] = self.df[col].astype(str).str.strip()
        
        # Convert salary data
        if 'base_salary' in self.df.columns:
            self.df['base_salary'] = self.df['base_salary'].apply(self._parse_salary)
        
        # Convert posted date
        if 'job_posted_date' in self.df.columns:
            self.df['job_posted_date'] = pd.to_datetime(self.df['job_posted_date'], errors='coerce')
        
        # Convert numeric fields
        if 'job_num_applicants' in self.df.columns:
            self.df['job_num_applicants'] = pd.to_numeric(self.df['job_num_applicants'], errors='coerce')
    
    def _parse_salary(self, salary_str: str) -> Optional[Dict]:
        """Parse salary string to structured format"""
        if pd.isna(salary_str) or salary_str == 'nan':
            return None
        
        try:
            # Handle JSON string format
            if isinstance(salary_str, str) and salary_str.startswith('{'):
                return json.loads(salary_str)
            return None
        except:
            return None
    
    def _convert_to_standard_format(self):
        """Convert DataFrame to standardized JobData objects"""
        self.jobs_cache = []
        
        for _, row in self.df.iterrows():
            try:
                # Extract skills from job summary (basic extraction)
                skills = self._extract_skills_from_text(row.get('job_summary', ''))
                
                # Create standardized job object
                job = JobData(
                    title=row.get('job_title', ''),
                    company=row.get('company_name', ''),
                    location=row.get('job_location', ''),
                    description=row.get('job_summary', ''),
                    url=row.get('url', ''),
                    salary=self._format_salary(row.get('base_salary')),
                    experience_level=row.get('job_seniority_level'),
                    skills=skills,
                    posted_date=str(row.get('job_posted_date')) if pd.notna(row.get('job_posted_date')) else None,
                    # Additional LinkedIn fields
                    job_posting_id=row.get('job_posting_id'),
                    company_url=row.get('company_url'),
                    company_logo=row.get('company_logo'),
                    country_code=row.get('country_code'),
                    job_employment_type=row.get('job_employment_type'),
                    job_industries=row.get('job_industries'),
                    job_function=row.get('job_function'),
                    job_num_applicants=row.get('job_num_applicants'),
                    application_availability=row.get('application_availability'),
                    apply_link=row.get('apply_link'),
                    base_salary=row.get('base_salary'),
                    job_base_pay_range=row.get('job_base_pay_range'),
                    job_posted_time=row.get('job_posted_time')
                )
                
                # Validate job before adding
                if self._validate_job(job):
                    self.jobs_cache.append(job)
                    
            except Exception as e:
                self.logger.error(f"Error converting job row: {e}")
                continue
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract potential skills from job description"""
        if not text:
            return []
        
        # Common technical skills
        skill_patterns = [
            r'\b(?:Python|Java|JavaScript|React|Angular|Vue|Node\.js|SQL|MongoDB|AWS|Azure|Docker|Kubernetes)\b',
            r'\b(?:Machine Learning|AI|Data Science|Analytics|Business Intelligence)\b',
            r'\b(?:Project Management|Agile|Scrum|Kanban)\b',
            r'\b(?:Marketing|Sales|Customer Service|HR|Finance|Operations)\b'
        ]
        
        skills = set()
        for pattern in skill_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            skills.update(matches)
        
        return list(skills)
    
    def _format_salary(self, salary_data: Optional[Dict]) -> Optional[str]:
        """Format salary data to readable string"""
        if not salary_data:
            return None
        
        try:
            if isinstance(salary_data, dict):
                currency = salary_data.get('currency', '')
                min_amount = salary_data.get('min_amount')
                max_amount = salary_data.get('max_amount')
                payment_period = salary_data.get('payment_period', '')
                
                if min_amount and max_amount:
                    return f"{currency}{min_amount}-{max_amount}/{payment_period}"
                elif min_amount:
                    return f"{currency}{min_amount}/{payment_period}"
            
            return str(salary_data)
        except:
            return None
    
    def _validate_job(self, job: JobData) -> bool:
        """Validate job data before including in results"""
        # Check required fields
        if not job.title or not job.company or not job.location:
            return False
        
        # Basic spam detection
        spam_keywords = ['work from home', 'earn money', 'make money', 'quick cash', 'get rich']
        title_lower = job.title.lower()
        
        if any(keyword in title_lower for keyword in spam_keywords):
            return False
        
        return True
    
    def _create_search_index(self):
        """Create search index for fast keyword matching"""
        self.search_index = {
            'titles': {},
            'companies': {},
            'locations': {},
            'skills': {},
            'industries': {}
        }
        
        for i, job in enumerate(self.jobs_cache):
            # Index by title keywords
            if job.title and isinstance(job.title, str):
                title_words = re.findall(r'\b\w+\b', job.title.lower())
                for word in title_words:
                    if len(word) > 2:  # Skip short words
                        if word not in self.search_index['titles']:
                            self.search_index['titles'][word] = []
                        self.search_index['titles'][word].append(i)
            
            # Index by company
            if job.company and isinstance(job.company, str):
                company_lower = job.company.lower()
                if company_lower not in self.search_index['companies']:
                    self.search_index['companies'][company_lower] = []
                self.search_index['companies'][company_lower].append(i)
            
            # Index by location
            if job.location and isinstance(job.location, str):
                location_lower = job.location.lower()
                if location_lower not in self.search_index['locations']:
                    self.search_index['locations'][location_lower] = []
                self.search_index['locations'][location_lower].append(i)
            
            # Index by skills
            if job.skills and isinstance(job.skills, list):
                for skill in job.skills:
                    if isinstance(skill, str):
                        skill_lower = skill.lower()
                        if skill_lower not in self.search_index['skills']:
                            self.search_index['skills'][skill_lower] = []
                        self.search_index['skills'][skill_lower].append(i)
            
            # Index by industries
            if job.job_industries and isinstance(job.job_industries, str):
                industry_lower = job.job_industries.lower()
                if industry_lower not in self.search_index['industries']:
                    self.search_index['industries'][industry_lower] = []
                self.search_index['industries'][industry_lower].append(i)
    
    def search_jobs(self, query: str, location: str = None, 
                   experience_level: str = None, limit: int = 20, 
                   sort_by_date: bool = True) -> List[JobData]:
        """
        Search jobs by keyword, location, and experience level with semantic matching
        
        Args:
            query: Search query (job title, skills, etc.)
            location: Location filter
            experience_level: Experience level filter
            limit: Maximum number of results
            sort_by_date: Sort results by posted date (most recent first)
        
        Returns:
            List of matching JobData objects
        """
        matching_indices = set()
        
        # Search by query with semantic matching
        if query:
            query_lower = query.lower()
            query_words = re.findall(r'\b\w+\b', query_lower)
            
            # Enhanced semantic search with job role prioritization
            for word in query_words:
                if len(word) > 2:
                    # Search in titles with semantic variations
                    if word in self.search_index['titles']:
                        matching_indices.update(self.search_index['titles'][word])
                    
                    # Search for related terms (e.g., "ai" should match "artificial intelligence")
                    related_terms = self._get_related_terms(word)
                    for term in related_terms:
                        if term in self.search_index['titles']:
                            matching_indices.update(self.search_index['titles'][term])
                    
                    # Search in skills
                    if word in self.search_index['skills']:
                        matching_indices.update(self.search_index['skills'][word])
                    
                    # Search in companies
                    if word in self.search_index['companies']:
                        matching_indices.update(self.search_index['companies'][word])
            
            # Apply job role filtering for better relevance (optimized for speed)
            if matching_indices:
                # Use list comprehension for faster filtering
                if 'ai engineer' in query_lower or 'artificial intelligence' in query_lower:
                    ai_terms = ['ai', 'artificial intelligence', 'machine learning', 'ml', 'deep learning']
                    matching_indices = {idx for idx in matching_indices 
                                      if any(term in self.jobs_cache[idx].title.lower() for term in ai_terms)}
                elif 'software engineer' in query_lower or 'software developer' in query_lower:
                    software_terms = ['software', 'developer', 'programmer', 'coding']
                    matching_indices = {idx for idx in matching_indices 
                                      if any(term in self.jobs_cache[idx].title.lower() for term in software_terms)}
                elif 'data scientist' in query_lower or 'data analyst' in query_lower:
                    data_terms = ['data', 'analyst', 'scientist', 'analytics']
                    matching_indices = {idx for idx in matching_indices 
                                      if any(term in self.jobs_cache[idx].title.lower() for term in data_terms)}
                elif 'designer' in query_lower:
                    design_terms = ['designer', 'design', 'ui', 'ux', 'graphic']
                    matching_indices = {idx for idx in matching_indices 
                                      if any(term in self.jobs_cache[idx].title.lower() for term in design_terms)}
                # For other searches, keep all matches (no additional filtering needed)
        
        # Filter by location
        if location:
            location_lower = location.lower()
            location_matches = set()
            
            for idx in matching_indices:
                job = self.jobs_cache[idx]
                if location_lower in job.location.lower():
                    location_matches.add(idx)
            
            matching_indices = location_matches
        
        # Filter by experience level
        if experience_level:
            exp_matches = set()
            exp_lower = experience_level.lower()
            
            for idx in matching_indices:
                job = self.jobs_cache[idx]
                if job.experience_level and isinstance(job.experience_level, str) and exp_lower in job.experience_level.lower():
                    exp_matches.add(idx)
            
            matching_indices = exp_matches
        
        # Convert indices to jobs
        results = [self.jobs_cache[idx] for idx in matching_indices]
        
        # Sort by date if requested
        if sort_by_date:
            results = self._sort_jobs_by_date(results)
        
        # Limit results
        results = results[:limit]
        
        self.logger.info(f"Found {len(results)} jobs matching query: '{query}'")
        return results
    
    def _get_related_terms(self, word: str) -> List[str]:
        """Get semantically related terms for enhanced search"""
        word_lower = word.lower()
        
        # Define semantic relationships
        semantic_mapping = {
            "ai": ["artificial", "intelligence", "machine", "learning", "ml"],
            "ml": ["machine", "learning", "artificial", "intelligence", "ai"],
            "software": ["developer", "programmer", "engineer", "coding"],
            "developer": ["software", "programmer", "engineer", "coding"],
            "engineer": ["developer", "programmer", "software"],
            "designer": ["graphic", "ui", "ux", "visual", "creative"],
            "manager": ["lead", "supervisor", "director", "head"],
            "analyst": ["data", "business", "systems", "research"],
            "data": ["analyst", "scientist", "engineer", "analytics"]
        }
        
        return semantic_mapping.get(word_lower, [])
    
    def _sort_jobs_by_date(self, jobs: List[JobData]) -> List[JobData]:
        """Sort jobs by posted date (most recent first)"""
        def get_date_key(job):
            if not job.posted_date:
                return datetime.min  # Put jobs without dates at the end
            try:
                # Handle different date formats
                if 'T' in job.posted_date:
                    return datetime.fromisoformat(job.posted_date.replace('Z', '+00:00'))
                else:
                    return datetime.strptime(job.posted_date, '%Y-%m-%d')
            except:
                return datetime.min  # Put invalid dates at the end
        
        return sorted(jobs, key=get_date_key, reverse=True)
    
    def filter_jobs(self, filters: Dict[str, Any], limit: int = 20, 
                   sort_by_date: bool = True) -> List[JobData]:
        """
        Filter jobs by multiple criteria
        
        Args:
            filters: Dictionary of filters
                - location: str
                - experience_level: str
                - employment_type: str
                - country_code: str
                - min_salary: float
                - max_salary: float
                - industries: List[str]
                - posted_within_days: int
            limit: Maximum number of results
            sort_by_date: Sort results by posted date (most recent first)
        
        Returns:
            List of filtered JobData objects
        """
        filtered_jobs = self.jobs_cache.copy()
        
        # Apply filters
        for key, value in filters.items():
            if value is None:
                continue
                
            if key == 'location':
                filtered_jobs = [job for job in filtered_jobs 
                               if value.lower() in job.location.lower()]
            
            elif key == 'experience_level':
                filtered_jobs = [job for job in filtered_jobs 
                               if job.experience_level and isinstance(job.experience_level, str) and 
                               value.lower() in job.experience_level.lower()]
            
            elif key == 'employment_type':
                filtered_jobs = [job for job in filtered_jobs 
                               if job.job_employment_type and isinstance(job.job_employment_type, str) and 
                               value.lower() in job.job_employment_type.lower()]
            
            elif key == 'country_code':
                filtered_jobs = [job for job in filtered_jobs 
                               if job.country_code and isinstance(job.country_code, str) and 
                               job.country_code.upper() == value.upper()]
            
            elif key == 'industries':
                if isinstance(value, list):
                    filtered_jobs = [job for job in filtered_jobs 
                                   if job.job_industries and isinstance(job.job_industries, str) and 
                                   any(ind.lower() in job.job_industries.lower() 
                                       for ind in value)]
            
            elif key == 'posted_within_days':
                cutoff_date = datetime.now() - timedelta(days=value)
                filtered_jobs = [job for job in filtered_jobs 
                               if job.posted_date and 
                               datetime.fromisoformat(job.posted_date.replace('Z', '+00:00')) > cutoff_date]
        
        # Sort by date if requested
        if sort_by_date:
            filtered_jobs = self._sort_jobs_by_date(filtered_jobs)
        
        return filtered_jobs[:limit]
    
    def get_job_by_id(self, job_id: str) -> Optional[JobData]:
        """Get a specific job by its posting ID"""
        for job in self.jobs_cache:
            if job.job_posting_id == job_id:
                return job
        return None
    
    def get_jobs_by_company(self, company_name: str, limit: int = 20) -> List[JobData]:
        """Get all jobs from a specific company"""
        company_lower = company_name.lower()
        results = []
        
        for job in self.jobs_cache:
            if company_lower in job.company.lower():
                results.append(job)
                if len(results) >= limit:
                    break
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get dataset statistics"""
        if not self.jobs_cache:
            return {}
        
        stats = {
            'total_jobs': len(self.jobs_cache),
            'unique_companies': len(set(job.company for job in self.jobs_cache)),
            'unique_locations': len(set(job.location for job in self.jobs_cache)),
            'experience_levels': {},
            'employment_types': {},
            'countries': {},
            'industries': {}
        }
        
        # Count experience levels
        for job in self.jobs_cache:
            if job.experience_level:
                stats['experience_levels'][job.experience_level] = \
                    stats['experience_levels'].get(job.experience_level, 0) + 1
        
        # Count employment types
        for job in self.jobs_cache:
            if job.job_employment_type:
                stats['employment_types'][job.job_employment_type] = \
                    stats['employment_types'].get(job.job_employment_type, 0) + 1
        
        # Count countries
        for job in self.jobs_cache:
            if job.country_code:
                stats['countries'][job.country_code] = \
                    stats['countries'].get(job.country_code, 0) + 1
        
        # Count industries
        for job in self.jobs_cache:
            if job.job_industries:
                stats['industries'][job.job_industries] = \
                    stats['industries'].get(job.job_industries, 0) + 1
        
        return stats
    
    def export_to_json(self, jobs: List[JobData], filename: str = "exported_jobs.json"):
        """Export jobs to JSON file"""
        try:
            job_dicts = [asdict(job) for job in jobs]
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(job_dicts, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Exported {len(jobs)} jobs to {filename}")
        except Exception as e:
            self.logger.error(f"Error exporting jobs: {e}")
    
    def get_recent_jobs(self, limit: int = 20, days: int = 30) -> List[JobData]:
        """
        Get the most recent jobs posted within specified days
        
        Args:
            limit: Maximum number of results
            days: Number of days to look back
        
        Returns:
            List of recent JobData objects
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_jobs = []
        
        for job in self.jobs_cache:
            if job.posted_date:
                try:
                    if 'T' in job.posted_date:
                        job_date = datetime.fromisoformat(job.posted_date.replace('Z', '+00:00'))
                    else:
                        job_date = datetime.strptime(job.posted_date, '%Y-%m-%d')
                    
                    if job_date >= cutoff_date:
                        recent_jobs.append(job)
                except:
                    continue
        
        # Sort by date (most recent first)
        recent_jobs = self._sort_jobs_by_date(recent_jobs)
        
        return recent_jobs[:limit]
    
    def reload_dataset(self):
        """Reload the dataset from CSV"""
        self._load_dataset()
        self._create_search_index()
        self.logger.info("Dataset reloaded successfully")
