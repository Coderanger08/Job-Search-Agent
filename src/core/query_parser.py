"""
Pure LLM-powered Query Parser for Bangladesh Job Search RAG System
Uses DeepSeek to understand natural language queries and extract structured information.
"""

import json
import re
import requests
import logging
from typing import Dict, List, Any, Optional
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config import Config

logger = logging.getLogger(__name__)


class QueryParser:
    """LLM-powered query parser for understanding job search queries"""
    
    # Job role mapping for semantic search
    JOB_ROLE_MAPPING = {
        "ai engineer": [
            "AI Engineer", "Artificial Intelligence Engineer", "Machine Learning Engineer", 
            "ML Engineer", "AI/ML Engineer", "Deep Learning Engineer", "AI Developer",
            "Machine Learning Developer", "AI Research Engineer", "AI Software Engineer"
        ],
        "software engineer": [
            "Software Engineer", "Software Developer", "Developer", "Programmer",
            "Full Stack Developer", "Backend Developer", "Frontend Developer",
            "Web Developer", "Application Developer", "Software Programmer"
        ],
        "data scientist": [
            "Data Scientist", "Data Analyst", "Data Engineer", "Business Intelligence Analyst",
            "Data Science Engineer", "Analytics Engineer", "Data Science Developer"
        ],
        "designer": [
            "Designer", "Graphic Designer", "UI/UX Designer", "Product Designer",
            "Visual Designer", "Web Designer", "Creative Designer", "UI Designer", "UX Designer"
        ],
        "manager": [
            "Manager", "Project Manager", "Product Manager", "Program Manager",
            "Engineering Manager", "Development Manager", "Team Lead", "Lead"
        ],
        "analyst": [
            "Analyst", "Business Analyst", "Systems Analyst", "Data Analyst",
            "Financial Analyst", "Market Analyst", "Research Analyst"
        ]
    }
    
    def __init__(self):
        """Initialize the query parser with Mistral LLM"""
        self.config = Config()
        self.llm_config = self.config.get_llm_config()
        
        # Initialize Mistral via Hugging Face
        if self.llm_config.get("huggingface_api_key"):
            self.huggingface_api_key = self.llm_config["huggingface_api_key"]
            self.api_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
            self.headers = {
                "Authorization": f"Bearer {self.huggingface_api_key}",
                "Content-Type": "application/json"
            }
            logger.info("✅ Mistral initialized for query parsing")
        else:
            raise ValueError("Hugging Face API key is required for query parsing")
        
        # Query parsing prompt template
        self.parsing_prompt = """
You are a job search query parser for Bangladesh. Extract structured information from user queries.

Parse the following job search query and return a JSON object with these fields:
- job_type: The main job role/position (e.g., "python developer", "ui/ux designer")
- location: The job location (e.g., "dhaka", "chittagong", "remote")
- skills: List of required skills/technologies (e.g., ["python", "react", "django"])
- experience_level: Experience level if mentioned (e.g., "entry level", "senior", "mid level")
- salary_range: Salary range if mentioned (e.g., "above 50k", "30k-60k")
- company: Company name if mentioned (e.g., "daffodil group", "google")
- remote: Boolean indicating if remote work is requested
- additional_keywords: Any other relevant keywords for search

Examples:

# Basic Job Search Queries
Query: "Find Python developer jobs in Dhaka"
Output: {"job_type": "python developer", "location": "dhaka", "skills": ["python"], "experience_level": null, "salary_range": null, "company": null, "remote": false, "additional_keywords": []}

Query: "Show me software engineer positions"
Output: {"job_type": "software engineer", "location": null, "skills": [], "experience_level": null, "salary_range": null, "company": null, "remote": false, "additional_keywords": []}

Query: "Looking for UI/UX designer roles"
Output: {"job_type": "ui/ux designer", "location": null, "skills": [], "experience_level": null, "salary_range": null, "company": null, "remote": false, "additional_keywords": []}

# Experience Level Queries
Query: "Senior React developer jobs with salary above 80k BDT"
Output: {"job_type": "react developer", "location": null, "skills": ["react"], "experience_level": "senior", "salary_range": "above 80k", "company": null, "remote": false, "additional_keywords": []}

Query: "Entry level marketing positions"
Output: {"job_type": "marketing", "location": null, "skills": [], "experience_level": "entry level", "salary_range": null, "company": null, "remote": false, "additional_keywords": []}

Query: "Junior developer jobs for freshers"
Output: {"job_type": "developer", "location": null, "skills": [], "experience_level": "junior", "salary_range": null, "company": null, "remote": false, "additional_keywords": ["freshers"]}

# Remote Work Queries
Query: "Remote UI/UX designer positions"
Output: {"job_type": "ui/ux designer", "location": null, "skills": [], "experience_level": null, "salary_range": null, "company": null, "remote": true, "additional_keywords": []}

Query: "Work from home developer jobs"
Output: {"job_type": "developer", "location": null, "skills": [], "experience_level": null, "salary_range": null, "company": null, "remote": true, "additional_keywords": []}

Query: "Online marketing positions"
Output: {"job_type": "marketing", "location": null, "skills": [], "experience_level": null, "salary_range": null, "company": null, "remote": true, "additional_keywords": []}

# Company-Focused Queries
Query: "Show me jobs at Daffodil Group"
Output: {"job_type": "job", "location": null, "skills": [], "experience_level": null, "salary_range": null, "company": "daffodil group", "remote": false, "additional_keywords": []}

Query: "Jobs at Google Bangladesh"
Output: {"job_type": "job", "location": null, "skills": [], "experience_level": null, "salary_range": null, "company": "google", "remote": false, "additional_keywords": []}

Query: "What companies hire Python developers?"
Output: {"job_type": "python developer", "location": null, "skills": ["python"], "experience_level": null, "salary_range": null, "company": null, "remote": false, "additional_keywords": ["companies"]}

# Skill-Based Queries
Query: "Jobs requiring Python and Django"
Output: {"job_type": "developer", "location": null, "skills": ["python", "django"], "experience_level": null, "salary_range": null, "company": null, "remote": false, "additional_keywords": []}

Query: "Find jobs requiring React and Node.js"
Output: {"job_type": "developer", "location": null, "skills": ["react", "node.js"], "experience_level": null, "salary_range": null, "company": null, "remote": false, "additional_keywords": []}

Query: "What skills are needed for UI Designer jobs?"
Output: {"job_type": "ui designer", "location": null, "skills": [], "experience_level": null, "salary_range": null, "company": null, "remote": false, "additional_keywords": ["skills needed"]}

# Location Variations
Query: "Software Engineer jobs in Bangladesh"
Output: {"job_type": "software engineer", "location": "bangladesh", "skills": [], "experience_level": null, "salary_range": null, "company": null, "remote": false, "additional_keywords": []}

Query: "Remote developer positions"
Output: {"job_type": "developer", "location": null, "skills": [], "experience_level": null, "salary_range": null, "company": null, "remote": true, "additional_keywords": []}

Query: "Jobs in Dhaka and Chittagong"
Output: {"job_type": "job", "location": "dhaka", "skills": [], "experience_level": null, "salary_range": null, "company": null, "remote": false, "additional_keywords": ["chittagong"]}

# Salary Queries
Query: "High paying software engineer jobs"
Output: {"job_type": "software engineer", "location": null, "skills": [], "experience_level": null, "salary_range": "high paying", "company": null, "remote": false, "additional_keywords": []}

Query: "Jobs with salary above 50k BDT"
Output: {"job_type": "job", "location": null, "skills": [], "experience_level": null, "salary_range": "above 50k", "company": null, "remote": false, "additional_keywords": []}

Query: "What's the average salary for Software Engineers?"
Output: {"job_type": "software engineer", "location": null, "skills": [], "experience_level": null, "salary_range": "average", "company": null, "remote": false, "additional_keywords": ["salary information"]}

# Conversational Queries
Query: "I'm looking for a marketing job"
Output: {"job_type": "marketing", "location": null, "skills": [], "experience_level": null, "salary_range": null, "company": null, "remote": false, "additional_keywords": []}

Query: "Help me find graphic design work"
Output: {"job_type": "graphic designer", "location": null, "skills": [], "experience_level": null, "salary_range": null, "company": null, "remote": false, "additional_keywords": []}

Query: "Need a data scientist position"
Output: {"job_type": "data scientist", "location": null, "skills": [], "experience_level": null, "salary_range": null, "company": null, "remote": false, "additional_keywords": []}

# Complex Queries
Query: "Senior full stack developer jobs in Dhaka with React and Node.js experience"
Output: {"job_type": "full stack developer", "location": "dhaka", "skills": ["react", "node.js"], "experience_level": "senior", "salary_range": null, "company": null, "remote": false, "additional_keywords": []}

Query: "Remote Python developer positions at startups with competitive salary"
Output: {"job_type": "python developer", "location": null, "skills": ["python"], "experience_level": null, "salary_range": "competitive", "company": null, "remote": true, "additional_keywords": ["startups"]}

Now parse this query: "{query}"

Return only the JSON object, no additional text.
"""
    
    def parse_query(self, query: str) -> Dict[str, Any]:
        """
        Parse a natural language job search query using fast fallback parsing
        
        Args:
            query: Natural language query from user
            
        Returns:
            Dictionary with structured query information
        """
        # Use fast fallback parsing for better performance
        return self._fallback_parse(query)
    
    def _clean_query(self, query: str) -> str:
        """Clean and normalize the query"""
        # Remove extra whitespace
        query = re.sub(r'\s+', ' ', query.strip())
        
        # Convert to lowercase for consistency
        query = query.lower()
        
        return query
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response and extract JSON with enhanced error handling"""
        try:
            # Clean the response first
            response = response.strip()
            
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                
                # Clean up common JSON issues
                json_str = json_str.replace('None', 'null')  # Fix Python None
                json_str = json_str.replace('True', 'true')  # Fix Python True
                json_str = json_str.replace('False', 'false')  # Fix Python False
                
                # Fix unquoted keys
                json_str = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_str)
                
                # Fix unquoted string values
                json_str = re.sub(r':\s*([a-zA-Z_][a-zA-Z0-9_\s]+)\s*([,}])', r':"\1"\2', json_str)
                
                # Try to parse
                parsed = json.loads(json_str)
                
                # Validate required fields
                if 'job_type' not in parsed:
                    raise ValueError("Missing job_type field")
                
                return parsed
            else:
                raise ValueError("No JSON found in LLM response")
                
        except (json.JSONDecodeError, ValueError) as e:
            print(f"JSON parsing error: {e}")
            print(f"Response was: {response}")
            # Use the original query for fallback instead of the response
            return None
    
    def _create_fallback_parsed_data(self, response: str) -> Dict[str, Any]:
        """Create fallback parsed data when JSON parsing fails"""
        # Extract basic information from the response text
        response_lower = response.lower()
        
        # Try to extract job type from common patterns
        job_type = None
        if 'ai engineer' in response_lower or 'artificial intelligence' in response_lower:
            job_type = 'ai engineer'
        elif 'software engineer' in response_lower or 'developer' in response_lower:
            job_type = 'software engineer'
        elif 'designer' in response_lower:
            job_type = 'designer'
        elif 'manager' in response_lower:
            job_type = 'manager'
        elif 'analyst' in response_lower:
            job_type = 'analyst'
        else:
            job_type = 'job'
        
        return {
            "job_type": job_type,
            "location": None,
            "skills": [],
            "experience_level": None,
            "salary_range": None,
            "company": None,
            "remote": False,
            "additional_keywords": [],
            "search_query": f"{job_type} jobs",
            "is_relevant": True
        }
    
    def _fallback_parse(self, query: str) -> Dict[str, Any]:
        """Fallback parsing when LLM fails - Enhanced version"""
        query_lower = query.lower()
        
        print(f"DEBUG: Fallback parsing query: '{query}' -> '{query_lower}'")
        
        # Check if query is job-related
        if not self._is_job_related(query_lower):
            return {
                "job_type": "job",
                "location": None,
                "skills": [],
                "experience_level": None,
                "salary_range": None,
                "company": None,
                "remote": False,
                "additional_keywords": [],
                "search_query": "jobs Bangladesh",  # Generic search
                "is_relevant": False,
                "suggestion": "Try searching for specific job types like 'software developer', 'marketing manager', etc."
            }
        
        # Enhanced job type extraction with priority for longer phrases
        job_type = None
        
        # Check for specific job types first (longer phrases) - these should take priority
        if 'ai engineer' in query_lower or 'artificial intelligence engineer' in query_lower or 'machine learning engineer' in query_lower:
            job_type = 'ai engineer'
            print(f"DEBUG: Found 'ai engineer' in query")
        elif 'software engineer' in query_lower or 'software developer' in query_lower:
            job_type = 'software engineer'
            print(f"DEBUG: Found 'software engineer' in query")
        elif 'data scientist' in query_lower or 'data analyst' in query_lower:
            job_type = 'data scientist'
            print(f"DEBUG: Found 'data scientist' in query")
        elif 'graphic designer' in query_lower or 'ui designer' in query_lower or 'ux designer' in query_lower:
            job_type = 'designer'
            print(f"DEBUG: Found 'designer' in query")
        elif 'project manager' in query_lower or 'product manager' in query_lower:
            job_type = 'manager'
            print(f"DEBUG: Found 'manager' in query")
        elif 'business analyst' in query_lower or 'systems analyst' in query_lower:
            job_type = 'analyst'
            print(f"DEBUG: Found 'analyst' in query")
        else:
            # Only if no longer phrases match, then check single words
            job_keywords = ["developer", "engineer", "designer", "manager", "analyst", "consultant", "job", "position", "role", "career"]
            for keyword in job_keywords:
                if keyword in query_lower:
                    job_type = keyword
                    print(f"DEBUG: Found single keyword '{keyword}' in query")
                    break
        
        if not job_type:
            job_type = "job"
            print(f"DEBUG: No job type found, using default 'job'")
        
        print(f"DEBUG: Final job_type: '{job_type}'")
        
        return {
            "job_type": job_type,
            "location": None,
            "skills": [],
            "experience_level": None,
            "salary_range": None,
            "company": None,
            "remote": False,
            "additional_keywords": [],
            "search_query": f"{job_type} jobs",
            "is_relevant": True
        }
    
    def _generate_search_query(self, parsed_data: Dict[str, Any]) -> str:
        """Generate a search query from parsed data with semantic role mapping"""
        job_type = parsed_data.get("job_type", "").lower()
        
        # Get semantic job role variations
        role_variations = self.JOB_ROLE_MAPPING.get(job_type, [job_type])
        
        # Build search query with role variations
        search_terms = []
        
        # Add primary job type and its variations
        if role_variations:
            # For AI Engineer, include specific variations
            if job_type == 'ai engineer':
                search_terms.extend(['ai engineer', 'artificial intelligence engineer', 'machine learning engineer', 'ml engineer'])
            else:
                search_terms.extend(role_variations[:3])  # Limit to top 3 variations
        
        # Add skills
        if parsed_data.get("skills"):
            search_terms.extend(parsed_data["skills"])
        
        # Add location
        if parsed_data.get("location"):
            search_terms.append(parsed_data["location"])
        
        # Add company
        if parsed_data.get("company"):
            search_terms.append(parsed_data["company"])
        
        # Add experience level
        if parsed_data.get("experience_level"):
            search_terms.append(parsed_data["experience_level"])
        
        # Add remote keyword if needed
        if parsed_data.get("remote"):
            search_terms.append("remote")
        
        # Add additional keywords
        if parsed_data.get("additional_keywords"):
            search_terms.extend(parsed_data["additional_keywords"])
        
        # Join and return
        search_query = " ".join(search_terms)
        return search_query
    
    def _fallback_parse(self, query: str) -> Dict[str, Any]:
        """Fallback parsing when LLM fails"""
        query_lower = query.lower()
        
        # Check if query is job-related
        if not self._is_job_related(query_lower):
            return {
                "job_type": "job",
                "location": None,
                "skills": [],
                "experience_level": None,
                "salary_range": None,
                "company": None,
                "remote": False,
                "additional_keywords": [],
                "search_query": "jobs Bangladesh",  # Generic search
                "is_relevant": False,
                "suggestion": "Try searching for specific job types like 'software developer', 'marketing manager', etc."
            }
        
        # Basic keyword extraction
        job_keywords = ["developer", "engineer", "designer", "manager", "analyst", "consultant", "job", "position", "role", "career"]
        location_keywords = ["dhaka", "chittagong", "sylhet", "remote", "bangladesh"]
        
        job_type = None
        location = None
        remote = False
        
        # Extract job type
        for keyword in job_keywords:
            if keyword in query_lower:
                job_type = keyword
                break
        
        # Extract location
        for keyword in location_keywords:
            if keyword in query_lower:
                if keyword == "remote":
                    remote = True
                else:
                    location = keyword
                break
        
        return {
            "job_type": job_type or "job",
            "location": location,
            "skills": [],
            "experience_level": None,
            "salary_range": None,
            "company": None,
            "remote": remote,
            "additional_keywords": [],
            "search_query": f"{query} jobs Bangladesh",
            "is_relevant": True
        }
    
    def _is_job_related(self, query: str) -> bool:
        """Check if query is job-related using Mistral LLM"""
        try:
            # Use Mistral to intelligently determine if query is job-related
            relevance_prompt = f"""
You are a job search assistant. Determine if the following user query is related to job searching, employment, careers, or work.

User Query: "{query}"

Respond with a JSON object:
{{
    "is_job_related": true/false,
    "reason": "brief explanation",
    "suggestion": "helpful suggestion for job search if relevant"
}}

Examples:
- "Find Python developer jobs" → {{"is_job_related": true, "reason": "Direct job search query", "suggestion": "Great! I can help you find Python developer positions."}}
- "What's the weather like?" → {{"is_job_related": false, "reason": "Weather query, not job-related", "suggestion": "I'm a job search assistant. Try asking about jobs, careers, or employment opportunities."}}
- "I need help with my resume" → {{"is_job_related": true, "reason": "Resume help is job-related", "suggestion": "I can help you find jobs that match your skills and experience."}}
- "Where can I buy groceries?" → {{"is_job_related": false, "reason": "Shopping query, not job-related", "suggestion": "I'm focused on job search. Try asking about job opportunities or career advice."}}

Respond only with the JSON object.
"""
            
            # Get Mistral response
            payload = {
                "inputs": relevance_prompt,
                "parameters": {
                    "max_new_tokens": 200,
                    "temperature": 0.1,
                    "do_sample": True,
                    "return_full_text": False
                }
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    content = result[0].get('generated_text', '')
                    
                    # Parse JSON response
                    try:
                        json_match = re.search(r'\{.*\}', content, re.DOTALL)
                        if json_match:
                            relevance_data = json.loads(json_match.group())
                            return relevance_data.get("is_job_related", False)
                    except:
                        pass
            
            # Fallback to keyword-based detection
            return self._fallback_relevance_check(query)
            
        except Exception as e:
            logger.error(f"Error checking relevance with Mistral: {e}")
            # Fallback to keyword-based detection
            return self._fallback_relevance_check(query)
    
    def _fallback_relevance_check(self, query: str) -> bool:
        """Fallback keyword-based relevance check"""
        query_lower = query.lower()
        
        # Job-related keywords
        job_keywords = [
            "job", "work", "career", "position", "role", "employment", "hire", "hiring",
            "developer", "engineer", "designer", "manager", "analyst", "consultant",
            "programmer", "coder", "architect", "specialist", "coordinator",
            "salary", "pay", "compensation", "benefits", "remote", "work from home",
            "full time", "part time", "contract", "freelance", "internship", "resume", "cv"
        ]
        
        # Non-job keywords (indicating irrelevant queries)
        non_job_keywords = [
            "weather", "temperature", "rain", "sunny", "hot", "cold",
            "food", "restaurant", "cook", "recipe", "eat", "dinner", "lunch",
            "movie", "film", "watch", "entertainment", "game", "play",
            "shopping", "buy", "purchase", "store", "market", "mall",
            "travel", "trip", "vacation", "holiday", "flight", "hotel",
            "health", "medical", "doctor", "hospital", "medicine", "sick",
            "sports", "football", "cricket", "basketball", "tennis",
            "music", "song", "concert", "band", "artist", "album"
        ]
        
        # Count job-related vs non-job keywords
        job_count = sum(1 for keyword in job_keywords if keyword in query_lower)
        non_job_count = sum(1 for keyword in non_job_keywords if keyword in query_lower)
        
        # Query is job-related if it has more job keywords than non-job keywords
        return job_count > non_job_count
    
    def _is_inappropriate_content(self, query: str) -> bool:
        """Check if query contains inappropriate or explicit content"""
        query_lower = query.lower()
        
        # Inappropriate content indicators (professional detection)
        inappropriate_patterns = [
            # Explicit content
            "porn", "xxx", "adult", "nsfw", "explicit", "sexual", "intimate",
            "nude", "naked", "sex", "dating", "hookup", "escort", "prostitute",
            
            # Violence
            "kill", "murder", "violence", "weapon", "gun", "bomb", "attack",
            "fight", "assault", "threat", "harm", "hurt", "injure",
            
            # Illegal activities
            "drug", "cocaine", "heroin", "marijuana", "weed", "illegal",
            "steal", "rob", "fraud", "scam", "hack", "crack", "pirate",
            
            # Hate speech
            "hate", "racist", "discriminate", "slur", "offensive", "insult",
            
            # Other inappropriate
            "curse", "swear", "fuck", "shit", "bitch", "damn", "hell"
        ]
        
        # Check for inappropriate patterns
        for pattern in inappropriate_patterns:
            if pattern in query_lower:
                return True
        
        return False
    
    def _get_intelligent_response(self, query: str) -> Dict[str, Any]:
        """Get intelligent response for irrelevant queries using Mistral"""
        try:
            response_prompt = f"""
You are a professional job search assistant. A user asked a question that's not related to job searching: "{query}"

IMPORTANT: If the query contains explicit, inappropriate, or 18+ content, respond professionally and redirect to job search topics.

Provide a professional, helpful response that:
1. Acknowledges their question professionally
2. Explains that you're a job search assistant
3. Offers to help with job-related questions
4. Gives examples of what you can help with

Keep your response concise, professional, and appropriate. Respond with a JSON object:
{{
    "response": "your professional response",
    "suggestions": ["suggestion 1", "suggestion 2", "suggestion 3"],
    "is_inappropriate": true/false
}}

Examples:
- For "What's the weather like?" → {{"response": "I'm a job search assistant, so I can't help with weather info. But I can help you find jobs! Try asking about job opportunities, career advice, or resume tips.", "suggestions": ["Search for job opportunities", "Get career guidance", "Find resume tips"], "is_inappropriate": false}}
- For explicit content → {{"response": "I'm a professional job search assistant focused on helping with careers and employment. I can help you find job opportunities, improve your resume, or explore career paths.", "suggestions": ["Search for job opportunities", "Get career guidance", "Find resume tips"], "is_inappropriate": true}}

Respond only with the JSON object.
"""
            
            payload = {
                "inputs": response_prompt,
                "parameters": {
                    "max_new_tokens": 300,
                    "temperature": 0.3,
                    "do_sample": True,
                    "return_full_text": False
                }
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    content = result[0].get('generated_text', '')
                    
                    # Parse JSON response
                    try:
                        json_match = re.search(r'\{.*\}', content, re.DOTALL)
                        if json_match:
                            return json.loads(json_match.group())
                    except:
                        pass
            
            # Fallback response
            return {
                "response": f"I'm a job search assistant, so I can't help with '{query}'. But I can help you find jobs, explore careers, or get career advice!",
                "suggestions": [
                    "Try asking about job opportunities",
                    "Ask for career advice",
                    "Get help with your resume"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting intelligent response: {e}")
            return {
                "response": "I'm a job search assistant. I can help you find jobs, explore careers, or get career advice!",
                "suggestions": [
                    "Search for specific job types",
                    "Get career guidance",
                    "Find resume tips"
                ]
            }
    
    def get_search_templates(self, parsed_data: Dict[str, Any]) -> List[str]:
        """Generate search query templates for different data sources"""
        templates = []
        search_templates = self.config.get_search_templates()
        
        # Basic job search template
        if parsed_data.get("job_type") and parsed_data.get("location"):
            template = search_templates["job_search"].format(
                job_type=parsed_data["job_type"],
                location=parsed_data["location"]
            )
            templates.append(template)
        
        # Company search template
        if parsed_data.get("company"):
            template = search_templates["company_search"].format(
                company=parsed_data["company"]
            )
            templates.append(template)
        
        # Skill search template
        if parsed_data.get("skills"):
            for skill in parsed_data["skills"]:
                template = search_templates["skill_search"].format(skill=skill)
                templates.append(template)
        
        # Remote search template
        if parsed_data.get("remote"):
            template = search_templates["remote_search"].format(
                job_type=parsed_data.get("job_type", "job")
            )
            templates.append(template)
        
        return templates
    
    def search_jobs_with_database(self, query: str, job_db_manager, limit: int = 20) -> Dict[str, Any]:
        """
        Search jobs using the job database manager with parsed query
        
        Args:
            query: Natural language query
            job_db_manager: JobDatabaseManager instance
            limit: Maximum number of results
            
        Returns:
            Dictionary with results and metadata
        """
        try:
            # Parse the query
            parsed_data = self.parse_query(query)
            
            # Check for inappropriate content first
            if self._is_inappropriate_content(query):
                return {
                    "jobs": [],
                    "is_relevant": False,
                    "is_inappropriate": True,
                    "response": "I'm a professional job search assistant focused on helping with careers and employment. I can help you find job opportunities, improve your resume, or explore career paths.",
                    "suggestions": [
                        "Search for job opportunities",
                        "Get career guidance", 
                        "Find resume tips"
                    ],
                    "parsed_data": parsed_data
                }
            
            # Check if query is relevant
            if not parsed_data.get("is_relevant", True):
                # Get intelligent response for irrelevant query
                intelligent_response = self._get_intelligent_response(query)
                return {
                    "jobs": [],
                    "is_relevant": False,
                    "is_inappropriate": intelligent_response.get("is_inappropriate", False),
                    "response": intelligent_response.get("response", "I'm a job search assistant. I can help you find jobs!"),
                    "suggestions": intelligent_response.get("suggestions", ["Try asking about job opportunities"]),
                    "parsed_data": parsed_data
                }
            
            # Build search parameters
            search_params = self._build_search_params(parsed_data)
            
            # Search using job database manager
            results = job_db_manager.search_jobs(
                query=search_params["query"],
                location=search_params["location"],
                experience_level=search_params["experience_level"],
                limit=limit
            )
            
            # Apply additional filters
            if search_params["filters"]:
                results = self._apply_additional_filters(results, search_params["filters"])
            
            return {
                "jobs": results,
                "is_relevant": True,
                "parsed_data": parsed_data,
                "search_params": search_params
            }
            
        except Exception as e:
            logger.error(f"Error searching jobs: {e}")
            # Fallback to basic search
            fallback_results = job_db_manager.search_jobs(query, limit=limit)
            return {
                "jobs": fallback_results,
                "is_relevant": True,
                "parsed_data": {"job_type": "job", "search_query": query},
                "error": str(e)
            }
    
    def _build_search_params(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build search parameters for job database manager"""
        # Use the enhanced search query that was already generated
        search_query = parsed_data.get("search_query", "")
        
        # If no search query was generated, build one using the enhanced method
        if not search_query:
            search_query = self._generate_search_query(parsed_data)
        
        # Build filters
        filters = {}
        
        if parsed_data.get("location") and not parsed_data.get("remote"):
            filters["location"] = parsed_data["location"]
        
        if parsed_data.get("experience_level"):
            filters["experience_level"] = parsed_data["experience_level"]
        
        if parsed_data.get("remote"):
            filters["remote"] = True
        
        if parsed_data.get("salary_range"):
            filters["salary_range"] = parsed_data["salary_range"]
        
        return {
            "query": search_query,
            "location": parsed_data.get("location"),
            "experience_level": parsed_data.get("experience_level"),
            "filters": filters
        }
    
    def _apply_additional_filters(self, jobs: List[Any], filters: Dict[str, Any]) -> List[Any]:
        """Apply additional filters to job results"""
        filtered_jobs = jobs
        
        # Filter by remote work
        if filters.get("remote"):
            filtered_jobs = [job for job in filtered_jobs 
                           if "remote" in job.location.lower() or 
                              "work from home" in job.title.lower()]
        
        # Filter by salary range (basic implementation)
        if filters.get("salary_range"):
            salary_filter = filters["salary_range"].lower()
            if "above" in salary_filter or "high" in salary_filter:
                # Keep jobs with salary information
                filtered_jobs = [job for job in filtered_jobs if job.salary]
        
        return filtered_jobs
    
    def validate_parsed_data(self, parsed_data: Dict[str, Any]) -> bool:
        """Validate that parsed data has required fields"""
        required_fields = ["job_type", "search_query"]
        
        for field in required_fields:
            if not parsed_data.get(field):
                return False
        
        return True
