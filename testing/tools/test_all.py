"""
Main test file that imports all tests from subdirectories
Run this file with: python -m pytest testing/tools/test_all.py
"""

# Import all tests from the subdirectories
from .alerts.test_alert_tools import *
from .rules.test_rule_tools import *
from .exceptions.test_exception_tools import *
from .endpoint.test_endpoint_tools import *
