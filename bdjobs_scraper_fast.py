"""
Fast BDJobs Scraper - Optimized for Speed
Uses requests + BeautifulSoup instead of Selenium for 10x faster performance
"""

import requests
import time
import random
import re
from urllib.parse import urlencode, urljoin
from typing import List, Dict, Optional
import logging
from bs4 import BeautifulSoup
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BDJobsFastScraper:
    """Fast BDJobs.com job scraper using requests + BeautifulSoup"""
    
    def __init__(self):
        self.base_url = "https://jobs.bdjobs.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.timeout = 10
        
    def build_search_url(self, job_title: str, location: str = "") -> str:
        """Build search URL for BDJobs"""
        # Clean and format the job title for better search results
        clean_title = job_title.strip().replace(' ', '+')
        
        # Try different BDJobs URL formats
        # Format 1: Standard search
        params = {
            'q': clean_title,
            'location': location if location else 'Bangladesh',
            'sort': 'date'  # Sort by date to get latest jobs
        }
        
        search_url = f"{self.base_url}/jobsearch.asp?{urlencode(params)}"
        logger.info(f"🔍 Built search URL: {search_url}")
        return search_url
    
    def search_jobs(self, job_title: str, location: str = "", max_results: int = 10) -> List[Dict]:
        """Fast job search using requests + BeautifulSoup"""
        return self.get_jobs(job_title, location, max_results)
    
    def get_jobs(self, job_title: str, location: str = "", max_results: int = 10) -> List[Dict]:
        """Fast job search using requests + BeautifulSoup"""
        logger.info(f"🚀 Fast BDJobs search for '{job_title}' in '{location}'")
        
        try:
            # Build search URL
            search_url = self.build_search_url(job_title, location)
            logger.info(f"🔍 Searching: {search_url}")
            
            # Make request with better headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
            
            start_time = time.time()
            response = self.session.get(search_url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            # Check if we got a proper response
            if len(response.text) < 1000:
                logger.warning(f"⚠️ Response too short ({len(response.text)} chars), might be an error page")
                return []
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check if we got search results or an error page
            page_title = soup.find('title')
            if page_title:
                page_title_text = page_title.get_text().lower()
                if 'error' in page_title_text or 'not found' in page_title_text:
                    logger.warning(f"⚠️ Got error page: {page_title_text}")
                    return []
            
            # Extract job listings
            jobs = self._extract_jobs_from_html(soup, max_results)
            
            # Filter jobs to ensure they match the search title
            filtered_jobs = self._filter_jobs_by_title(jobs, job_title)
            
            processing_time = time.time() - start_time
            logger.info(f"✅ Fast BDJobs search completed in {processing_time:.2f}s - Found {len(filtered_jobs)} matching jobs out of {len(jobs)} total")
            
            return filtered_jobs
            
        except Exception as e:
            logger.error(f"❌ Fast BDJobs search failed: {e}")
            return []
    
    def _extract_jobs_from_html(self, soup: BeautifulSoup, max_results: int) -> List[Dict]:
        """Extract job listings from HTML using BeautifulSoup"""
        jobs = []
        
        try:
            # BDJobs specific selectors - look for job listing containers
            job_containers = []
            
            # Try multiple BDJobs-specific selectors
            selectors_to_try = [
                'div.job-list-item',
                'div.job-item',
                'div.job-listing',
                'div.search-result-item',
                'div.job-search-result',
                'table.job-list tr',
                'div[class*="job"]',
                'div[class*="listing"]',
                'div[class*="result"]'
            ]
            
            for selector in selectors_to_try:
                containers = soup.select(selector)
                if containers:
                    job_containers = containers
                    logger.info(f"✅ Found {len(containers)} job containers using selector: {selector}")
                    break
            
            # If no specific containers found, try a more general approach
            if not job_containers:
                # Look for any div that contains job-related text
                all_divs = soup.find_all('div')
                for div in all_divs:
                    div_text = div.get_text().lower()
                    if any(keyword in div_text for keyword in ['job', 'position', 'vacancy', 'career', 'employment']):
                        if div.find('a'):  # Must have a link
                            job_containers.append(div)
            
            logger.info(f"🔍 Found {len(job_containers)} potential job containers")
            
            for container in job_containers[:max_results * 2]:  # Check more containers
                try:
                    job = self._extract_single_job(container)
                    if job and self._validate_job(job):
                        jobs.append(job)
                        if len(jobs) >= max_results:
                            break
                except Exception as e:
                    logger.debug(f"⚠️ Error extracting job from container: {e}")
                    continue
            
            # If no jobs found with containers, try extracting from links
            if not jobs:
                logger.info("🔄 Trying link-based extraction method...")
                jobs = self._extract_jobs_from_links(soup, max_results)
            
            return jobs
            
        except Exception as e:
            logger.error(f"❌ Job extraction failed: {e}")
            return []

    def _extract_jobs_from_links(self, soup: BeautifulSoup, max_results: int) -> List[Dict]:
        """Extract jobs by looking for job-related links"""
        jobs = []
        try:
            # Look for links that might be job listings
            links = soup.find_all('a', href=True)
            
            for link in links:
                try:
                    href = link.get('href', '').lower()
                    link_text = link.get_text(strip=True)
                    
                    # Check if this looks like a job link
                    is_job_link = (
                        'job' in href or 
                        'detail' in href or 
                        'career' in href or
                        'position' in href or
                        'vacancy' in href
                    )
                    
                    # Check if link text looks like a job title
                    is_job_title = (
                        len(link_text) > 5 and 
                        len(link_text) < 100 and
                        any(keyword in link_text.lower() for keyword in [
                            'engineer', 'developer', 'designer', 'manager', 'analyst', 
                            'specialist', 'coordinator', 'assistant', 'officer', 'executive'
                        ])
                    )
                    
                    if is_job_link or is_job_title:
                        # Try to extract company from nearby text
                        company = self._extract_company_from_context(link)
                        
                        job = {
                            'title': link_text,
                            'company': company or 'Company not specified',
                            'location': 'Location not specified',
                            'summary': f'Job posting for {link_text}',
                            'url': urljoin(self.base_url, link.get('href')) if not link.get('href').startswith('http') else link.get('href'),
                            'salary': None,
                            'requirements': [],
                            'source': 'BDJobs Fast Scraper (Link)',
                            'quality_score': 0.6
                        }
                        
                        if self._validate_job(job):
                            jobs.append(job)
                            if len(jobs) >= max_results:
                                break
                                
                except Exception as e:
                    logger.debug(f"⚠️ Error processing link: {e}")
                    continue
            
            return jobs
            
        except Exception as e:
            logger.error(f"❌ Link-based extraction failed: {e}")
            return []

    def _extract_company_from_context(self, link_element) -> str:
        """Extract company name from the context around a job link"""
        try:
            # Look for company name in nearby elements
            parent = link_element.parent
            if parent:
                # Look for company-related text in parent
                parent_text = parent.get_text()
                company_patterns = [
                    r'at\s+([A-Z][a-zA-Z\s&]+(?:Ltd|Limited|Corp|Corporation|Inc|Company))',
                    r'([A-Z][a-zA-Z\s&]+(?:Ltd|Limited|Corp|Corporation|Inc|Company))',
                    r'Company:\s*([A-Z][a-zA-Z\s&]+)',
                    r'Employer:\s*([A-Z][a-zA-Z\s&]+)'
                ]
                
                for pattern in company_patterns:
                    import re
                    match = re.search(pattern, parent_text)
                    if match:
                        return match.group(1).strip()
            
            # Look in sibling elements
            siblings = link_element.find_next_siblings()
            for sibling in siblings[:3]:  # Check first 3 siblings
                sibling_text = sibling.get_text()
                if any(keyword in sibling_text.lower() for keyword in ['ltd', 'limited', 'corp', 'company']):
                    # Extract potential company name
                    words = sibling_text.split()
                    for i, word in enumerate(words):
                        if any(keyword in word.lower() for keyword in ['ltd', 'limited', 'corp', 'company']):
                            if i > 0:
                                return ' '.join(words[max(0, i-2):i+1])
            
            return None
            
        except Exception:
            return None
    
    def _extract_single_job(self, container) -> Optional[Dict]:
        """Extract a single job from a container element"""
        try:
            # Extract job title
            title = self._extract_text(container, [
                'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                '.job-title', '.title', '.position',
                '[class*="title"]', '[class*="position"]'
            ])
            
            if not title:
                return None
            
            # Extract company name
            company = self._extract_text(container, [
                '.company', '.employer', '.organization',
                '[class*="company"]', '[class*="employer"]'
            ]) or "Company not specified"
            
            # Extract location
            location = self._extract_text(container, [
                '.location', '.place', '.city',
                '[class*="location"]', '[class*="place"]'
            ]) or "Location not specified"
            
            # Extract job URL
            job_url = self._extract_url(container)
            
            # Extract summary/description
            summary = self._extract_text(container, [
                '.description', '.summary', '.details',
                '[class*="description"]', '[class*="summary"]'
            ]) or f"Job posting for {title}"
            
            # Extract salary
            salary = self._extract_text(container, [
                '.salary', '.compensation', '.pay',
                '[class*="salary"]', '[class*="pay"]'
            ])
            
            # Extract requirements
            requirements = self._extract_requirements(container)
            
            return {
                'title': title.strip(),
                'company': company.strip(),
                'location': location.strip(),
                'summary': summary.strip(),
                'url': job_url,
                'salary': salary.strip() if salary else None,
                'requirements': requirements,
                'source': 'BDJobs Fast Scraper',
                'quality_score': 0.8
            }
            
        except Exception as e:
            logger.debug(f"⚠️ Error in single job extraction: {e}")
            return None
    
    def _extract_text(self, container, selectors: List[str]) -> Optional[str]:
        """Extract text using multiple selectors"""
        for selector in selectors:
            try:
                element = container.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    if text and len(text) > 2:
                        return text
            except Exception:
                continue
        return None
    
    def _extract_url(self, container) -> str:
        """Extract job URL from container"""
        try:
            # Look for links
            links = container.find_all('a', href=True)
            for link in links:
                href = link.get('href')
                if href and ('job' in href.lower() or 'detail' in href.lower()):
                    if href.startswith('http'):
                        return href
                    else:
                        return urljoin(self.base_url, href)
            
            # If no job-specific link found, return base URL
            return self.base_url
            
        except Exception:
            return self.base_url
    
    def _extract_requirements(self, container) -> List[str]:
        """Extract job requirements"""
        requirements = []
        try:
            # Look for requirement lists
            req_elements = container.find_all(['li', 'p'], string=re.compile(r'experience|skill|requirement', re.I))
            for elem in req_elements:
                text = elem.get_text(strip=True)
                if text and len(text) > 10:
                    requirements.append(text)
            
            return requirements[:5]  # Limit to 5 requirements
            
        except Exception:
            return []
    
    def _direct_extraction(self, soup: BeautifulSoup, max_results: int) -> List[Dict]:
        """Direct extraction when container method fails"""
        jobs = []
        try:
            # Instead of creating fake jobs, try to find actual job listings
            # Look for job-related links and extract from them
            job_links = soup.find_all('a', href=True)
            
            for link in job_links[:max_results * 2]:  # Check more links to find valid jobs
                try:
                    href = link.get('href')
                    if href and ('job' in href.lower() or 'detail' in href.lower()):
                        # Extract job title from link text
                        title = link.get_text(strip=True)
                        if title and len(title) > 5 and len(title) < 100:
                            # Check if this looks like a job title
                            if any(keyword in title.lower() for keyword in ['engineer', 'developer', 'designer', 'manager', 'analyst', 'specialist', 'coordinator', 'assistant', 'officer']):
                                job = {
                                    'title': title,
                                    'company': 'Company not specified',
                                    'location': 'Location not specified',
                                    'summary': f'Job posting for {title}',
                                    'url': urljoin(self.base_url, href) if not href.startswith('http') else href,
                                    'salary': None,
                                    'requirements': [],
                                    'source': 'BDJobs Fast Scraper (Direct)',
                                    'quality_score': 0.5
                                }
                                jobs.append(job)
                                
                                if len(jobs) >= max_results:
                                    break
                except Exception as e:
                    logger.debug(f"⚠️ Error processing link: {e}")
                    continue
            
            return jobs
            
        except Exception as e:
            logger.error(f"❌ Direct extraction failed: {e}")
            return []

    def _validate_job(self, job: Dict) -> bool:
        """Validate job data and ensure it matches the search criteria"""
        required_fields = ['title', 'company', 'location', 'summary']
        
        # Check if all required fields are present
        if not all(job.get(field) for field in required_fields):
            return False
        
        # Additional validation: ensure title is not too generic
        title = job.get('title', '').lower()
        if len(title) < 3 or title in ['job', 'position', 'vacancy', 'opportunity']:
            return False
        
        return True

    def _filter_jobs_by_title(self, jobs: List[Dict], search_title: str) -> List[Dict]:
        """Filter jobs to ensure they match the search title"""
        if not search_title or not jobs:
            return jobs
        
        search_title_lower = search_title.lower()
        filtered_jobs = []
        
        for job in jobs:
            job_title = job.get('title', '').lower()
            
            # Check if the job title contains the search terms
            search_terms = search_title_lower.split()
            title_terms = job_title.split()
            
            # Calculate similarity score
            matching_terms = sum(1 for term in search_terms if any(term in title_term for title_term in title_terms))
            similarity_score = matching_terms / len(search_terms) if search_terms else 0
            
            # More lenient filtering - accept jobs with at least 30% term similarity
            # or if any major keyword matches (engineer, developer, designer, etc.)
            major_keywords = ['engineer', 'developer', 'designer', 'manager', 'analyst', 'specialist', 'coordinator']
            has_major_keyword = any(keyword in job_title for keyword in major_keywords)
            
            if similarity_score >= 0.3 or has_major_keyword:
                filtered_jobs.append(job)
                logger.debug(f"✅ Job '{job.get('title')}' matches search '{search_title}' (score: {similarity_score:.2f}, major_keyword: {has_major_keyword})")
            else:
                logger.debug(f"❌ Job '{job.get('title')}' doesn't match search '{search_title}' (score: {similarity_score:.2f})")
        
        logger.info(f"🔍 Filtered {len(jobs)} jobs to {len(filtered_jobs)} matching '{search_title}'")
        return filtered_jobs
    
    def close(self):
        """Close the session"""
        if self.session:
            self.session.close()

# Test the fast scraper
if __name__ == "__main__":
    scraper = BDJobsFastScraper()
    
    print("🧪 Testing Fast BDJobs Scraper...")
    print("=" * 50)
    
    # Test search
    jobs = scraper.search_jobs("software engineer", "Dhaka", max_results=5)
    
    print(f"✅ Found {len(jobs)} jobs")
    for i, job in enumerate(jobs, 1):
        print(f"\n{i}. {job['title']}")
        print(f"   Company: {job['company']}")
        print(f"   Location: {job['location']}")
        print(f"   URL: {job['url']}")
        print(f"   Quality Score: {job['quality_score']}")
    
    scraper.close()
    print("\n✅ Fast scraper test completed!")
