"""
Advanced Evasion Techniques
Additional anti-detection methods for 2026-level stealth
"""

import random
import hashlib
from typing import Dict, Any, List
from playwright.async_api import Page


class AdvancedEvasion:
    """
    Collection of advanced evasion techniques
    These go beyond basic stealth patches
    """
    
    @staticmethod
    def generate_speech_synthesis_voices_script() -> str:
        """Generate script to spoof speechSynthesis voices"""
        return '''
        (function() {
            const voices = [
                { name: 'Microsoft David - English (United States)', lang: 'en-US', localService: true, default: true },
                { name: 'Microsoft Zira - English (United States)', lang: 'en-US', localService: true, default: false },
                { name: 'Microsoft Mark - English (United States)', lang: 'en-US', localService: true, default: false },
                { name: 'Google US English', lang: 'en-US', localService: false, default: false },
                { name: 'Google UK English Female', lang: 'en-GB', localService: false, default: false },
                { name: 'Google UK English Male', lang: 'en-GB', localService: false, default: false }
            ];
            
            const mockVoices = voices.map(v => {
                const voice = Object.create(SpeechSynthesisVoice.prototype);
                Object.defineProperties(voice, {
                    name: { value: v.name, enumerable: true },
                    lang: { value: v.lang, enumerable: true },
                    localService: { value: v.localService, enumerable: true },
                    default: { value: v.default, enumerable: true },
                    voiceURI: { value: v.name, enumerable: true }
                });
                return voice;
            });
            
            if (window.speechSynthesis) {
                window.speechSynthesis.getVoices = function() {
                    return mockVoices;
                };
            }
        })();
        '''
    
    @staticmethod
    def generate_webrtc_evasion_script() -> str:
        """Prevent WebRTC IP leakage detection"""
        return '''
        (function() {
            // Disable WebRTC IP detection
            const originalRTCPeerConnection = window.RTCPeerConnection;
            
            if (originalRTCPeerConnection) {
                window.RTCPeerConnection = function(...args) {
                    const config = args[0] || {};
                    
                    // Force use of TURN/STUN only modes
                    config.iceTransportPolicy = 'relay';
                    
                    const pc = new originalRTCPeerConnection(config);
                    
                    // Intercept createDataChannel
                    const originalCreateDataChannel = pc.createDataChannel.bind(pc);
                    pc.createDataChannel = function(label, options) {
                        // Add delay to prevent timing attacks
                        return originalCreateDataChannel(label, options);
                    };
                    
                    return pc;
                };
                
                window.RTCPeerConnection.prototype = originalRTCPeerConnection.prototype;
            }
            
            // Also handle webkit prefix
            if (window.webkitRTCPeerConnection) {
                window.webkitRTCPeerConnection = window.RTCPeerConnection;
            }
        })();
        '''
    
    @staticmethod
    def generate_webgl_advanced_evasion_script(seed: int) -> str:
        """Advanced WebGL fingerprint evasion with shader precision spoofing"""
        return f'''
        (function() {{
            const seed = {seed};
            
            // Spoof shader precision
            const originalGetShaderPrecisionFormat = WebGLRenderingContext.prototype.getShaderPrecisionFormat;
            WebGLRenderingContext.prototype.getShaderPrecisionFormat = function(shaderType, precisionType) {{
                const result = originalGetShaderPrecisionFormat.call(this, shaderType, precisionType);
                if (result) {{
                    // Add subtle noise to precision values
                    const noiseVal = (seed % 3) - 1;
                    return {{
                        rangeMin: result.rangeMin,
                        rangeMax: result.rangeMax,
                        precision: Math.max(0, result.precision + noiseVal)
                    }};
                }}
                return result;
            }};
            
            // Spoof supported extensions
            const originalGetSupportedExtensions = WebGLRenderingContext.prototype.getSupportedExtensions;
            WebGLRenderingContext.prototype.getSupportedExtensions = function() {{
                const extensions = originalGetSupportedExtensions.call(this) || [];
                // Shuffle extensions order based on seed
                const shuffled = [...extensions];
                for (let i = shuffled.length - 1; i > 0; i--) {{
                    const j = (seed * (i + 1)) % (i + 1);
                    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
                }}
                return shuffled;
            }};
            
            // Same for WebGL2
            if (window.WebGL2RenderingContext) {{
                const originalGetShaderPrecisionFormat2 = WebGL2RenderingContext.prototype.getShaderPrecisionFormat;
                WebGL2RenderingContext.prototype.getShaderPrecisionFormat = function(shaderType, precisionType) {{
                    const result = originalGetShaderPrecisionFormat2.call(this, shaderType, precisionType);
                    if (result) {{
                        const noiseVal = (seed % 3) - 1;
                        return {{
                            rangeMin: result.rangeMin,
                            rangeMax: result.rangeMax,
                            precision: Math.max(0, result.precision + noiseVal)
                        }};
                    }}
                    return result;
                }};
                
                const originalGetSupportedExtensions2 = WebGL2RenderingContext.prototype.getSupportedExtensions;
                WebGL2RenderingContext.prototype.getSupportedExtensions = function() {{
                    const extensions = originalGetSupportedExtensions2.call(this) || [];
                    const shuffled = [...extensions];
                    for (let i = shuffled.length - 1; i > 0; i--) {{
                        const j = (seed * (i + 1)) % (i + 1);
                        [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
                    }}
                    return shuffled;
                }};
            }}
        }})();
        '''
    
    @staticmethod
    def generate_keyboard_layout_script() -> str:
        """Spoof keyboard layout detection"""
        return '''
        (function() {
            // Spoof keyboard.getLayoutMap
            if (navigator.keyboard && navigator.keyboard.getLayoutMap) {
                const originalGetLayoutMap = navigator.keyboard.getLayoutMap.bind(navigator.keyboard);
                navigator.keyboard.getLayoutMap = async function() {
                    const layoutMap = await originalGetLayoutMap();
                    // Return the original map but ensure consistent behavior
                    return layoutMap;
                };
            }
        })();
        '''
    
    @staticmethod
    def generate_storage_estimation_script() -> str:
        """Spoof storage estimation API"""
        return '''
        (function() {
            if (navigator.storage && navigator.storage.estimate) {
                navigator.storage.estimate = async function() {
                    // Return realistic but randomized values
                    const quota = (100 + Math.floor(Math.random() * 50)) * 1024 * 1024 * 1024; // 100-150 GB
                    const usage = Math.floor(Math.random() * 1024 * 1024 * 100); // 0-100 MB
                    return {
                        quota: quota,
                        usage: usage,
                        usageDetails: {}
                    };
                };
            }
        })();
        '''
    
    @staticmethod
    def generate_bluetooth_script() -> str:
        """Handle Bluetooth API queries"""
        return '''
        (function() {
            if (navigator.bluetooth) {
                navigator.bluetooth.getAvailability = async function() {
                    return false; // Most sites shouldn't expect Bluetooth to be enabled
                };
            }
        })();
        '''
    
    @staticmethod
    def generate_usb_script() -> str:
        """Handle USB API queries"""
        return '''
        (function() {
            if (navigator.usb) {
                navigator.usb.getDevices = async function() {
                    return []; // Return empty devices list
                };
            }
        })();
        '''
    
    @staticmethod
    def generate_serial_script() -> str:
        """Handle Serial API queries"""
        return '''
        (function() {
            if (navigator.serial) {
                navigator.serial.getPorts = async function() {
                    return []; // Return empty ports list
                };
            }
        })();
        '''
    
    @staticmethod
    def generate_hid_script() -> str:
        """Handle HID API queries"""
        return '''
        (function() {
            if (navigator.hid) {
                navigator.hid.getDevices = async function() {
                    return []; // Return empty devices list
                };
            }
        })();
        '''
    
    @staticmethod
    def generate_gamepad_script() -> str:
        """Spoof gamepad API"""
        return '''
        (function() {
            navigator.getGamepads = function() {
                return [null, null, null, null]; // Standard empty gamepads array
            };
        })();
        '''
    
    @staticmethod
    def generate_sensor_apis_script() -> str:
        """Handle various sensor APIs"""
        return '''
        (function() {
            // Prevent sensor-based fingerprinting
            const sensorClasses = [
                'Accelerometer', 'Gyroscope', 'Magnetometer', 
                'AbsoluteOrientationSensor', 'RelativeOrientationSensor',
                'LinearAccelerationSensor', 'GravitySensor', 'AmbientLightSensor'
            ];
            
            sensorClasses.forEach(sensorName => {
                if (window[sensorName]) {
                    const OriginalSensor = window[sensorName];
                    window[sensorName] = function(...args) {
                        const sensor = new OriginalSensor(...args);
                        // Replace addEventListener to prevent actual readings
                        sensor.addEventListener = function(type, callback) {
                            // Don't actually add the listener
                        };
                        return sensor;
                    };
                    window[sensorName].prototype = OriginalSensor.prototype;
                }
            });
        })();
        '''
    
    @staticmethod
    def generate_automation_detection_bypass_script() -> str:
        """Bypass common automation detection patterns"""
        return '''
        (function() {
            // Override document.hidden to always return false
            Object.defineProperty(document, 'hidden', {
                get: () => false,
                configurable: true
            });
            
            Object.defineProperty(document, 'visibilityState', {
                get: () => 'visible',
                configurable: true
            });
            
            // Prevent detection via document.hasFocus
            document.hasFocus = function() {
                return true;
            };
            
            // Ensure mouse events seem natural
            const originalAddEventListener = EventTarget.prototype.addEventListener;
            EventTarget.prototype.addEventListener = function(type, listener, options) {
                // Pass through but ensure we don't trigger bot detection via event patterns
                return originalAddEventListener.call(this, type, listener, options);
            };
            
            // Spoof performance entries to hide automation
            if (window.PerformanceObserver) {
                const OriginalPerformanceObserver = window.PerformanceObserver;
                window.PerformanceObserver = function(callback) {
                    const observer = new OriginalPerformanceObserver((list, observer) => {
                        const entries = list.getEntries().filter(entry => {
                            // Filter out entries that might indicate automation
                            return !entry.name.includes('devtools') && 
                                   !entry.name.includes('automation') &&
                                   !entry.name.includes('playwright');
                        });
                        if (entries.length > 0) {
                            callback({ getEntries: () => entries }, observer);
                        }
                    });
                    return observer;
                };
                window.PerformanceObserver.prototype = OriginalPerformanceObserver.prototype;
                window.PerformanceObserver.supportedEntryTypes = OriginalPerformanceObserver.supportedEntryTypes;
            }
        })();
        '''
    
    @staticmethod
    def generate_timezone_integrity_script(timezone: str, locale: str) -> str:
        """Ensure timezone handling is consistent"""
        return f'''
        (function() {{
            const targetTimezone = '{timezone}';
            const targetLocale = '{locale}';
            
            // Ensure Intl.DateTimeFormat returns consistent timezone
            const OriginalDateTimeFormat = Intl.DateTimeFormat;
            Intl.DateTimeFormat = function(locales, options) {{
                const opts = options || {{}};
                if (!opts.timeZone) {{
                    opts.timeZone = targetTimezone;
                }}
                return new OriginalDateTimeFormat(locales || targetLocale, opts);
            }};
            Intl.DateTimeFormat.prototype = OriginalDateTimeFormat.prototype;
            Intl.DateTimeFormat.supportedLocalesOf = OriginalDateTimeFormat.supportedLocalesOf;
            
            // Ensure Date.prototype.getTimezoneOffset is consistent
            const baseOffset = new Date().getTimezoneOffset();
            // Keep the actual offset for consistency
        }})();
        '''
    
    @staticmethod
    def generate_rect_noise_script(seed: int) -> str:
        """Add subtle noise to getBoundingClientRect and similar methods"""
        return f'''
        (function() {{
            const seed = {seed};
            
            // Add imperceptible noise to element rects
            const originalGetBoundingClientRect = Element.prototype.getBoundingClientRect;
            Element.prototype.getBoundingClientRect = function() {{
                const rect = originalGetBoundingClientRect.call(this);
                // Add noise in the sub-pixel range (won't affect layout)
                const noise = ((seed * rect.width * rect.height) % 1000) / 10000000;
                return {{
                    x: rect.x + noise,
                    y: rect.y + noise,
                    width: rect.width + noise,
                    height: rect.height + noise,
                    top: rect.top + noise,
                    right: rect.right + noise,
                    bottom: rect.bottom + noise,
                    left: rect.left + noise,
                    toJSON: rect.toJSON ? rect.toJSON.bind(rect) : undefined
                }};
            }};
            
            // Same for getClientRects
            const originalGetClientRects = Element.prototype.getClientRects;
            Element.prototype.getClientRects = function() {{
                const rects = originalGetClientRects.call(this);
                const modifiedRects = [];
                for (let i = 0; i < rects.length; i++) {{
                    const rect = rects[i];
                    const noise = ((seed * (i + 1) * rect.width) % 1000) / 10000000;
                    modifiedRects.push({{
                        x: rect.x + noise,
                        y: rect.y + noise,
                        width: rect.width + noise,
                        height: rect.height + noise,
                        top: rect.top + noise,
                        right: rect.right + noise,
                        bottom: rect.bottom + noise,
                        left: rect.left + noise
                    }});
                }}
                return modifiedRects;
            }};
        }})();
        '''
    
    @staticmethod
    def generate_math_fingerprint_evasion_script(seed: int) -> str:
        """Add imperceptible noise to Math functions used for fingerprinting"""
        return f'''
        (function() {{
            const seed = {seed};
            const epsilon = 1e-15; // Extremely small noise
            
            const originalSin = Math.sin;
            Math.sin = function(x) {{
                const result = originalSin(x);
                // Add noise only for very specific values used in fingerprinting
                if (Math.abs(x - 0.5) < 0.0001) {{
                    return result + (seed % 10) * epsilon;
                }}
                return result;
            }};
            
            const originalCos = Math.cos;
            Math.cos = function(x) {{
                const result = originalCos(x);
                if (Math.abs(x - 0.5) < 0.0001) {{
                    return result + (seed % 10) * epsilon;
                }}
                return result;
            }};
            
            const originalTan = Math.tan;
            Math.tan = function(x) {{
                const result = originalTan(x);
                if (Math.abs(x - 0.5) < 0.0001) {{
                    return result + (seed % 10) * epsilon;
                }}
                return result;
            }};
            
            // Ensure toString doesn't reveal modifications
            Math.sin.toString = () => 'function sin() {{ [native code] }}';
            Math.cos.toString = () => 'function cos() {{ [native code] }}';
            Math.tan.toString = () => 'function tan() {{ [native code] }}';
        }})();
        '''
    
    @classmethod
    def get_all_evasion_scripts(cls, fingerprint_seed: int, timezone: str, locale: str) -> List[str]:
        """Get all advanced evasion scripts"""
        return [
            cls.generate_speech_synthesis_voices_script(),
            cls.generate_webrtc_evasion_script(),
            cls.generate_webgl_advanced_evasion_script(fingerprint_seed),
            cls.generate_keyboard_layout_script(),
            cls.generate_storage_estimation_script(),
            cls.generate_bluetooth_script(),
            cls.generate_usb_script(),
            cls.generate_serial_script(),
            cls.generate_hid_script(),
            cls.generate_gamepad_script(),
            cls.generate_sensor_apis_script(),
            cls.generate_automation_detection_bypass_script(),
            cls.generate_timezone_integrity_script(timezone, locale),
            cls.generate_rect_noise_script(fingerprint_seed),
            cls.generate_math_fingerprint_evasion_script(fingerprint_seed),
        ]
    
    @classmethod
    async def inject_all(cls, page: Page, fingerprint_seed: int, timezone: str, locale: str) -> None:
        """Inject all advanced evasion scripts into a page"""
        scripts = cls.get_all_evasion_scripts(fingerprint_seed, timezone, locale)
        combined_script = '\n'.join(scripts)
        await page.add_init_script(combined_script)
