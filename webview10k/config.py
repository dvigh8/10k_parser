"""Configuration module for the 10-K parser application.

This module handles logging configuration using either Logfire or default Python logging.

Attributes:
    LOGFIRE_TOKEN (str): Environment variable for Logfire authentication token
    log: Configured logger instance (either Logfire or standard Python logging)

Environment Variables:
    LOGFIRE_TOKEN: Required for Logfire integration. If not set, falls back to standard logging.

Notes:
    - If LOGFIRE_TOKEN is set, configures Logfire for application logging
    - If LOGFIRE_TOKEN is not set, uses Python's built-in logging with INFO level
"""
import os
import logfire as log

LOGFIRE_TOKEN = os.getenv("LOGFIRE_TOKEN")

if LOGFIRE_TOKEN:
    log.configure(token=LOGFIRE_TOKEN)
else:
    import logging as log
    log.basicConfig(level=log.INFO)
    log.info("Logfire token not found. Using default logging configuration.")


