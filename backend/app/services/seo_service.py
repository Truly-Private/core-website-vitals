"""
SEO Analysis Service for Core Website Vitals.
Wraps existing SEO analysis modules in an async service layer.
"""

import asyncio
import sys
import os
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import threading
import multiprocessing

# Add the backend directory to the Python path to import existing modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.models.schemas import AnalysisType, AnalysisStatus
from app.core.config import get_settings
import structlog

# Import existing SEO modules
try:
    from modules.on_page_analyzer import OnPageAnalyzer
    from modules.technical_seo_analyzer import TechnicalSEOAnalyzer
    from modules.content_analyzer import ContentAnalyzer
    from modules.scoring_module import ScoringModule
    # Import the SEOAnalyzer from the seo_analyzer_main.py file
    from seo_analyzer_main import SEOAnalyzer
except ImportError as e:
    # If modules are not found, create placeholder classes
    structlog.get_logger().error("Failed to import SEO modules", error=str(e))
    
    class OnPageAnalyzer:
        def __init__(self, config=None):
            self.config = config or {}
        def analyze(self, url: str) -> dict:
            return {"OnPageAnalyzer": {"error": "Module not available"}}
    
    class TechnicalSEOAnalyzer:
        def __init__(self, config=None):
            self.config = config or {}
        def analyze(self, url: str) -> dict:
            return {"TechnicalSEOAnalyzer": {"error": "Module not available"}}
    
    class ContentAnalyzer:
        def __init__(self, config=None):
            self.config = config or {}
        def analyze(self, url: str) -> dict:
            return {"ContentAnalyzer": {"error": "Module not available"}}
    
    class ScoringModule:
        def __init__(self, config=None):
            self.config = config or {}
        def analyze(self, url: str, full_report_data: dict = None) -> dict:
            return {"ScoringModule": {"error": "Module not available"}}
    
    class SEOAnalyzer:
        def __init__(self, url: str, output_format: str = "json", config: dict = None):
            self.url = url
            self.config = config or {}
        def run_analysis(self, target_url: str, cli_keywords: List[str] = None) -> dict:
            return {"error": "SEO modules not available"}

logger = structlog.get_logger(__name__)


class SEOAnalysisService:
    """
    Service layer that wraps existing SEO analysis modules.
    Provides async interface and configuration management.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.process_executor = ProcessPoolExecutor(max_workers=2)
        self.default_config = self._get_default_config()
        self.analysis_cache = {}
        self.cache_lock = threading.Lock()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for SEO analysis modules."""
        return {
            "OnPageAnalyzer": {
                "title_min_length": 20,
                "title_max_length": 70,
                "desc_min_length": 70,
                "desc_max_length": 160,
                "content_min_words": 300,
                "links_min_count": 5,
                "active_check_limit": 10,
                "url_max_length": 100,
                "url_max_depth": 4
            },
            "TechnicalSEOAnalyzer": {
                "check_robots_txt": True,
                "check_sitemap": True,
                "check_ssl": True,
                "check_mobile_responsive": True,
                "check_structured_data": True
            },
            "ContentAnalyzer": {
                "top_n_keywords_count": 10,
                "spellcheck_language": "en",
                "min_readability_score": 60,
                "target_keywords": []
            },
            "ScoringModule": {
                "weights": {},
                "category_weights": {
                    "OnPage": 0.40,
                    "Technical": 0.35,
                    "Content": 0.25
                }
            },
            "Global": {
                "request_timeout": 30,
                "max_retries": 3,
                "retry_delay": 5
            }
        }
    
    def _validate_url(self, url: str) -> bool:
        """
        Validate URL format and accessibility.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid
        """
        try:
            parsed = urlparse(url)
            return all([parsed.scheme, parsed.netloc])
        except Exception:
            return False
    
    def _normalize_url(self, url: str) -> str:
        """
        Normalize URL by adding protocol if missing.
        
        Args:
            url: URL to normalize
            
        Returns:
            Normalized URL
        """
        if not url.startswith(('http://', 'https://')):
            return 'https://' + url
        return url
    
    async def analyze_url(
        self,
        url: str,
        analysis_type: AnalysisType = AnalysisType.FULL_SEO,
        target_keywords: Optional[List[str]] = None,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform SEO analysis on a URL.
        
        Args:
            url: URL to analyze
            analysis_type: Type of analysis to perform
            target_keywords: Keywords to target for content analysis
            custom_config: Custom configuration overrides
            
        Returns:
            Analysis results
        """
        try:
            # Validate and normalize URL
            if not self._validate_url(url):
                raise ValueError(f"Invalid URL: {url}")
            
            url = self._normalize_url(url)
            
            # Check cache first
            cache_key = f"{url}_{analysis_type}_{hash(str(target_keywords))}"
            if cache_key in self.analysis_cache:
                cached_result = self.analysis_cache[cache_key]
                cache_age = datetime.utcnow() - cached_result["timestamp"]
                if cache_age.total_seconds() < 3600:  # Cache for 1 hour
                    logger.info("Returning cached analysis result", url=url)
                    return cached_result["result"]
            
            # Prepare configuration
            config = self.default_config.copy()
            if custom_config:
                for key, value in custom_config.items():
                    if key in config and isinstance(config[key], dict) and isinstance(value, dict):
                        config[key].update(value)
                    else:
                        config[key] = value
            
            # Add target keywords to content analyzer config
            if target_keywords:
                config["ContentAnalyzer"]["target_keywords"] = target_keywords
            
            # Run analysis based on type
            if analysis_type == AnalysisType.FULL_SEO:
                result = await self._run_full_analysis(url, config)
            elif analysis_type == AnalysisType.QUICK_SCAN:
                result = await self._run_quick_analysis(url, config)
            elif analysis_type == AnalysisType.TECHNICAL_ONLY:
                result = await self._run_technical_analysis(url, config)
            elif analysis_type == AnalysisType.CONTENT_ONLY:
                result = await self._run_content_analysis(url, config)
            else:
                raise ValueError(f"Unknown analysis type: {analysis_type}")
            
            # Cache result
            with self.cache_lock:
                self.analysis_cache[cache_key] = {
                    "result": result,
                    "timestamp": datetime.utcnow()
                }
            
            logger.info("SEO analysis completed successfully", 
                       url=url, analysis_type=analysis_type)
            
            return result
            
        except Exception as e:
            logger.error("SEO analysis failed", 
                        url=url, analysis_type=analysis_type, error=str(e))
            raise
    
    async def _run_full_analysis(self, url: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run full SEO analysis including all modules.
        
        Args:
            url: URL to analyze
            config: Configuration for analysis
            
        Returns:
            Full analysis results
        """
        try:
            # Use thread executor for CPU-intensive analysis
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._run_analysis_sync,
                url,
                config,
                []  # No specific keywords for full analysis
            )
            
            return result
            
        except Exception as e:
            logger.error("Full analysis failed", url=url, error=str(e))
            raise
    
    async def _run_quick_analysis(self, url: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run quick SEO analysis with essential checks only.
        
        Args:
            url: URL to analyze
            config: Configuration for analysis
            
        Returns:
            Quick analysis results
        """
        try:
            # Modify config for quick analysis
            quick_config = config.copy()
            quick_config["OnPageAnalyzer"]["active_check_limit"] = 5
            quick_config["ContentAnalyzer"]["top_n_keywords_count"] = 5
            quick_config["Global"]["request_timeout"] = 15
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._run_analysis_sync,
                url,
                quick_config,
                []
            )
            
            return result
            
        except Exception as e:
            logger.error("Quick analysis failed", url=url, error=str(e))
            raise
    
    async def _run_technical_analysis(self, url: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run technical SEO analysis only.
        
        Args:
            url: URL to analyze
            config: Configuration for analysis
            
        Returns:
            Technical analysis results
        """
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._run_technical_only_sync,
                url,
                config
            )
            
            return result
            
        except Exception as e:
            logger.error("Technical analysis failed", url=url, error=str(e))
            raise
    
    async def _run_content_analysis(self, url: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run content analysis only.
        
        Args:
            url: URL to analyze
            config: Configuration for analysis
            
        Returns:
            Content analysis results
        """
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._run_content_only_sync,
                url,
                config
            )
            
            return result
            
        except Exception as e:
            logger.error("Content analysis failed", url=url, error=str(e))
            raise
    
    def _run_analysis_sync(self, url: str, config: Dict[str, Any], keywords: List[str]) -> Dict[str, Any]:
        """
        Synchronous wrapper for the existing SEO analyzer.
        
        Args:
            url: URL to analyze
            config: Configuration
            keywords: Target keywords
            
        Returns:
            Analysis results
        """
        try:
            analyzer = SEOAnalyzer(url=url, output_format="json", config=config)
            result = analyzer.run_analysis(target_url=url, cli_keywords=keywords)
            
            return result
            
        except Exception as e:
            logger.error("Synchronous analysis failed", url=url, error=str(e))
            return {
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "target_url": url,
                "domain": urlparse(url).netloc,
                "error": str(e),
                "seo_attributes": {}
            }
    
    def _run_technical_only_sync(self, url: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run only technical SEO analysis.
        
        Args:
            url: URL to analyze
            config: Configuration
            
        Returns:
            Technical analysis results
        """
        try:
            tech_analyzer = TechnicalSEOAnalyzer(config=config.get("TechnicalSEOAnalyzer", {}))
            tech_results = tech_analyzer.analyze(url)
            
            result = {
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "target_url": url,
                "domain": urlparse(url).netloc,
                "seo_attributes": tech_results
            }
            
            return result
            
        except Exception as e:
            logger.error("Technical analysis sync failed", url=url, error=str(e))
            return {
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "target_url": url,
                "domain": urlparse(url).netloc,
                "error": str(e),
                "seo_attributes": {}
            }
    
    def _run_content_only_sync(self, url: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run only content analysis.
        
        Args:
            url: URL to analyze
            config: Configuration
            
        Returns:
            Content analysis results
        """
        try:
            content_analyzer = ContentAnalyzer(config=config.get("ContentAnalyzer", {}))
            content_results = content_analyzer.analyze(url)
            
            result = {
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "target_url": url,
                "domain": urlparse(url).netloc,
                "seo_attributes": content_results
            }
            
            return result
            
        except Exception as e:
            logger.error("Content analysis sync failed", url=url, error=str(e))
            return {
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "target_url": url,
                "domain": urlparse(url).netloc,
                "error": str(e),
                "seo_attributes": {}
            }
    
    async def batch_analyze_urls(
        self,
        urls: List[str],
        analysis_type: AnalysisType = AnalysisType.FULL_SEO,
        target_keywords: Optional[List[str]] = None,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple URLs concurrently.
        
        Args:
            urls: List of URLs to analyze
            analysis_type: Type of analysis to perform
            target_keywords: Keywords to target for content analysis
            custom_config: Custom configuration overrides
            
        Returns:
            List of analysis results
        """
        try:
            # Create analysis tasks
            tasks = []
            for url in urls:
                task = self.analyze_url(
                    url=url,
                    analysis_type=analysis_type,
                    target_keywords=target_keywords,
                    custom_config=custom_config
                )
                tasks.append(task)
            
            # Run analyses concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error("Batch analysis failed for URL", 
                                url=urls[i], error=str(result))
                    processed_results.append({
                        "analysis_timestamp": datetime.utcnow().isoformat(),
                        "target_url": urls[i],
                        "domain": urlparse(urls[i]).netloc,
                        "error": str(result),
                        "seo_attributes": {}
                    })
                else:
                    processed_results.append(result)
            
            return processed_results
            
        except Exception as e:
            logger.error("Batch analysis failed", error=str(e))
            raise
    
    async def get_analysis_preview(self, url: str) -> Dict[str, Any]:
        """
        Get a quick preview of analysis without full processing.
        
        Args:
            url: URL to preview
            
        Returns:
            Preview information
        """
        try:
            if not self._validate_url(url):
                raise ValueError(f"Invalid URL: {url}")
            
            url = self._normalize_url(url)
            parsed = urlparse(url)
            
            # Basic URL analysis
            preview = {
                "url": url,
                "domain": parsed.netloc,
                "scheme": parsed.scheme,
                "path": parsed.path,
                "is_https": parsed.scheme == 'https',
                "estimated_analysis_time": self._estimate_analysis_time(url),
                "supported_analysis_types": [
                    AnalysisType.FULL_SEO,
                    AnalysisType.QUICK_SCAN,
                    AnalysisType.TECHNICAL_ONLY,
                    AnalysisType.CONTENT_ONLY
                ]
            }
            
            return preview
            
        except Exception as e:
            logger.error("Analysis preview failed", url=url, error=str(e))
            raise
    
    def _estimate_analysis_time(self, url: str) -> Dict[str, int]:
        """
        Estimate analysis time based on URL complexity.
        
        Args:
            url: URL to estimate
            
        Returns:
            Estimated times in seconds
        """
        base_time = 30  # Base time for simple analysis
        
        # Add time based on URL complexity
        parsed = urlparse(url)
        path_segments = len(parsed.path.split('/'))
        
        if path_segments > 3:
            base_time += 10
        if parsed.query:
            base_time += 5
        
        return {
            "full_seo": base_time + 60,
            "quick_scan": base_time + 15,
            "technical_only": base_time + 20,
            "content_only": base_time + 30
        }
    
    async def validate_analysis_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate analysis configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            Validation results
        """
        try:
            validation_result = {
                "is_valid": True,
                "errors": [],
                "warnings": []
            }
            
            # Check required sections
            required_sections = ["OnPageAnalyzer", "TechnicalSEOAnalyzer", "ContentAnalyzer", "ScoringModule"]
            for section in required_sections:
                if section not in config:
                    validation_result["warnings"].append(f"Missing section: {section}")
            
            # Validate specific configuration values
            if "OnPageAnalyzer" in config:
                on_page_config = config["OnPageAnalyzer"]
                if on_page_config.get("title_min_length", 0) > on_page_config.get("title_max_length", 100):
                    validation_result["errors"].append("title_min_length cannot be greater than title_max_length")
            
            if "Global" in config:
                global_config = config["Global"]
                if global_config.get("request_timeout", 10) < 5:
                    validation_result["warnings"].append("request_timeout below 5 seconds may cause failures")
            
            validation_result["is_valid"] = len(validation_result["errors"]) == 0
            
            return validation_result
            
        except Exception as e:
            logger.error("Config validation failed", error=str(e))
            return {
                "is_valid": False,
                "errors": [str(e)],
                "warnings": []
            }
    
    def cleanup_cache(self):
        """Clean up expired cache entries."""
        try:
            current_time = datetime.utcnow()
            with self.cache_lock:
                expired_keys = []
                for key, cached_data in self.analysis_cache.items():
                    age = current_time - cached_data["timestamp"]
                    if age.total_seconds() > 3600:  # 1 hour expiration
                        expired_keys.append(key)
                
                for key in expired_keys:
                    del self.analysis_cache[key]
                
                logger.info("Cache cleanup completed", 
                           expired_entries=len(expired_keys))
                
        except Exception as e:
            logger.error("Cache cleanup failed", error=str(e))
    
    async def shutdown(self):
        """Shutdown the service and cleanup resources."""
        try:
            self.executor.shutdown(wait=True)
            self.process_executor.shutdown(wait=True)
            self.analysis_cache.clear()
            logger.info("SEO Analysis Service shutdown completed")
            
        except Exception as e:
            logger.error("Service shutdown failed", error=str(e))


# Service instance
_seo_service = None


def get_seo_service() -> SEOAnalysisService:
    """
    Get SEO Analysis Service instance (singleton).
    
    Returns:
        SEOAnalysisService instance
    """
    global _seo_service
    if _seo_service is None:
        _seo_service = SEOAnalysisService()
    return _seo_service


async def analyze_url_async(
    url: str,
    analysis_type: AnalysisType = AnalysisType.FULL_SEO,
    target_keywords: Optional[List[str]] = None,
    custom_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convenience function for URL analysis.
    
    Args:
        url: URL to analyze
        analysis_type: Type of analysis
        target_keywords: Keywords to target
        custom_config: Custom configuration
        
    Returns:
        Analysis results
    """
    service = get_seo_service()
    return await service.analyze_url(
        url=url,
        analysis_type=analysis_type,
        target_keywords=target_keywords,
        custom_config=custom_config
    )


# Export main functions and classes
__all__ = [
    "SEOAnalysisService",
    "get_seo_service",
    "analyze_url_async"
]