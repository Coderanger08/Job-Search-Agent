"""
Advanced Web Search Engine - Layer 1
Multi-engine, fault-tolerant web search with intelligent rotation and rate limiting
"""

import requests
import time
import random
import logging
from typing import List, Dict, Optional, Tuple
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchEngine(Enum):
    """Supported search engines"""
    GOOGLE = "google"
    BING = "bing"
    DUCKDUCKGO = "duckduckgo"
    YAHOO = "yahoo"

@dataclass
class SearchResult:
    """Structure for search results"""
    title: str
    url: str
    snippet: str
    engine: str
    rank: int

class UserAgentRotator:
    """Rotates user agents to avoid detection"""
    
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36'
        ]
        self.current_index = 0
    
    def get_random_agent(self) -> str:
        """Get a random user agent"""
        return random.choice(self.user_agents)
    
    def get_next_agent(self) -> str:
        """Get the next user agent in rotation"""
        agent = self.user_agents[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.user_agents)
        return agent

class RateLimiter:
    """Intelligent rate limiting with exponential backoff"""
    
    def __init__(self):
        self.request_times = {}
        self.failure_counts = {}
        self.base_delay = 1.0
        self.max_delay = 30.0
        self.backoff_multiplier = 2.0
    
    def should_wait(self, engine: str) -> float:
        """Calculate wait time before next request"""
        current_time = time.time()
        last_request = self.request_times.get(engine, 0)
        failures = self.failure_counts.get(engine, 0)
        
        # Calculate dynamic delay based on failures
        delay = min(self.base_delay * (self.backoff_multiplier ** failures), self.max_delay)
        
        # Add jitter to avoid thundering herd
        jitter = random.uniform(0.5, 1.5)
        delay *= jitter
        
        time_since_last = current_time - last_request
        wait_time = max(0, delay - time_since_last)
        
        return wait_time
    
    def record_request(self, engine: str, success: bool):
        """Record request outcome for rate limiting"""
        self.request_times[engine] = time.time()
        
        if success:
            # Reset failure count on success
            self.failure_counts[engine] = 0
        else:
            # Increment failure count
            self.failure_counts[engine] = self.failure_counts.get(engine, 0) + 1
    
    def wait_if_needed(self, engine: str):
        """Wait if rate limiting is needed"""
        wait_time = self.should_wait(engine)
        if wait_time > 0:
            logger.info(f"⏳ Rate limiting {engine}: waiting {wait_time:.2f}s")
            time.sleep(wait_time)

class SearchEngineAdapter:
    """Base class for search engine adapters"""
    
    def __init__(self, user_agent_rotator: UserAgentRotator, rate_limiter: RateLimiter):
        self.user_agent_rotator = user_agent_rotator
        self.rate_limiter = rate_limiter
        self.session = requests.Session()
        self.timeout = 15
    
    def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """Search method to be implemented by subclasses"""
        raise NotImplementedError
    
    def _make_request(self, url: str, engine: str, params: Dict = None) -> Optional[requests.Response]:
        """Make HTTP request with rate limiting and error handling"""
        try:
            # Apply rate limiting
            self.rate_limiter.wait_if_needed(engine)
            
            headers = {
                'User-Agent': self.user_agent_rotator.get_random_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = self.session.get(
                url, 
                params=params, 
                headers=headers, 
                timeout=self.timeout,
                allow_redirects=True
            )
            
            # Record successful request
            self.rate_limiter.record_request(engine, True)
            return response
            
        except requests.RequestException as e:
            logger.warning(f"⚠️ Request failed for {engine}: {e}")
            # Record failed request
            self.rate_limiter.record_request(engine, False)
            return None

class GoogleSearchAdapter(SearchEngineAdapter):
    """Google search adapter"""
    
    def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """Search Google"""
        try:
            url = "https://www.google.com/search"
            params = {
                'q': query,
                'num': min(num_results, 10),  # Google limits to 10
                'hl': 'en'
            }
            
            response = self._make_request(url, SearchEngine.GOOGLE.value, params)
            if not response or response.status_code != 200:
                return []
            
            return self._parse_google_results(response.text, query)
            
        except Exception as e:
            logger.error(f"❌ Google search failed: {e}")
            return []
    
    def _parse_google_results(self, html: str, query: str) -> List[SearchResult]:
        """Parse Google search results"""
        results = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Multiple selectors for robustness
        selectors = [
            'div.g',  # Standard result
            'div[data-ved]',  # Alternative selector
            '.rc'  # Classic selector
        ]
        
        for selector in selectors:
            result_elements = soup.select(selector)
            if result_elements:
                break
        
        for i, element in enumerate(result_elements[:10]):
            try:
                # Extract title and URL
                title_element = element.select_one('h3')
                link_element = element.select_one('a')
                snippet_element = element.select_one('.VwiC3b, .s3v9rd, .st')
                
                if title_element and link_element:
                    title = title_element.get_text(strip=True)
                    url = link_element.get('href', '')
                    snippet = snippet_element.get_text(strip=True) if snippet_element else ''
                    
                    # Clean URL (remove Google redirect)
                    if url.startswith('/url?q='):
                        url = url.split('/url?q=')[1].split('&')[0]
                    
                    if url and title:
                        results.append(SearchResult(
                            title=title,
                            url=url,
                            snippet=snippet,
                            engine=SearchEngine.GOOGLE.value,
                            rank=i + 1
                        ))
            except Exception as e:
                logger.debug(f"Error parsing Google result {i}: {e}")
                continue
        
        return results

class BingSearchAdapter(SearchEngineAdapter):
    """Bing search adapter"""
    
    def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """Search Bing"""
        try:
            url = "https://www.bing.com/search"
            params = {
                'q': query,
                'count': min(num_results, 10)
            }
            
            response = self._make_request(url, SearchEngine.BING.value, params)
            if not response or response.status_code != 200:
                return []
            
            return self._parse_bing_results(response.text, query)
            
        except Exception as e:
            logger.error(f"❌ Bing search failed: {e}")
            return []
    
    def _parse_bing_results(self, html: str, query: str) -> List[SearchResult]:
        """Parse Bing search results"""
        results = []
        soup = BeautifulSoup(html, 'html.parser')
        
        result_elements = soup.select('li.b_algo')
        
        for i, element in enumerate(result_elements[:10]):
            try:
                title_element = element.select_one('h2 a')
                snippet_element = element.select_one('.b_caption p, .b_dList')
                
                if title_element:
                    title = title_element.get_text(strip=True)
                    url = title_element.get('href', '')
                    snippet = snippet_element.get_text(strip=True) if snippet_element else ''
                    
                    if url and title:
                        results.append(SearchResult(
                            title=title,
                            url=url,
                            snippet=snippet,
                            engine=SearchEngine.BING.value,
                            rank=i + 1
                        ))
            except Exception as e:
                logger.debug(f"Error parsing Bing result {i}: {e}")
                continue
        
        return results

class DuckDuckGoSearchAdapter(SearchEngineAdapter):
    """DuckDuckGo search adapter"""
    
    def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """Search DuckDuckGo"""
        try:
            url = "https://html.duckduckgo.com/html/"
            params = {
                'q': query
            }
            
            response = self._make_request(url, SearchEngine.DUCKDUCKGO.value, params)
            if not response or response.status_code != 200:
                return []
            
            return self._parse_duckduckgo_results(response.text, query)
            
        except Exception as e:
            logger.error(f"❌ DuckDuckGo search failed: {e}")
            return []
    
    def _parse_duckduckgo_results(self, html: str, query: str) -> List[SearchResult]:
        """Parse DuckDuckGo search results"""
        results = []
        soup = BeautifulSoup(html, 'html.parser')
        
        result_elements = soup.select('.result')
        
        for i, element in enumerate(result_elements[:10]):
            try:
                title_element = element.select_one('.result__title a')
                snippet_element = element.select_one('.result__snippet')
                
                if title_element:
                    title = title_element.get_text(strip=True)
                    url = title_element.get('href', '')
                    snippet = snippet_element.get_text(strip=True) if snippet_element else ''
                    
                    if url and title:
                        results.append(SearchResult(
                            title=title,
                            url=url,
                            snippet=snippet,
                            engine=SearchEngine.DUCKDUCKGO.value,
                            rank=i + 1
                        ))
            except Exception as e:
                logger.debug(f"Error parsing DuckDuckGo result {i}: {e}")
                continue
        
        return results

class AdvancedWebSearchEngine:
    """Advanced multi-engine web search with intelligent fallbacks"""
    
    def __init__(self):
        self.user_agent_rotator = UserAgentRotator()
        self.rate_limiter = RateLimiter()
        
        # Initialize search adapters
        self.adapters = {
            SearchEngine.GOOGLE: GoogleSearchAdapter(self.user_agent_rotator, self.rate_limiter),
            SearchEngine.BING: BingSearchAdapter(self.user_agent_rotator, self.rate_limiter),
            SearchEngine.DUCKDUCKGO: DuckDuckGoSearchAdapter(self.user_agent_rotator, self.rate_limiter),
        }
        
        # Engine priority (most reliable first)
        self.engine_priority = [
            SearchEngine.DUCKDUCKGO,  # Most lenient
            SearchEngine.BING,        # Good alternative
            SearchEngine.GOOGLE,      # Most comprehensive but strict
        ]
        
        self.max_concurrent_searches = 2
        self.fallback_enabled = True
    
    def search(self, query: str, num_results: int = 10, engines: List[SearchEngine] = None) -> List[SearchResult]:
        """
        Advanced search with intelligent fallbacks
        
        Args:
            query: Search query
            num_results: Number of results per engine
            engines: Specific engines to use (None = use all)
        
        Returns:
            List of SearchResult objects
        """
        if engines is None:
            engines = self.engine_priority
        
        logger.info(f"🔍 Advanced search: '{query}' across {len(engines)} engines")
        
        all_results = []
        successful_engines = []
        
        # Try engines in parallel with limited concurrency
        with ThreadPoolExecutor(max_workers=self.max_concurrent_searches) as executor:
            # Submit search tasks
            future_to_engine = {
                executor.submit(self._search_single_engine, engine, query, num_results): engine 
                for engine in engines
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_engine, timeout=60):
                engine = future_to_engine[future]
                try:
                    results = future.result()
                    if results:
                        all_results.extend(results)
                        successful_engines.append(engine)
                        logger.info(f"✅ {engine.value}: Found {len(results)} results")
                    else:
                        logger.warning(f"⚠️ {engine.value}: No results found")
                except Exception as e:
                    logger.error(f"❌ {engine.value}: Search failed - {e}")
        
        # If no results and fallback is enabled, try remaining engines sequentially
        if not all_results and self.fallback_enabled:
            logger.info("🔄 Activating fallback mode...")
            remaining_engines = [e for e in self.engine_priority if e not in engines]
            
            for engine in remaining_engines:
                try:
                    results = self._search_single_engine(engine, query, num_results)
                    if results:
                        all_results.extend(results)
                        successful_engines.append(engine)
                        logger.info(f"🎯 Fallback success with {engine.value}: {len(results)} results")
                        break
                except Exception as e:
                    logger.error(f"❌ Fallback {engine.value} failed: {e}")
        
        # Remove duplicates and sort by relevance
        unique_results = self._deduplicate_results(all_results)
        sorted_results = self._sort_results_by_relevance(unique_results, query)
        
        logger.info(f"🎉 Search completed: {len(sorted_results)} unique results from {len(successful_engines)} engines")
        return sorted_results[:num_results]
    
    def _search_single_engine(self, engine: SearchEngine, query: str, num_results: int) -> List[SearchResult]:
        """Search using a single engine"""
        try:
            adapter = self.adapters.get(engine)
            if not adapter:
                logger.error(f"❌ No adapter found for {engine.value}")
                return []
            
            return adapter.search(query, num_results)
        except Exception as e:
            logger.error(f"❌ Error searching {engine.value}: {e}")
            return []
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results based on URL"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            # Normalize URL for comparison
            normalized_url = result.url.lower().rstrip('/')
            if normalized_url not in seen_urls:
                seen_urls.add(normalized_url)
                unique_results.append(result)
        
        return unique_results
    
    def _sort_results_by_relevance(self, results: List[SearchResult], query: str) -> List[SearchResult]:
        """Sort results by relevance score"""
        def calculate_relevance(result: SearchResult) -> float:
            score = 0.0
            query_terms = query.lower().split()
            
            # Title relevance (highest weight)
            title_lower = result.title.lower()
            title_matches = sum(1 for term in query_terms if term in title_lower)
            score += title_matches * 3.0
            
            # Snippet relevance
            snippet_lower = result.snippet.lower()
            snippet_matches = sum(1 for term in query_terms if term in snippet_lower)
            score += snippet_matches * 1.0
            
            # Engine reliability bonus
            engine_bonus = {
                SearchEngine.GOOGLE.value: 1.2,
                SearchEngine.BING.value: 1.1,
                SearchEngine.DUCKDUCKGO.value: 1.0,
            }
            score *= engine_bonus.get(result.engine, 1.0)
            
            # Rank penalty (lower rank = higher relevance)
            score -= result.rank * 0.1
            
            return score
        
        return sorted(results, key=calculate_relevance, reverse=True)
    
    def get_engine_status(self) -> Dict[str, Dict]:
        """Get status of all search engines"""
        status = {}
        for engine in SearchEngine:
            failure_count = self.rate_limiter.failure_counts.get(engine.value, 0)
            last_request = self.rate_limiter.request_times.get(engine.value, 0)
            
            status[engine.value] = {
                'available': engine in self.adapters,
                'failure_count': failure_count,
                'last_request': last_request,
                'status': 'healthy' if failure_count < 3 else 'degraded' if failure_count < 10 else 'failing'
            }
        
        return status

# Test functionality
if __name__ == "__main__":
    # Test the advanced search engine
    search_engine = AdvancedWebSearchEngine()
    
    print("🧪 Testing Advanced Web Search Engine...")
    print("=" * 50)
    
    # Test query
    test_query = "software engineer jobs site:linkedin.com"
    print(f"Query: {test_query}")
    
    results = search_engine.search(test_query, num_results=5)
    
    print(f"\n📊 Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.title}")
        print(f"   🔗 {result.url}")
        print(f"   📄 {result.snippet[:100]}...")
        print(f"   🔍 Engine: {result.engine} | Rank: {result.rank}")
    
    # Show engine status
    print(f"\n🔧 Engine Status:")
    status = search_engine.get_engine_status()
    for engine, info in status.items():
        print(f"   {engine}: {info['status']} (failures: {info['failure_count']})")
