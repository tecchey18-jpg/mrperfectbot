"""
Browser Package
Stealth browser automation with anti-detection
"""

from .fingerprint import Fingerprint, FingerprintGenerator
from .stealth import StealthConfig, inject_stealth_scripts
from .evasion import AdvancedEvasion
from .context import BrowserContextManager

__all__ = [
    'Fingerprint', 
    'FingerprintGenerator',
    'StealthConfig',
    'inject_stealth_scripts',
    'AdvancedEvasion',
    'BrowserContextManager'
]
