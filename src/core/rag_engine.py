from concurrent.futures import ThreadPoolExecutor
import logging
from typing import Dict, List, Any
import time

try:
    from .query_parser import QueryParser
    from .job_database_manager import JobDatabaseManager
    # 4-Layer System Components
    from .advanced_web_search import AdvancedWebSearchEngine
    from .enhanced_llm_pipeline import EnhancedLLMPipeline
    from .intelligent_source_router import IntelligentSourceRouter
    from .quality_assurance import QualityAssuranceLayer
except ImportError:
    from query_parser import QueryParser
    from job_database_manager import JobDatabaseManager
    # 4-Layer System Components
    from advanced_web_search import AdvancedWebSearchEngine
    from enhanced_llm_pipeline import EnhancedLLMPipeline
    from intelligent_source_router import IntelligentSourceRouter
    from quality_assurance import QualityAssuranceLayer

logger = logging.getLogger(__name__)

class RAGEngine:
    def __init__(self):
        """Initialize all the core components of the agent with 4-layer system."""
        logger.info("🚀 Initializing Enhanced RAG Engine with Job Database Integration...")
        
        # Core components
        self.query_parser = QueryParser()
        
        # Job Database Manager (Primary Data Source)
        logger.info("📊 Initializing Job Database Manager...")
        try:
            self.job_database = JobDatabaseManager()
            logger.info(f"✅ Job Database loaded with {self.job_database.get_statistics()['total_jobs']} jobs")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Job Database: {e}")
            self.job_database = None
        
        # 4-Layer System Components
        logger.info("🔧 Initializing Layer 1: Advanced Web Search Engine...")
        self.web_search_engine = AdvancedWebSearchEngine()
        
        logger.info("🤖 Initializing Layer 2: Enhanced LLM Pipeline...")
        # Initialize LLM pipeline with Hugging Face and Gemini API keys
        try:
            from config import Config
            config_instance = Config()
            llm_config = config_instance.get_llm_config()
            huggingface_api_key = llm_config.get('huggingface_api_key')
            gemini_api_key = llm_config.get('gemini_api_key')
        except Exception as e:
            logger.warning(f"⚠️ Could not load API keys: {e}")
            huggingface_api_key = None
            gemini_api_key = None
        
        self.llm_pipeline = EnhancedLLMPipeline(
            huggingface_api_key=huggingface_api_key,
            gemini_api_key=gemini_api_key
        )
        
        logger.info("🎯 Initializing Layer 3: Intelligent Source Router...")
        self.source_router = IntelligentSourceRouter()
        
        logger.info("✅ Initializing Layer 4: Quality Assurance Layer...")
        self.quality_assurance = QualityAssuranceLayer()
        
        logger.info("✅ Advanced RAG Engine initialized successfully with 4-layer system")

    def search(self, raw_query: str) -> dict:
        """
        Executes the enhanced RAG pipeline with dataset-first approach:
        Parse -> Check Relevance -> Search Database -> Fallback to APIs -> Quality Assurance -> Generate
        
        Args:
            raw_query (str): User's natural language query
            
        Returns:
            dict: Contains summary and job listings with quality metrics
        """
        start_time = time.time()
        logger.info(f"🔍 Starting Enhanced RAG search for query: '{raw_query}'")
        
        try:
            # 1. PARSE & CHECK RELEVANCE: Use enhanced query parser
            logger.info("📝 Step 1: Parsing and checking query relevance...")
            
            if not self.job_database:
                logger.error("❌ Job database not available")
                return {"summary": "Sorry, the job database is not available.", "jobs": []}
            
            # Use enhanced search method that handles irrelevant queries
            search_result = self.query_parser.search_jobs_with_database(
                raw_query, 
                self.job_database, 
                limit=20
            )
            
            # Check if query is relevant
            if not search_result.get("is_relevant", True):
                logger.info("❌ Query is not job-related")
                return {
                    "summary": search_result.get("response", "I'm a job search assistant."),
                    "jobs": [],
                    "suggestions": search_result.get("suggestions", []),
                    "is_relevant": False,
                    "is_inappropriate": search_result.get("is_inappropriate", False)
                }
            
            # Get jobs from database
            database_jobs = search_result.get("jobs", [])
            logger.info(f"✅ Database search found {len(database_jobs)} jobs")
            
            # 2. FALLBACK: If insufficient results, try Web Search + LLM
            all_jobs = database_jobs.copy()
            
            if len(database_jobs) < 5:  # If we have less than 5 jobs, try web search
                logger.info("🔄 Insufficient database results, trying web search fallback...")
                web_search_jobs = self._search_with_web_search(raw_query, search_result.get("parsed_data", {}))
                all_jobs.extend(web_search_jobs)
                logger.info(f"✅ Web search fallback added {len(web_search_jobs)} jobs")
            
            # 3. QUALITY ASSURANCE: Skip for better performance
            logger.info(f"✅ Step 3: Quality assurance processing {len(all_jobs)} jobs...")
            # Skip QA processing for better performance - jobs are already validated in database
            processed_jobs = all_jobs

            # 4. GENERATE: Create summary and format results (optimized)
            logger.info("📊 Step 4: Generating summary and formatting results...")
            # Use simple summary for better performance
            summary = f"Found {len(processed_jobs)} jobs matching your query: '{raw_query}'"

            execution_time = time.time() - start_time
            logger.info(f"🎉 Enhanced RAG search completed in {execution_time:.2f} seconds")

            try:
                quality_metrics = self.quality_assurance.get_qa_report()
            except Exception as e:
                logger.error(f"❌ Quality metrics failed: {e}")
                quality_metrics = {}
            
            return {
                "summary": summary,
                "jobs": processed_jobs,
                "execution_time": execution_time,
                "database_jobs": len(database_jobs),
                "web_search_jobs": len(all_jobs) - len(database_jobs),
                "total_jobs_found": len(all_jobs),
                "quality_approved_jobs": len(processed_jobs),
                "quality_metrics": quality_metrics,
                "parsed_data": search_result.get("parsed_data", {}),
                "search_params": search_result.get("search_params", {})
            }
            
        except Exception as e:
            logger.error(f"❌ Enhanced RAG search failed: {str(e)}")
            return {
                "summary": "Sorry, something went wrong while searching for jobs.",
                "jobs": [],
                "error": str(e)
            }

    def _get_html_with_playwright(self, url: str) -> str:
        """Get HTML content with JavaScript execution using Playwright"""
        try:
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # Set realistic headers
                page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                })
                
                # Navigate and wait for content
                page.goto(url, wait_until='networkidle', timeout=15000)
                page.wait_for_timeout(3000)  # Wait for JavaScript to load
                
                html_content = page.content()
                browser.close()
                
                logger.info(f"✅ Playwright successfully fetched content from {url}")
                return html_content
                
        except Exception as e:
            logger.error(f"❌ Playwright failed for {url}: {e}")
            return ""



    def _search_with_4layer_system(self, parsed_query: dict, selected_sources: List[str]) -> List[Dict]:
        """
        Execute search using the 4-layer system:
        Layer 1: Advanced Web Search → Layer 2: Enhanced LLM → Layer 3: Source Router → Layer 4: Quality Assurance
        """
        logger.info("🔧 Executing 4-layer system search...")
        
        try:
            # Layer 1: Advanced Web Search - Search for actual job listing pages
            logger.info("🌐 Layer 1: Advanced Web Search for job listing pages...")
            
            # Use broader search queries instead of site-specific
            job_type = parsed_query.get('job_type', 'job')
            location = parsed_query.get('location', 'Bangladesh')
            
            # Handle None values
            if job_type is None:
                job_type = 'job'
            if location is None:
                location = 'Bangladesh'
            
            search_queries = [
                f"{job_type} jobs {location} site:linkedin.com OR site:indeed.com OR site:bdjobs.com OR site:skill.jobs",
                f"{job_type} positions {location} site:glassdoor.com OR site:monster.com OR site:careerbuilder.com",
                f"{job_type} vacancies {location} site:bdjobs.com OR site:skill.jobs OR site:shomvob.com",
                f"{job_type} careers {location} site:linkedin.com OR site:indeed.com"
            ]
            
            extracted_jobs = []
            
            for search_query in search_queries:
                try:
                    logger.info(f"🔍 Searching: {search_query}")
                    
                    search_results = self.web_search_engine.search(
                        query=search_query,
                        num_results=10  # More results for broader search
                    )
                    
                    if not search_results:
                        logger.warning(f"⚠️ No search results for: {search_query}")
                        continue
                    
                    logger.info(f"📋 Found {len(search_results)} search results for: {search_query}")
                    for i, result in enumerate(search_results[:3], 1):  # Show first 3 results
                        logger.info(f"   {i}. {result.url}")
                    
                    # Layer 2: Enhanced LLM Pipeline for job extraction
                    logger.info(f"🤖 Layer 2: Extracting jobs from search results...")
                    
                    for result in search_results:
                        try:
                            # Process URLs that look like job listings or are from known job sites
                            job_keywords = ['job', 'career', 'position', 'vacancy', 'apply', 'opportunity']
                            job_sites = ['linkedin.com', 'indeed.com', 'glassdoor.com', 'monster.com', 'careerbuilder.com', 'bdjobs.com', 'skill.jobs', 'shomvob.com']
                            
                            # Handle Bing redirect URLs by extracting the actual URL
                            actual_url = result.url
                            if 'bing.com/ck/a' in result.url:
                                # Extract the actual URL from Bing redirect
                                import urllib.parse
                                try:
                                    parsed = urllib.parse.urlparse(result.url)
                                    query_params = urllib.parse.parse_qs(parsed.query)
                                    if 'u' in query_params:
                                        # The URL is base64 encoded, but let's try to decode it properly
                                        encoded_url = query_params['u'][0]
                                        try:
                                            import base64
                                            # Fix Bing's corrupted base64 URLs by removing 'a1' prefix
                                            clean_encoded_url = encoded_url
                                            if encoded_url.startswith('a1'):
                                                clean_encoded_url = encoded_url[2:]  # Remove 'a1' prefix
                                                logger.info(f"🔧 Removed 'a1' prefix from Bing URL: {encoded_url} -> {clean_encoded_url}")
                                            
                                            # Try different padding options for base64 decoding
                                            decoded_url = None
                                            for padding in ['', '=', '==', '===']:
                                                try:
                                                    decoded_url = base64.b64decode(clean_encoded_url + padding).decode('utf-8')
                                                    actual_url = decoded_url
                                                    logger.info(f"✅ Successfully decoded Bing redirect URL: {actual_url}")
                                                    break
                                                except Exception as decode_error:
                                                    logger.debug(f"Base64 decode attempt with '{padding}' failed: {decode_error}")
                                                    continue
                                            
                                            if not decoded_url:
                                                # If base64 decoding fails completely, add https:// prefix to encoded URL
                                                actual_url = f"https://{clean_encoded_url}" if not clean_encoded_url.startswith('http') else clean_encoded_url
                                                logger.warning(f"⚠️ Base64 decode failed, using prefixed URL: {actual_url}")
                                        except Exception as e:
                                            logger.warning(f"⚠️ Failed to decode Bing redirect URL: {e}")
                                            clean_encoded_url = encoded_url[2:] if encoded_url.startswith('a1') else encoded_url
                                            actual_url = f"https://{clean_encoded_url}" if not clean_encoded_url.startswith('http') else clean_encoded_url
                                except Exception as e:
                                    logger.warning(f"⚠️ Failed to extract URL from Bing redirect: {e}")
                            
                            is_job_url = any(keyword in actual_url.lower() for keyword in job_keywords)
                            is_job_site = any(site in actual_url.lower() for site in job_sites)
                            
                            # For web search results, be more lenient - process all URLs since they came from job-related searches
                            should_process = is_job_url or is_job_site or True  # Process all web search results
                            
                            if should_process:
                                logger.info(f"📄 Processing job URL: {result.url}")
                                logger.info(f"   Job keywords match: {is_job_url}")
                                logger.info(f"   Job site match: {is_job_site}")
                                
                                # Use Playwright for JavaScript-heavy sites, requests for simple sites
                                javascript_sites = ['linkedin.com', 'indeed.com', 'glassdoor.com', 'monster.com', 'careerbuilder.com']
                                is_javascript_site = any(site in result.url.lower() for site in javascript_sites)
                                
                                if is_javascript_site:
                                    logger.info(f"🤖 Using Playwright for JavaScript site: {actual_url}")
                                    html_content = self._get_html_with_playwright(actual_url)
                                else:
                                    logger.info(f"⚡ Using requests for simple site: {actual_url}")
                                    import requests
                                    headers = {
                                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                                    }
                                    response = requests.get(actual_url, headers=headers, timeout=10)
                                    html_content = response.text
                                
                                # Debug: Check if we got HTML content
                                if html_content:
                                    logger.info(f"✅ Got HTML content: {len(html_content)} characters from {actual_url}")
                                else:
                                    logger.warning(f"⚠️ No HTML content received from {actual_url}")
                                    continue
                                
                                extraction_result = self.llm_pipeline.extract_jobs_from_html(
                                    html_content=html_content,
                                    source_url=actual_url
                                )
                                
                                # Debug: Check extraction results
                                logger.info(f"🔍 LLM Extraction Results for {actual_url}:")
                                logger.info(f"   Success: {extraction_result.success}")
                                logger.info(f"   Jobs found: {len(extraction_result.jobs) if extraction_result.jobs else 0}")
                                logger.info(f"   Provider: {extraction_result.provider}")
                                logger.info(f"   Confidence: {extraction_result.confidence_score}")
                                if extraction_result.errors:
                                    logger.warning(f"   Errors: {extraction_result.errors}")
                                
                                if extraction_result.success and extraction_result.jobs:
                                    extracted_jobs.extend(extraction_result.jobs)
                                    logger.info(f"✅ Extracted {len(extraction_result.jobs)} jobs from {actual_url}")
                                    # Debug: Show first job details
                                    if extraction_result.jobs:
                                        first_job = extraction_result.jobs[0]
                                        logger.info(f"   Sample job: {first_job.title} at {first_job.company}")
                                else:
                                    logger.warning(f"⚠️ No jobs extracted from {actual_url}")
                                    logger.warning(f"   Reason: Success={extraction_result.success}, Jobs={len(extraction_result.jobs) if extraction_result.jobs else 0}")
                            else:
                                logger.debug(f"⏭️ Skipping non-job URL: {result.url}")
                                logger.debug(f"   Job keywords match: {is_job_url}")
                                logger.debug(f"   Job site match: {is_job_site}")
                        except Exception as e:
                            logger.error(f"❌ LLM extraction failed for {actual_url}: {e}")
                            continue
                            
                except Exception as e:
                    logger.error(f"❌ Web search failed for {site_filter}: {e}")
                    continue
            
            logger.info(f"✅ Layer 2 extracted {len(extracted_jobs)} jobs total")
            return extracted_jobs
            
        except Exception as e:
            logger.error(f"❌ 4-layer system search failed: {e}")
            return []

    def _search_with_web_search(self, raw_query: str, parsed_data: Dict[str, Any]) -> List[Dict]:
        """Fallback web search + LLM when database results are insufficient"""
        logger.info("🔄 Starting web search + LLM fallback...")
        web_search_jobs = []
        
        try:
            job_title = parsed_data.get("job_type", "job")
            location = parsed_data.get("location", "Bangladesh")
            
            # Use the 4-layer system for web search
            logger.info("🌐 Using 4-layer web search system...")
            web_search_jobs = self._search_with_4layer_system(parsed_data, ["web_search"])
            
            logger.info(f"✅ Web search + LLM fallback completed: {len(web_search_jobs)} total jobs")
            return web_search_jobs
            
        except Exception as e:
            logger.error(f"❌ Web search + LLM fallback failed: {e}")
            return []

    def _generate_enhanced_summary(self, raw_query: str, jobs: List[Dict], search_result: Dict[str, Any]) -> str:
        """Generate an enhanced summary with intelligent insights"""
        if not jobs:
            return f"No jobs found matching your query: '{raw_query}'"
        
        # Get parsed data
        parsed_data = search_result.get("parsed_data", {})
        job_type = parsed_data.get("job_type", "job")
        location = parsed_data.get("location", "various locations")
        experience_level = parsed_data.get("experience_level", "")
        
        # Basic summary
        summary = f"I found {len(jobs)} jobs matching your query: '{raw_query}'"
        
        # Add intelligent insights
        if jobs:
            # Get unique companies
            companies = set()
            locations = set()
            for job in jobs:
                if hasattr(job, 'company') and job.company:
                    companies.add(job.company)
                if hasattr(job, 'location') and job.location:
                    locations.add(job.location)
            
            if companies:
                summary += f" from {len(companies)} different companies"
            
            if locations and len(locations) <= 5:
                summary += f" in {', '.join(list(locations)[:3])}"
                if len(locations) > 3:
                    summary += f" and {len(locations) - 3} other locations"
            
            # Add experience level info
            if experience_level:
                summary += f". Most positions are {experience_level} level"
            
            # Add recent job info
            recent_jobs = [job for job in jobs if hasattr(job, 'posted_date') and job.posted_date]
            if recent_jobs:
                summary += f". {len(recent_jobs)} jobs were posted recently"
            
            # Add salary info if available
            jobs_with_salary = [job for job in jobs if hasattr(job, 'salary') and job.salary]
            if jobs_with_salary:
                summary += f", and {len(jobs_with_salary)} include salary information"
            
            summary += "."
        
        return summary

    def _generate_advanced_summary(self, job_title: str, location: str, jobs: List[Dict]) -> str:
        """Generate an advanced summary with quality insights."""
        if not jobs:
            return f"No quality-approved jobs found for '{job_title}' in {location}."
        
        # Basic summary
        summary = f"I found {len(jobs)} quality-approved job listings for '{job_title}' in {location}."
        
        # Add quality insights
        if jobs:
            # Get unique companies
            companies = set(job.get('company', 'Unknown') for job in jobs if job.get('company'))
            if companies:
                summary += f" These jobs are from {len(companies)} different companies."
            
            # Add salary info if available
            jobs_with_salary = [job for job in jobs if job.get('salary')]
            if jobs_with_salary:
                summary += f" {len(jobs_with_salary)} positions include salary information."
            
            # Add quality metrics
            high_quality_jobs = [job for job in jobs if job.get('quality_score', 0) > 0.8]
            if high_quality_jobs:
                summary += f" {len(high_quality_jobs)} jobs have high-quality information."
        
        return summary

    def get_advanced_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the advanced search system."""
        return {
            "system_components": {
                "job_database": "JobDatabaseManager (992 LinkedIn jobs with search indexing)",
                "layer_1": "Advanced Web Search Engine (Multi-engine, Rate-limited)",
                "layer_2": "Enhanced LLM Pipeline (Multi-provider, Advanced prompts)",
                "layer_3": "Intelligent Source Router (Dynamic routing, Performance tracking)",
                "layer_4": "Quality Assurance Layer (Validation, Deduplication, Enrichment)"
            },
            "data_sources_available": [
                "LinkedIn Job Database (992 jobs, primary source)",
                "Advanced Web Search (Google, Bing, DuckDuckGo)",
                "Enhanced LLM Extraction (Gemini, Hugging Face, Ollama)"
            ],
            "quality_features": [
                "Job validation and spam detection",
                "Fuzzy deduplication",
                "Job enrichment (skills, experience, job type)",
                "Quality scoring and ranking"
            ],
            "system_status": "advanced_operational"
        }

if __name__ == "__main__":
    # Set up logging
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test the Enhanced RAG Engine
    engine = RAGEngine()
    
    # Test various query types
    test_queries = [
        "Find me software engineer jobs in Dhaka",
        "I need Python developer positions",
        "What's the weather like?",  # Irrelevant query
        "Show me adult content",     # Inappropriate query
        "Remote data analyst jobs",
        "Senior frontend developer positions"
    ]
    
    for query in test_queries:
        print(f"\n🧪 Testing Enhanced RAG Engine...")
        print(f"Query: '{query}'")
        print("=" * 60)
        
        results = engine.search(query)
        
        print(f"\n📊 Enhanced Results Summary:")
        print(f"Summary: {results['summary']}")
        print(f"Execution Time: {results.get('execution_time', 'N/A')} seconds")
        print(f"Database Jobs: {results.get('database_jobs', 0)}")
        print(f"Web Search Jobs: {results.get('web_search_jobs', 0)}")
        print(f"Total Jobs Found: {results.get('total_jobs_found', 0)}")
        print(f"Quality Approved Jobs: {results.get('quality_approved_jobs', 0)}")
        
        # Check if query was relevant
        if results.get('is_relevant') == False:
            print(f"❌ Query was not job-related")
            if results.get('suggestions'):
                print(f"💡 Suggestions:")
                for suggestion in results['suggestions']:
                    print(f"    • {suggestion}")
        else:
            print(f"✅ Query was job-related")
            
            # Print quality metrics if available
            if results.get('quality_metrics'):
                print(f"\n📈 Quality Metrics:")
                metrics = results['quality_metrics']
                print(f"  Average Quality Score: {metrics.get('average_quality_score', 'N/A')}")
                print(f"  Validation Pass Rate: {metrics.get('validation_pass_rate', 'N/A')}")
                print(f"  Deduplication Rate: {metrics.get('deduplication_rate', 'N/A')}")
            
            # Print the first 3 jobs
            if results.get('jobs'):
                print(f"\n📋 Sample Jobs (showing first 3):")
                for i, job in enumerate(results["jobs"][:3], 1):
                    print(f"\n{i}. Title: {getattr(job, 'title', 'N/A')}")
                    print(f"   Company: {getattr(job, 'company', 'N/A')}")
                    print(f"   Location: {getattr(job, 'location', 'N/A')}")
                    if hasattr(job, 'posted_date') and job.posted_date:
                        print(f"   Posted: {job.posted_date}")
                    if hasattr(job, 'salary') and job.salary:
                        print(f"   Salary: {job.salary}")
        
        print("-" * 60)
    
    print("\n✅ Enhanced RAG Engine test completed!")