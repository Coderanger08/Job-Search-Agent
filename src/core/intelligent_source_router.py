"""
Intelligent Source Router - Layer 3
Dynamic source selection, performance monitoring, and adaptive learning
"""

import time
import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict, deque
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SourceType(Enum):
    """Types of data sources"""
    API = "api"
    SCRAPER = "scraper"
    WEB_SEARCH = "web_search"
    HYBRID = "hybrid"

class QueryType(Enum):
    """Types of job search queries"""
    GENERAL_JOB_SEARCH = "general_job_search"
    COMPANY_SPECIFIC = "company_specific"
    SKILL_BASED = "skill_based"
    LOCATION_SPECIFIC = "location_specific"
    EXPERIENCE_LEVEL = "experience_level"
    REMOTE_WORK = "remote_work"
    SALARY_RANGE = "salary_range"
    RECENT_POSTINGS = "recent_postings"

@dataclass
class SourcePerformance:
    """Performance metrics for a data source"""
    source_id: str
    source_type: SourceType
    success_rate: float = 0.0
    avg_response_time: float = 0.0
    avg_jobs_found: float = 0.0
    last_used: float = 0.0
    failure_count: int = 0
    total_requests: int = 0
    is_available: bool = True
    priority_score: float = 0.0

@dataclass
class QueryProfile:
    """Profile for different query types"""
    query_type: QueryType
    preferred_sources: List[str]
    min_sources: int = 2
    max_sources: int = 5
    timeout: float = 30.0
    expected_jobs: int = 10

class PerformanceTracker:
    """Tracks and analyzes source performance"""
    
    def __init__(self, history_size: int = 100):
        self.history_size = history_size
        self.performance_history = defaultdict(lambda: deque(maxlen=history_size))
        self.source_metrics = {}
        self.lock = threading.Lock()
    
    def record_request(self, source_id: str, success: bool, response_time: float, jobs_found: int):
        """Record a request result"""
        with self.lock:
            timestamp = time.time()
            result = {
                'timestamp': timestamp,
                'success': success,
                'response_time': response_time,
                'jobs_found': jobs_found
            }
            
            self.performance_history[source_id].append(result)
            self._update_metrics(source_id)
    
    def _update_metrics(self, source_id: str):
        """Update performance metrics for a source"""
        history = self.performance_history[source_id]
        if not history:
            return
        
        total_requests = len(history)
        successful_requests = sum(1 for r in history if r['success'])
        success_rate = successful_requests / total_requests if total_requests > 0 else 0.0
        
        avg_response_time = sum(r['response_time'] for r in history) / total_requests
        avg_jobs_found = sum(r['jobs_found'] for r in history) / total_requests
        
        # Calculate priority score
        priority_score = self._calculate_priority_score(success_rate, avg_response_time, avg_jobs_found)
        
        self.source_metrics[source_id] = SourcePerformance(
            source_id=source_id,
            success_rate=success_rate,
            avg_response_time=avg_response_time,
            avg_jobs_found=avg_jobs_found,
            last_used=history[-1]['timestamp'] if history else 0.0,
            failure_count=total_requests - successful_requests,
            total_requests=total_requests,
            is_available=success_rate > 0.3,  # Consider available if >30% success
            priority_score=priority_score
        )
    
    def _calculate_priority_score(self, success_rate: float, response_time: float, jobs_found: float) -> float:
        """Calculate priority score based on performance metrics"""
        # Normalize metrics (0-1 scale)
        normalized_success = success_rate
        normalized_speed = max(0, 1 - (response_time / 30.0))  # 30s = 0 score
        normalized_yield = min(1, jobs_found / 20.0)  # 20 jobs = 1 score
        
        # Weighted combination
        score = (
            normalized_success * 0.5 +    # Success rate is most important
            normalized_speed * 0.3 +      # Speed is second
            normalized_yield * 0.2        # Job yield is third
        )
        
        return score
    
    def get_source_metrics(self, source_id: str) -> Optional[SourcePerformance]:
        """Get performance metrics for a source"""
        return self.source_metrics.get(source_id)
    
    def get_all_metrics(self) -> Dict[str, SourcePerformance]:
        """Get metrics for all sources"""
        return self.source_metrics.copy()
    
    def get_top_sources(self, source_type: SourceType = None, limit: int = 5) -> List[SourcePerformance]:
        """Get top performing sources"""
        metrics = self.get_all_metrics()
        
        if source_type:
            metrics = {k: v for k, v in metrics.items() if v.source_type == source_type}
        
        # Sort by priority score
        sorted_sources = sorted(metrics.values(), key=lambda x: x.priority_score, reverse=True)
        return sorted_sources[:limit]

class QueryAnalyzer:
    """Analyzes queries to determine optimal source selection"""
    
    def __init__(self):
        self.query_profiles = self._initialize_query_profiles()
        self.keyword_patterns = self._initialize_keyword_patterns()
    
    def _initialize_query_profiles(self) -> Dict[QueryType, QueryProfile]:
        """Initialize query type profiles"""
        return {
            QueryType.GENERAL_JOB_SEARCH: QueryProfile(
                query_type=QueryType.GENERAL_JOB_SEARCH,
                preferred_sources=['scraper_bdjobs', 'scraper_linkedin', 'web_search', 'api_linkedin', 'api_indeed'],
                min_sources=2,
                max_sources=4,
                timeout=30.0,
                expected_jobs=15
            ),
            QueryType.COMPANY_SPECIFIC: QueryProfile(
                query_type=QueryType.COMPANY_SPECIFIC,
                preferred_sources=['scraper_bdjobs', 'scraper_linkedin', 'api_linkedin', 'web_search'],
                min_sources=2,
                max_sources=3,
                timeout=25.0,
                expected_jobs=8
            ),
            QueryType.SKILL_BASED: QueryProfile(
                query_type=QueryType.SKILL_BASED,
                preferred_sources=['scraper_bdjobs', 'scraper_linkedin', 'scraper_skilljobs', 'web_search', 'api_linkedin'],
                min_sources=2,
                max_sources=4,
                timeout=30.0,
                expected_jobs=12
            ),
            QueryType.LOCATION_SPECIFIC: QueryProfile(
                query_type=QueryType.LOCATION_SPECIFIC,
                preferred_sources=['scraper_bdjobs', 'scraper_skilljobs', 'web_search'],
                min_sources=2,
                max_sources=3,
                timeout=25.0,
                expected_jobs=10
            ),
            QueryType.REMOTE_WORK: QueryProfile(
                query_type=QueryType.REMOTE_WORK,
                preferred_sources=['api_linkedin', 'web_search', 'api_indeed'],
                min_sources=2,
                max_sources=4,
                timeout=30.0,
                expected_jobs=12
            ),
            QueryType.RECENT_POSTINGS: QueryProfile(
                query_type=QueryType.RECENT_POSTINGS,
                preferred_sources=['scraper_bdjobs', 'scraper_skilljobs', 'web_search'],
                min_sources=2,
                max_sources=3,
                timeout=20.0,
                expected_jobs=8
            )
        }
    
    def _initialize_keyword_patterns(self) -> Dict[QueryType, List[str]]:
        """Initialize keyword patterns for query classification"""
        return {
            QueryType.COMPANY_SPECIFIC: [
                'at', 'company', 'corporation', 'ltd', 'inc', 'group', 'tech', 'software'
            ],
            QueryType.SKILL_BASED: [
                'python', 'java', 'react', 'javascript', 'aws', 'docker', 'kubernetes',
                'machine learning', 'ai', 'data science', 'frontend', 'backend'
            ],
            QueryType.LOCATION_SPECIFIC: [
                'in', 'at', 'dhaka', 'chittagong', 'sylhet', 'bangladesh', 'remote'
            ],
            QueryType.EXPERIENCE_LEVEL: [
                'senior', 'junior', 'entry', 'lead', 'principal', 'fresher', 'experienced'
            ],
            QueryType.REMOTE_WORK: [
                'remote', 'work from home', 'wfh', 'online', 'virtual', 'telecommute'
            ],
            QueryType.SALARY_RANGE: [
                'salary', 'pay', 'compensation', 'budget', 'above', 'below', 'range'
            ],
            QueryType.RECENT_POSTINGS: [
                'recent', 'latest', 'new', 'today', 'this week', 'fresh', 'just posted'
            ]
        }
    
    def classify_query(self, parsed_data: Dict[str, Any]) -> QueryType:
        """Classify the query type based on parsed data from Query Parser"""
        
        # Use parsed data to determine query type (no need to re-analyze raw query)
        if parsed_data.get('company'):
            return QueryType.COMPANY_SPECIFIC
        elif parsed_data.get('skills'):
            return QueryType.SKILL_BASED
        elif parsed_data.get('location') and parsed_data.get('location').lower() != 'bangladesh':
            return QueryType.LOCATION_SPECIFIC
        elif parsed_data.get('remote'):
            return QueryType.REMOTE_WORK
        elif parsed_data.get('salary_range'):
            return QueryType.SALARY_RANGE
        elif parsed_data.get('experience_level'):
            return QueryType.EXPERIENCE_LEVEL
        elif parsed_data.get('job_type') == 'recent':
            return QueryType.RECENT_POSTINGS
        
        # Default to general job search
        return QueryType.GENERAL_JOB_SEARCH
    
    def get_query_profile(self, query_type: QueryType) -> QueryProfile:
        """Get the profile for a query type"""
        return self.query_profiles.get(query_type, self.query_profiles[QueryType.GENERAL_JOB_SEARCH])

class IntelligentSourceRouter:
    """Intelligent router that selects optimal data sources"""
    
    def __init__(self):
        self.performance_tracker = PerformanceTracker()
        self.query_analyzer = QueryAnalyzer()
        self.available_sources = self._initialize_sources()
        self.adaptive_learning = True
        self.max_concurrent_sources = 3
    
    def _initialize_sources(self) -> Dict[str, Dict[str, Any]]:
        """Initialize available data sources"""
        return {
            'api_linkedin': {
                'id': 'api_linkedin',
                'name': 'LinkedIn API',
                'type': SourceType.API,
                'priority': 1.0,
                'enabled': True,
                'config': {'api_key_required': True}
            },
            'api_indeed': {
                'id': 'api_indeed',
                'name': 'Indeed API',
                'type': SourceType.API,
                'priority': 0.9,
                'enabled': True,
                'config': {'api_key_required': True}
            },
            'scraper_bdjobs': {
                'id': 'scraper_bdjobs',
                'name': 'BDJobs Scraper',
                'type': SourceType.SCRAPER,
                'priority': 0.8,
                'enabled': True,
                'config': {'requires_selenium': True}
            },
            'scraper_linkedin': {
                'id': 'scraper_linkedin',
                'name': 'LinkedIn Scraper',
                'type': SourceType.SCRAPER,
                'priority': 0.8,
                'enabled': True,
                'config': {'requires_selenium': False}
            },
            'scraper_skilljobs': {
                'id': 'scraper_skilljobs',
                'name': 'Skill.jobs Scraper',
                'type': SourceType.SCRAPER,
                'priority': 0.7,
                'enabled': True,
                'config': {'requires_selenium': True}
            },
            'scraper_shomvob': {
                'id': 'scraper_shomvob',
                'name': 'Shomvob Scraper',
                'type': SourceType.SCRAPER,
                'priority': 0.6,
                'enabled': True,
                'config': {'requires_selenium': True}
            },
            'web_search': {
                'id': 'web_search',
                'name': 'Advanced Web Search',
                'type': SourceType.WEB_SEARCH,
                'priority': 0.5,
                'enabled': True,
                'config': {'multi_engine': True}
            }
        }
    
    def select_sources(self, parsed_data: Dict[str, Any], max_sources: int = 5) -> List[str]:
        """
        Select optimal data sources for a query
        
        Args:
            parsed_data: Parsed query data from Query Parser
            max_sources: Maximum number of sources to select
            
        Returns:
            List of selected source IDs
        """
        # Classify the query using parsed data
        query_type = self.query_analyzer.classify_query(parsed_data)
        query_profile = self.query_analyzer.get_query_profile(query_type)
        
        logger.info(f"🎯 Query classified as: {query_type.value}")
        
        # Get available sources
        available_sources = self._get_available_sources()
        
        # Filter by query profile preferences
        preferred_sources = self._filter_by_preferences(available_sources, query_profile.preferred_sources)
        
        # Rank sources by performance and priority
        ranked_sources = self._rank_sources(preferred_sources, query_type)
        
        # Select optimal number of sources
        selected_sources = self._select_optimal_sources(ranked_sources, query_profile, max_sources)
        
        logger.info(f"📡 Selected sources: {selected_sources}")
        return selected_sources
    
    def _get_available_sources(self) -> List[Dict[str, Any]]:
        """Get list of available and enabled sources"""
        available = []
        
        for source_id, source_config in self.available_sources.items():
            if not source_config['enabled']:
                continue
            
            # Check if source is available based on performance
            metrics = self.performance_tracker.get_source_metrics(source_id)
            if metrics and not metrics.is_available:
                continue
            
            available.append({
                'id': source_id,
                'config': source_config,
                'metrics': metrics
            })
        
        return available
    
    def _filter_by_preferences(self, sources: List[Dict], preferred_sources: List[str]) -> List[Dict]:
        """Filter sources by query profile preferences"""
        if not preferred_sources:
            return sources
        
        # Create preference map
        preference_map = {source: i for i, source in enumerate(preferred_sources)}
        
        # Sort by preference (preferred sources first)
        def preference_key(source):
            return preference_map.get(source['id'], len(preferred_sources))
        
        return sorted(sources, key=preference_key)
    
    def _rank_sources(self, sources: List[Dict], query_type: QueryType) -> List[Dict]:
        """Rank sources by performance and priority"""
        def rank_key(source):
            config = source['config']
            metrics = source.get('metrics')
            
            # Base priority from config
            base_priority = config['priority']
            
            # Performance boost from metrics
            performance_boost = 0.0
            if metrics:
                performance_boost = metrics.priority_score * 0.3
            
            # Query type specific adjustments
            query_boost = self._get_query_type_boost(config, query_type)
            
            return base_priority + performance_boost + query_boost
        
        return sorted(sources, key=rank_key, reverse=True)
    
    def _get_query_type_boost(self, source_config: Dict, query_type: QueryType) -> float:
        """Get query type specific boost for a source"""
        boosts = {
            QueryType.COMPANY_SPECIFIC: {
                'api_linkedin': 0.2,
                'api_indeed': 0.1,
                'web_search': 0.1
            },
            QueryType.LOCATION_SPECIFIC: {
                'scraper_bdjobs': 0.2,
                'scraper_skilljobs': 0.2,
                'scraper_shomvob': 0.1
            },
            QueryType.SKILL_BASED: {
                'web_search': 0.2,
                'api_linkedin': 0.1,
                'scraper_skilljobs': 0.1
            },
            QueryType.REMOTE_WORK: {
                'api_linkedin': 0.2,
                'api_indeed': 0.1,
                'web_search': 0.1
            }
        }
        
        query_boosts = boosts.get(query_type, {})
        return query_boosts.get(source_config['id'], 0.0)
    
    def _select_optimal_sources(self, ranked_sources: List[Dict], query_profile: QueryProfile, max_sources: int) -> List[str]:
        """Select optimal number of sources based on query profile"""
        # Determine number of sources to use
        num_sources = min(
            max_sources,
            query_profile.max_sources,
            len(ranked_sources)
        )
        
        # Ensure minimum sources if available
        if num_sources < query_profile.min_sources and len(ranked_sources) >= query_profile.min_sources:
            num_sources = query_profile.min_sources
        
        # Select top sources
        selected = ranked_sources[:num_sources]
        return [source['id'] for source in selected]
    
    def record_source_result(self, source_id: str, success: bool, response_time: float, jobs_found: int):
        """Record the result of a source request"""
        self.performance_tracker.record_request(source_id, success, response_time, jobs_found)
        
        if self.adaptive_learning:
            self._update_source_availability(source_id, success)
    
    def _update_source_availability(self, source_id: str, success: bool):
        """Update source availability based on recent performance"""
        metrics = self.performance_tracker.get_source_metrics(source_id)
        if metrics:
            # Mark as unavailable if recent failure rate is too high
            if metrics.failure_count >= 5 and metrics.success_rate < 0.2:
                logger.warning(f"⚠️ Marking {source_id} as unavailable due to poor performance")
                metrics.is_available = False
    
    def get_source_status(self) -> Dict[str, Dict]:
        """Get status of all sources"""
        status = {}
        
        for source_id, source_config in self.available_sources.items():
            metrics = self.performance_tracker.get_source_metrics(source_id)
            
            status[source_id] = {
                'name': source_config['name'],
                'type': source_config['type'].value,
                'enabled': source_config['enabled'],
                'available': metrics.is_available if metrics else True,
                'success_rate': metrics.success_rate if metrics else 0.0,
                'avg_response_time': metrics.avg_response_time if metrics else 0.0,
                'priority_score': metrics.priority_score if metrics else source_config['priority'],
                'total_requests': metrics.total_requests if metrics else 0
            }
        
        return status
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for all sources"""
        all_metrics = self.performance_tracker.get_all_metrics()
        
        summary = {
            'total_sources': len(self.available_sources),
            'available_sources': len([m for m in all_metrics.values() if m.is_available]),
            'top_performers': [
                {
                    'source_id': m.source_id,
                    'success_rate': m.success_rate,
                    'priority_score': m.priority_score
                }
                for m in self.performance_tracker.get_top_sources(limit=3)
            ],
            'source_types': {
                source_type.value: len([m for m in all_metrics.values() if m.source_type == source_type])
                for source_type in SourceType
            }
        }
        
        return summary

# Test functionality
if __name__ == "__main__":
    # Test the intelligent source router
    router = IntelligentSourceRouter()
    
    print("🧪 Testing Intelligent Source Router...")
    print("=" * 50)
    
    # Test queries with parsed data (simulating Query Parser output)
    test_queries = [
        {"job_title": "Python developer", "company": "Google", "skills": ["python"]},
        {"job_title": "Software engineer", "location": "Dhaka"},
        {"job_title": "React developer", "remote": True, "skills": ["react"]},
        {"job_title": "Java developer", "company": "TechCorp", "experience_level": "senior"},
        {"job_title": "fresher", "job_type": "recent"}
    ]
    
    for parsed_data in test_queries:
        print(f"\n🔍 Parsed Data: {parsed_data}")
        sources = router.select_sources(parsed_data)
        print(f"📡 Selected sources: {sources}")
        
        # Simulate some results
        for source_id in sources:
            success = True
            response_time = 2.5
            jobs_found = 8
            router.record_source_result(source_id, success, response_time, jobs_found)
    
    # Show performance summary
    print(f"\n📊 Performance Summary:")
    summary = router.get_performance_summary()
    for key, value in summary.items():
        print(f"   {key}: {value}")
    
    # Show source status
    print(f"\n🔧 Source Status:")
    status = router.get_source_status()
    for source_id, info in status.items():
        print(f"   {source_id}: {'✅' if info['available'] else '❌'} Available")
        print(f"      Success Rate: {info['success_rate']:.2f}")
        print(f"      Priority Score: {info['priority_score']:.2f}")
