#!/usr/bin/env python
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from modules.on_page_analyzer import OnPageAnalyzer
    print("✓ OnPageAnalyzer imported successfully")
except Exception as e:
    print(f"✗ Failed to import OnPageAnalyzer: {e}")

try:
    from modules.technical_seo_analyzer import TechnicalSEOAnalyzer
    print("✓ TechnicalSEOAnalyzer imported successfully")
except Exception as e:
    print(f"✗ Failed to import TechnicalSEOAnalyzer: {e}")

try:
    from modules.content_analyzer import ContentAnalyzer
    print("✓ ContentAnalyzer imported successfully")
except Exception as e:
    print(f"✗ Failed to import ContentAnalyzer: {e}")

try:
    from modules.scoring_module import ScoringModule
    print("✓ ScoringModule imported successfully")
except Exception as e:
    print(f"✗ Failed to import ScoringModule: {e}")

try:
    from seo_analyzer_main import SEOAnalyzer
    print("✓ SEOAnalyzer imported successfully")
except Exception as e:
    print(f"✗ Failed to import SEOAnalyzer: {e}")

try:
    from app.services.seo_service import get_seo_service
    seo_service = get_seo_service()
    print("✓ SEO service created successfully")
except Exception as e:
    print(f"✗ Failed to create SEO service: {e}")