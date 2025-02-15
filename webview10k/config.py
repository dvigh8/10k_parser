import os
import logfire as log

LOGFIRE_TOKEN = os.getenv("LOGFIRE_TOKEN")

if LOGFIRE_TOKEN:
    log.configure(token=LOGFIRE_TOKEN)
else:
    import logging as log
    log.basicConfig(level=log.INFO)
    log.info("Logfire token not found. Using default logging configuration.")


