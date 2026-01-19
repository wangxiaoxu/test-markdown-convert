"""
Configuration management for the converter service.

This module provides centralized configuration using environment variables
with sensible defaults for all settings.
"""

import os
from functools import lru_cache


class Settings:
    """Application settings loaded from environment variables.
    
    All settings have sensible defaults and can be overridden via
    environment variables.
    """
    
    # Application info
    APP_NAME: str = "Markdown Converter"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Pandoc-based document conversion service"
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # File handling
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    TEMP_DIR: str = "/tmp/converter"
    ALLOWED_INPUT_FORMATS: list[str] = [".md", ".markdown", ".txt"]
    
    # Pandoc settings
    PANDOC_TIMEOUT: int = 30  # seconds
    PDF_ENGINE: str = "xelatex"
    
    # CORS settings
    CORS_ORIGINS: list[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]
    
    def __init__(self):
        """Initialize settings from environment variables."""
        # Server settings
        self.HOST = os.getenv("HOST", self.HOST)
        self.PORT = int(os.getenv("PORT", str(self.PORT)))
        
        # Logging
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", self.LOG_LEVEL).upper()
        
        # File handling
        self.MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", str(self.MAX_FILE_SIZE)))
        self.TEMP_DIR = os.getenv("TEMP_DIR", self.TEMP_DIR)
        
        # Pandoc settings
        self.PANDOC_TIMEOUT = int(os.getenv("PANDOC_TIMEOUT", str(self.PANDOC_TIMEOUT)))
        self.PDF_ENGINE = os.getenv("PDF_ENGINE", self.PDF_ENGINE)
        
        # CORS - parse comma-separated origins
        cors_origins = os.getenv("CORS_ORIGINS")
        if cors_origins:
            self.CORS_ORIGINS = [origin.strip() for origin in cors_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.
    
    Returns:
        Settings instance (cached).
    """
    return Settings()


# Convenience access
settings = get_settings()
