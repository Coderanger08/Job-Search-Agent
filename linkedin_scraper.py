import time
import pandas as pd
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import re
import urllib.parse

class LinkedInScraper:
    """
    A class to scrape job postings from LinkedIn.
    """
    def __init__(self, chrome_driver_path, username, password):
        """
        Initializes the LinkedInScraper with necessary details.
        """
        self.chrome_driver_path = chrome_driver_path
        self.username = username
        self.password = password
        self.driver = None
        

    def _setup_driver(self):
        """
        Sets up the Chrome WebDriver with performance logging enabled.
        """
        chrome_options = Options()
        # Add options to prevent detection
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Enable performance logging
        chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        
        # Add user data directory to save session
        import os
        user_data_dir = os.path.join(os.getcwd(), "linkedin_session")
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        
        service = Service(self.chrome_driver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def _is_logged_in(self):
        """Check if already logged into LinkedIn"""
        try:
            self.driver.get("https://www.linkedin.com/feed/")
            time.sleep(3)
            # Check if we're redirected to login page or stay on feed
            current_url = self.driver.current_url
            if "login" in current_url or "signup" in current_url:
                return False
            return True
        except:
            return False

    def login(self):
        # First check if already logged in
        if self._is_logged_in():
            print("Already logged in to LinkedIn.")
            return
            
        self.driver.get("https://www.linkedin.com/login")
        time.sleep(3)
        try:
            username_field = self.driver.find_element(By.ID, "username")
            username_field.send_keys(self.username)
            time.sleep(1)
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys(self.password)
            time.sleep(1)
            password_field.send_keys(Keys.RETURN)
            print("Login successful.")
            time.sleep(5)
        except NoSuchElementException:
            print("Login fields not found. The page structure might have changed.")
            self.driver.quit()
            raise

    def search_jobs(self, job_title, location):
        """
        Searches for jobs on LinkedIn using a constructed URL.
        """
        print("Searching for jobs...")
        job_title_encoded = urllib.parse.quote_plus(job_title)
        location_encoded = urllib.parse.quote_plus(location)
        
        search_url = f"https://www.linkedin.com/jobs/search/?keywords={job_title_encoded}&location={location_encoded}"
        
        self.driver.get(search_url)
        print(f"Navigated to search results page for '{job_title}' in '{location}'.")
        time.sleep(5) # Wait for the job listings to load

    def scrape_jobs(self):
        """
        Scrapes job details by intercepting network requests.
        """
        print("Scraping job listings from network traffic...")
        
        jobs_list = []
        
        # Get performance logs
        logs = self.driver.get_log("performance")
        
        for log in logs:
            message = json.loads(log["message"])["message"]
            if "Network.responseReceived" in message["method"]:
                params = message.get("params")
                if params and "response" in params:
                    url = params["response"]["url"]
                    # Target the specific API call for job search results
                    if "/api/voyagerJobsDashJobCards" in url:
                        try:
                            requestId = params["requestId"]
                            response_body = self.driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": requestId})
                            data = json.loads(response_body['body'])
                            
                            # The data is nested within 'elements' or 'included'
                            job_elements = data.get('elements', [])
                            if not job_elements and 'included' in data:
                                job_elements = data.get('included', [])

                            for element in job_elements:
                                parsed_job = self._parse_job_element(element)
                                if parsed_job:
                                    jobs_list.append(parsed_job)

                            print(f"Found {len(jobs_list)} jobs in a network response.")
                            return jobs_list
                        except Exception as e:
                            print(f"Error processing network response: {e}")
                            
        print("Could not find the job search API response in the network logs.")
        return jobs_list

    def _parse_job_element(self, element):
        """
        Parses a single job element from the JSON response,
        handling various possible data structures.
        """
        # Find the primary container for job details
        job_posting = element.get('jobPosting')
        if not job_posting:
            job_posting = element # Fallback if data is at the top level

        # --- Extract Title ---
        title_obj = job_posting.get('title', {})
        title = title_obj.get('text', 'N/A') if isinstance(title_obj, dict) else title_obj

        # --- Extract Company ---
        company_obj = job_posting.get('primarySubtitle', {})
        company = company_obj.get('text', 'N/A') if isinstance(company_obj, dict) else company_obj

        # --- Extract Location ---
        location_obj = job_posting.get('secondarySubtitle', {})
        location = location_obj.get('text', 'N/A') if isinstance(location_obj, dict) else location_obj

        # Ultimate fallback for company and location if they are still N/A
        if (not company or company == 'N/A') and 'entityUrn' in element:
            # The data is sometimes in a completely different part of the `included` array
            # This is a simplification; a real implementation would need to search the full JSON
            # For now, we will leave it as a known issue that some companies/locations might not be found.
            pass

        # --- Extract URL ---
        job_id = None
        tracking_urn = job_posting.get('trackingUrn')
        if tracking_urn and isinstance(tracking_urn, str):
            try:
                job_id = re.search(r'\d+', tracking_urn.split(':')[-1]).group()
            except:
                job_id = None
        
        # Fallback for job ID in another location
        if not job_id:
            entity_urn = element.get('entityUrn')
            if entity_urn and 'fsd_jobPosting' in entity_urn:
                try:
                    job_id = re.search(r'\d+', entity_urn.split(':')[-1]).group()
                except:
                    job_id = None

        job_url = f"https://www.linkedin.com/jobs/view/{job_id}/" if job_id else 'N/A'
        
        if title and title != 'N/A':
            return {
                "title": title.strip(),
                "company": company.strip() if company else "N/A",
                "location": location.strip() if location else "N/A",
                "url": job_url
            }
        return None

    def run_scraper(self, job_title, location, num_pages=5):
        """
        Main method to run the full scraping process.
        """
        self._setup_driver()
        self.login()
        self.search_jobs(job_title, location)
        
        job_data = self.scrape_jobs()
        
        if job_data:
            df = pd.DataFrame(job_data)
            df.to_csv("linkedin_jobs.csv", index=False)
            print(f"Successfully scraped {len(job_data)} jobs and saved to linkedin_jobs.csv")

            print(f"\n🎉 Found {len(job_data)} jobs on LinkedIn:")
            for i, job in enumerate(job_data, 1):
                print(f"\n{i}. {job['title']}")
                print(f"   Company: {job['company']}")
                print(f"   Location: {job['location']}")
                print(f"   URL: {job['url']}")
        else:
            print("No jobs were found or scraped.")
        
        time.sleep(5) # Keep browser open for a bit
        self.driver.quit()

if __name__ == '__main__':
    # Configuration - To be moved to a config file later
    CHROME_DRIVER_PATH = "C:\\Users\\faisa\\OneDrive\\Desktop\\AI Engineer\\Job search RAG\\drivers\\chromedriver-win64\\chromedriver.exe" # IMPORTANT: Update this path
    LINKEDIN_USERNAME = "faisal.tiujpn@gmail.com"
    LINKEDIN_PASSWORD = "job@gent25"

    scraper = LinkedInScraper(CHROME_DRIVER_PATH, LINKEDIN_USERNAME, LINKEDIN_PASSWORD)
    scraper.run_scraper("Graphic Designer", "Bangladesh")

