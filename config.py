"""
Configuration Management
Centralized configuration with environment variable support
Industrial-Grade Terabox Extractor - 2026 Edition
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class BrowserConfig:
    """Browser automation configuration with hardened stealth flags"""
    headless: bool = True
    slow_mo: int = 0
    timeout: int = 60000  # 60 seconds
    navigation_timeout: int = 45000
    
    # Chromium launch arguments (maximum stealth)
    launch_args: List[str] = field(default_factory=lambda: [
        # Core stealth flags
        '--disable-blink-features=AutomationControlled',
        '--disable-features=IsolateOrigins,site-per-process',
        '--disable-site-isolation-trials',
        '--disable-web-security',
        '--disable-features=CrossSiteDocumentBlockingIfIsolating',
        '--disable-features=CrossSiteDocumentBlockingAlways',
        
        # Sandbox settings for cloud deployment
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        
        # GPU and rendering
        '--disable-accelerated-2d-canvas',
        '--disable-gpu',
        '--disable-gpu-sandbox',
        '--disable-software-rasterizer',
        
        # Window settings
        '--window-size=1920,1080',
        '--start-maximized',
        '--hide-scrollbars',
        '--mute-audio',
        
        # Background process optimization
        '--disable-background-timer-throttling',
        '--disable-backgrounding-occluded-windows',
        '--disable-renderer-backgrounding',
        '--disable-background-networking',
        
        # Disable telemetry and tracking
        '--disable-infobars',
        '--disable-breakpad',
        '--disable-component-extensions-with-background-pages',
        '--disable-extensions',
        '--disable-features=TranslateUI',
        '--disable-ipc-flooding-protection',
        '--disable-default-apps',
        '--disable-hang-monitor',
        '--disable-sync',
        '--disable-client-side-phishing-detection',
        '--disable-domain-reliability',
        '--disable-features=OptimizationGuideModelDownloading,OptimizationHintsFetching,OptimizationTargetPrediction,OptimizationHints',
        
        # Network settings
        '--enable-features=NetworkService,NetworkServiceInProcess',
        
        # Appearance
        '--force-color-profile=srgb',
        '--metrics-recording-only',
        '--no-first-run',
        '--password-store=basic',
        '--use-mock-keychain',
        '--export-tagged-pdf',
        '--disable-popup-blocking',
        '--disable-prompt-on-repost',
        
        # Additional stealth
        '--disable-blink-features=IdleDetection',
        '--disable-features=UserAgentClientHint',
        '--disable-reading-from-canvas',
        '--disable-features=PaintHolding',
        '--disable-partial-raster',
        '--disable-skia-runtime-opts',
        '--disable-speech-api',
        '--disable-voice-input',
        '--disable-wake-on-wifi',
        '--disable-webgl',
        '--disable-webgl2',
        '--enable-webgl-draft-extensions',
        '--no-default-browser-check',
        '--no-pings',
        '--use-gl=swiftshader',
        '--ignore-gpu-blocklist',
        '--disable-features=AudioServiceOutOfProcess',
        '--disable-features=IsolateOrigins',
        '--disable-features=site-per-process',
        '--disable-features=TranslateUI',
        '--disable-features=BlinkGenPropertyTrees',
    ])


@dataclass
class ExtractionConfig:
    """Extraction pipeline configuration"""
    max_retries: int = 3
    retry_delay_base: float = 2.0
    retry_delay_max: float = 10.0
    
    # Layer timeouts (ms)
    network_layer_timeout: int = 30000
    js_layer_timeout: int = 10000
    dom_layer_timeout: int = 45000
    
    # Minimum file size to consider as target (bytes)
    min_file_size: int = 512 * 1024  # 512KB
    
    # CDN patterns for Terabox (comprehensive list)
    cdn_patterns: List[str] = field(default_factory=lambda: [
        'cdnst', 'd.terabox', 'data.terabox', 'download.terabox',
        'cdn.terabox', 'st.terabox', 'd2.terabox', 'd3.terabox',
        'd4.terabox', 'd5.terabox', 'stream', 'datadown', 'nxcdn',
        'dxcdn', 'hot.terabox', 'cold.terabox', 'jp-store', 'asia-store',
        'us-store', 'eu-store', 'video-cdn', 'file-cdn', 'media-cdn',
        'storage', 'dl.terabox', 'get.terabox', 'fetch.terabox',
        'pan.terabox', 'pcs.terabox', 'c.terabox', 'f.terabox',
    ])
    
    # Signature query parameters (indicates signed URL)
    signature_params: List[str] = field(default_factory=lambda: [
        'sign', 'time', 'timestamp', 'expires', 'expiry', 'exp',
        'token', 'auth', 'signature', 'key', 'secret', 'sig',
        'fid', 'uk', 'devuid', 'dp-logid', 'shareid', 'fsid',
        'rand', 'vuk', 'app_id', 'check_blue_name', 'clienttype',
        'channel', 'version', 'web', 'dp-callid', 'scene',
    ])
    
    # Supported domains
    supported_domains: List[str] = field(default_factory=lambda: [
        'terabox.com', '1024tera.com', 'teraboxapp.com', '4funbox.co',
        'mirrobox.com', 'nephobox.com', 'freeterabox.com', 'momerybox.com',
        'teraboxlink.com', 'terafileshare.com', 'terabox.fun', 'terabox.app',
        '1024terabox.com', 'teraboxshare.com', 'terabox.tech', 'gcloud.live',
    ])


@dataclass
class BotConfig:
    """Telegram bot configuration"""
    token: str = field(default_factory=lambda: os.getenv('BOT_TOKEN', ''))
    admin_ids: List[int] = field(default_factory=list)
    rate_limit_requests: int = 5
    rate_limit_window: int = 60  # seconds
    
    # Processing settings
    processing_timeout: int = 120  # seconds
    max_concurrent_extractions: int = 3


@dataclass
class Config:
    """Main configuration container"""
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    extraction: ExtractionConfig = field(default_factory=ExtractionConfig)
    bot: BotConfig = field(default_factory=BotConfig)
    
    # Debug mode
    debug: bool = field(default_factory=lambda: os.getenv('DEBUG', 'false').lower() == 'true')
    
    # Logging level
    log_level: str = field(default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO'))


# Global configuration instance
config = Config()
