import json
import datetime
from dateutil import parser
import dateutil
import time
import random
import yaml
import logging
import os
import traceback
from collections import deque,defaultdict
import re
import threading

def log_message(message, level=logging.INFO):
    logger = logging.getLogger()
    log_func = {
        logging.DEBUG: logger.debug,
        logging.INFO: logger.info,
        logging.WARNING: logger.warning,
        logging.ERROR: logger.error,
        logging.CRITICAL: logger.critical
    }
    log_func.get(level, logger.info)(message)