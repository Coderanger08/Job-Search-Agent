"""
Enhanced BDJobs Scraper - Job Search Agent Day 1
Scrapes real job data from BDJobs.com with improved data extraction
"""

import pandas as pd
import time
import random
import re
from urllib.parse import urlencode, urljoin
from typing import List, Dict, Optional
import logging

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
try:
    from fake_useragent import UserAgent
except ImportError:
    # Fallback UserAgent class if fake_useragent is not installed
    class UserAgent:
        def __init__(self):
            self.user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
        
        def random(self):
            import random
            return random.choice(self.user_agents)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BDJobsEnhancedScraper:
    """Enhanced BDJobs.com job scraper with better data extraction"""
    
    def __init__(self):
        self.base_url = "https://jobs.bdjobs.com"
        self.driver = None
        self.ua = UserAgent()
        
    def setup_driver(self):
        """Setup Chrome WebDriver with optimized options for BDJobs"""
        if self.driver:
            return
            
        logger.info("Setting up Chrome WebDriver for BDJobs...")
        
        # Chrome options optimized for BDJobs
        chrome_options = Options()
        chrome_options.add_argument(f"--user-agent={self.ua.random}")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")  # Faster loading
        
        # Run in visible mode to see what's happening
        # chrome_options.add_argument("--headless")  # Uncomment for headless mode
        
        # Setup service
        service = Service(ChromeDriverManager().install())
        
        try:
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(10)
            logger.info("✅ WebDriver setup successful for BDJobs")
        except Exception as e:
            logger.error(f"❌ WebDriver setup failed: {e}")
            # Try alternative setup methods
            try:
                logger.info("🔄 Trying alternative WebDriver setup...")
                self.driver = webdriver.Chrome(options=chrome_options)
                self.driver.implicitly_wait(10)
                logger.info("✅ Alternative WebDriver setup successful")
            except Exception as e2:
                logger.error(f"❌ Alternative WebDriver setup also failed: {e2}")
                raise Exception(f"WebDriver setup failed: {e}. Alternative method also failed: {e2}")
    
    def close_driver(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("WebDriver closed")
    
    def build_search_url(self, job_title: str, location: str = "") -> str:
        """Build BDJobs search URL with correct format"""
        # BDJobs actual search format: https://jobs.bdjobs.com/jobsearch.asp?fcatId=8&icatId=
        # Let's use a more reliable approach
        base_search_url = f"{self.base_url}/jobsearch.asp"
        
        # Build parameters based on BDJobs actual format
        params = {}
        
        # Add job title if provided
        if job_title and job_title.strip():
            params['q'] = job_title.strip()
        
        # Add location if provided
        if location and location.strip():
            params['loc'] = location.strip()
        
        # Add category ID for IT/Software jobs (fcatId=8 for IT/Software)
        if 'software' in job_title.lower() or 'developer' in job_title.lower() or 'programmer' in job_title.lower():
            params['fcatId'] = '8'  # IT/Software category
        
        # Remove empty parameters
        params = {k: v for k, v in params.items() if v}
        
        if params:
            url = f"{base_search_url}?" + urlencode(params)
        else:
            url = base_search_url
            
        logger.info(f"Built BDJobs URL: {url}")
        return url
    
    def navigate_to_page(self, url: str) -> bool:
        """Navigate to URL using WebDriver"""
        try:
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Random delay to avoid detection
            time.sleep(random.uniform(2, 4))
            return True
            
        except Exception as e:
            logger.error(f"❌ Navigation failed: {e}")
            return False
    
    def validate_job_title(self, title: str) -> bool:
        """Validate job title - filter out phone numbers, emails, etc. (supports Bengali)"""
        if not title or len(title.strip()) < 3:
            return False
            
        # Filter out phone numbers (including Bengali digits)
        if re.match(r'^[\d\s\+\-\(\)০-৯]+$', title.strip()):
            return False
            
        # Filter out email addresses
        if '@' in title and '.' in title:
            return False
            
        # Filter out very short titles (but allow Bengali titles)
        if len(title.strip()) < 3:  # Reduced minimum for Bengali
            return False
            
        # Allow Bengali characters and common job-related words
        bengali_job_words = [
            'কর্মকর্তা', 'কর্মচারী', 'ম্যানেজার', 'অফিসার', 'এক্সিকিউটিভ',
            'সহকারী', 'সিনিয়র', 'জুনিয়র', 'ডিজাইনার', 'ডেভেলপার',
            'অ্যাকাউন্ট্যান্ট', 'মার্কেটিং', 'সেলস', 'অ্যাডমিন', 'এইচআর'
        ]
        
        # Check if title contains Bengali job-related words
        if any(word in title for word in bengali_job_words):
            return True
            
        # Allow mixed Bengali-English titles
        return True
    
    def extract_experience_level(self, title: str, summary: str) -> str:
        """Extract experience level from job title and summary"""
        text = f"{title} {summary}".lower()
        
        if any(word in text for word in ['senior', 'sr.', 'lead', 'head', 'manager', 'director']):
            return "Senior"
        elif any(word in text for word in ['junior', 'jr.', 'entry', 'fresh', 'trainee']):
            return "Junior"
        elif any(word in text for word in ['mid', 'intermediate']):
            return "Mid-level"
        else:
            return "Experience level not specified"
    
    def extract_job_type(self, title: str, summary: str) -> str:
        """Extract job type from job title and summary"""
        text = f"{title} {summary}".lower()
        
        if any(word in text for word in ['part-time', 'part time', 'contract', 'freelance']):
            return "Part-time/Contract"
        elif any(word in text for word in ['full-time', 'full time', 'permanent']):
            return "Full-time"
        else:
            return "Job type not specified"
    
    def extract_deadline(self, summary: str) -> str:
        """Extract deadline from job summary"""
        # Look for date patterns in summary
        date_patterns = [
            r'deadline[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            r'apply by[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            r'last date[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{1,2}-\d{1,2}-\d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, summary, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "Deadline not specified"
    
    def extract_requirements(self, summary: str) -> str:
        """Extract requirements from job summary"""
        if not summary or summary == "Job description not available":
            return "Requirements not specified"
        
        # Look for requirements section
        req_patterns = [
            r'requirements?[:\s]+([^.]+)',
            r'qualifications?[:\s]+([^.]+)',
            r'skills?[:\s]+([^.]+)',
            r'experience[:\s]+([^.]+)'
        ]
        
        for pattern in req_patterns:
            match = re.search(pattern, summary, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # If no specific requirements found, return first sentence
        sentences = summary.split('.')
        if sentences:
            return sentences[0].strip()
        
        return "Requirements not specified"
    
    def extract_job_info(self, job_element) -> Optional[Dict]:
        """Extract enhanced job information from BDJobs job element with field presence tracking"""
        try:
            job_data = {
                'title': '',
                'company': '',
                'location': '',
                'salary': '',
                'summary': '',
                'url': '',
                'date_posted': '',
                'requirements': '',
                'deadline': '',
                'experience_level': '',
                'job_type': '',
                'field_presence': {}  # Track which fields were actually found
            }
            
            # Extract job title with multiple selector strategies
            title_selectors = [
                ".job-title", ".title", ".jobname", ".job-name",
                "h2", "h3", "a[href*='jobdetails']", ".job-link"
            ]
            
            for selector in title_selectors:
                try:
                    title_elem = job_element.find_element(By.CSS_SELECTOR, selector)
                    title = title_elem.text.strip()
                    if self.validate_job_title(title):
                        job_data['title'] = title
                        job_data['field_presence']['title'] = True
                        break
                except NoSuchElementException:
                    continue
            
            if not job_data['title']:
                return None
            
            # Extract job URL
            try:
                url_elem = job_element.find_element(By.CSS_SELECTOR, "a[href*='jobdetails']")
                job_data['url'] = url_elem.get_attribute('href')
                job_data['field_presence']['url'] = True
            except NoSuchElementException:
                job_data['url'] = ""
                job_data['field_presence']['url'] = False
            
            # Extract company name from onclick attribute (BDJobs specific)
            try:
                # Find the link with onclick attribute
                onclick_link = job_element.find_element(By.CSS_SELECTOR, "a[onclick*='clickJObTitle']")
                onclick_value = onclick_link.get_attribute('onclick')
                
                # Parse onclick to extract company name (third parameter)
                # Format: clickJObTitle(id,'title','company')
                if onclick_value and "clickJObTitle" in onclick_value:
                    # Extract the third parameter (company name)
                    parts = onclick_value.split("'")
                    if len(parts) >= 4:  # Should have at least 4 parts: clickJObTitle(, id, ', title, ', company, ')
                        company = parts[3].strip()  # 4th part (index 3) is the company name
                        if company and company != "Not specified" and len(company) > 2:
                            job_data['company'] = company
                            job_data['field_presence']['company'] = True
                        else:
                            job_data['company'] = "Unknown Company"
                            job_data['field_presence']['company'] = False
                    else:
                        job_data['company'] = "Unknown Company"
                        job_data['field_presence']['company'] = False
                else:
                    job_data['company'] = "Unknown Company"
                    job_data['field_presence']['company'] = False
            except NoSuchElementException:
                # Fallback to traditional selectors if onclick method fails
                company_selectors = [
                    ".company-name", ".companyname", ".org-name", ".employer",
                    ".company", ".org", ".employer-name", ".company-title"
                ]
                
                for selector in company_selectors:
                    try:
                        company_elem = job_element.find_element(By.CSS_SELECTOR, selector)
                        company = company_elem.text.strip()
                        if company and company != "Not specified" and len(company) > 2:
                            job_data['company'] = company
                            job_data['field_presence']['company'] = True
                            break
                    except NoSuchElementException:
                        continue
                
                if not job_data['company']:
                    job_data['company'] = "Unknown Company"
                    job_data['field_presence']['company'] = False
            
            # Extract location
            location_selectors = [
                ".location", ".job-location", ".loc", ".place",
                ".job-place", ".location-name"
            ]
            
            for selector in location_selectors:
                try:
                    location_elem = job_element.find_element(By.CSS_SELECTOR, selector)
                    job_data['location'] = location_elem.text.strip()
                    job_data['field_presence']['location'] = True
                    break
                except NoSuchElementException:
                    continue
            
            if not job_data['location']:
                job_data['location'] = "Bangladesh"
                job_data['field_presence']['location'] = False
            
            # Extract salary with enhanced selectors
            salary_selectors = [
                ".salary", ".sal", ".package", ".compensation",
                ".job-salary", ".salary-range"
            ]
            
            for selector in salary_selectors:
                try:
                    salary_elem = job_element.find_element(By.CSS_SELECTOR, selector)
                    salary = salary_elem.text.strip()
                    if salary and salary != "Not specified":
                        job_data['salary'] = salary
                        job_data['field_presence']['salary'] = True
                        break
                except NoSuchElementException:
                    continue
            
            if not job_data['salary']:
                job_data['salary'] = "Salary not disclosed"
                job_data['field_presence']['salary'] = False
            
            # Extract job description/summary with enhanced selectors
            summary_selectors = [
                ".job-description", ".desc", ".summary", ".job-summary",
                ".description", ".job-desc", ".details"
            ]
            
            for selector in summary_selectors:
                try:
                    desc_elem = job_element.find_element(By.CSS_SELECTOR, selector)
                    summary = desc_elem.text.strip()
                    if summary and summary != "No description available":
                        job_data['summary'] = summary
                        job_data['field_presence']['summary'] = True
                        break
                except NoSuchElementException:
                    continue
            
            if not job_data['summary']:
                job_data['summary'] = "Job description not available"
                job_data['field_presence']['summary'] = False
            
            # Extract posting date
            date_selectors = [
                ".date", ".posted-date", ".job-date", ".publish-date",
                ".date-posted", ".job-posted"
            ]
            
            for selector in date_selectors:
                try:
                    date_elem = job_element.find_element(By.CSS_SELECTOR, selector)
                    job_data['date_posted'] = date_elem.text.strip()
                    job_data['field_presence']['date_posted'] = True
                    break
                except NoSuchElementException:
                    continue
            
            if not job_data['date_posted']:
                job_data['date_posted'] = "Date not specified"
                job_data['field_presence']['date_posted'] = False
            
            # Extract deadline directly from job card elements
            deadline_selectors = [
                ".deadline", ".last-date", ".apply-by", ".closing-date",
                ".application-deadline", ".deadline-date", ".last-date-to-apply",
                "[class*='deadline']", "[class*='date']", ".calendar",
                "span[title*='deadline']", "span[title*='date']"
            ]
            
            for selector in deadline_selectors:
                try:
                    deadline_elem = job_element.find_element(By.CSS_SELECTOR, selector)
                    deadline_text = deadline_elem.text.strip()
                    # Check if it looks like a date
                    if re.search(r'\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}', deadline_text, re.IGNORECASE):
                        job_data['deadline'] = deadline_text
                        job_data['field_presence']['deadline'] = True
                        break
                except NoSuchElementException:
                    continue
            
            if not job_data['deadline']:
                # Fallback: try to extract from summary
                job_data['deadline'] = self.extract_deadline(job_data['summary'])
                job_data['field_presence']['deadline'] = job_data['deadline'] != "Deadline not specified"
            
            # Extract enhanced fields
            job_data['requirements'] = self.extract_requirements(job_data['summary'])
            job_data['field_presence']['requirements'] = job_data['requirements'] != "Requirements not specified"
            
            job_data['experience_level'] = self.extract_experience_level(job_data['title'], job_data['summary'])
            job_data['field_presence']['experience_level'] = job_data['experience_level'] != "Experience level not specified"
            
            job_data['job_type'] = self.extract_job_type(job_data['title'], job_data['summary'])
            job_data['field_presence']['job_type'] = job_data['job_type'] != "Job type not specified"
            
            return job_data
            
        except Exception as e:
            logger.error(f"Error extracting BDJobs job data: {e}")
            return None
    
    def search_jobs(self, job_title: str, location: str = "", max_jobs: int = 20) -> List[Dict]:
        """Search for jobs on BDJobs using enhanced extraction"""
        logger.info(f"🔍 Searching BDJobs for '{job_title}' in '{location}'")
        
        try:
            # Setup driver if not already done
            self.setup_driver()
            
            # Build URL and navigate
            url = self.build_search_url(job_title, location)
            if not self.navigate_to_page(url):
                return []
            
            # Wait for job results to load
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".job-list, .job-item, .joblist, [class*='job']"))
                )
            except TimeoutException:
                logger.warning("⚠️ BDJobs results took too long to load")
            
            # Find job containers with enhanced selector strategies
            job_containers = []
            selectors = [
                ".job-item",           # Common BDJobs format
                ".job-list-item",      # Alternative format
                ".joblist tr",         # Table format
                ".job",                # Generic job class
                "[class*='job-']",     # Any class containing 'job-'
                "tr[class*='job']",    # Table rows with job class
                ".job-result",         # Another possible format
                ".job-listing"         # Alternative format
            ]
            
            for selector in selectors:
                try:
                    containers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if containers:
                        job_containers = containers
                        logger.info(f"✅ Found {len(job_containers)} jobs on BDJobs using selector: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"BDJobs selector {selector} failed: {e}")
                    continue
            
            if not job_containers:
                logger.error("❌ No job containers found on BDJobs")
                return []
            
            # Extract job data with enhanced validation
            jobs = []
            for i, container in enumerate(job_containers[:max_jobs]):
                try:
                    job_data = self.extract_job_info(container)
                    if job_data and job_data.get('title') and self.validate_job_title(job_data['title']):
                        jobs.append(job_data)
                        logger.info(f"✅ Extracted BDJobs job {i+1}: {job_data['title']} at {job_data['company']}")
                        
                        # Save progress incrementally
                        if len(jobs) >= max_jobs:
                            break
                    else:
                        logger.debug(f"⚠️ Skipped BDJobs job {i+1}: Invalid data")
                        
                except Exception as e:
                    logger.error(f"❌ Error extracting BDJobs job {i+1}: {e}")
                    continue
                
                # Random delay between extractions
                time.sleep(random.uniform(0.5, 1.5))
            
            logger.info(f"🎉 Successfully extracted {len(jobs)} jobs from BDJobs")
            return jobs
            
        except Exception as e:
            logger.error(f"❌ BDJobs search failed: {e}")
            return []
        
        finally:
            # Don't close driver here - let it be reused
            pass

def test_bdjobs_enhanced_scraper():
    """Test the enhanced BDJobs scraper"""
    scraper = BDJobsEnhancedScraper()
    
    try:
        # Test with Software Engineer jobs
        jobs = scraper.search_jobs("Software Engineer", "Dhaka", max_jobs=5)
        
        if jobs:
            print(f"\n🎉 Found {len(jobs)} Software Engineer jobs on BDJobs:")
            for i, job in enumerate(jobs, 1):
                print(f"\n{i}. {job['title']}")
                print(f"   Company: {job['company']}")
                print(f"   Location: {job['location']}")
                print(f"   Salary: {job['salary']}")
                print(f"   Experience: {job['experience_level']}")
                print(f"   Job Type: {job['job_type']}")
                print(f"   Requirements: {job['requirements'][:100]}...")
                print(f"   Deadline: {job['deadline']}")
                print(f"   URL: {job['url']}")
            
            # Save to CSV for testing
            df = pd.DataFrame(jobs)
            df.to_csv('bdjobs_enhanced_test.csv', index=False)
            print(f"\n✅ Saved {len(jobs)} jobs to 'bdjobs_enhanced_test.csv'")
        else:
            print("❌ No jobs found")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        scraper.close_driver()

if __name__ == "__main__":
    test_bdjobs_enhanced_scraper()
