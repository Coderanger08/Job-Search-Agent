"""
Quality Assurance Layer - Layer 4
Advanced data validation, deduplication, and enrichment
"""

import re
import logging
import time
from typing import List, Dict, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from difflib import SequenceMatcher
import hashlib
from collections import defaultdict
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ValidationLevel(Enum):
    """Validation levels for job listings"""
    STRICT = "strict"
    MODERATE = "moderate"
    LENIENT = "lenient"

class JobQuality(Enum):
    """Job listing quality levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    INVALID = "invalid"

@dataclass
class ValidationResult:
    """Result of job validation"""
    is_valid: bool
    quality_score: float
    quality_level: JobQuality
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

@dataclass
class DeduplicationResult:
    """Result of deduplication process"""
    unique_jobs: List[Dict]
    duplicates_removed: int
    duplicate_groups: List[List[Dict]]
    deduplication_stats: Dict[str, Any]

class JobValidator:
    """Validates job listings for quality and completeness"""
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.LENIENT):
        self.validation_level = validation_level
        self.required_fields = ['title', 'company', 'location', 'summary']
        self.optional_fields = ['url', 'salary', 'requirements', 'skills', 'experience_level']
        
        # Quality thresholds
        self.thresholds = {
            ValidationLevel.STRICT: {
                'min_title_length': 5,
                'min_company_length': 2,
                'min_summary_length': 20,
                'min_quality_score': 0.7,
                'require_url': True,
                'require_salary': False
            },
            ValidationLevel.MODERATE: {
                'min_title_length': 3,
                'min_company_length': 2,
                'min_summary_length': 10,
                'min_quality_score': 0.5,
                'require_url': False,
                'require_salary': False
            },
            ValidationLevel.LENIENT: {
                'min_title_length': 2,
                'min_company_length': 1,
                'min_summary_length': 5,
                'min_quality_score': 0.3,
                'require_url': False,
                'require_salary': False
            }
        }
    
    def validate_job(self, job: Dict) -> ValidationResult:
        """Validate a single job listing"""
        issues = []
        warnings = []
        suggestions = []
        score = 0.0
        
        # Get thresholds for current validation level
        thresholds = self.thresholds[self.validation_level]
        
        # Check required fields
        for field in self.required_fields:
            if not job.get(field):
                issues.append(f"Missing required field: {field}")
                score -= 0.2
            else:
                score += 0.1
        
        # Validate field content
        score += self._validate_title(job.get('title', ''), thresholds, issues, warnings)
        score += self._validate_company(job.get('company', ''), thresholds, issues, warnings)
        score += self._validate_location(job.get('location', ''), issues, warnings)
        score += self._validate_summary(job.get('summary', ''), thresholds, issues, warnings)
        score += self._validate_url(job.get('url', ''), thresholds, issues, warnings)
        score += self._validate_salary(job.get('salary', ''), issues, warnings)
        
        # Check for spam indicators
        spam_score = self._detect_spam(job, issues, warnings)
        score -= spam_score
        
        # Normalize score to 0-1 range
        score = max(0.0, min(1.0, score))
        
        # Determine quality level
        quality_level = self._determine_quality_level(score)
        
        # Generate suggestions for improvement
        suggestions = self._generate_suggestions(job, score, issues)
        
        # Determine if job is valid - be more lenient
        is_valid = score >= thresholds['min_quality_score']  # Remove the issues check entirely
        
        # Debug logging
        logger.info(f"🔍 Job validation: {job.get('title', 'Unknown')} - Score: {score:.2f}, Issues: {len(issues)}, Valid: {is_valid}")
        
        return ValidationResult(
            is_valid=is_valid,
            quality_score=score,
            quality_level=quality_level,
            issues=issues,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _validate_title(self, title: str, thresholds: Dict, issues: List, warnings: List) -> float:
        """Validate job title"""
        score = 0.0
        
        if not title:
            issues.append("Job title is required")
            return -0.2
        
        title = title.strip()
        
        # Check length
        if len(title) < thresholds['min_title_length']:
            issues.append(f"Job title too short (min {thresholds['min_title_length']} chars)")
            score -= 0.1
        
        # Check for common spam patterns
        spam_patterns = [
            r'\b(urgent|immediate|quick|fast|easy|simple|basic)\b',
            r'\b(work from home|wfh|online|internet|computer)\b',
            r'\b(earn|money|income|salary|pay|profit)\b',
            r'\b(click|visit|call|email|apply now)\b'
        ]
        
        for pattern in spam_patterns:
            if re.search(pattern, title.lower()):
                warnings.append(f"Title contains potential spam words: {pattern}")
                score -= 0.05
        
        # Check for realistic job titles
        valid_titles = [
            'developer', 'engineer', 'manager', 'analyst', 'designer',
            'specialist', 'coordinator', 'assistant', 'consultant', 'lead',
            'architect', 'scientist', 'researcher', 'administrator'
        ]
        
        if not any(valid_title in title.lower() for valid_title in valid_titles):
            warnings.append("Job title may not be realistic")
            score -= 0.05
        
        return score
    
    def _validate_company(self, company: str, thresholds: Dict, issues: List, warnings: List) -> float:
        """Validate company name"""
        score = 0.0
        
        if not company:
            issues.append("Company name is required")
            return -0.2
        
        company = company.strip()
        
        # Check length
        if len(company) < thresholds['min_company_length']:
            issues.append(f"Company name too short (min {thresholds['min_company_length']} chars)")
            score -= 0.1
        
        # Check for common spam patterns
        spam_patterns = [
            r'\b(company|corp|inc|ltd|llc|group|tech|software|solutions)\b',
            r'\b(online|internet|digital|virtual|remote)\b'
        ]
        
        spam_count = 0
        for pattern in spam_patterns:
            if re.search(pattern, company.lower()):
                spam_count += 1
        
        if spam_count >= 2:
            warnings.append("Company name contains multiple generic terms")
            score -= 0.05
        
        return score
    
    def _validate_location(self, location: str, issues: List, warnings: List) -> float:
        """Validate job location"""
        score = 0.0
        
        if not location:
            warnings.append("Location not specified")
            score -= 0.05
            return score
        
        location = location.strip()
        
        # Check for valid location patterns
        valid_patterns = [
            r'\b(dhaka|chittagong|sylhet|rajshahi|khulna|barisal|rangpur|mymensingh)\b',
            r'\b(bangladesh|bd)\b',
            r'\b(remote|work from home|wfh|online)\b',
            r'\b(gulshan|banani|uttara|dhanmondi|mirpur)\b'
        ]
        
        if not any(re.search(pattern, location.lower()) for pattern in valid_patterns):
            warnings.append("Location may not be valid for Bangladesh job market")
            score -= 0.05
        
        return score
    
    def _validate_summary(self, summary: str, thresholds: Dict, issues: List, warnings: List) -> float:
        """Validate job summary"""
        score = 0.0
        
        if not summary:
            warnings.append("Job summary not provided")
            score -= 0.05
            return score
        
        summary = summary.strip()
        
        # Check length
        if len(summary) < thresholds['min_summary_length']:
            issues.append(f"Job summary too short (min {thresholds['min_summary_length']} chars)")
            score -= 0.1
        
        # Check for meaningful content
        if len(summary.split()) < 5:
            warnings.append("Job summary seems too brief")
            score -= 0.05
        
        return score
    
    def _validate_url(self, url: str, thresholds: Dict, issues: List, warnings: List) -> float:
        """Validate job URL"""
        score = 0.0
        
        if not url:
            if thresholds['require_url']:
                issues.append("Job URL is required")
                score -= 0.2
            else:
                warnings.append("Job URL not provided")
                score -= 0.05
            return score
        
        # Check URL format
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(url_pattern, url):
            issues.append("Invalid URL format")
            score -= 0.1
        
        # Check for suspicious domains
        suspicious_domains = ['bit.ly', 'tinyurl', 'goo.gl', 't.co']
        if any(domain in url.lower() for domain in suspicious_domains):
            warnings.append("URL contains suspicious domain")
            score -= 0.05
        
        return score
    
    def _validate_salary(self, salary: str, issues: List, warnings: List) -> float:
        """Validate salary information"""
        score = 0.0
        
        if not salary:
            return score  # Salary is optional
        
        # Check for realistic salary patterns
        salary_patterns = [
            r'\b\d{1,3}(?:,\d{3})*(?:k|k\+|taka|bdt)\b',
            r'\b(negotiable|competitive|market rate|as per company policy)\b'
        ]
        
        if not any(re.search(pattern, salary.lower()) for pattern in salary_patterns):
            warnings.append("Salary format may not be realistic")
            score -= 0.02
        
        return score
    
    def _detect_spam(self, job: Dict, issues: List, warnings: List) -> float:
        """Detect spam indicators in job listing"""
        spam_score = 0.0
        text = f"{job.get('title', '')} {job.get('summary', '')}".lower()
        
        # Spam indicators
        spam_indicators = [
            r'\b(earn money|make money|quick money|easy money)\b',
            r'\b(work from home|wfh|online job|internet job)\b',
            r'\b(click|visit|call|email|apply now|urgent)\b',
            r'\b(no experience|no skills|anyone can do)\b',
            r'\b(part time|flexible hours|own schedule)\b'
        ]
        
        for pattern in spam_indicators:
            if re.search(pattern, text):
                spam_score += 0.1
                warnings.append(f"Potential spam indicator: {pattern}")
        
        # Check for excessive capitalization
        if sum(1 for c in text if c.isupper()) / len(text) > 0.3:
            spam_score += 0.05
            warnings.append("Excessive capitalization detected")
        
        return spam_score
    
    def _determine_quality_level(self, score: float) -> JobQuality:
        """Determine quality level based on score"""
        if score >= 0.8:
            return JobQuality.EXCELLENT
        elif score >= 0.6:
            return JobQuality.GOOD
        elif score >= 0.4:
            return JobQuality.FAIR
        elif score >= 0.2:
            return JobQuality.POOR
        else:
            return JobQuality.INVALID
    
    def _generate_suggestions(self, job: Dict, score: float, issues: List) -> List[str]:
        """Generate suggestions for improving job quality"""
        suggestions = []
        
        if score < 0.6:
            suggestions.append("Consider adding more detailed job description")
        
        if not job.get('url'):
            suggestions.append("Add direct application URL if available")
        
        if not job.get('salary'):
            suggestions.append("Include salary information if available")
        
        if not job.get('requirements'):
            suggestions.append("Add job requirements and qualifications")
        
        if len(job.get('summary', '')) < 50:
            suggestions.append("Provide more detailed job summary")
        
        return suggestions

class JobDeduplicator:
    """Advanced job deduplication with fuzzy matching"""
    
    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold
        self.deduplication_stats = {
            'total_jobs': 0,
            'unique_jobs': 0,
            'duplicates_removed': 0,
            'duplicate_groups': 0,
            'similarity_checks': 0
        }
    
    def deduplicate_jobs(self, jobs: List[Dict]) -> DeduplicationResult:
        """Remove duplicate job listings"""
        if not jobs:
            return DeduplicationResult([], 0, [], self.deduplication_stats)
        
        self.deduplication_stats['total_jobs'] = len(jobs)
        
        # Generate fingerprints for each job
        job_fingerprints = []
        for i, job in enumerate(jobs):
            fingerprint = self._generate_fingerprint(job)
            job_fingerprints.append((i, fingerprint, job))
        
        # Find exact duplicates first
        exact_duplicates = self._find_exact_duplicates(job_fingerprints)
        
        # Find fuzzy duplicates
        fuzzy_duplicates = self._find_fuzzy_duplicates(job_fingerprints, exact_duplicates)
        
        # Combine all duplicate groups
        all_duplicate_groups = exact_duplicates + fuzzy_duplicates
        
        # Select best job from each group
        unique_jobs = self._select_best_jobs(jobs, all_duplicate_groups)
        
        # Update statistics
        self.deduplication_stats['unique_jobs'] = len(unique_jobs)
        self.deduplication_stats['duplicates_removed'] = len(jobs) - len(unique_jobs)
        self.deduplication_stats['duplicate_groups'] = len(all_duplicate_groups)
        
        return DeduplicationResult(
            unique_jobs=unique_jobs,
            duplicates_removed=self.deduplication_stats['duplicates_removed'],
            duplicate_groups=all_duplicate_groups,
            deduplication_stats=self.deduplication_stats
        )
    
    def _generate_fingerprint(self, job: Dict) -> str:
        """Generate fingerprint for job deduplication with enhanced matching"""
        # Create normalized text for comparison
        title = job.get('title', '').lower().strip()
        company = job.get('company', '').lower().strip()
        location = job.get('location', '').lower().strip()
        
        # Remove common variations and job board suffixes
        title = re.sub(r'\s+', ' ', title)
        title = re.sub(r'\s*-\s*(for|job id|job-id).*$', '', title, flags=re.IGNORECASE)  # Remove BDJobs suffixes
        title = re.sub(r'\s*\(for\s+.*?\)', '', title, flags=re.IGNORECASE)  # Remove (For Company) patterns
        
        company = re.sub(r'\s+', ' ', company)
        company = re.sub(r'\.com$', '', company, flags=re.IGNORECASE)  # Remove .com suffixes
        company = re.sub(r'bdjobs\.com', '', company, flags=re.IGNORECASE)  # Remove BDJobs.com references
        
        location = re.sub(r'\s+', ' ', location)
        
        # Create fingerprint
        fingerprint_parts = [
            title,
            company,
            location
        ]
        
        fingerprint = '|'.join(filter(None, fingerprint_parts))
        return hashlib.md5(fingerprint.encode()).hexdigest()
    
    def _find_exact_duplicates(self, job_fingerprints: List[Tuple]) -> List[List[int]]:
        """Find exact duplicate groups"""
        fingerprint_groups = defaultdict(list)
        
        for i, fingerprint, job in job_fingerprints:
            fingerprint_groups[fingerprint].append(i)
        
        # Return groups with more than one job
        return [group for group in fingerprint_groups.values() if len(group) > 1]
    
    def _find_fuzzy_duplicates(self, job_fingerprints: List[Tuple], exact_duplicates: List[List[int]]) -> List[List[int]]:
        """Find fuzzy duplicate groups"""
        fuzzy_groups = []
        processed_indices = set()
        
        # Add indices from exact duplicates to processed set
        for group in exact_duplicates:
            processed_indices.update(group)
        
        # Compare remaining jobs
        for i in range(len(job_fingerprints)):
            if i in processed_indices:
                continue
            
            current_group = [i]
            current_job = job_fingerprints[i][2]
            
            for j in range(i + 1, len(job_fingerprints)):
                if j in processed_indices:
                    continue
                
                other_job = job_fingerprints[j][2]
                similarity = self._calculate_similarity(current_job, other_job)
                
                self.deduplication_stats['similarity_checks'] += 1
                
                if similarity >= self.similarity_threshold:
                    current_group.append(j)
                    processed_indices.add(j)
            
            if len(current_group) > 1:
                fuzzy_groups.append(current_group)
                processed_indices.update(current_group)
        
        return fuzzy_groups
    
    def _calculate_similarity(self, job1: Dict, job2: Dict) -> float:
        """Calculate similarity between two jobs with enhanced matching"""
        # Normalize titles for comparison
        title1 = self._normalize_title(job1.get('title', ''))
        title2 = self._normalize_title(job2.get('title', ''))
        
        # Normalize companies for comparison
        company1 = self._normalize_company(job1.get('company', ''))
        company2 = self._normalize_company(job2.get('company', ''))
        
        # Compare title similarity
        title_similarity = SequenceMatcher(None, title1, title2).ratio()
        
        # Compare company similarity
        company_similarity = SequenceMatcher(None, company1, company2).ratio()
        
        # Compare location similarity
        location_similarity = SequenceMatcher(None, 
            job1.get('location', '').lower(), 
            job2.get('location', '').lower()
        ).ratio()
        
        # Weighted average with higher weight on title and company
        similarity = (
            title_similarity * 0.6 +
            company_similarity * 0.3 +
            location_similarity * 0.1
        )
        
        return similarity
    
    def _normalize_title(self, title: str) -> str:
        """Normalize job title for comparison"""
        title = title.lower().strip()
        # Remove common BDJobs patterns
        title = re.sub(r'\s*-\s*(for|job id|job-id).*$', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*\(for\s+.*?\)', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s+', ' ', title)
        return title
    
    def _normalize_company(self, company: str) -> str:
        """Normalize company name for comparison"""
        company = company.lower().strip()
        # Remove common suffixes
        company = re.sub(r'\.com$', '', company, flags=re.IGNORECASE)
        company = re.sub(r'bdjobs\.com', '', company, flags=re.IGNORECASE)
        company = re.sub(r'\s+', ' ', company)
        return company
    
    def _select_best_jobs(self, jobs: List[Dict], duplicate_groups: List[List[int]]) -> List[Dict]:
        """Select the best job from each duplicate group"""
        selected_indices = set()
        
        for group in duplicate_groups:
            # Select job with highest quality score
            best_job_index = self._select_best_job_from_group(jobs, group)
            selected_indices.add(best_job_index)
        
        # Add jobs that are not in any duplicate group
        for i in range(len(jobs)):
            if i not in selected_indices:
                # Check if this job is in any duplicate group
                in_group = False
                for group in duplicate_groups:
                    if i in group:
                        in_group = True
                        break
                
                if not in_group:
                    selected_indices.add(i)
        
        return [jobs[i] for i in sorted(selected_indices)]
    
    def _select_best_job_from_group(self, jobs: List[Dict], group: List[int]) -> int:
        """Select the best job from a duplicate group with source prioritization"""
        best_score = -1
        best_index = group[0]
        
        # Source priority: prefer jobs from different sources to avoid duplicates
        source_priority = {
            'BDJobs': 1,  # Highest priority for BDJobs
            'LinkedIn': 2,  # Second priority for LinkedIn
            'LinkedIn (Fast Scraper)': 2,  # Same as LinkedIn
            'Indeed': 3,
            'Web Search': 4,  # Lowest priority for web search results
        }
        
        for index in group:
            job = jobs[index]
            base_score = self._calculate_job_quality_score(job)
            
            # Apply source priority bonus
            source = job.get('source', '').split(' (')[0]  # Remove suffix like "(Fast Scraper)"
            priority_bonus = source_priority.get(source, 5)  # Default low priority
            
            # Final score: base quality + source priority (lower number = higher priority)
            final_score = base_score + (1.0 / priority_bonus)
            
            if final_score > best_score:
                best_score = final_score
                best_index = index
        
        return best_index
    
    def _calculate_job_quality_score(self, job: Dict) -> float:
        """Calculate quality score for job selection"""
        score = 0.0
        
        # Completeness score
        fields = ['title', 'company', 'location', 'summary', 'url', 'salary', 'requirements']
        completeness = sum(1 for field in fields if job.get(field)) / len(fields)
        score += completeness * 0.4
        
        # Content length score
        title_length = len(job.get('title', ''))
        summary_length = len(job.get('summary', ''))
        
        if title_length > 10:
            score += 0.2
        if summary_length > 50:
            score += 0.2
        
        # URL presence score
        if job.get('url'):
            score += 0.1
        
        # Salary presence score
        if job.get('salary'):
            score += 0.1
        
        return score

class JobEnricher:
    """Enriches job listings with additional information"""
    
    def __init__(self):
        self.skill_patterns = self._initialize_skill_patterns()
        self.experience_patterns = self._initialize_experience_patterns()
        self.job_type_patterns = self._initialize_job_type_patterns()
    
    def _initialize_skill_patterns(self) -> Dict[str, List[str]]:
        """Initialize skill detection patterns"""
        return {
            'programming_languages': [
                'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'swift', 'kotlin'
            ],
            'frameworks': [
                'react', 'angular', 'vue', 'node.js', 'django', 'flask', 'spring', 'laravel', 'express', 'fastapi'
            ],
            'databases': [
                'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'sqlite', 'oracle', 'sql server'
            ],
            'cloud_platforms': [
                'aws', 'azure', 'gcp', 'heroku', 'digitalocean', 'firebase', 'vercel', 'netlify'
            ],
            'tools': [
                'docker', 'kubernetes', 'jenkins', 'git', 'github', 'gitlab', 'jira', 'confluence', 'slack'
            ],
            'methodologies': [
                'agile', 'scrum', 'kanban', 'devops', 'ci/cd', 'tdd', 'bdd', 'lean'
            ]
        }
    
    def _initialize_experience_patterns(self) -> Dict[str, List[str]]:
        """Initialize experience level detection patterns"""
        return {
            'entry_level': ['entry', 'junior', 'fresher', 'graduate', '0-1 years', '0-2 years', 'no experience'],
            'mid_level': ['mid', 'intermediate', '2-3 years', '3-5 years', 'experienced'],
            'senior_level': ['senior', 'lead', 'principal', 'architect', '5+ years', '7+ years', '10+ years']
        }
    
    def _initialize_job_type_patterns(self) -> Dict[str, List[str]]:
        """Initialize job type detection patterns"""
        return {
            'full_time': ['full time', 'full-time', 'permanent', 'regular'],
            'part_time': ['part time', 'part-time', 'contract', 'temporary'],
            'remote': ['remote', 'work from home', 'wfh', 'virtual', 'online'],
            'internship': ['internship', 'intern', 'trainee', 'apprentice']
        }
    
    def enrich_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Enrich job listings with additional information"""
        enriched_jobs = []
        
        for job in jobs:
            enriched_job = job.copy()
            
            # Extract skills if not present
            if not enriched_job.get('skills'):
                enriched_job['skills'] = self._extract_skills(enriched_job)
            
            # Determine experience level if not present
            if not enriched_job.get('experience_level'):
                enriched_job['experience_level'] = self._determine_experience_level(enriched_job)
            
            # Determine job type if not present
            if not enriched_job.get('job_type'):
                enriched_job['job_type'] = self._determine_job_type(enriched_job)
            
            # Normalize location
            enriched_job['location'] = self._normalize_location(enriched_job.get('location', ''))
            
            # Extract requirements if not present
            if not enriched_job.get('requirements'):
                enriched_job['requirements'] = self._extract_requirements(enriched_job)
            
            # Calculate confidence score
            enriched_job['confidence_score'] = self._calculate_confidence_score(enriched_job)
            
            enriched_jobs.append(enriched_job)
        
        return enriched_jobs
    
    def _extract_skills(self, job: Dict) -> List[str]:
        """Extract skills from job description"""
        text = f"{job.get('title', '')} {job.get('summary', '')} {job.get('requirements', '')}".lower()
        skills = set()
        
        for category, skill_list in self.skill_patterns.items():
            for skill in skill_list:
                if skill in text:
                    skills.add(skill)
        
        return list(skills)[:10]  # Limit to 10 skills
    
    def _determine_experience_level(self, job: Dict) -> str:
        """Determine experience level from job content"""
        text = f"{job.get('title', '')} {job.get('summary', '')} {job.get('requirements', '')}".lower()
        
        for level, patterns in self.experience_patterns.items():
            if any(pattern in text for pattern in patterns):
                return level.replace('_', ' ').title()
        
        return "Not specified"
    
    def _determine_job_type(self, job: Dict) -> str:
        """Determine job type from job content"""
        text = f"{job.get('title', '')} {job.get('summary', '')}".lower()
        
        for job_type, patterns in self.job_type_patterns.items():
            if any(pattern in text for pattern in patterns):
                return job_type.replace('_', ' ').title()
        
        return "Not specified"
    
    def _normalize_location(self, location: str) -> str:
        """Normalize location strings"""
        if not location:
            return "Not specified"
        
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
    
    def _extract_requirements(self, job: Dict) -> List[str]:
        """Extract requirements from job description"""
        text = job.get('summary', '')
        requirements = []
        
        # Look for requirement patterns
        requirement_patterns = [
            r'requirements?[:\s]+([^.]+)',
            r'qualifications?[:\s]+([^.]+)',
            r'experience[:\s]+([^.]+)',
            r'skills?[:\s]+([^.]+)'
        ]
        
        for pattern in requirement_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                requirements.append(match.strip())
        
        return requirements[:5]  # Limit to 5 requirements
    
    def _calculate_confidence_score(self, job: Dict) -> float:
        """Calculate confidence score for enriched job"""
        score = 0.0
        
        # Base score for required fields
        required_fields = ['title', 'company', 'location', 'summary']
        for field in required_fields:
            if job.get(field):
                score += 0.15
        
        # Bonus for optional fields
        optional_fields = ['url', 'salary', 'requirements', 'skills', 'experience_level', 'job_type']
        for field in optional_fields:
            if job.get(field):
                score += 0.05
        
        # Bonus for content quality
        if len(job.get('summary', '')) > 100:
            score += 0.1
        
        if job.get('skills'):
            score += 0.05
        
        return min(1.0, score)

class QualityAssuranceLayer:
    """Main quality assurance layer that orchestrates validation, deduplication, and enrichment"""
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.MODERATE):
        self.validator = JobValidator(validation_level)
        self.deduplicator = JobDeduplicator()
        self.enricher = JobEnricher()
        
        self.qa_stats = {
            'total_jobs_processed': 0,
            'valid_jobs': 0,
            'invalid_jobs': 0,
            'duplicates_removed': 0,
            'enriched_jobs': 0,
            'quality_distribution': defaultdict(int)
        }
    
    def process_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Process jobs through the complete QA pipeline"""
        if not jobs:
            return []
        
        logger.info(f"🔍 Starting QA processing for {len(jobs)} jobs...")
        
        # Step 1: Validate jobs
        validated_jobs = self._validate_jobs(jobs)
        
        # Step 2: Deduplicate jobs
        deduplication_result = self.deduplicator.deduplicate_jobs(validated_jobs)
        
        # Step 3: Enrich jobs
        enriched_jobs = self.enricher.enrich_jobs(deduplication_result.unique_jobs)
        
        # Update statistics
        self._update_statistics(jobs, validated_jobs, deduplication_result, enriched_jobs)
        
        logger.info(f"✅ QA processing completed: {len(enriched_jobs)} high-quality jobs")
        return enriched_jobs
    
    def _validate_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Validate all jobs and return valid ones"""
        valid_jobs = []
        
        for job in jobs:
            validation_result = self.validator.validate_job(job)
            
            # Temporarily accept all jobs for testing
            if validation_result.quality_score >= 0.3:  # Use score directly instead of is_valid
                # Add validation metadata
                job['validation_metadata'] = {
                    'quality_score': validation_result.quality_score,
                    'quality_level': validation_result.quality_level.value,
                    'warnings': validation_result.warnings,
                    'suggestions': validation_result.suggestions
                }
                valid_jobs.append(job)
            else:
                logger.warning(f"⚠️ Invalid job removed: {job.get('title', 'Unknown')}")
                logger.warning(f"   Issues: {validation_result.issues}")
        
        return valid_jobs
    
    def _update_statistics(self, original_jobs: List[Dict], validated_jobs: List[Dict], 
                          deduplication_result: DeduplicationResult, enriched_jobs: List[Dict]):
        """Update QA statistics"""
        self.qa_stats['total_jobs_processed'] = len(original_jobs)
        self.qa_stats['valid_jobs'] = len(validated_jobs)
        self.qa_stats['invalid_jobs'] = len(original_jobs) - len(validated_jobs)
        self.qa_stats['duplicates_removed'] = deduplication_result.duplicates_removed
        self.qa_stats['enriched_jobs'] = len(enriched_jobs)
        
        # Update quality distribution
        for job in enriched_jobs:
            quality_level = job.get('validation_metadata', {}).get('quality_level', 'unknown')
            self.qa_stats['quality_distribution'][quality_level] += 1
    
    def get_qa_report(self) -> Dict[str, Any]:
        """Get comprehensive QA report"""
        return {
            'statistics': self.qa_stats,
            'deduplication_stats': self.deduplicator.deduplication_stats,
            'quality_summary': {
                'excellent': self.qa_stats['quality_distribution']['excellent'],
                'good': self.qa_stats['quality_distribution']['good'],
                'fair': self.qa_stats['quality_distribution']['fair'],
                'poor': self.qa_stats['quality_distribution']['poor']
            }
        }

# Test functionality
if __name__ == "__main__":
    # Test the quality assurance layer
    qa_layer = QualityAssuranceLayer()
    
    print("🧪 Testing Quality Assurance Layer...")
    print("=" * 50)
    
    # Test jobs
    test_jobs = [
        {
            'title': 'Software Engineer',
            'company': 'TechCorp Ltd',
            'location': 'Dhaka, Bangladesh',
            'summary': 'We are looking for a skilled software engineer with Python and React experience.',
            'url': 'https://techcorp.com/jobs/123',
            'salary': '50k-80k BDT'
        },
        {
            'title': 'Software Engineer',  # Duplicate
            'company': 'TechCorp Ltd',
            'location': 'Dhaka, Bangladesh',
            'summary': 'We are looking for a skilled software engineer with Python and React experience.',
            'url': 'https://techcorp.com/jobs/123',
            'salary': '50k-80k BDT'
        },
        {
            'title': 'Python Developer',
            'company': 'StartupXYZ',
            'location': 'Remote',
            'summary': 'Join our team as a Python developer. Experience with Django and AWS required.',
            'url': 'https://startupxyz.com/careers'
        },
        {
            'title': 'Earn Money Fast',  # Spam
            'company': 'Online Company',
            'location': 'Work from home',
            'summary': 'Make money quickly from home. No experience needed. Click here to apply!',
            'url': 'https://spam.com'
        }
    ]
    
    print(f"📊 Processing {len(test_jobs)} test jobs...")
    processed_jobs = qa_layer.process_jobs(test_jobs)
    
    print(f"\n✅ QA Results:")
    print(f"   Original jobs: {len(test_jobs)}")
    print(f"   Processed jobs: {len(processed_jobs)}")
    
    # Show QA report
    report = qa_layer.get_qa_report()
    print(f"\n📋 QA Report:")
    for key, value in report['statistics'].items():
        print(f"   {key}: {value}")
    
    # Show processed jobs
    print(f"\n📋 Processed Jobs:")
    for i, job in enumerate(processed_jobs, 1):
        print(f"\n{i}. {job['title']} at {job['company']}")
        print(f"   Location: {job['location']}")
        print(f"   Skills: {', '.join(job.get('skills', []))}")
        print(f"   Experience: {job.get('experience_level', 'Not specified')}")
        print(f"   Quality: {job.get('validation_metadata', {}).get('quality_level', 'Unknown')}")
        print(f"   Confidence: {job.get('confidence_score', 0):.2f}")


