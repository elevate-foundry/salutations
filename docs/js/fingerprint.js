/**
 * Device Fingerprinting for Salutations GitHub Pages
 * Privacy-conscious visitor identification
 */

class DeviceFingerprint {
    constructor() {
        this.fingerprint = {};
        this.visitorId = null;
        this.sessionId = this.generateSessionId();
    }

    /**
     * Collect device fingerprint data
     */
    async collectFingerprint() {
        // Screen properties
        this.fingerprint.screen = {
            width: window.screen.width,
            height: window.screen.height,
            pixelRatio: window.devicePixelRatio || 1,
            colorDepth: window.screen.colorDepth,
            orientation: this.getOrientation()
        };

        // Browser properties
        this.fingerprint.browser = {
            userAgent: navigator.userAgent,
            language: navigator.language,
            languages: navigator.languages || [],
            platform: navigator.platform,
            vendor: navigator.vendor,
            cookieEnabled: navigator.cookieEnabled,
            doNotTrack: navigator.doNotTrack,
            hardwareConcurrency: navigator.hardwareConcurrency || 0,
            maxTouchPoints: navigator.maxTouchPoints || 0
        };

        // WebGL fingerprint
        this.fingerprint.webgl = this.getWebGLFingerprint();

        // Canvas fingerprint
        this.fingerprint.canvas = await this.getCanvasFingerprint();

        // Audio fingerprint
        this.fingerprint.audio = await this.getAudioFingerprint();

        // Timezone and locale
        this.fingerprint.timezone = {
            offset: new Date().getTimezoneOffset(),
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
        };

        // Fonts detection
        this.fingerprint.fonts = this.detectFonts();

        // Plugins (limited in modern browsers)
        this.fingerprint.plugins = this.getPlugins();

        // Storage capabilities
        this.fingerprint.storage = {
            localStorage: this.testStorage('localStorage'),
            sessionStorage: this.testStorage('sessionStorage'),
            indexedDB: !!window.indexedDB,
            webSQL: !!window.openDatabase
        };

        // Network information
        if (navigator.connection) {
            this.fingerprint.network = {
                effectiveType: navigator.connection.effectiveType,
                downlink: navigator.connection.downlink,
                rtt: navigator.connection.rtt,
                saveData: navigator.connection.saveData
            };
        }

        // Generate unique visitor ID
        this.visitorId = await this.generateVisitorId();

        return {
            visitorId: this.visitorId,
            sessionId: this.sessionId,
            fingerprint: this.fingerprint,
            timestamp: new Date().toISOString(),
            page: window.location.pathname
        };
    }

    /**
     * Get screen orientation
     */
    getOrientation() {
        if (window.screen.orientation) {
            return window.screen.orientation.type;
        }
        return window.innerWidth > window.innerHeight ? 'landscape' : 'portrait';
    }

    /**
     * WebGL fingerprinting
     */
    getWebGLFingerprint() {
        try {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            
            if (!gl) return null;

            const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
            
            return {
                vendor: gl.getParameter(gl.VENDOR),
                renderer: gl.getParameter(gl.RENDERER),
                unmaskedVendor: debugInfo ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) : null,
                unmaskedRenderer: debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : null,
                shadingLanguageVersion: gl.getParameter(gl.SHADING_LANGUAGE_VERSION),
                version: gl.getParameter(gl.VERSION)
            };
        } catch (e) {
            return null;
        }
    }

    /**
     * Canvas fingerprinting
     */
    async getCanvasFingerprint() {
        try {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            // Draw test text
            ctx.textBaseline = 'top';
            ctx.font = '14px "Arial"';
            ctx.textBaseline = 'alphabetic';
            ctx.fillStyle = '#f60';
            ctx.fillRect(125, 1, 62, 20);
            ctx.fillStyle = '#069';
            ctx.fillText('Salutations 🤖', 2, 15);
            ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
            ctx.fillText('Salutations 🤖', 4, 17);
            
            // Get canvas data
            const dataURL = canvas.toDataURL();
            
            // Hash the data
            return this.simpleHash(dataURL);
        } catch (e) {
            return null;
        }
    }

    /**
     * Audio fingerprinting
     */
    async getAudioFingerprint() {
        try {
            const audioContext = window.AudioContext || window.webkitAudioContext;
            if (!audioContext) return null;

            const context = new audioContext();
            const oscillator = context.createOscillator();
            const analyser = context.createAnalyser();
            const gain = context.createGain();
            const scriptProcessor = context.createScriptProcessor(4096, 1, 1);

            oscillator.type = 'triangle';
            oscillator.frequency.setValueAtTime(10000, context.currentTime);

            gain.gain.setValueAtTime(0, context.currentTime);

            oscillator.connect(analyser);
            analyser.connect(scriptProcessor);
            scriptProcessor.connect(gain);
            gain.connect(context.destination);

            return new Promise((resolve) => {
                let fingerprint = [];
                
                scriptProcessor.onaudioprocess = (event) => {
                    const output = event.inputBuffer.getChannelData(0);
                    fingerprint = Array.from(output.slice(0, 100));
                    
                    oscillator.disconnect();
                    analyser.disconnect();
                    scriptProcessor.disconnect();
                    gain.disconnect();
                    
                    resolve(this.simpleHash(fingerprint.join(',')));
                };

                oscillator.start(0);
                oscillator.stop(0.1);
            });
        } catch (e) {
            return null;
        }
    }

    /**
     * Detect installed fonts
     */
    detectFonts() {
        const baseFonts = ['monospace', 'sans-serif', 'serif'];
        const testFonts = [
            'Arial', 'Verdana', 'Times New Roman', 'Courier New',
            'Georgia', 'Palatino', 'Comic Sans MS', 'Impact',
            'Helvetica', 'Futura', 'Roboto', 'Ubuntu'
        ];

        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        const testString = 'mmmmmmmmmmlli';
        const textSize = '72px';

        const detectedFonts = [];

        baseFonts.forEach(baseFont => {
            testFonts.forEach(testFont => {
                ctx.font = `${textSize} ${testFont}, ${baseFont}`;
                const testWidth = ctx.measureText(testString).width;

                ctx.font = `${textSize} ${baseFont}`;
                const baseWidth = ctx.measureText(testString).width;

                if (testWidth !== baseWidth) {
                    detectedFonts.push(testFont);
                }
            });
        });

        return [...new Set(detectedFonts)];
    }

    /**
     * Get browser plugins
     */
    getPlugins() {
        if (!navigator.plugins) return [];
        
        const plugins = [];
        for (let i = 0; i < navigator.plugins.length; i++) {
            plugins.push({
                name: navigator.plugins[i].name,
                description: navigator.plugins[i].description,
                filename: navigator.plugins[i].filename
            });
        }
        return plugins;
    }

    /**
     * Test storage availability
     */
    testStorage(type) {
        try {
            const storage = window[type];
            const test = '__storage_test__';
            storage.setItem(test, test);
            storage.removeItem(test);
            return true;
        } catch (e) {
            return false;
        }
    }

    /**
     * Simple hash function
     */
    simpleHash(str) {
        let hash = 0;
        if (!str || str.length === 0) return hash;
        
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        
        return Math.abs(hash).toString(36);
    }

    /**
     * Generate unique visitor ID from fingerprint
     */
    async generateVisitorId() {
        const fingerprintString = JSON.stringify(this.fingerprint);
        const encoder = new TextEncoder();
        const data = encoder.encode(fingerprintString);
        const hashBuffer = await crypto.subtle.digest('SHA-256', data);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
        return hashHex.substring(0, 16);
    }

    /**
     * Generate session ID
     */
    generateSessionId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    /**
     * Save fingerprint to localStorage
     */
    saveFingerprint(data) {
        try {
            const stored = localStorage.getItem('salutations_visitors') || '[]';
            const visitors = JSON.parse(stored);
            visitors.push(data);
            
            // Keep only last 100 visits
            if (visitors.length > 100) {
                visitors.shift();
            }
            
            localStorage.setItem('salutations_visitors', JSON.stringify(visitors));
            localStorage.setItem('salutations_visitor_id', data.visitorId);
        } catch (e) {
            console.error('Could not save fingerprint:', e);
        }
    }

    /**
     * Send fingerprint to analytics endpoint
     */
    async sendAnalytics(data) {
        try {
            // For GitHub Pages, we'll store in localStorage
            // In production, this would send to an analytics server
            this.saveFingerprint(data);
            
            // Log to console for debugging
            console.log('🔍 Device Fingerprint Collected:', {
                visitorId: data.visitorId,
                sessionId: data.sessionId,
                timestamp: data.timestamp,
                page: data.page,
                browser: data.fingerprint.browser.userAgent.split(' ').pop(),
                screen: `${data.fingerprint.screen.width}x${data.fingerprint.screen.height}`,
                platform: data.fingerprint.browser.platform
            });
            
            // Display visitor info on page (optional)
            this.displayVisitorInfo(data);
        } catch (e) {
            console.error('Analytics error:', e);
        }
    }

    /**
     * Display visitor info on the page
     */
    displayVisitorInfo(data) {
        const existingInfo = document.getElementById('visitor-info');
        if (existingInfo) {
            existingInfo.remove();
        }

        const info = document.createElement('div');
        info.id = 'visitor-info';
        info.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(99, 102, 241, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 12px;
            padding: 15px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            color: #667eea;
            z-index: 9999;
            max-width: 300px;
            cursor: pointer;
            transition: all 0.3s ease;
        `;

        info.innerHTML = `
            <div style="font-weight: bold; margin-bottom: 8px;">🔍 Visitor Fingerprint</div>
            <div>ID: ${data.visitorId.substring(0, 8)}...</div>
            <div>Session: ${data.sessionId.substring(0, 8)}...</div>
            <div>Screen: ${data.fingerprint.screen.width}x${data.fingerprint.screen.height}</div>
            <div>Platform: ${data.fingerprint.browser.platform}</div>
            <div style="margin-top: 8px; font-size: 10px; opacity: 0.7;">Click to dismiss</div>
        `;

        info.onclick = () => info.remove();
        
        document.body.appendChild(info);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (info.parentNode) {
                info.style.opacity = '0';
                setTimeout(() => info.remove(), 300);
            }
        }, 10000);
    }

    /**
     * Initialize fingerprinting
     */
    async init() {
        try {
            const data = await this.collectFingerprint();
            await this.sendAnalytics(data);
            return data;
        } catch (e) {
            console.error('Fingerprint initialization error:', e);
            return null;
        }
    }
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.deviceFingerprint = new DeviceFingerprint();
        window.deviceFingerprint.init();
    });
} else {
    window.deviceFingerprint = new DeviceFingerprint();
    window.deviceFingerprint.init();
}

// Track page navigation
window.addEventListener('popstate', () => {
    if (window.deviceFingerprint) {
        window.deviceFingerprint.init();
    }
});
