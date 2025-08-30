"""
Enhanced LLM Pipeline - Layer 2
Multi-stage prompts, validation, and fallback models for job extraction
"""

import json
import logging
import time
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMProvider(Enum):
    """Supported LLM providers"""
    MISTRAL = "mistral"  # Primary LLM (completely free and high quality)
    DEEPSEEK = "deepseek"  # Backup LLM
    GEMINI = "gemini"
    HUGGINGFACE = "huggingface"
    OLLAMA = "ollama"

@dataclass
class JobListing:
    """Standardized job listing structure"""
    title: str
    company: str
    location: str
    summary: str
    url: str
    salary: Optional[str] = None
    requirements: List[str] = None
    experience_level: Optional[str] = None
    job_type: Optional[str] = None
    posted_date: Optional[str] = None
    skills: List[str] = None
    benefits: List[str] = None
    confidence_score: float = 0.0
    source: str = ""
    extraction_method: str = ""

@dataclass
class ExtractionResult:
    """Result of LLM extraction"""
    jobs: List[JobListing]
    success: bool
    provider: str
    processing_time: float
    confidence_score: float
    errors: List[str] = None

class PromptTemplate:
    """Advanced prompt templates for different extraction scenarios"""
    
    JOB_EXTRACTION_SYSTEM = """You are an expert job data extraction specialist. Your task is to extract structured job information from HTML content with high accuracy and completeness."""
    
    JOB_EXTRACTION_MAIN = """
Extract ALL job listings from the provided HTML content. For each job, provide the following information in valid JSON format:

REQUIRED FIELDS:
- "title": Job title/position name
- "company": Company or organization name
- "location": Job location (city, country, or "Remote")
- "summary": Brief 1-2 sentence job description
- "url": Direct link to the job posting (must be complete URL)

OPTIONAL FIELDS (use null if not found):
- "salary": Salary range or amount
- "requirements": Array of key requirements/qualifications
- "experience_level": Experience level (Entry, Mid, Senior, etc.)
- "job_type": Employment type (Full-time, Part-time, Contract, etc.)
- "posted_date": When the job was posted
- "skills": Array of required technical skills
- "benefits": Array of benefits offered

EXTRACTION RULES:
1. Extract ONLY genuine job postings, ignore ads or promotional content
2. Ensure all URLs are complete and functional
3. Keep summaries concise but informative
4. Normalize location names (e.g., "Dhaka, Bangladesh" not "dhaka bd")
5. Extract skills from requirements where possible
6. If multiple similar jobs exist, extract each separately

Return ONLY a valid JSON array of job objects. No additional text or formatting.

HTML CONTENT:
{html_content}
"""

    JOB_VALIDATION = """
Validate and improve the following job listing data. Check for:
1. Missing or incomplete required fields
2. Invalid or broken URLs
3. Unclear job titles or descriptions
4. Inconsistent formatting

Fix any issues and return the improved JSON. If a job listing is invalid or spam, remove it.

Original data:
{job_data}
"""

    QUERY_UNDERSTANDING = """
Analyze this job search query and extract the key search parameters:

Query: "{query}"

Extract and return JSON with:
- "job_titles": Array of possible job titles/roles
- "skills": Array of technical skills mentioned
- "locations": Array of locations mentioned
- "experience_level": Experience level if mentioned
- "job_type": Employment type if mentioned
- "companies": Array of company names if mentioned
- "keywords": Additional relevant keywords
- "search_intent": Primary intent (job_search, company_research, salary_inquiry, etc.)

Return only valid JSON.
"""

class GeminiLLM:
    """Gemini LLM implementation"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        if not genai:
            raise ImportError("google-generativeai package not installed")
        
        self.api_key = api_key
        self.model_name = model_name
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.max_retries = 3
        self.retry_delay = 2.0
    
    def extract_jobs(self, html_content: str, timeout: float = 30.0) -> ExtractionResult:
        """Extract jobs using Gemini"""
        start_time = time.time()
        
        try:
            prompt = PromptTemplate.JOB_EXTRACTION_MAIN.format(html_content=html_content)
            
            # Make request with retries
            for attempt in range(self.max_retries):
                try:
                    response = self.model.generate_content(
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.1,
                            top_p=0.8,
                            max_output_tokens=4096,
                        )
                    )
                    
                    if response and response.text:
                        jobs = self._parse_job_response(response.text)
                        processing_time = time.time() - start_time
                        
                        return ExtractionResult(
                            jobs=jobs,
                            success=True,
                            provider=LLMProvider.GEMINI.value,
                            processing_time=processing_time,
                            confidence_score=0.9,  # Gemini is generally reliable
                            errors=[]
                        )
                
                except Exception as e:
                    logger.warning(f"⚠️ Gemini attempt {attempt + 1} failed: {e}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (2 ** attempt))
                    continue
            
            # All attempts failed
            processing_time = time.time() - start_time
            return ExtractionResult(
                jobs=[],
                success=False,
                provider=LLMProvider.GEMINI.value,
                processing_time=processing_time,
                confidence_score=0.0,
                errors=[f"All {self.max_retries} attempts failed"]
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ Gemini extraction failed: {e}")
            return ExtractionResult(
                jobs=[],
                success=False,
                provider=LLMProvider.GEMINI.value,
                processing_time=processing_time,
                confidence_score=0.0,
                errors=[str(e)]
            )
    
    def _parse_job_response(self, response_text: str) -> List[JobListing]:
        """Parse Gemini response into JobListing objects"""
        try:
            # Clean the response text
            cleaned_text = self._clean_json_response(response_text)
            
            # Parse JSON
            job_data = json.loads(cleaned_text)
            
            if not isinstance(job_data, list):
                logger.warning("⚠️ Expected JSON array, got single object")
                job_data = [job_data] if isinstance(job_data, dict) else []
            
            jobs = []
            for i, job_dict in enumerate(job_data):
                try:
                    job = self._dict_to_job_listing(job_dict)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    logger.warning(f"⚠️ Error parsing job {i}: {e}")
                    continue
            
            return jobs
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing failed: {e}")
            logger.debug(f"Response text: {response_text[:500]}...")
            return []
        except Exception as e:
            logger.error(f"❌ Response parsing failed: {e}")
            return []
    
    def _clean_json_response(self, text: str) -> str:
        """Clean LLM response to extract valid JSON"""
        # Remove markdown code blocks
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*$', '', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Find JSON array or object
        json_match = re.search(r'(\[.*\]|\{.*\})', text, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        return text
    
    def _dict_to_job_listing(self, job_dict: Dict) -> Optional[JobListing]:
        """Convert dictionary to JobListing object"""
        try:
            # Validate required fields
            required_fields = ['title', 'company', 'location', 'summary', 'url']
            for field in required_fields:
                if not job_dict.get(field):
                    logger.warning(f"⚠️ Missing required field: {field}")
                    return None
            
            # Create JobListing
            return JobListing(
                title=str(job_dict['title']).strip(),
                company=str(job_dict['company']).strip(),
                location=str(job_dict['location']).strip(),
                summary=str(job_dict['summary']).strip(),
                url=str(job_dict['url']).strip(),
                salary=job_dict.get('salary'),
                requirements=job_dict.get('requirements', []) or [],
                experience_level=job_dict.get('experience_level'),
                job_type=job_dict.get('job_type'),
                posted_date=job_dict.get('posted_date'),
                skills=job_dict.get('skills', []) or [],
                benefits=job_dict.get('benefits', []) or [],
                confidence_score=0.8,
                source="llm_extraction",
                extraction_method=LLMProvider.GEMINI.value
            )
            
        except Exception as e:
            logger.error(f"❌ Error creating JobListing: {e}")
            return None

class MistralLLM:
    """Mistral LLM implementation (Primary - completely free and high quality)"""
    
    def __init__(self, api_key: str, model_name: str = "mistralai/Mistral-7B-Instruct-v0.2"):
        if not api_key:
            raise ValueError("Hugging Face API key is required for Mistral")
        
        self.api_key = api_key
        self.model_name = model_name
        self.api_url = f"https://api-inference.huggingface.co/models/{model_name}"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        logger.info(f"✅ Mistral LLM initialized: {model_name}")
    
    def extract_jobs(self, html_content: str, timeout: float = 30.0) -> ExtractionResult:
        """Extract jobs using Mistral via Hugging Face API"""
        start_time = time.time()
        
        try:
            # Prepare the prompt for job extraction
            prompt = PromptTemplate.JOB_EXTRACTION_MAIN + f"""
            
HTML CONTENT TO EXTRACT FROM:
{html_content[:4000]}...

Return ONLY valid JSON array of job objects. No additional text or explanations.
"""
            
            # Prepare the API request for Hugging Face
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 2000,
                    "temperature": 0.1,  # Low temperature for consistent output
                    "do_sample": True,
                    "return_full_text": False
                }
            }
            
            # Make API request
            import requests
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    content = result[0].get('generated_text', '')
                    jobs = self._parse_job_response(content)
                    
                    processing_time = time.time() - start_time
                    return ExtractionResult(
                        jobs=jobs,
                        success=len(jobs) > 0,
                        provider=LLMProvider.MISTRAL.value,
                        processing_time=processing_time,
                        confidence_score=0.9,  # High confidence for Mistral
                        errors=[]
                    )
                else:
                    raise Exception("No content in API response")
            else:
                raise Exception(f"API request failed with status {response.status_code}: {response.text}")
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ Mistral extraction failed: {e}")
            return ExtractionResult(
                jobs=[],
                success=False,
                provider=LLMProvider.MISTRAL.value,
                processing_time=processing_time,
                confidence_score=0.0,
                errors=[str(e)]
            )
    
    def _parse_job_response(self, response_text: str) -> List[JobListing]:
        """Parse DeepSeek response into JobListing objects"""
        try:
            # Clean the response text
            cleaned_text = self._clean_json_response(response_text)
            
            # Parse JSON
            job_data = json.loads(cleaned_text)
            
            if not isinstance(job_data, list):
                logger.warning("⚠️ Expected JSON array, got single object")
                job_data = [job_data] if isinstance(job_data, dict) else []
            
            jobs = []
            for i, job_dict in enumerate(job_data):
                try:
                    job = self._dict_to_job_listing(job_dict)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    logger.warning(f"⚠️ Error parsing job {i}: {e}")
                    continue
            
            return jobs
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing failed: {e}")
            logger.debug(f"Response text: {response_text[:500]}...")
            return []
        except Exception as e:
            logger.error(f"❌ Response parsing failed: {e}")
            return []
    
    def _clean_json_response(self, text: str) -> str:
        """Clean LLM response to extract valid JSON"""
        # Remove markdown code blocks
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*$', '', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Find JSON array or object
        json_match = re.search(r'(\[.*\]|\{.*\})', text, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        return text
    
    def _dict_to_job_listing(self, job_dict: Dict) -> Optional[JobListing]:
        """Convert dictionary to JobListing object"""
        try:
            # Validate required fields
            required_fields = ['title', 'company', 'location', 'summary', 'url']
            for field in required_fields:
                if not job_dict.get(field):
                    logger.warning(f"⚠️ Missing required field: {field}")
                    return None
            
            # Create JobListing
            return JobListing(
                title=str(job_dict['title']).strip(),
                company=str(job_dict['company']).strip(),
                location=str(job_dict['location']).strip(),
                summary=str(job_dict['summary']).strip(),
                url=str(job_dict['url']).strip(),
                salary=job_dict.get('salary'),
                requirements=job_dict.get('requirements', []) or [],
                experience_level=job_dict.get('experience_level'),
                job_type=job_dict.get('job_type'),
                posted_date=job_dict.get('posted_date'),
                skills=job_dict.get('skills', []) or [],
                benefits=job_dict.get('benefits', []) or [],
                confidence_score=0.9,
                source="llm_extraction",
                extraction_method=LLMProvider.DEEPSEEK.value
            )
            
        except Exception as e:
            logger.error(f"❌ Error creating JobListing: {e}")
            return None

class HuggingFaceLLM:
    """Hugging Face LLM implementation (fallback)"""
    
    def __init__(self, model_name: str = "gpt2", api_key: str = None):
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("transformers package not installed")
        
        self.model_name = model_name
        self.api_key = api_key
        self.pipeline = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize Hugging Face model"""
        try:
            if self.api_key:
                # Use API key for Hugging Face Inference API
                import requests
                self.api_url = f"https://api-inference.huggingface.co/models/{self.model_name}"
                self.headers = {"Authorization": f"Bearer {self.api_key}"}
                logger.info(f"✅ Hugging Face API initialized: {self.model_name}")
            else:
                # Use local model (fallback)
                self.pipeline = pipeline("text-generation", model=self.model_name)
                logger.info(f"✅ Hugging Face local model loaded: {self.model_name}")
        except Exception as e:
            logger.error(f"❌ Failed to load Hugging Face model: {e}")
    
    def extract_jobs(self, html_content: str, timeout: float = 30.0) -> ExtractionResult:
        """Extract jobs using Hugging Face API or local model"""
        start_time = time.time()
        
        try:
            if self.api_key:
                # Use Hugging Face Inference API
                jobs = self._api_extraction(html_content)
            elif self.pipeline:
                # Use local model
                jobs = self._local_extraction(html_content)
            else:
                # Fallback to simple HTML extraction
                jobs = self._simple_html_extraction(html_content)
            
            processing_time = time.time() - start_time
            
            return ExtractionResult(
                jobs=jobs,
                success=len(jobs) > 0,
                provider=LLMProvider.HUGGINGFACE.value,
                processing_time=processing_time,
                confidence_score=0.7 if self.api_key else 0.6,
                errors=[]
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ Hugging Face extraction failed: {e}")
            return ExtractionResult(
                jobs=[],
                success=False,
                provider=LLMProvider.HUGGINGFACE.value,
                processing_time=processing_time,
                confidence_score=0.0,
                errors=[str(e)]
            )
    
    def _api_extraction(self, html_content: str) -> List[JobListing]:
        """Extract jobs using Hugging Face Inference API"""
        try:
            import requests
            
            # Prepare prompt for job extraction
            prompt = f"""
            Extract job listings from this HTML content. Return a JSON array of job objects with these fields:
            - title: Job title
            - company: Company name
            - location: Job location
            - summary: Job description
            - url: Job URL (if available)
            - salary: Salary information (if available)
            
            HTML Content:
            {html_content[:2000]}...
            
            JSON Response:
            """
            
            # Make API request
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={"inputs": prompt, "parameters": {"max_length": 1000}},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get('generated_text', '')
                    # Parse the generated text to extract JSON
                    return self._parse_api_response(generated_text)
            
            logger.warning(f"⚠️ Hugging Face API returned status {response.status_code}")
            return []
            
        except Exception as e:
            logger.error(f"❌ Hugging Face API extraction failed: {e}")
            return []
    
    def _local_extraction(self, html_content: str) -> List[JobListing]:
        """Extract jobs using local Hugging Face model"""
        try:
            # Prepare prompt
            prompt = f"Extract job listings from: {html_content[:1000]}..."
            
            # Generate response
            response = self.pipeline(prompt, max_length=500, num_return_sequences=1)
            
            if response and len(response) > 0:
                generated_text = response[0]['generated_text']
                return self._parse_api_response(generated_text)
            
            return []
            
        except Exception as e:
            logger.error(f"❌ Local Hugging Face extraction failed: {e}")
            return []
    
    def _parse_api_response(self, response_text: str) -> List[JobListing]:
        """Parse Hugging Face API response into JobListing objects"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                job_data = json.loads(json_match.group())
                jobs = []
                for job_dict in job_data:
                    try:
                        job = self._dict_to_job_listing(job_dict)
                        if job:
                            jobs.append(job)
                    except Exception as e:
                        logger.warning(f"⚠️ Error parsing job from API: {e}")
                        continue
                return jobs
            
            return []
            
        except Exception as e:
            logger.error(f"❌ Failed to parse Hugging Face API response: {e}")
            return []
    
    def _simple_html_extraction(self, html_content: str) -> List[JobListing]:
        """Simple HTML extraction without LLM (fallback method)"""
        from bs4 import BeautifulSoup
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            jobs = []
            
            # Look for common job listing patterns
            job_patterns = [
                {'title': 'h1, h2, h3', 'company': '.company, [class*="company"]'},
                {'title': '[class*="job-title"]', 'company': '[class*="company"]'},
                {'title': '[class*="title"]', 'company': '[class*="employer"]'},
            ]
            
            for pattern in job_patterns:
                titles = soup.select(pattern['title'])
                companies = soup.select(pattern['company'])
                
                for i, (title_elem, company_elem) in enumerate(zip(titles[:5], companies[:5])):
                    try:
                        job = JobListing(
                            title=title_elem.get_text(strip=True),
                            company=company_elem.get_text(strip=True),
                            location="Not specified",
                            summary="Job details available on original site",
                            url="",
                            confidence_score=0.4,
                            source="simple_extraction",
                            extraction_method=LLMProvider.HUGGINGFACE.value
                        )
                        jobs.append(job)
                    except Exception:
                        continue
                
                if jobs:
                    break
            
            return jobs[:3]  # Limit to 3 jobs for fallback
            
        except Exception as e:
            logger.error(f"❌ Simple HTML extraction failed: {e}")
            return []


class OllamaLLM:
    """Ollama LLM implementation (local, free)"""
    
    def __init__(self, model_name: str = "llama2"):
        if not OLLAMA_AVAILABLE:
            raise ImportError("ollama package not installed")
        
        self.model_name = model_name
        self.client = ollama.Client()
        self._test_connection()
    
    def _test_connection(self):
        """Test connection to Ollama server"""
        try:
            # Test if Ollama server is running
            models = self.client.list()
            logger.info(f"✅ Ollama connection successful. Available models: {[m['name'] for m in models['models']]}")
        except Exception as e:
            logger.warning(f"⚠️ Ollama server not running or model not available: {e}")
            logger.info("💡 To use Ollama: 1) Install Ollama 2) Run 'ollama serve' 3) Run 'ollama pull llama2'")
    
    def extract_jobs(self, html_content: str, timeout: float = 30.0) -> ExtractionResult:
        """Extract jobs using Ollama LLM"""
        start_time = time.time()
        
        try:
            # Prepare the prompt for job extraction
            prompt = PromptTemplate.JOB_EXTRACTION_MAIN.format(html_content=html_content[:8000])  # Limit content size
            
            # Call Ollama API
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    "temperature": 0.1,  # Low temperature for consistent extraction
                    "top_p": 0.9,
                    "max_tokens": 2000
                }
            )
            
            # Parse the response
            jobs = self._parse_ollama_response(response['response'])
            processing_time = time.time() - start_time
            
            return ExtractionResult(
                jobs=jobs,
                success=len(jobs) > 0,
                provider=LLMProvider.OLLAMA.value,
                processing_time=processing_time,
                confidence_score=0.8,  # Good confidence for local LLM
                errors=[]
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ Ollama extraction failed: {e}")
            return ExtractionResult(
                jobs=[],
                success=False,
                provider=LLMProvider.OLLAMA.value,
                processing_time=processing_time,
                confidence_score=0.0,
                errors=[str(e)]
            )
    
    def _parse_ollama_response(self, response_text: str) -> List[JobListing]:
        """Parse Ollama response into JobListing objects"""
        try:
            # Extract JSON from response
            import json
            import re
            
            # Find JSON array in the response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if not json_match:
                logger.warning("❌ No JSON array found in Ollama response")
                return []
            
            json_str = json_match.group()
            job_data = json.loads(json_str)
            
            jobs = []
            for job_item in job_data:
                try:
                    job = JobListing(
                        title=job_item.get('title', 'Unknown'),
                        company=job_item.get('company', 'Unknown'),
                        location=job_item.get('location', 'Not specified'),
                        summary=job_item.get('summary', 'Job details available on original site'),
                        url=job_item.get('url', ''),
                        salary=job_item.get('salary'),
                        requirements=job_item.get('requirements', []),
                        experience_level=job_item.get('experience_level'),
                        job_type=job_item.get('job_type'),
                        posted_date=job_item.get('posted_date'),
                        skills=job_item.get('skills', []),
                        benefits=job_item.get('benefits', []),
                        confidence_score=0.8,
                        source="ollama_extraction",
                        extraction_method=LLMProvider.OLLAMA.value
                    )
                    jobs.append(job)
                except Exception as e:
                    logger.error(f"❌ Error creating JobListing from Ollama: {e}")
                    continue
            
            return jobs
            
        except Exception as e:
            logger.error(f"❌ Failed to parse Ollama response: {e}")
            return []
            logger.error(f"❌ Simple extraction failed: {e}")
            return []

class EnhancedLLMPipeline:
    """Enhanced LLM pipeline with multiple providers and intelligent fallbacks"""
    
    def __init__(self, gemini_api_key: str = None, huggingface_api_key: str = None):
        self.providers = {}
        self.provider_priority = []
        
        # Initialize Mistral as primary LLM (completely free and high quality)
        if huggingface_api_key:
            try:
                self.providers[LLMProvider.MISTRAL] = MistralLLM(huggingface_api_key)
                self.provider_priority.append(LLMProvider.MISTRAL)
                logger.info("✅ Mistral LLM initialized as primary")
            except Exception as e:
                logger.warning(f"⚠️ Mistral initialization failed: {e}")
        
        # Initialize Gemini as fallback
        if gemini_api_key and genai:
            try:
                self.providers[LLMProvider.GEMINI] = GeminiLLM(gemini_api_key)
                self.provider_priority.append(LLMProvider.GEMINI)
                logger.info("✅ Gemini LLM initialized as fallback")
            except Exception as e:
                logger.warning(f"⚠️ Gemini initialization failed: {e}")
        
        # Initialize Hugging Face if available
        if TRANSFORMERS_AVAILABLE:
            try:
                # Initialize Hugging Face with API key if available
                try:
                    from config import Config
                    config_instance = Config()
                    huggingface_api_key = config_instance.get_llm_config().get('huggingface_api_key')
                    if huggingface_api_key:
                        self.providers[LLMProvider.HUGGINGFACE] = HuggingFaceLLM(api_key=huggingface_api_key)
                        logger.info("✅ Hugging Face LLM initialized with API key")
                    else:
                        logger.warning("⚠️ Hugging Face API key not found, using fallback")
                        self.providers[LLMProvider.HUGGINGFACE] = HuggingFaceLLM()
                except Exception as e:
                    logger.warning(f"⚠️ Could not initialize Hugging Face with API key: {e}")
                    self.providers[LLMProvider.HUGGINGFACE] = HuggingFaceLLM()
                
                self.provider_priority.append(LLMProvider.HUGGINGFACE)
                logger.info("✅ Hugging Face LLM initialized")
            except Exception as e:
                logger.warning(f"⚠️ Hugging Face initialization failed: {e}")
        
        # Initialize Ollama if available
        if OLLAMA_AVAILABLE:
            try:
                self.providers[LLMProvider.OLLAMA] = OllamaLLM()
                self.provider_priority.append(LLMProvider.OLLAMA)
                logger.info("✅ Ollama LLM initialized")
            except Exception as e:
                logger.warning(f"⚠️ Ollama initialization failed: {e}")
        
        self.max_concurrent_extractions = 1  # Conservative for now
        self.extraction_timeout = 45.0
    
    def extract_jobs_from_html(self, html_content: str, source_url: str = "") -> ExtractionResult:
        """
        Extract jobs from HTML using the best available LLM
        
        Args:
            html_content: Raw HTML content
            source_url: Source URL for context
            
        Returns:
            ExtractionResult with job listings
        """
        if not self.providers:
            logger.error("❌ No LLM providers available")
            return ExtractionResult(
                jobs=[],
                success=False,
                provider="none",
                processing_time=0.0,
                confidence_score=0.0,
                errors=["No LLM providers available"]
            )
        
        logger.info(f"🧠 Starting LLM extraction from {source_url[:50]}...")
        
        # Try providers in priority order
        for provider in self.provider_priority:
            llm = self.providers.get(provider)
            if not llm:
                continue
            
            try:
                logger.info(f"🔄 Trying {provider.value} for extraction...")
                result = llm.extract_jobs(html_content, self.extraction_timeout)
                
                if result.success and result.jobs:
                    # Enrich jobs with source information
                    for job in result.jobs:
                        if not job.url and source_url:
                            job.url = source_url
                        job.source = source_url
                    
                    logger.info(f"✅ {provider.value} extracted {len(result.jobs)} jobs")
                    return result
                else:
                    logger.warning(f"⚠️ {provider.value} extraction failed or returned no jobs")
                    
            except Exception as e:
                logger.error(f"❌ {provider.value} extraction error: {e}")
                continue
        
        # All providers failed - try simple fallback extraction
        logger.warning("⚠️ All LLM providers failed, trying fallback extraction...")
        try:
            fallback_jobs = self._fallback_extraction(html_content, source_url)
            if fallback_jobs:
                logger.info(f"✅ Fallback extraction found {len(fallback_jobs)} jobs")
                return ExtractionResult(
                    jobs=fallback_jobs,
                    success=True,
                    provider="fallback",
                    processing_time=0.0,
                    confidence_score=0.3,
                    errors=[]
                )
        except Exception as e:
            logger.error(f"❌ Fallback extraction also failed: {e}")
        
        logger.error("❌ All extraction methods failed")
        return ExtractionResult(
            jobs=[],
            success=False,
            provider="failed",
            processing_time=0.0,
            confidence_score=0.0,
            errors=["All LLM providers failed"]
        )
    
    def validate_and_enhance_jobs(self, jobs: List[JobListing]) -> List[JobListing]:
        """Validate and enhance job listings"""
        enhanced_jobs = []
        
        for job in jobs:
            try:
                # Basic validation
                if not all([job.title, job.company, job.location, job.summary]):
                    logger.warning(f"⚠️ Skipping incomplete job: {job.title}")
                    continue
                
                # URL validation
                if job.url and not job.url.startswith(('http://', 'https://')):
                    logger.warning(f"⚠️ Invalid URL for {job.title}: {job.url}")
                    job.url = ""
                
                # Enhance with additional processing
                job = self._enhance_single_job(job)
                enhanced_jobs.append(job)
                
            except Exception as e:
                logger.warning(f"⚠️ Error validating job {job.title}: {e}")
                continue
        
        logger.info(f"✅ Validated {len(enhanced_jobs)}/{len(jobs)} jobs")
        return enhanced_jobs
    
    def _fallback_extraction(self, html_content: str, source_url: str) -> List[JobListing]:
        """Simple fallback extraction using basic HTML parsing"""
        try:
            from bs4 import BeautifulSoup
            import re
            
            soup = BeautifulSoup(html_content, 'html.parser')
            jobs = []
            
            # Look for common job title patterns
            job_title_selectors = [
                'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                '.job-title', '.title', '.position',
                '[class*="title"]', '[class*="position"]'
            ]
            
            # Look for company name patterns
            company_selectors = [
                '.company', '.employer', '.organization',
                '[class*="company"]', '[class*="employer"]'
            ]
            
            # Extract potential job titles
            job_titles = []
            for selector in job_title_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    if text and len(text) > 5 and len(text) < 100:
                        # Check if it looks like a job title
                        if any(keyword in text.lower() for keyword in ['engineer', 'developer', 'designer', 'manager', 'analyst', 'specialist', 'coordinator']):
                            job_titles.append(text)
            
            # Extract potential company names
            company_names = []
            for selector in company_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    if text and len(text) > 2 and len(text) < 50:
                        company_names.append(text)
            
            # Create job listings from extracted data
            if job_titles:
                for title in job_titles[:3]:  # Limit to 3 jobs
                    job = JobListing(
                        title=title,
                        company=company_names[0] if company_names else "Company not specified",
                        location="Location not specified",
                        summary=f"Job posting for {title}",
                        url=source_url,
                        source=source_url,
                        salary="Salary not specified",
                        requirements=[],
                        experience_level="Not specified",
                        job_type="Not specified",
                        skills=[],
                        confidence_score=0.3,
                        extraction_method="fallback"
                    )
                    jobs.append(job)
            
            return jobs
            
        except Exception as e:
            logger.error(f"❌ Fallback extraction failed: {e}")
            return []

    def _enhance_single_job(self, job: JobListing) -> JobListing:
        """Enhance a single job listing"""
        # Normalize location
        if job.location:
            job.location = self._normalize_location(job.location)
        
        # Extract skills from requirements and summary
        if not job.skills:
            job.skills = self._extract_skills(job.summary + " " + " ".join(job.requirements or []))
        
        # Determine experience level from title/requirements
        if not job.experience_level:
            job.experience_level = self._determine_experience_level(job.title, job.requirements or [])
        
        # Boost confidence score based on completeness
        completeness_score = sum([
            bool(job.title),
            bool(job.company),
            bool(job.location),
            bool(job.summary),
            bool(job.url),
            bool(job.salary),
            bool(job.requirements),
            bool(job.skills)
        ]) / 8.0
        
        job.confidence_score = min(job.confidence_score + completeness_score * 0.2, 1.0)
        
        return job
    
    def _normalize_location(self, location: str) -> str:
        """Normalize location strings"""
        location = location.strip()
        
        # Common normalizations
        normalizations = {
            'dhaka': 'Dhaka, Bangladesh',
            'chittagong': 'Chittagong, Bangladesh',
            'sylhet': 'Sylhet, Bangladesh',
            'remote': 'Remote',
            'bangladesh': 'Bangladesh'
        }
        
        location_lower = location.lower()
        for key, value in normalizations.items():
            if key in location_lower and value not in location:
                return value
        
        return location
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract technical skills from text"""
        if not text:
            return []
        
        # Common technical skills
        skills_patterns = [
            r'\b(python|java|javascript|react|node\.?js|angular|vue|php|c\+\+|c#|ruby|go|rust|swift|kotlin)\b',
            r'\b(html|css|sql|mongodb|postgresql|mysql|redis|elasticsearch)\b',
            r'\b(aws|azure|gcp|docker|kubernetes|jenkins|git|linux|windows)\b',
            r'\b(machine learning|ai|data science|blockchain|devops|frontend|backend|fullstack)\b'
        ]
        
        skills = set()
        text_lower = text.lower()
        
        for pattern in skills_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            skills.update(matches)
        
        return list(skills)[:10]  # Limit to 10 skills
    
    def _determine_experience_level(self, title: str, requirements: List[str]) -> str:
        """Determine experience level from title and requirements"""
        text = (title + " " + " ".join(requirements or [])).lower()
        
        if any(word in text for word in ['senior', 'lead', 'principal', 'architect', '5+ years', '7+ years']):
            return 'Senior'
        elif any(word in text for word in ['junior', 'entry', 'graduate', 'fresher', '0-2 years']):
            return 'Entry Level'
        elif any(word in text for word in ['mid', 'intermediate', '2-5 years', '3+ years']):
            return 'Mid Level'
        
        return 'Not specified'
    
    def get_provider_status(self) -> Dict[str, Dict]:
        """Get status of all LLM providers"""
        status = {}
        for provider in LLMProvider:
            status[provider.value] = {
                'available': provider in self.providers,
                'initialized': provider in self.providers,
                'priority': self.provider_priority.index(provider) if provider in self.provider_priority else -1
            }
        return status

# Test functionality
if __name__ == "__main__":
    # Test the enhanced LLM pipeline
    print("🧪 Testing Enhanced LLM Pipeline...")
    print("=" * 50)
    
    # Mock HTML content for testing
    test_html = """
    <div class="job-listing">
        <h2>Software Engineer</h2>
        <div class="company">TechCorp Ltd</div>
        <div class="location">Dhaka, Bangladesh</div>
        <p class="description">We are looking for a skilled software engineer with Python and React experience.</p>
        <div class="requirements">
            <ul>
                <li>3+ years Python experience</li>
                <li>React and JavaScript knowledge</li>
                <li>Experience with AWS</li>
            </ul>
        </div>
    </div>
    """
    
    # Test without API key (will use fallback)
    pipeline = EnhancedLLMPipeline()
    
    print(f"🔧 Provider Status:")
    status = pipeline.get_provider_status()
    for provider, info in status.items():
        print(f"   {provider}: {'✅' if info['available'] else '❌'} Available")
    
    if pipeline.providers:
        print(f"\n🧠 Testing job extraction...")
        result = pipeline.extract_jobs_from_html(test_html, "https://example.com/jobs")
        
        print(f"✅ Extraction Result:")
        print(f"   Success: {result.success}")
        print(f"   Provider: {result.provider}")
        print(f"   Jobs found: {len(result.jobs)}")
        print(f"   Processing time: {result.processing_time:.2f}s")
        print(f"   Confidence: {result.confidence_score:.2f}")
        
        for i, job in enumerate(result.jobs, 1):
            print(f"\n   Job {i}:")
            print(f"     Title: {job.title}")
            print(f"     Company: {job.company}")
            print(f"     Location: {job.location}")
            print(f"     Skills: {', '.join(job.skills) if job.skills else 'None'}")
            print(f"     Confidence: {job.confidence_score:.2f}")
    else:
        print("❌ No LLM providers available for testing")
