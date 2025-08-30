import requests
import time
import pandas as pd
from bs4 import BeautifulSoup
import urllib.parse
import re
import json
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class LinkedInFastScraper:
    """
    Fast LinkedIn job scraper that works without login or browser windows.
    Scrapes LinkedIn's public job search results using requests + BeautifulSoup.
    """
    
    def __init__(self):
        """Initialize the LinkedIn scraper"""
        self.session = requests.Session()
        self.base_url = "https://www.linkedin.com/jobs/search"
        
        # Set up headers to mimic a real browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        self.session.headers.update(self.headers)
    
    def search_jobs(self, job_title: str, location: str = "Bangladesh", max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search for jobs on LinkedIn using public search results.
        
        Args:
            job_title: Job title to search for
            location: Location to search in (default: Bangladesh)
            max_results: Maximum number of results to return
            
        Returns:
            List of job dictionaries
        """
        try:
            logger.info(f"Searching LinkedIn for '{job_title}' jobs in '{location}'")
            
            # Encode search parameters
            job_title_encoded = urllib.parse.quote_plus(job_title)
            location_encoded = urllib.parse.quote_plus(location)
            
            # Construct search URL
            search_url = f"{self.base_url}/?keywords={job_title_encoded}&location={location_encoded}&f_TPR=r86400"  # Last 24 hours
            
            logger.info(f"Searching URL: {search_url}")
            
            # Make the request
            response = self.session.get(search_url, timeout=30)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract job listings
            jobs = self._extract_jobs_from_html(soup, max_results)
            
            logger.info(f"Found {len(jobs)} jobs on LinkedIn")
            return jobs
            
        except requests.RequestException as e:
            logger.error(f"Request error while searching LinkedIn: {e}")
            return []
        except Exception as e:
            logger.error(f"Error searching LinkedIn jobs: {e}")
            return []
    
    def _extract_jobs_from_html(self, soup: BeautifulSoup, max_results: int) -> List[Dict[str, Any]]:
        """
        Extract job listings from LinkedIn HTML.
        
        Args:
            soup: BeautifulSoup object of the page
            max_results: Maximum number of results to extract
            
        Returns:
            List of job dictionaries
        """
        jobs = []
        
        try:
            # Look for job cards in the search results
            # LinkedIn uses different selectors, let's try multiple approaches
            job_selectors = [
                'div[data-job-id]',  # Job cards with data-job-id attribute
                '.job-search-card',   # Common job card class
                '.job-result-card',   # Alternative job card class
                'li.job-result-card', # List item job cards
                '.base-card',         # Base card class
                '[data-entity-urn*="fsd_jobPosting"]'  # Job posting entities
            ]
            
            job_elements = []
            for selector in job_selectors:
                job_elements = soup.select(selector)
                if job_elements:
                    logger.info(f"Found {len(job_elements)} job elements using selector: {selector}")
                    break
            
            if not job_elements:
                # Fallback: look for any elements that might contain job data
                logger.warning("No job elements found with standard selectors, trying fallback approach")
                job_elements = soup.find_all(['div', 'li'], class_=re.compile(r'job|card|result', re.I))
            
            for i, job_element in enumerate(job_elements[:max_results]):
                try:
                    job_data = self._extract_job_data(job_element)
                    if job_data and job_data.get('title'):
                        jobs.append(job_data)
                        logger.debug(f"Extracted job {i+1}: {job_data['title']}")
                except Exception as e:
                    logger.warning(f"Error extracting job {i+1}: {e}")
                    continue
            
            # If we still don't have jobs, try to extract from JSON-LD structured data
            if not jobs:
                jobs = self._extract_jobs_from_json_ld(soup, max_results)
            
        except Exception as e:
            logger.error(f"Error extracting jobs from HTML: {e}")
        
        return jobs
    
    def _extract_job_data(self, job_element) -> Optional[Dict[str, Any]]:
        """
        Extract job data from a single job element.
        
        Args:
            job_element: BeautifulSoup element containing job data
            
        Returns:
            Job dictionary or None if extraction fails
        """
        try:
            job_data = {}
            
            # Extract job title
            title_selectors = [
                'h3.base-search-card__title',
                '.job-result-card__title',
                '.job-search-card__title',
                'h3',
                '.title',
                '[data-test-job-card-title]'
            ]
            
            for selector in title_selectors:
                title_elem = job_element.select_one(selector)
                if title_elem:
                    job_data['title'] = title_elem.get_text(strip=True)
                    break
            
            # Extract company name
            company_selectors = [
                '.job-result-card__subtitle',
                '.job-search-card__subtitle',
                '.base-search-card__subtitle',
                '.company-name',
                '[data-test-job-card-company-name]'
            ]
            
            for selector in company_selectors:
                company_elem = job_element.select_one(selector)
                if company_elem:
                    job_data['company'] = company_elem.get_text(strip=True)
                    break
            
            # Extract location
            location_selectors = [
                '.job-result-card__location',
                '.job-search-card__location',
                '.base-search-card__metadata',
                '.location',
                '[data-test-job-card-location]'
            ]
            
            for selector in location_selectors:
                location_elem = job_element.select_one(selector)
                if location_elem:
                    job_data['location'] = location_elem.get_text(strip=True)
                    break
            
            # Extract job URL
            url_selectors = [
                'a[href*="/jobs/view/"]',
                'a[href*="/jobs/"]',
                'a.base-card__full-link',
                'a.job-result-card__full-link'
            ]
            
            for selector in url_selectors:
                url_elem = job_element.select_one(selector)
                if url_elem:
                    href = url_elem.get('href')
                    if href:
                        if href.startswith('/'):
                            job_data['url'] = f"https://www.linkedin.com{href}"
                        else:
                            job_data['url'] = href
                    break
            
            # Extract job ID from URL or data attributes
            if 'url' in job_data:
                job_id_match = re.search(r'/jobs/view/(\d+)/', job_data['url'])
                if job_id_match:
                    job_data['job_id'] = job_id_match.group(1)
            
            # Extract from data attributes
            job_id = job_element.get('data-job-id') or job_element.get('data-entity-urn')
            if job_id:
                job_data['job_id'] = job_id
            
            # Add source information
            job_data['source'] = 'LinkedIn'
            job_data['scraped_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
            
            return job_data if job_data.get('title') else None
            
        except Exception as e:
            logger.warning(f"Error extracting job data: {e}")
            return None
    
    def _extract_jobs_from_json_ld(self, soup: BeautifulSoup, max_results: int) -> List[Dict[str, Any]]:
        """
        Extract job data from JSON-LD structured data if available.
        
        Args:
            soup: BeautifulSoup object of the page
            max_results: Maximum number of results to extract
            
        Returns:
            List of job dictionaries
        """
        jobs = []
        
        try:
            # Look for JSON-LD scripts
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            
            for script in json_ld_scripts:
                try:
                    data = json.loads(script.string)
                    
                    # Handle different JSON-LD structures
                    if isinstance(data, dict):
                        if data.get('@type') == 'JobPosting':
                            job_data = self._parse_json_ld_job(data)
                            if job_data:
                                jobs.append(job_data)
                        elif data.get('@type') == 'ItemList' and 'itemListElement' in data:
                            for item in data['itemListElement']:
                                if item.get('@type') == 'JobPosting':
                                    job_data = self._parse_json_ld_job(item)
                                    if job_data:
                                        jobs.append(job_data)
                                        if len(jobs) >= max_results:
                                            break
                    
                    elif isinstance(data, list):
                        for item in data:
                            if item.get('@type') == 'JobPosting':
                                job_data = self._parse_json_ld_job(item)
                                if job_data:
                                    jobs.append(job_data)
                                    if len(jobs) >= max_results:
                                        break
                
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    logger.warning(f"Error parsing JSON-LD: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error extracting jobs from JSON-LD: {e}")
        
        return jobs
    
    def _parse_json_ld_job(self, job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse a single job from JSON-LD data.
        
        Args:
            job_data: Job data from JSON-LD
            
        Returns:
            Job dictionary or None if parsing fails
        """
        try:
            job = {
                'title': job_data.get('title', ''),
                'company': job_data.get('hiringOrganization', {}).get('name', ''),
                'location': job_data.get('jobLocation', {}).get('addressLocality', ''),
                'url': job_data.get('url', ''),
                'source': 'LinkedIn',
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Extract job ID from URL
            if job['url']:
                job_id_match = re.search(r'/jobs/view/(\d+)/', job['url'])
                if job_id_match:
                    job['job_id'] = job_id_match.group(1)
            
            return job if job['title'] else None
            
        except Exception as e:
            logger.warning(f"Error parsing JSON-LD job: {e}")
            return None
    
    def get_jobs(self, job_title: str, location: str = "Bangladesh", max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Main method to get jobs from LinkedIn.
        
        Args:
            job_title: Job title to search for
            location: Location to search in
            max_results: Maximum number of results to return
            
        Returns:
            List of job dictionaries
        """
        logger.info(f"Starting LinkedIn job search for '{job_title}' in '{location}'")
        
        jobs = self.search_jobs(job_title, location, max_results)
        
        if jobs:
            logger.info(f"Successfully found {len(jobs)} jobs on LinkedIn")
            # Save to CSV for debugging
            df = pd.DataFrame(jobs)
            df.to_csv("linkedin_jobs_fast.csv", index=False)
            logger.info("Saved LinkedIn jobs to linkedin_jobs_fast.csv")
        else:
            logger.warning("No jobs found on LinkedIn")
        
        return jobs

# Test the scraper
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Test the scraper
    scraper = LinkedInFastScraper()
    jobs = scraper.get_jobs("Graphic Designer", "Bangladesh", 5)
    
    print(f"\n🎉 Found {len(jobs)} jobs on LinkedIn:")
    for i, job in enumerate(jobs, 1):
        print(f"\n{i}. {job.get('title', 'N/A')}")
        print(f"   Company: {job.get('company', 'N/A')}")
        print(f"   Location: {job.get('location', 'N/A')}")
        print(f"   URL: {job.get('url', 'N/A')}")
