"""
Advanced Stealth Configuration and Script Injection
2026-level anti-detection for Playwright
"""

import json
from dataclasses import dataclass
from typing import Dict, Any, Optional
from .fingerprint import Fingerprint


@dataclass
class StealthConfig:
    """Configuration for stealth patches"""
    hide_webdriver: bool = True
    hide_automation: bool = True
    mock_plugins: bool = True
    mock_languages: bool = True
    mock_permissions: bool = True
    mock_webgl: bool = True
    mock_canvas: bool = True
    mock_audio: bool = True
    mock_fonts: bool = True
    mock_battery: bool = True
    mock_connection: bool = True
    mock_hardware: bool = True
    spoof_chrome_runtime: bool = True
    patch_iframe: bool = True


def generate_stealth_script(fingerprint: Fingerprint, config: Optional[StealthConfig] = None) -> str:
    """
    Generate comprehensive stealth JavaScript
    This script is injected before any page content loads
    """
    if config is None:
        config = StealthConfig()
    
    fp_json = json.dumps({
        'platform': fingerprint.platform,
        'languages': fingerprint.languages,
        'deviceMemory': fingerprint.device_memory,
        'hardwareConcurrency': fingerprint.hardware_concurrency,
        'webglVendor': fingerprint.webgl_vendor,
        'webglRenderer': fingerprint.webgl_renderer,
        'colorDepth': fingerprint.color_depth,
        'pixelRatio': fingerprint.pixel_ratio,
        'doNotTrack': fingerprint.do_not_track,
        'touchSupport': fingerprint.touch_support,
        'audioSeed': fingerprint.audio_context_seed,
        'canvasSeed': fingerprint.canvas_seed,
        'fonts': fingerprint.fonts,
        'battery': fingerprint.battery,
        'connection': fingerprint.connection,
        'screen': fingerprint.screen,
        'viewport': fingerprint.viewport,
    })
    
    return f'''
    (function() {{
        'use strict';
        
        const fp = {fp_json};
        
        // ==================== WEBDRIVER EVASION ====================
        
        // Delete webdriver from navigator prototype
        if (navigator.webdriver !== undefined) {{
            Object.defineProperty(navigator, 'webdriver', {{
                get: () => undefined,
                configurable: true
            }});
        }}
        
        // Remove from prototype chain
        const originalProto = Navigator.prototype;
        const webdriverDescriptor = Object.getOwnPropertyDescriptor(originalProto, 'webdriver');
        if (webdriverDescriptor) {{
            delete Navigator.prototype.webdriver;
        }}
        
        // ==================== AUTOMATION FLAGS ====================
        
        // Remove Playwright/Puppeteer specific globals
        const automationGlobals = [
            '__playwright',
            '__pw_manual',
            '__PW_inspect',
            '__playwright_evaluation_script__',
            'cdc_adoQpoasnfa76pfcZLmcfl_Array',
            'cdc_adoQpoasnfa76pfcZLmcfl_Promise',
            'cdc_adoQpoasnfa76pfcZLmcfl_Symbol',
            '__driver_evaluate',
            '__webdriver_evaluate',
            '__selenium_evaluate',
            '__fxdriver_evaluate',
            '__driver_unwrapped',
            '__webdriver_unwrapped',
            '__selenium_unwrapped',
            '__fxdriver_unwrapped',
            '_Selenium_IDE_Recorder',
            '_selenium',
            'calledSelenium',
            '$chrome_asyncScriptInfo',
            '$cdc_asdjflasutopfhvcZLmcfl_',
            '$wdc_',
            '__lastWatirAlert',
            '__lastWatirConfirm',
            '__lastWatirPrompt',
            '__webdriver_script_function',
            '__webdriver_script_func',
            '__webdriver_script_fn',
            'webdriver',
            '_WEBDRIVER_ELEM_CACHE',
            'ChromeDriverw',
            'driver-hierarchical-id'
        ];
        
        automationGlobals.forEach(prop => {{
            try {{
                if (prop in window) {{
                    delete window[prop];
                }}
            }} catch(e) {{}}
        }});
        
        // Clean document properties
        const docAutomation = ['$cdc_asdjflasutopfhvcZLmcfl_', 'webdriver'];
        docAutomation.forEach(prop => {{
            try {{
                if (prop in document) {{
                    delete document[prop];
                }}
            }} catch(e) {{}}
        }});
        
        // ==================== CHROME RUNTIME ====================
        
        // Create realistic window.chrome object
        if (!window.chrome) {{
            window.chrome = {{}};
        }}
        
        window.chrome.app = {{
            InstallState: {{ DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' }},
            RunningState: {{ CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running' }},
            getDetails: function() {{ return null; }},
            getIsInstalled: function() {{ return false; }},
            installState: function(callback) {{ callback && callback('not_installed'); }},
            isInstalled: false,
            runningState: function() {{ return 'cannot_run'; }}
        }};
        
        window.chrome.csi = function() {{
            return {{
                startE: Date.now(),
                onloadT: Date.now(),
                pageT: Math.random() * 1000 + 500,
                tran: 15
            }};
        }};
        
        window.chrome.loadTimes = function() {{
            return {{
                commitLoadTime: Date.now() / 1000,
                connectionInfo: 'h2',
                finishDocumentLoadTime: Date.now() / 1000 + Math.random(),
                finishLoadTime: Date.now() / 1000 + Math.random() * 2,
                firstPaintAfterLoadTime: 0,
                firstPaintTime: Date.now() / 1000 + Math.random() * 0.5,
                navigationType: 'Other',
                npnNegotiatedProtocol: 'h2',
                requestTime: Date.now() / 1000 - Math.random() * 2,
                startLoadTime: Date.now() / 1000 - Math.random(),
                wasAlternateProtocolAvailable: false,
                wasFetchedViaSpdy: true,
                wasNpnNegotiated: true
            }};
        }};
        
        window.chrome.runtime = {{
            OnInstalledReason: {{
                CHROME_UPDATE: 'chrome_update',
                INSTALL: 'install',
                SHARED_MODULE_UPDATE: 'shared_module_update',
                UPDATE: 'update'
            }},
            OnRestartRequiredReason: {{
                APP_UPDATE: 'app_update',
                OS_UPDATE: 'os_update',
                PERIODIC: 'periodic'
            }},
            PlatformArch: {{
                ARM: 'arm',
                ARM64: 'arm64',
                MIPS: 'mips',
                MIPS64: 'mips64',
                X86_32: 'x86-32',
                X86_64: 'x86-64'
            }},
            PlatformNaclArch: {{
                ARM: 'arm',
                MIPS: 'mips',
                MIPS64: 'mips64',
                X86_32: 'x86-32',
                X86_64: 'x86-64'
            }},
            PlatformOs: {{
                ANDROID: 'android',
                CROS: 'cros',
                LINUX: 'linux',
                MAC: 'mac',
                OPENBSD: 'openbsd',
                WIN: 'win'
            }},
            RequestUpdateCheckStatus: {{
                NO_UPDATE: 'no_update',
                THROTTLED: 'throttled',
                UPDATE_AVAILABLE: 'update_available'
            }},
            connect: function() {{ return {{ onDisconnect: {{ addListener: function() {{}} }}, onMessage: {{ addListener: function() {{}} }}, postMessage: function() {{}} }}; }},
            sendMessage: function() {{}},
            id: undefined
        }};
        
        // ==================== NAVIGATOR PROPERTIES ====================
        
        // Platform
        Object.defineProperty(navigator, 'platform', {{
            get: () => fp.platform,
            configurable: true
        }});
        
        // Languages
        Object.defineProperty(navigator, 'languages', {{
            get: () => Object.freeze([...fp.languages]),
            configurable: true
        }});
        
        Object.defineProperty(navigator, 'language', {{
            get: () => fp.languages[0],
            configurable: true
        }});
        
        // Device memory
        Object.defineProperty(navigator, 'deviceMemory', {{
            get: () => fp.deviceMemory,
            configurable: true
        }});
        
        // Hardware concurrency
        Object.defineProperty(navigator, 'hardwareConcurrency', {{
            get: () => fp.hardwareConcurrency,
            configurable: true
        }});
        
        // Do Not Track
        Object.defineProperty(navigator, 'doNotTrack', {{
            get: () => fp.doNotTrack,
            configurable: true
        }});
        
        // Max touch points
        Object.defineProperty(navigator, 'maxTouchPoints', {{
            get: () => fp.touchSupport.maxTouchPoints,
            configurable: true
        }});
        
        // ==================== PLUGINS ====================
        
        // Create realistic plugins array
        const createPlugin = (name, description, filename, mimeTypes) => {{
            const plugin = Object.create(Plugin.prototype);
            Object.defineProperties(plugin, {{
                name: {{ value: name, enumerable: true }},
                description: {{ value: description, enumerable: true }},
                filename: {{ value: filename, enumerable: true }},
                length: {{ value: mimeTypes.length, enumerable: true }}
            }});
            mimeTypes.forEach((mt, i) => {{
                const mimeType = Object.create(MimeType.prototype);
                Object.defineProperties(mimeType, {{
                    type: {{ value: mt.type, enumerable: true }},
                    suffixes: {{ value: mt.suffixes, enumerable: true }},
                    description: {{ value: mt.description, enumerable: true }},
                    enabledPlugin: {{ value: plugin, enumerable: true }}
                }});
                Object.defineProperty(plugin, i, {{ value: mimeType, enumerable: true }});
                Object.defineProperty(plugin, mt.type, {{ value: mimeType, enumerable: false }});
            }});
            return plugin;
        }};
        
        const plugins = [
            createPlugin('PDF Viewer', 'Portable Document Format', 'internal-pdf-viewer', [
                {{ type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format' }},
                {{ type: 'text/pdf', suffixes: 'pdf', description: 'Portable Document Format' }}
            ]),
            createPlugin('Chrome PDF Viewer', 'Portable Document Format', 'internal-pdf-viewer', [
                {{ type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format' }}
            ]),
            createPlugin('Chromium PDF Viewer', 'Portable Document Format', 'internal-pdf-viewer', [
                {{ type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format' }}
            ]),
            createPlugin('Microsoft Edge PDF Viewer', 'Portable Document Format', 'internal-pdf-viewer', [
                {{ type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format' }}
            ]),
            createPlugin('WebKit built-in PDF', 'Portable Document Format', 'internal-pdf-viewer', [
                {{ type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format' }}
            ])
        ];
        
        const pluginArray = Object.create(PluginArray.prototype);
        plugins.forEach((plugin, i) => {{
            Object.defineProperty(pluginArray, i, {{ value: plugin, enumerable: true }});
            Object.defineProperty(pluginArray, plugin.name, {{ value: plugin, enumerable: false }});
        }});
        Object.defineProperty(pluginArray, 'length', {{ value: plugins.length, enumerable: true }});
        pluginArray.item = function(index) {{ return this[index] || null; }};
        pluginArray.namedItem = function(name) {{ return this[name] || null; }};
        pluginArray.refresh = function() {{}};
        
        Object.defineProperty(navigator, 'plugins', {{
            get: () => pluginArray,
            configurable: true
        }});
        
        // ==================== PERMISSIONS API ====================
        
        const originalQuery = Permissions.prototype.query;
        Permissions.prototype.query = function(parameters) {{
            if (parameters.name === 'notifications') {{
                return Promise.resolve({{ state: Notification.permission, onchange: null }});
            }}
            // Return prompt for most permissions
            const permissionStates = {{
                'geolocation': 'prompt',
                'camera': 'prompt',
                'microphone': 'prompt',
                'background-sync': 'granted',
                'accessibility-events': 'prompt',
                'clipboard-read': 'prompt',
                'clipboard-write': 'granted',
                'payment-handler': 'prompt',
                'persistent-storage': 'prompt',
                'idle-detection': 'prompt',
                'midi': 'prompt'
            }};
            const state = permissionStates[parameters.name] || 'prompt';
            return Promise.resolve({{ state: state, onchange: null }});
        }};
        
        // ==================== WEBGL SPOOFING ====================
        
        const getParameterProxyHandler = {{
            apply: function(target, thisArg, args) {{
                const param = args[0];
                
                // UNMASKED_VENDOR_WEBGL
                if (param === 37445) {{
                    return fp.webglVendor;
                }}
                // UNMASKED_RENDERER_WEBGL
                if (param === 37446) {{
                    return fp.webglRenderer;
                }}
                
                return Reflect.apply(target, thisArg, args);
            }}
        }};
        
        // Patch WebGLRenderingContext
        try {{
            const getParameterOriginal = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = new Proxy(getParameterOriginal, getParameterProxyHandler);
        }} catch(e) {{}}
        
        // Patch WebGL2RenderingContext
        try {{
            const getParameter2Original = WebGL2RenderingContext.prototype.getParameter;
            WebGL2RenderingContext.prototype.getParameter = new Proxy(getParameter2Original, getParameterProxyHandler);
        }} catch(e) {{}}
        
        // ==================== CANVAS FINGERPRINT NOISE ====================
        
        const canvasSeed = fp.canvasSeed;
        
        // Add subtle noise to canvas toDataURL
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function(type, quality) {{
            const context = this.getContext('2d');
            if (context) {{
                const imageData = context.getImageData(0, 0, this.width, this.height);
                const data = imageData.data;
                // Add imperceptible noise based on seed
                for (let i = 0; i < data.length; i += 4) {{
                    const noise = ((canvasSeed * (i + 1)) % 3) - 1; // -1, 0, or 1
                    data[i] = Math.max(0, Math.min(255, data[i] + noise));
                }}
                context.putImageData(imageData, 0, 0);
            }}
            return originalToDataURL.call(this, type, quality);
        }};
        
        // Patch getImageData
        const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
        CanvasRenderingContext2D.prototype.getImageData = function(...args) {{
            const imageData = originalGetImageData.apply(this, args);
            const data = imageData.data;
            for (let i = 0; i < data.length; i += 4) {{
                const noise = ((canvasSeed * (i + 1)) % 3) - 1;
                data[i] = Math.max(0, Math.min(255, data[i] + noise));
            }}
            return imageData;
        }};
        
        // ==================== AUDIO CONTEXT FINGERPRINT ====================
        
        const audioSeed = fp.audioSeed;
        
        // Patch AudioContext
        const originalGetChannelData = AudioBuffer.prototype.getChannelData;
        AudioBuffer.prototype.getChannelData = function(channel) {{
            const array = originalGetChannelData.call(this, channel);
            // Add imperceptible noise
            for (let i = 0; i < array.length; i += 100) {{
                array[i] = array[i] + (audioSeed * 0.0000001);
            }}
            return array;
        }};
        
        const originalCopyFromChannel = AudioBuffer.prototype.copyFromChannel;
        AudioBuffer.prototype.copyFromChannel = function(destination, channelNumber, startInChannel) {{
            originalCopyFromChannel.call(this, destination, channelNumber, startInChannel || 0);
            for (let i = 0; i < destination.length; i += 100) {{
                destination[i] = destination[i] + (audioSeed * 0.0000001);
            }}
        }};
        
        // ==================== BATTERY API ====================
        
        if (navigator.getBattery) {{
            const mockBattery = {{
                charging: fp.battery.charging,
                chargingTime: fp.battery.chargingTime,
                dischargingTime: fp.battery.dischargingTime,
                level: fp.battery.level,
                addEventListener: function() {{}},
                removeEventListener: function() {{}},
                dispatchEvent: function() {{ return true; }},
                onchargingchange: null,
                onchargingtimechange: null,
                ondischargingtimechange: null,
                onlevelchange: null
            }};
            
            navigator.getBattery = function() {{
                return Promise.resolve(mockBattery);
            }};
        }}
        
        // ==================== NETWORK CONNECTION ====================
        
        if (navigator.connection) {{
            Object.defineProperties(navigator.connection, {{
                effectiveType: {{ get: () => fp.connection.effectiveType, configurable: true }},
                downlink: {{ get: () => fp.connection.downlink, configurable: true }},
                rtt: {{ get: () => fp.connection.rtt, configurable: true }},
                saveData: {{ get: () => fp.connection.saveData, configurable: true }}
            }});
        }}
        
        // ==================== SCREEN PROPERTIES ====================
        
        Object.defineProperties(screen, {{
            width: {{ get: () => fp.screen.width, configurable: true }},
            height: {{ get: () => fp.screen.height, configurable: true }},
            availWidth: {{ get: () => fp.screen.width, configurable: true }},
            availHeight: {{ get: () => fp.screen.height - 40, configurable: true }},
            colorDepth: {{ get: () => fp.colorDepth, configurable: true }},
            pixelDepth: {{ get: () => fp.colorDepth, configurable: true }}
        }});
        
        Object.defineProperty(window, 'devicePixelRatio', {{
            get: () => fp.pixelRatio,
            configurable: true
        }});
        
        Object.defineProperty(window, 'outerWidth', {{
            get: () => fp.screen.width,
            configurable: true
        }});
        
        Object.defineProperty(window, 'outerHeight', {{
            get: () => fp.screen.height,
            configurable: true
        }});
        
        // ==================== TIMING ATTACK PROTECTION ====================
        
        const originalNow = performance.now.bind(performance);
        const timeOffset = Math.random() * 0.001; // Sub-millisecond jitter
        
        performance.now = function() {{
            return originalNow() + timeOffset;
        }};
        
        // ==================== IFRAME CONSISTENCY ====================
        
        // Ensure iframes have consistent window properties
        const originalCreateElement = document.createElement.bind(document);
        document.createElement = function(tagName, options) {{
            const element = originalCreateElement(tagName, options);
            if (tagName.toLowerCase() === 'iframe') {{
                element.addEventListener('load', function() {{
                    try {{
                        if (element.contentWindow) {{
                            Object.defineProperty(element.contentWindow.navigator, 'webdriver', {{
                                get: () => undefined
                            }});
                        }}
                    }} catch(e) {{}}
                }});
            }}
            return element;
        }};
        
        // ==================== MEDIA DEVICES ====================
        
        // Spoof media devices enumeration
        if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {{
            const originalEnumerate = navigator.mediaDevices.enumerateDevices.bind(navigator.mediaDevices);
            navigator.mediaDevices.enumerateDevices = async function() {{
                const devices = await originalEnumerate();
                // Add some randomness to device IDs
                return devices.map((device, index) => ({{
                    deviceId: 'device_' + (canvasSeed + index).toString(16),
                    groupId: 'group_' + Math.floor(canvasSeed / (index + 1)).toString(16),
                    kind: device.kind,
                    label: ''  // Usually empty without permissions
                }}));
            }};
        }}
        
        // ==================== CDP DETECTION BYPASS ====================
        
        // Remove CDP-specific markers
        try {{
            Object.defineProperty(document, '$cdc_asdjflasutopfhvcZLmcfl_', {{
                get: () => undefined,
                set: () => true
            }});
        }} catch(e) {{}}
        
        // Prevent detection of Runtime.enable
        const originalError = Error;
        window.Error = function(...args) {{
            const error = new originalError(...args);
            const stack = error.stack;
            if (stack && stack.includes('Runtime.enable')) {{
                return new originalError('');
            }}
            return error;
        }};
        window.Error.prototype = originalError.prototype;
        
        // ==================== FONT DETECTION EVASION ====================
        
        // Limit font detection attempts
        const fontProbeHistory = new Set();
        const maxFontProbes = 500;
        
        const originalFontCheck = document.fonts && document.fonts.check ? 
            document.fonts.check.bind(document.fonts) : null;
        
        if (originalFontCheck) {{
            document.fonts.check = function(fontSpec, text) {{
                if (fontProbeHistory.size > maxFontProbes) {{
                    return false;
                }}
                fontProbeHistory.add(fontSpec);
                
                // Only return true for fonts in our list
                const fontName = fontSpec.split(' ').pop().replace(/['"]/g, '');
                if (fp.fonts.some(f => fontName.toLowerCase().includes(f.toLowerCase()))) {{
                    return originalFontCheck(fontSpec, text);
                }}
                return false;
            }};
        }}
        
        // ==================== CLEAN UP ====================
        
        // Prevent fingerprinting via toString
        const nativeToString = Function.prototype.toString;
        Function.prototype.toString = function() {{
            if (this === Function.prototype.toString) {{
                return 'function toString() {{ [native code] }}';
            }}
            if (this.name === 'getParameter' || this.name === 'toDataURL' || 
                this.name === 'getImageData' || this.name === 'query') {{
                return 'function ' + this.name + '() {{ [native code] }}';
            }}
            return nativeToString.call(this);
        }};
        
        console.log('%c[Stealth] Anti-detection patches applied', 'color: green');
    }})();
    '''


async def inject_stealth_scripts(page, fingerprint: Fingerprint, config: Optional[StealthConfig] = None) -> None:
    """
    Inject stealth scripts into page before content loads
    """
    stealth_script = generate_stealth_script(fingerprint, config)
    
    # Add script to run on every navigation
    await page.add_init_script(stealth_script)
