"""
Real-time Git Fitness Dashboard
Shows live fitness score as you code!
"""

import asyncio
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

app = FastAPI(title="Git Fitness Dashboard", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active websocket connections
active_connections: List[WebSocket] = []

# Cache for fitness data
fitness_cache = {
    "score": 0.0,
    "components": {},
    "reasons": [],
    "suggestions": [],
    "timestamp": None,
    "changes_detected": False,
    "file_count": 0,
    "last_check": None
}

class GitChangeHandler(FileSystemEventHandler):
    """Watches for file changes and triggers fitness recalculation"""
    
    def __init__(self, loop=None):
        self.last_event_time = datetime.now()
        self.debounce_seconds = 2  # Wait 2 seconds after last change
        self.loop = loop or asyncio.get_event_loop()
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        # Ignore certain files/patterns
        ignored = ['.git', 'target', 'node_modules', '__pycache__', '.pyc', 'fitness.json']
        if any(ig in event.src_path for ig in ignored):
            return
        
        self.last_event_time = datetime.now()
        # Schedule the coroutine in the main event loop
        asyncio.run_coroutine_threadsafe(self.debounced_update(), self.loop)
    
    async def debounced_update(self):
        """Wait for changes to settle before updating"""
        await asyncio.sleep(self.debounce_seconds)
        
        # Check if this is still the latest event
        if (datetime.now() - self.last_event_time).total_seconds() >= self.debounce_seconds - 0.1:
            await update_fitness()

async def update_fitness():
    """Run the Rust fitness analyzer and update cache"""
    try:
        # Check if agit binary exists
        agit_path = Path("rust/target/release/agit")
        if not agit_path.exists():
            # Try to build it
            subprocess.run(["cargo", "build", "--release"], 
                         cwd="rust", capture_output=True, timeout=30)
        
        # Run fitness check
        result = subprocess.run(
            ["./rust/target/release/agit", "check"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            # Parse the output
            output = result.stdout
            fitness_data = parse_fitness_output(output)
            
            # Update cache
            fitness_cache.update(fitness_data)
            fitness_cache["timestamp"] = datetime.now().isoformat()
            fitness_cache["last_check"] = datetime.now().isoformat()
            
            # Broadcast to all connected clients
            await broadcast_update(fitness_cache)
            
            return fitness_cache
    except Exception as e:
        print(f"Error updating fitness: {e}")
        fitness_cache["error"] = str(e)
        await broadcast_update(fitness_cache)
    
    return fitness_cache

def parse_fitness_output(output: str) -> Dict:
    """Parse the agit check output into structured data"""
    data = {
        "score": 0.0,
        "components": {},
        "reasons": [],
        "suggestions": [],
        "changes_detected": False,
        "file_count": 0
    }
    
    lines = output.split('\n')
    
    for i, line in enumerate(lines):
        # Parse score
        if "Score:" in line:
            try:
                score_str = line.split("Score:")[1].split("/")[0].strip()
                data["score"] = float(score_str)
                data["changes_detected"] = True
            except:
                pass
        
        # Parse components
        elif "File metrics:" in line:
            try:
                val = float(line.split(":")[1].strip())
                data["components"]["file_metrics"] = val
            except:
                pass
        elif "Code complexity:" in line:
            try:
                val = float(line.split(":")[1].strip())
                data["components"]["complexity"] = val
            except:
                pass
        elif "Coherence:" in line and "•" in line:
            try:
                val = float(line.split(":")[1].strip())
                data["components"]["coherence"] = val
            except:
                pass
        elif "Tests:" in line and "•" in line:
            try:
                val = float(line.split(":")[1].strip())
                data["components"]["tests"] = val
            except:
                pass
        elif "Risk:" in line and "•" in line:
            try:
                val = float(line.split(":")[1].strip())
                data["components"]["risk"] = val
            except:
                pass
        elif "Documentation:" in line and "•" in line:
            try:
                val = float(line.split(":")[1].strip())
                data["components"]["documentation"] = val
            except:
                pass
        
        # Parse reasons
        elif "Analysis:" in line:
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith("•"):
                reason = lines[j].strip()[1:].strip()
                data["reasons"].append(reason)
                j += 1
        
        # Parse suggestions
        elif "💡" in line:
            suggestion = line.split("💡")[1].strip()
            data["suggestions"].append(suggestion)
        
        # Count files
        elif "No changes detected" in line:
            data["changes_detected"] = False
    
    return data

async def broadcast_update(data: Dict):
    """Send update to all connected WebSocket clients"""
    disconnected = []
    
    for connection in active_connections:
        try:
            await connection.send_json(data)
        except:
            disconnected.append(connection)
    
    # Remove disconnected clients
    for conn in disconnected:
        if conn in active_connections:
            active_connections.remove(conn)

@app.on_event("startup")
async def startup_event():
    """Start file watcher on app startup"""
    # Initial fitness check
    await update_fitness()
    
    # Start file watcher with current event loop
    loop = asyncio.get_running_loop()
    event_handler = GitChangeHandler(loop)
    observer = Observer()
    observer.schedule(event_handler, ".", recursive=True)
    observer.start()
    
    # Schedule periodic updates (every 30 seconds)
    asyncio.create_task(periodic_update())

async def periodic_update():
    """Periodically update fitness even without file changes"""
    while True:
        await asyncio.sleep(30)
        await update_fitness()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    active_connections.append(websocket)
    
    # Send current fitness data immediately
    await websocket.send_json(fitness_cache)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

@app.get("/")
async def dashboard():
    """Serve the fitness dashboard"""
    return HTMLResponse(content=dashboard_html)

@app.get("/api/fitness")
async def get_fitness():
    """Get current fitness data via REST API"""
    return fitness_cache

@app.post("/api/refresh")
async def refresh_fitness():
    """Manually trigger a fitness update"""
    return await update_fitness()

# Beautiful dashboard HTML
dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Git Fitness Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .dashboard {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 800px;
            width: 100%;
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 2.5rem;
            text-align: center;
        }
        
        .subtitle {
            color: #666;
            text-align: center;
            margin-bottom: 30px;
            font-size: 1.1rem;
        }
        
        .fitness-score {
            text-align: center;
            margin: 30px 0;
        }
        
        .score-circle {
            width: 200px;
            height: 200px;
            margin: 0 auto;
            position: relative;
        }
        
        .score-value {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 3rem;
            font-weight: bold;
            color: #333;
        }
        
        .score-label {
            position: absolute;
            bottom: 35%;
            left: 50%;
            transform: translateX(-50%);
            font-size: 0.9rem;
            color: #666;
        }
        
        svg {
            transform: rotate(-90deg);
        }
        
        .progress-ring {
            transition: stroke-dashoffset 0.5s ease;
        }
        
        .components {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        
        .component {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            border-left: 4px solid #667eea;
        }
        
        .component-name {
            font-weight: 600;
            color: #333;
            margin-bottom: 5px;
        }
        
        .component-value {
            font-size: 1.5rem;
            color: #667eea;
        }
        
        .component-bar {
            height: 6px;
            background: #e0e0e0;
            border-radius: 3px;
            margin-top: 8px;
            overflow: hidden;
        }
        
        .component-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 3px;
            transition: width 0.5s ease;
        }
        
        .status {
            text-align: center;
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
            font-weight: 600;
        }
        
        .status.ready {
            background: #d4edda;
            color: #155724;
        }
        
        .status.waiting {
            background: #fff3cd;
            color: #856404;
        }
        
        .status.error {
            background: #f8d7da;
            color: #721c24;
        }
        
        .suggestions {
            background: #f0f8ff;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
        }
        
        .suggestions h3 {
            color: #333;
            margin-bottom: 10px;
        }
        
        .suggestion-item {
            padding: 8px 0;
            color: #666;
        }
        
        .suggestion-item:before {
            content: "💡 ";
            margin-right: 5px;
        }
        
        .live-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            background: #10b981;
            border-radius: 50%;
            animation: pulse 2s infinite;
            margin-left: 10px;
        }
        
        @keyframes pulse {
            0% {
                box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
            }
            70% {
                box-shadow: 0 0 0 10px rgba(16, 185, 129, 0);
            }
            100% {
                box-shadow: 0 0 0 0 rgba(16, 185, 129, 0);
            }
        }
        
        .timestamp {
            text-align: center;
            color: #999;
            font-size: 0.9rem;
            margin-top: 20px;
        }
        
        .braille-display {
            text-align: center;
            font-size: 2rem;
            margin: 20px 0;
            font-family: monospace;
            color: #667eea;
        }
    </style>
</head>
<body>
    <div class="dashboard">
        <h1>Git Fitness Dashboard <span class="live-indicator"></span></h1>
        <p class="subtitle">Real-time commit fitness tracking</p>
        
        <div class="fitness-score">
            <div class="score-circle">
                <svg width="200" height="200">
                    <circle
                        cx="100"
                        cy="100"
                        r="90"
                        stroke="#e0e0e0"
                        stroke-width="20"
                        fill="none"
                    />
                    <circle
                        class="progress-ring"
                        cx="100"
                        cy="100"
                        r="90"
                        stroke="url(#gradient)"
                        stroke-width="20"
                        fill="none"
                        stroke-dasharray="565.48"
                        stroke-dashoffset="565.48"
                    />
                    <defs>
                        <linearGradient id="gradient">
                            <stop offset="0%" stop-color="#667eea" />
                            <stop offset="100%" stop-color="#764ba2" />
                        </linearGradient>
                    </defs>
                </svg>
                <div class="score-value" id="score">0.00</div>
                <div class="score-label">FITNESS</div>
            </div>
        </div>
        
        <div class="braille-display" id="braille">⠀</div>
        
        <div class="status waiting" id="status">
            Waiting for changes...
        </div>
        
        <div class="components" id="components">
            <!-- Components will be inserted here -->
        </div>
        
        <div class="suggestions" id="suggestions-container" style="display: none;">
            <h3>Suggestions</h3>
            <div id="suggestions">
                <!-- Suggestions will be inserted here -->
            </div>
        </div>
        
        <div class="timestamp" id="timestamp">
            Last update: Never
        </div>
    </div>
    
    <script>
        let ws = null;
        
        function connectWebSocket() {
            ws = new WebSocket('ws://localhost:5001/ws');
            
            ws.onopen = () => {
                console.log('Connected to fitness dashboard');
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                updateDashboard(data);
            };
            
            ws.onclose = () => {
                console.log('Disconnected, reconnecting...');
                setTimeout(connectWebSocket, 3000);
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        }
        
        function updateDashboard(data) {
            // Update score
            const score = data.score || 0;
            document.getElementById('score').textContent = score.toFixed(2);
            
            // Update progress ring
            const ring = document.querySelector('.progress-ring');
            const radius = 90;
            const circumference = 2 * Math.PI * radius;
            const offset = circumference - (score * circumference);
            ring.style.strokeDashoffset = offset;
            
            // Generate Braille based on fitness
            const braille = generateBraille(score);
            document.getElementById('braille').textContent = braille;
            
            // Update status
            const statusEl = document.getElementById('status');
            if (data.error) {
                statusEl.className = 'status error';
                statusEl.textContent = `Error: ${data.error}`;
            } else if (!data.changes_detected) {
                statusEl.className = 'status waiting';
                statusEl.textContent = 'No changes detected - keep coding!';
            } else if (score >= 0.7) {
                statusEl.className = 'status ready';
                statusEl.textContent = '✅ Ready to commit!';
            } else {
                statusEl.className = 'status waiting';
                statusEl.textContent = '⏳ Keep improving...';
            }
            
            // Update components
            const componentsEl = document.getElementById('components');
            componentsEl.innerHTML = '';
            
            const componentNames = {
                'file_metrics': 'File Metrics',
                'complexity': 'Code Complexity',
                'coherence': 'Coherence',
                'tests': 'Test Coverage',
                'risk': 'Risk Assessment',
                'documentation': 'Documentation'
            };
            
            for (const [key, value] of Object.entries(data.components || {})) {
                const component = document.createElement('div');
                component.className = 'component';
                component.innerHTML = `
                    <div class="component-name">${componentNames[key] || key}</div>
                    <div class="component-value">${(value * 100).toFixed(0)}%</div>
                    <div class="component-bar">
                        <div class="component-fill" style="width: ${value * 100}%"></div>
                    </div>
                `;
                componentsEl.appendChild(component);
            }
            
            // Update suggestions
            const suggestionsContainer = document.getElementById('suggestions-container');
            const suggestionsEl = document.getElementById('suggestions');
            
            if (data.suggestions && data.suggestions.length > 0) {
                suggestionsContainer.style.display = 'block';
                suggestionsEl.innerHTML = data.suggestions
                    .map(s => `<div class="suggestion-item">${s}</div>`)
                    .join('');
            } else {
                suggestionsContainer.style.display = 'none';
            }
            
            // Update timestamp
            if (data.timestamp) {
                const time = new Date(data.timestamp);
                document.getElementById('timestamp').textContent = 
                    `Last update: ${time.toLocaleTimeString()}`;
            }
        }
        
        function generateBraille(score) {
            // Generate dynamic Braille based on fitness
            const brailleChars = ['⠀', '⠁', '⠃', '⠇', '⠏', '⠟', '⠿', '⣿'];
            const index = Math.floor(score * (brailleChars.length - 1));
            
            // Add BIFM topology character for high scores
            if (score > 0.8) {
                return `⠑⠝⠓.⣯`;  // enhance + high fitness
            } else if (score > 0.6) {
                return `⠥⠏⠙.⢑`;  // update + medium fitness
            } else if (score > 0.4) {
                return `⠋⠊⠭.⠑`;  // fix + low fitness
            } else {
                return brailleChars[index];
            }
        }
        
        // Connect on load
        connectWebSocket();
        
        // Refresh on click
        document.querySelector('.score-circle').addEventListener('click', () => {
            fetch('/api/refresh', { method: 'POST' })
                .then(response => response.json())
                .then(data => updateDashboard(data));
        });
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001, reload=True)
