"""
Official API Data Sources for Bangladesh Job Search RAG System
Implements Option 1: Official APIs (The Direct Route) for reliable job data
"""

import requests
import json
import time
import logging
import re
import google.generativeai as genai
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, quote_plus
from bs4 import BeautifulSoup
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config import Config

# Import our fast scrapers
try:
    from bdjobs_scraper_fast import BDJobsFastScraper
    from linkedin_scraper_fast import LinkedInFastScraper
except ImportError as e:
    logger.warning(f"Could not import fast scrapers: {e}")
    BDJobsFastScraper = None
    LinkedInFastScraper = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LinkedInJobsAPI:
    """LinkedIn Jobs API Manager - Most reliable official API"""
    
    def __init__(self):
        self.config = Config()
        self.api_key = self.config.LINKEDIN_API_KEY
        self.base_url = "https://api.linkedin.com/v2"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
    
    def search_jobs(self, job_title: str, location: str = "Bangladesh", max_results: int = 20) -> List[Dict]:
        """Search jobs using LinkedIn Jobs API"""
        if not self.api_key:
            logger.warning("⚠️ LinkedIn API key not configured")
            return []
        
        try:
            logger.info(f"🔍 Searching LinkedIn Jobs for '{job_title}' in '{location}'")
            
            # LinkedIn Jobs API endpoint
            endpoint = f"{self.base_url}/jobSearch"
            
            # Build search parameters
            params = {
                "keywords": job_title,
                "location": location,
                "count": min(max_results, 50),  # LinkedIn limit
                "start": 0
            }
            
            # Make API request
            response = requests.get(endpoint, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                jobs = self._parse_linkedin_response(data)
                logger.info(f"✅ Found {len(jobs)} jobs on LinkedIn")
                return jobs
            else:
                logger.error(f"❌ LinkedIn API error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"❌ LinkedIn API request failed: {e}")
            return []
    
    def _parse_linkedin_response(self, data: Dict) -> List[Dict]:
        """Parse LinkedIn API response to standard format"""
        jobs = []
        
        try:
            elements = data.get("elements", [])
            
            for element in elements:
                job_data = {
                    'title': element.get("title", ""),
                    'company': element.get("companyName", ""),
                    'location': element.get("formattedLocation", ""),
                    'salary': element.get("salaryInsights", {}).get("salaryRange", "Salary not disclosed"),
                    'summary': element.get("description", "Job description not available"),
                    'url': element.get("applicationMethod", {}).get("applyUrl", ""),
                    'date_posted': element.get("listedAt", ""),
                    'requirements': self._extract_requirements(element.get("description", "")),
                    'deadline': "Deadline not specified",
                    'experience_level': self._extract_experience_level(element.get("title", ""), element.get("description", "")),
                    'job_type': self._extract_job_type(element.get("title", ""), element.get("description", "")),
                    'source': 'LinkedIn',
                    'field_presence': {
                        'title': bool(element.get("title")),
                        'company': bool(element.get("companyName")),
                        'location': bool(element.get("formattedLocation")),
                        'salary': bool(element.get("salaryInsights")),
                        'summary': bool(element.get("description")),
                        'url': bool(element.get("applicationMethod", {}).get("applyUrl")),
                        'date_posted': bool(element.get("listedAt"))
                    }
                }
                
                if job_data['title']:  # Only add jobs with titles
                    jobs.append(job_data)
                    
        except Exception as e:
            logger.error(f"❌ Error parsing LinkedIn response: {e}")
        
        return jobs
    
    def _extract_requirements(self, description: str) -> str:
        """Extract requirements from job description"""
        if not description:
            return "Requirements not specified"
        
        # Look for requirements section
        req_patterns = [
            r'requirements?[:\s]+([^.]+)',
            r'qualifications?[:\s]+([^.]+)',
            r'skills?[:\s]+([^.]+)',
            r'experience[:\s]+([^.]+)'
        ]
        
        for pattern in req_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Return first sentence if no requirements found
        sentences = description.split('.')
        return sentences[0].strip() if sentences else "Requirements not specified"
    
    def _extract_experience_level(self, title: str, description: str) -> str:
        """Extract experience level from title and description"""
        text = f"{title} {description}".lower()
        
        if any(word in text for word in ['senior', 'sr.', 'lead', 'head', 'manager', 'director']):
            return "Senior"
        elif any(word in text for word in ['junior', 'jr.', 'entry', 'fresh', 'trainee']):
            return "Junior"
        elif any(word in text for word in ['mid', 'intermediate']):
            return "Mid-level"
        else:
            return "Experience level not specified"
    
    def _extract_job_type(self, title: str, description: str) -> str:
        """Extract job type from title and description"""
        text = f"{title} {description}".lower()
        
        if any(word in text for word in ['part-time', 'part time', 'contract', 'freelance']):
            return "Part-time/Contract"
        elif any(word in text for word in ['full-time', 'full time', 'permanent']):
            return "Full-time"
        else:
            return "Job type not specified"


class IndeedJobsAPI:
    """Indeed Jobs API Manager"""
    
    def __init__(self):
        self.config = Config()
        self.api_key = self.config.INDEED_API_KEY
        self.base_url = "https://api.indeed.com/ads/apisearch"
        self.publisher_id = self.config.INDEED_PUBLISHER_ID
    
    def search_jobs(self, job_title: str, location: str = "Bangladesh", max_results: int = 20) -> List[Dict]:
        """Search jobs using Indeed API"""
        if not self.api_key or not self.publisher_id:
            logger.warning("⚠️ Indeed API credentials not configured")
            return []
        
        try:
            logger.info(f"🔍 Searching Indeed Jobs for '{job_title}' in '{location}'")
            
            # Indeed API parameters
            params = {
                "publisher": self.publisher_id,
                "q": job_title,
                "l": location,
                "limit": min(max_results, 25),  # Indeed limit
                "format": "json",
                "v": "2",  # API version
                "userip": "1.2.3.4",  # Required by Indeed
                "useragent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            # Make API request
            response = requests.get(self.base_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                jobs = self._parse_indeed_response(data)
                logger.info(f"✅ Found {len(jobs)} jobs on Indeed")
                return jobs
            else:
                logger.error(f"❌ Indeed API error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Indeed API request failed: {e}")
            return []
    
    def _parse_indeed_response(self, data: Dict) -> List[Dict]:
        """Parse Indeed API response to standard format"""
        jobs = []
        
        try:
            results = data.get("results", [])
            
            for result in results:
                job_data = {
                    'title': result.get("jobtitle", ""),
                    'company': result.get("company", ""),
                    'location': result.get("formattedLocation", ""),
                    'salary': result.get("salary", "Salary not disclosed"),
                    'summary': result.get("snippet", "Job description not available"),
                    'url': result.get("url", ""),
                    'date_posted': result.get("date", ""),
                    'requirements': self._extract_requirements(result.get("snippet", "")),
                    'deadline': "Deadline not specified",
                    'experience_level': self._extract_experience_level(result.get("jobtitle", ""), result.get("snippet", "")),
                    'job_type': self._extract_job_type(result.get("jobtitle", ""), result.get("snippet", "")),
                    'source': 'Indeed',
                    'field_presence': {
                        'title': bool(result.get("jobtitle")),
                        'company': bool(result.get("company")),
                        'location': bool(result.get("formattedLocation")),
                        'salary': bool(result.get("salary")),
                        'summary': bool(result.get("snippet")),
                        'url': bool(result.get("url")),
                        'date_posted': bool(result.get("date"))
                    }
                }
                
                if job_data['title']:  # Only add jobs with titles
                    jobs.append(job_data)
                    
        except Exception as e:
            logger.error(f"❌ Error parsing Indeed response: {e}")
        
        return jobs
    
    def _extract_requirements(self, snippet: str) -> str:
        """Extract requirements from job snippet"""
        if not snippet:
            return "Requirements not specified"
        
        # Indeed snippets are usually short, so return the full snippet
        return snippet[:200] + "..." if len(snippet) > 200 else snippet
    
    def _extract_experience_level(self, title: str, snippet: str) -> str:
        """Extract experience level from title and snippet"""
        text = f"{title} {snippet}".lower()
        
        if any(word in text for word in ['senior', 'sr.', 'lead', 'head', 'manager', 'director']):
            return "Senior"
        elif any(word in text for word in ['junior', 'jr.', 'entry', 'fresh', 'trainee']):
            return "Junior"
        elif any(word in text for word in ['mid', 'intermediate']):
            return "Mid-level"
        else:
            return "Experience level not specified"
    
    def _extract_job_type(self, title: str, snippet: str) -> str:
        """Extract job type from title and snippet"""
        text = f"{title} {snippet}".lower()
        
        if any(word in text for word in ['part-time', 'part time', 'contract', 'freelance']):
            return "Part-time/Contract"
        elif any(word in text for word in ['full-time', 'full time', 'permanent']):
            return "Full-time"
        else:
            return "Job type not specified"


class BrightDataScraper:
    """Bright Data Web Scraper - Replaces individual scrapers with unified API"""
    
    def __init__(self):
        self.config = Config()
        self.api_key = self.config.BRIGHTDATA_API_KEY
        self.base_url = "https://api.brightdata.com/web_scrapers"
        
        if not self.api_key:
            logger.warning("⚠️ Bright Data API key not configured")
        
        # Supported job sites with their domains
        self.job_sites = {
            'bdjobs': 'bdjobs.com',
            'skilljobs': 'skill.jobs', 
            'shomvob': 'shomvob.com',
            'linkedin': 'linkedin.com/jobs',
            'indeed': 'indeed.com/bd',
            'naukri': 'naukri.com',
            'glassdoor': 'glassdoor.com'
        }
    
    def search_jobs(self, job_title: str, location: str = "Bangladesh", max_results: int = 20) -> List[Dict]:
        """Search jobs across multiple sites using Bright Data"""
        if not self.api_key:
            logger.warning("⚠️ Bright Data API key not configured")
            return []
        
        logger.info(f"🚀 Bright Data search for '{job_title}' in '{location}'")
        
        all_jobs = []
        
        # Search each job site
        for site_name, domain in self.job_sites.items():
            try:
                logger.info(f"🔍 Searching {site_name} ({domain})...")
                site_jobs = self._search_single_site(job_title, location, domain, max_results // len(self.job_sites))
                all_jobs.extend(site_jobs)
                logger.info(f"✅ {site_name} returned {len(site_jobs)} jobs")
                
                # Rate limiting between sites
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ {site_name} search failed: {e}")
                continue
        
        # Remove duplicates
        unique_jobs = self._remove_duplicates(all_jobs)
        
        logger.info(f"🎉 Bright Data search completed: {len(unique_jobs)} unique jobs found")
        return unique_jobs[:max_results]
    
    def _search_single_site(self, job_title: str, location: str, domain: str, max_results: int) -> List[Dict]:
        """Search a single job site using Bright Data Web Scrapers API"""
        try:
            # Construct search URL for the job site
            search_url = self._construct_search_url(job_title, location, domain)
            
            # Bright Data Web Scrapers API parameters
            params = {
                'api_key': self.api_key,
                'url': search_url,
                'country': 'bd',  # Bangladesh
                'locale': 'en'
            }
            
            # Make API request
            response = requests.get(self.base_url, params=params, timeout=30)
            
            if response.status_code == 200:
                # Web Scrapers API returns HTML content
                html_content = response.text
                jobs = self._parse_html_content(html_content, domain, job_title)
                return jobs
            else:
                logger.error(f"❌ Bright Data Web Scrapers API error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Bright Data search failed for {domain}: {e}")
            return []
    
    def _construct_search_url(self, job_title: str, location: str, domain: str) -> str:
        """Construct search URL for specific job site"""
        # Clean job title for URL
        clean_title = job_title.replace(' ', '+')
        
        if domain == 'bdjobs.com':
            return f"https://jobs.bdjobs.com/jobsearch.asp?q={clean_title}&location={location}"
        elif domain == 'skill.jobs':
            return f"https://skill.jobs/search?q={clean_title}&location={location}"
        elif domain == 'shomvob.com':
            return f"https://shomvob.com/search?q={clean_title}&location={location}"
        elif domain == 'linkedin.com/jobs':
            return f"https://www.linkedin.com/jobs/search/?keywords={clean_title}&location={location}"
        elif domain == 'indeed.com/bd':
            return f"https://bd.indeed.com/jobs?q={clean_title}&l={location}"
        else:
            # Generic search URL
            return f"https://{domain}/search?q={clean_title}&location={location}"
    
    def _parse_html_content(self, html_content: str, domain: str, job_title: str) -> List[Dict]:
        """Parse HTML content from Web Scrapers API to extract job data"""
        jobs = []
        
        try:
            from bs4 import BeautifulSoup
            
            # Parse HTML content
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract job listings based on domain-specific selectors
            if domain == 'bdjobs.com':
                jobs = self._extract_bdjobs_jobs(soup, job_title)
            elif domain == 'skill.jobs':
                jobs = self._extract_skilljobs_jobs(soup, job_title)
            elif domain == 'linkedin.com/jobs':
                jobs = self._extract_linkedin_jobs(soup, job_title)
            elif domain == 'indeed.com/bd':
                jobs = self._extract_indeed_jobs(soup, job_title)
            else:
                # Generic extraction
                jobs = self._extract_generic_jobs(soup, job_title, domain)
                
        except Exception as e:
            logger.error(f"❌ Error parsing HTML content from {domain}: {e}")
        
        return jobs
    
    def _extract_bdjobs_jobs(self, soup, job_title: str) -> List[Dict]:
        """Extract jobs from BDJobs HTML"""
        jobs = []
        try:
            # Look for job containers
            job_containers = soup.find_all('div', class_=lambda x: x and 'job' in x.lower())
            
            for container in job_containers[:10]:  # Limit to 10 jobs
                title_elem = container.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if title and len(title) > 3:
                        job_data = {
                            'title': title,
                            'company': 'Company not specified',
                            'location': 'Location not specified',
                            'summary': f'Job posting for {title}',
                            'url': '',
                            'source': 'Bright Data (bdjobs.com)',
                            'field_presence': {
                                'title': True,
                                'company': False,
                                'location': False,
                                'summary': True,
                                'url': False
                            }
                        }
                        jobs.append(job_data)
        except Exception as e:
            logger.error(f"❌ Error extracting BDJobs jobs: {e}")
        
        return jobs
    
    def _extract_skilljobs_jobs(self, soup, job_title: str) -> List[Dict]:
        """Extract jobs from Skill.jobs HTML"""
        jobs = []
        try:
            # Look for job links or containers
            job_links = soup.find_all('a', href=True)
            
            for link in job_links[:10]:
                title = link.get_text(strip=True)
                if title and len(title) > 3 and any(keyword in title.lower() for keyword in ['engineer', 'developer', 'designer', 'manager']):
                    job_data = {
                        'title': title,
                        'company': 'Company not specified',
                        'location': 'Location not specified',
                        'summary': f'Job posting for {title}',
                        'url': link.get('href', ''),
                        'source': 'Bright Data (skill.jobs)',
                        'field_presence': {
                            'title': True,
                            'company': False,
                            'location': False,
                            'summary': True,
                            'url': bool(link.get('href'))
                        }
                    }
                    jobs.append(job_data)
        except Exception as e:
            logger.error(f"❌ Error extracting Skill.jobs jobs: {e}")
        
        return jobs
    
    def _extract_linkedin_jobs(self, soup, job_title: str) -> List[Dict]:
        """Extract jobs from LinkedIn HTML"""
        jobs = []
        try:
            # Look for job cards or listings
            job_cards = soup.find_all('div', class_=lambda x: x and any(word in x.lower() for word in ['job', 'card', 'listing']))
            
            for card in job_cards[:10]:
                title_elem = card.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if title and len(title) > 3:
                        job_data = {
                            'title': title,
                            'company': 'Company not specified',
                            'location': 'Location not specified',
                            'summary': f'Job posting for {title}',
                            'url': '',
                            'source': 'Bright Data (linkedin.com/jobs)',
                            'field_presence': {
                                'title': True,
                                'company': False,
                                'location': False,
                                'summary': True,
                                'url': False
                            }
                        }
                        jobs.append(job_data)
        except Exception as e:
            logger.error(f"❌ Error extracting LinkedIn jobs: {e}")
        
        return jobs
    
    def _extract_indeed_jobs(self, soup, job_title: str) -> List[Dict]:
        """Extract jobs from Indeed HTML"""
        jobs = []
        try:
            # Look for job containers
            job_containers = soup.find_all('div', class_=lambda x: x and 'job' in x.lower())
            
            for container in job_containers[:10]:
                title_elem = container.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if title and len(title) > 3:
                        job_data = {
                            'title': title,
                            'company': 'Company not specified',
                            'location': 'Location not specified',
                            'summary': f'Job posting for {title}',
                            'url': '',
                            'source': 'Bright Data (indeed.com/bd)',
                            'field_presence': {
                                'title': True,
                                'company': False,
                                'location': False,
                                'summary': True,
                                'url': False
                            }
                        }
                        jobs.append(job_data)
        except Exception as e:
            logger.error(f"❌ Error extracting Indeed jobs: {e}")
        
        return jobs
    
    def _extract_generic_jobs(self, soup, job_title: str, domain: str) -> List[Dict]:
        """Generic job extraction for unknown domains"""
        jobs = []
        try:
            # Look for any text that might be a job title
            all_text = soup.get_text()
            lines = all_text.split('\n')
            
            for line in lines[:20]:  # Check first 20 lines
                line = line.strip()
                if line and len(line) > 5 and len(line) < 100:
                    if any(keyword in line.lower() for keyword in ['engineer', 'developer', 'designer', 'manager', 'analyst']):
                        job_data = {
                            'title': line,
                            'company': 'Company not specified',
                            'location': 'Location not specified',
                            'summary': f'Job posting for {line}',
                            'url': '',
                            'source': f'Bright Data ({domain})',
                            'field_presence': {
                                'title': True,
                                'company': False,
                                'location': False,
                                'summary': True,
                                'url': False
                            }
                        }
                        jobs.append(job_data)
                        if len(jobs) >= 5:  # Limit to 5 jobs
                            break
        except Exception as e:
            logger.error(f"❌ Error extracting generic jobs from {domain}: {e}")
        
        return jobs
    
    def _extract_requirements(self, snippet: str) -> str:
        """Extract requirements from job snippet"""
        if not snippet:
            return "Requirements not specified"
        return snippet[:200] + "..." if len(snippet) > 200 else snippet
    
    def _extract_experience_level(self, title: str, snippet: str) -> str:
        """Extract experience level from title and snippet"""
        text = f"{title} {snippet}".lower()
        
        if any(word in text for word in ['senior', 'sr.', 'lead', 'head', 'manager', 'director']):
            return 'Senior'
        elif any(word in text for word in ['junior', 'jr.', 'entry', 'fresher', 'graduate']):
            return 'Junior'
        elif any(word in text for word in ['mid', 'intermediate', 'experienced']):
            return 'Mid-level'
        else:
            return 'Not specified'
    
    def _extract_job_type(self, title: str, snippet: str) -> str:
        """Extract job type from title and snippet"""
        text = f"{title} {snippet}".lower()
        
        if any(word in text for word in ['full-time', 'fulltime', 'permanent']):
            return 'Full-time'
        elif any(word in text for word in ['part-time', 'parttime']):
            return 'Part-time'
        elif any(word in text for word in ['contract', 'freelance', 'remote']):
            return 'Contract'
        else:
            return 'Not specified'
    
    def _remove_duplicates(self, jobs: List[Dict]) -> List[Dict]:
        """Remove duplicate jobs based on title and company"""
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            title = job.get('title', '').lower().strip()
            company = job.get('company', '').lower().strip()
            key = f"{title}|{company}"
            
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        return unique_jobs


class WebSearchDataSource:
    """Universal Web Search + LLM Data Source - Option 3"""
    
    def __init__(self):
        self.config = Config()
        if self.config.GEMINI_API_KEY:
            genai.configure(api_key=self.config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            logger.warning("⚠️ Gemini API key not configured for web search")
            self.model = None
        
        # User agent rotation for anti-detection
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
    
    def search(self, parsed_query: dict, target_domain: str, max_results: int = 5) -> List[Dict]:
        """
        Orchestrates the search, retrieval, and extraction for a target domain.
        """
        if not self.model:
            logger.warning("⚠️ Gemini model not available for web search")
            return []
        
        try:
            logger.info(f"🌐 Searching web for '{parsed_query.get('job_type', 'jobs')}' on {target_domain}")
            
            # Step 1: Construct Search Query
            search_query = self._construct_search_query(parsed_query, target_domain)
            
            # Step 2: Retrieve HTML
            html_content = self._get_html_from_search(search_query, max_results)
            if not html_content:
                return []
            
            # Step 3: Extract with Gemini
            extracted_jobs = self._extract_jobs_with_gemini(html_content, target_domain)
            
            # Step 4: Standardize and validate
            standardized_jobs = self._standardize_jobs(extracted_jobs, target_domain)
            
            logger.info(f"✅ Web search found {len(standardized_jobs)} jobs from {target_domain}")
            return standardized_jobs
            
        except Exception as e:
            logger.error(f"❌ Web search failed for {target_domain}: {e}")
            return []
    
    def _construct_search_query(self, parsed_query: dict, target_domain: str) -> str:
        """Construct a precise Google search query"""
        job_keywords = parsed_query.get('job_type', 'jobs')
        location = parsed_query.get('location', 'Bangladesh')
        
        # Enhanced search queries for specific job sites
        if target_domain == "linkedin.com/jobs":
            # LinkedIn specific search
            if location and location.lower() != 'bangladesh':
                search_query = f'"{job_keywords}" "{location}" Bangladesh site:linkedin.com/jobs'
            else:
                search_query = f'"{job_keywords}" Bangladesh site:linkedin.com/jobs'
        
        elif target_domain == "indeed.com/bd":
            # Indeed Bangladesh specific search
            if location and location.lower() != 'bangladesh':
                search_query = f'"{job_keywords}" "{location}" site:indeed.com/bd'
            else:
                search_query = f'"{job_keywords}" site:indeed.com/bd'
        
        elif target_domain in ["bdjobs.com", "skill.jobs", "shomvob.com"]:
            # Bangladesh job sites
            if location and location.lower() != 'bangladesh':
                search_query = f'"{job_keywords}" "{location}" site:{target_domain}'
            else:
                search_query = f'"{job_keywords}" site:{target_domain}'
        
        else:
            # Generic search for other sites
            if location and location.lower() != 'bangladesh':
                search_query = f'"{job_keywords}" "{location}" site:{target_domain}'
            else:
                search_query = f'"{job_keywords}" site:{target_domain}'
        
        logger.info(f"🔍 Generated web search query: {search_query}")
        return search_query
    
    def _get_html_from_search(self, search_query: str, max_results: int = 5) -> List[Dict]:
        """
        Executes a search and retrieves HTML from multiple results.
        Returns list of dicts with 'url' and 'html' keys.
        """
        try:
            import random
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # URL encode the search query
            encoded_query = quote_plus(search_query)
            google_url = f"https://www.google.com/search?q={encoded_query}&num={max_results}"
            
            logger.info(f"🔍 Searching Google: {google_url}")
            
            # Search Google
            response = requests.get(google_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find search result links (this selector may need updates)
            search_results = []
            
            # Try multiple selectors for Google search results
            selectors = [
                'div.g a[href^="http"]',
                'div.rc a[href^="http"]',
                'h3 a[href^="http"]',
                'a[href^="http"]'
            ]
            
            for selector in selectors:
                links = soup.select(selector)
                if links:
                    for link in links[:max_results]:
                        url = link.get('href', '')
                        if url and not url.startswith('https://www.google.com'):
                            search_results.append(url)
                    break
            
            if not search_results:
                logger.warning("⚠️ No search results found")
                return []
            
            # Get HTML from each result
            html_results = []
            for url in search_results[:max_results]:
                try:
                    logger.info(f"📄 Fetching: {url}")
                    page_response = requests.get(url, headers=headers, timeout=10)
                    page_response.raise_for_status()
                    
                    html_results.append({
                        'url': url,
                        'html': page_response.text
                    })
                    
                    # Rate limiting
                    time.sleep(1)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to fetch {url}: {e}")
                    continue
            
            return html_results
            
        except Exception as e:
            logger.error(f"❌ Error during web retrieval: {e}")
            return []
    
    def _extract_jobs_with_gemini(self, html_results: List[Dict], source_domain: str) -> List[Dict]:
        """Uses Gemini to extract structured job data from raw HTML"""
        all_jobs = []
        
        for result in html_results:
            try:
                # Truncate HTML to avoid token limits
                html_content = result['html'][:8000]  # Limit to 8k characters
                
                prompt = f"""
                You are an expert data extraction assistant for job listings. Parse the following HTML content from {source_domain} and extract all available job postings into a JSON array.

                IMPORTANT: Focus on extracting job listings. Look for job titles, company names, locations, and job descriptions.

                For each job object, extract these fields:
                - "title": The job title (required) - look for job titles, positions, roles
                - "company": The name of the company hiring - look for company names, employers
                - "location": The physical location of the job - look for cities, addresses, locations
                - "summary": A brief 1-2 sentence description of the job - look for job descriptions, responsibilities
                - "url": The direct URL to the job posting (if available) - look for apply links, job URLs
                - "salary": Salary information if mentioned - look for salary ranges, compensation
                - "requirements": Key requirements or qualifications - look for requirements, qualifications, skills
                - "experience_level": Junior/Mid/Senior if mentioned - look for experience levels
                - "job_type": Full-time/Part-time/Contract if mentioned - look for employment types

                SEARCH PATTERNS:
                - Job titles: Look for h1, h2, h3 tags, job-title classes, position titles
                - Company names: Look for company names, employer information
                - Locations: Look for location text, address information
                - Descriptions: Look for job descriptions, responsibilities, about sections

                If a field cannot be found, use null. Return ONLY a valid JSON array.
                If no jobs are found, return an empty array [].

                HTML Content to Parse:
                {html_content}
                """
                
                response = self.model.generate_content(prompt)
                
                # Parse JSON response
                try:
                    # Extract JSON from response
                    json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
                    if json_match:
                        jobs_data = json.loads(json_match.group())
                        if isinstance(jobs_data, list):
                            all_jobs.extend(jobs_data)
                    else:
                        logger.warning(f"⚠️ No JSON array found in Gemini response for {source_domain}")
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"⚠️ Failed to parse JSON from Gemini response: {e}")
                    continue
                    
            except Exception as e:
                logger.error(f"❌ Error during Gemini extraction for {source_domain}: {e}")
                continue
        
        return all_jobs
    
    def _standardize_jobs(self, jobs: List[Dict], source_domain: str) -> List[Dict]:
        """Standardize job data to match our format"""
        standardized_jobs = []
        
        for job in jobs:
            if not job.get('title'):  # Skip jobs without titles
                continue
                
            standardized_job = {
                'title': job.get('title', ''),
                'company': job.get('company', ''),
                'location': job.get('location', ''),
                'salary': job.get('salary', 'Salary not disclosed'),
                'summary': job.get('summary', 'Job description not available'),
                'url': job.get('url', ''),
                'date_posted': 'Date not specified',
                'requirements': job.get('requirements', 'Requirements not specified'),
                'deadline': 'Deadline not specified',
                'experience_level': job.get('experience_level', 'Experience level not specified'),
                'job_type': job.get('job_type', 'Job type not specified'),
                'source': source_domain,
                'field_presence': {
                    'title': bool(job.get('title')),
                    'company': bool(job.get('company')),
                    'location': bool(job.get('location')),
                    'salary': bool(job.get('salary')),
                    'summary': bool(job.get('summary')),
                    'url': bool(job.get('url')),
                    'date_posted': False
                }
            }
            
            standardized_jobs.append(standardized_job)
        
        return standardized_jobs


class APIScraperManager:
    """API and Scraper Manager - Orchestrates direct API access and manual scrapers"""
    
    def __init__(self):
        self.config = Config()
        self.linkedin_api = LinkedInJobsAPI()
        self.indeed_api = IndeedJobsAPI()
        self.web_search = WebSearchDataSource()
        self.brightdata_scraper = BrightDataScraper()  # New Bright Data scraper
        
        # Rate limiting
        self.request_delay = 1  # seconds between requests
        self.last_request_time = 0
    
    def search_all_apis(self, job_title: str, location: str = "", max_results: int = 30) -> List[Dict]:
        """Search all available APIs and scrapers"""
        logger.info(f"🚀 Starting API and scraper search for '{job_title}' in '{location}'")
        
        all_jobs = []
        
        # Search LinkedIn Jobs API (highest priority)
        try:
            linkedin_jobs = self.linkedin_api.search_jobs(job_title, location, max_results // 3)
            all_jobs.extend(linkedin_jobs)
            logger.info(f"✅ LinkedIn API returned {len(linkedin_jobs)} jobs")
        except Exception as e:
            logger.error(f"❌ LinkedIn API failed: {e}")
            # Fallback to LinkedIn fast scraper
            try:
                logger.info("🔄 Falling back to LinkedIn fast scraper...")
                linkedin_jobs = self.search_linkedin_fast(job_title, location, max_results // 3)
                all_jobs.extend(linkedin_jobs)
                logger.info(f"✅ LinkedIn fast scraper returned {len(linkedin_jobs)} jobs")
            except Exception as e2:
                logger.error(f"❌ LinkedIn fast scraper also failed: {e2}")
        
        # Rate limiting
        self._rate_limit()
        
        # Search Indeed API
        try:
            indeed_jobs = self.indeed_api.search_jobs(job_title, location, max_results // 3)
            all_jobs.extend(indeed_jobs)
            logger.info(f"✅ Indeed API returned {len(indeed_jobs)} jobs")
        except Exception as e:
            logger.error(f"❌ Indeed API failed: {e}")
        
        # Rate limiting
        self._rate_limit()
        
        # Search multiple job sites using Bright Data
        try:
            logger.info("🚀 Starting Bright Data scraper...")
            brightdata_jobs = self.brightdata_scraper.search_jobs(job_title, location, max_results // 2)
            all_jobs.extend(brightdata_jobs)
            logger.info(f"✅ Bright Data scraper returned {len(brightdata_jobs)} jobs")
            
        except Exception as e:
            logger.error(f"❌ Bright Data scraper failed: {e}")
        
        # Remove duplicates based on title and company
        unique_jobs = self._remove_duplicates(all_jobs)
        
        logger.info(f"🎉 API and scraper search completed: {len(unique_jobs)} unique jobs found")
        return unique_jobs[:max_results]
    
    def search_web_sources(self, parsed_query: dict, max_results: int = 20) -> List[Dict]:
        """Search extended web sources using web search + LLM"""
        logger.info(f"🌐 Starting web search for extended sources")
        
        all_web_jobs = []
        extended_sources = self.config.get_extended_sources()
        
        for domain in extended_sources:
            try:
                logger.info(f"🔍 Searching extended source: {domain}")
                jobs = self.web_search.search(parsed_query, domain, max_results=3)
                if jobs:
                    all_web_jobs.extend(jobs)
                    logger.info(f"✅ Found {len(jobs)} jobs from {domain}")
                
                # Rate limiting between sources
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Web search failed for {domain}: {e}")
                continue
        
        # Remove duplicates
        unique_web_jobs = self._remove_duplicates(all_web_jobs)
        
        logger.info(f"🎉 Web search completed: {len(unique_web_jobs)} unique jobs found")
        return unique_web_jobs[:max_results]
    
    def _rate_limit(self):
        """Implement rate limiting between API requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _remove_duplicates(self, jobs: List[Dict]) -> List[Dict]:
        """Remove duplicate jobs based on title and company"""
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            # Create a unique identifier
            identifier = f"{job.get('title', '').lower()}_{job.get('company', '').lower()}"
            
            if identifier not in seen:
                seen.add(identifier)
                unique_jobs.append(job)
        
        return unique_jobs
    
    def search_linkedin_fast(self, job_title: str, location: str = "Bangladesh", max_results: int = 10) -> List[Dict]:
        """Search LinkedIn using our fast scraper (no API key needed)"""
        if not LinkedInFastScraper:
            logger.warning("LinkedInFastScraper not available")
            return []
        
        try:
            logger.info(f"🔍 Searching LinkedIn with fast scraper for '{job_title}' in '{location}'")
            
            scraper = LinkedInFastScraper()
            jobs = scraper.get_jobs(job_title, location, max_results)
            
            # Convert to standard format
            formatted_jobs = []
            for job in jobs:
                formatted_job = {
                    'title': job.get('title', ''),
                    'company': job.get('company', ''),
                    'location': job.get('location', ''),
                    'summary': job.get('summary', f"Job posting for {job.get('title', '')}"),
                    'url': job.get('url', ''),
                    'source': 'LinkedIn (Fast Scraper)',
                    'scraped_at': job.get('scraped_at', ''),
                    'field_presence': {
                        'title': bool(job.get('title')),
                        'company': bool(job.get('company')),
                        'location': bool(job.get('location')),
                        'summary': bool(job.get('summary')),
                        'url': bool(job.get('url'))
                    }
                }
                formatted_jobs.append(formatted_job)
            
            logger.info(f"✅ Found {len(formatted_jobs)} jobs via LinkedIn fast scraper")
            return formatted_jobs
            
        except Exception as e:
            logger.error(f"❌ LinkedIn fast scraper failed: {e}")
            return []
    
    def search_bdjobs_fast(self, job_title: str, location: str = "Bangladesh", max_results: int = 10) -> List[Dict]:
        """Search BDJobs using our fast scraper"""
        if not BDJobsFastScraper:
            logger.warning("BDJobsFastScraper not available")
            return []
        
        try:
            logger.info(f"🔍 Searching BDJobs with fast scraper for '{job_title}' in '{location}'")
            
            scraper = BDJobsFastScraper()
            jobs = scraper.get_jobs(job_title, location, max_results)
            
            # Convert to standard format
            formatted_jobs = []
            for job in jobs:
                formatted_job = {
                    'title': job.get('title', ''),
                    'company': job.get('company', ''),
                    'location': job.get('location', ''),
                    'summary': job.get('summary', f"Job posting for {job.get('title', '')}"),
                    'url': job.get('url', ''),
                    'source': 'BDJobs (Fast Scraper)',
                    'scraped_at': job.get('scraped_at', ''),
                    'field_presence': {
                        'title': bool(job.get('title')),
                        'company': bool(job.get('company')),
                        'location': bool(job.get('location')),
                        'summary': bool(job.get('summary')),
                        'url': bool(job.get('url'))
                    }
                }
                formatted_jobs.append(formatted_job)
            
            logger.info(f"✅ Found {len(formatted_jobs)} jobs via BDJobs fast scraper")
            return formatted_jobs
            
        except Exception as e:
            logger.error(f"❌ BDJobs fast scraper failed: {e}")
            return []

    def get_api_status(self) -> Dict[str, bool]:
        """Check which APIs are available and configured"""
        status = {
            'linkedin': bool(self.config.LINKEDIN_API_KEY),
            'indeed': bool(self.config.INDEED_API_KEY and self.config.INDEED_PUBLISHER_ID),
            'web_search': bool(self.config.GEMINI_API_KEY),
            'brightdata': bool(self.config.BRIGHTDATA_API_KEY),  # New Bright Data status
            'bdjobs': bool(self.config.BDJOBS_API_KEY),
            'skilljobs': bool(self.config.SKILLJOBS_API_KEY),
            'shomvob': bool(self.config.SHOMVOB_API_KEY),
            'linkedin_fast': bool(LinkedInFastScraper),
            'bdjobs_fast': bool(BDJobsFastScraper)
        }
        
        return status


def test_api_data_sources():
    """Test the API data sources"""
    manager = APIDataSourceManager()
    
    # Check API status
    status = manager.get_api_status()
    print("🔍 API Status:")
    for api, available in status.items():
        print(f"  {api}: {'✅ Available' if available else '❌ Not configured'}")
    
    # Test API search
    if any([status['linkedin'], status['indeed']]):
        print("\n🔍 Testing API search...")
        jobs = manager.search_all_apis("Software Engineer", "Dhaka", max_results=10)
        
        if jobs:
            print(f"\n🎉 Found {len(jobs)} jobs via APIs:")
            for i, job in enumerate(jobs[:3], 1):  # Show first 3
                print(f"\n{i}. {job['title']}")
                print(f"   Company: {job['company']}")
                print(f"   Location: {job['location']}")
                print(f"   Source: {job['source']}")
        else:
            print("❌ No jobs found via APIs")
    
    # Test web search
    if status['web_search']:
        print("\n🌐 Testing web search...")
        parsed_query = {
            'job_type': 'Software Engineer',
            'location': 'Dhaka',
            'search_query': 'Software Engineer jobs Dhaka Bangladesh'
        }
        
        web_jobs = manager.search_web_sources(parsed_query, max_results=10)
        
        if web_jobs:
            print(f"\n🎉 Found {len(web_jobs)} jobs via web search:")
            for i, job in enumerate(web_jobs[:3], 1):  # Show first 3
                print(f"\n{i}. {job['title']}")
                print(f"   Company: {job['company']}")
                print(f"   Location: {job['location']}")
                print(f"   Source: {job['source']}")
        else:
            print("❌ No jobs found via web search")
    
    if not any(status.values()):
        print("\n⚠️ No APIs configured. Please add API keys to .env file")


if __name__ == "__main__":
    test_api_data_sources()
