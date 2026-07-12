"""MVP JSON-LD sitemap summoner.

Reads mvp_config.yaml, walks sitemaps, extracts JSON-LD, stores in S3.
Optional Browserless headless fetch when a source has headless: true.
"""

__version__ = "0.1.0"
