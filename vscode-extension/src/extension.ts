import * as vscode from 'vscode';
import * as child_process from 'child_process';
import * as path from 'path';
import neo4j from 'neo4j-driver';

let agentProcess: child_process.ChildProcess | null = null;
let statusBarItem: vscode.StatusBarItem;
let fitnessStatusBarItem: vscode.StatusBarItem;
let neo4jDriver: any = null;

export function activate(context: vscode.ExtensionContext) {
    console.log('Autonomous Git extension activated');

    // Create status bar items
    statusBarItem = vscode.window.createStatusBarItem(
        vscode.StatusBarAlignment.Left,
        100
    );
    statusBarItem.text = '$(robot) Autonomous Git: Inactive';
    statusBarItem.command = 'autonomousGit.start';
    statusBarItem.show();

    fitnessStatusBarItem = vscode.window.createStatusBarItem(
        vscode.StatusBarAlignment.Left,
        99
    );
    fitnessStatusBarItem.text = '$(pulse) Fitness: --';
    fitnessStatusBarItem.command = 'autonomousGit.checkFitness';

    context.subscriptions.push(statusBarItem, fitnessStatusBarItem);

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('autonomousGit.start', startAgent),
        vscode.commands.registerCommand('autonomousGit.stop', stopAgent),
        vscode.commands.registerCommand('autonomousGit.checkFitness', checkFitness),
        vscode.commands.registerCommand('autonomousGit.viewGraph', viewGraph),
        vscode.commands.registerCommand('autonomousGit.enableSCL', enableSCL)
    );

    // Initialize Neo4j connection
    initNeo4j();

    // Auto-start if enabled
    const config = vscode.workspace.getConfiguration('autonomousGit');
    if (config.get('enabled')) {
        startAgent();
    }
}

function initNeo4j() {
    const config = vscode.workspace.getConfiguration('autonomousGit');
    const uri = config.get<string>('neo4jUri') || 'bolt://localhost:7687';
    const user = config.get<string>('neo4jUser') || 'neo4j';
    const password = config.get<string>('neo4jPassword') || '';

    if (password) {
        try {
            neo4jDriver = neo4j.driver(uri, neo4j.auth.basic(user, password));
            console.log('Connected to Neo4j');
        } catch (error) {
            console.error('Failed to connect to Neo4j:', error);
        }
    }
}

async function startAgent() {
    if (agentProcess) {
        vscode.window.showWarningMessage('Agent is already running');
        return;
    }

    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        vscode.window.showErrorMessage('No workspace folder open');
        return;
    }

    const config = vscode.workspace.getConfiguration('autonomousGit');
    const threshold = config.get<number>('threshold') || 0.7;
    const interval = config.get<number>('interval') || 300;
    const autoPush = config.get<boolean>('autoPush') || false;
    const sclEnabled = config.get<boolean>('sclEnabled') || true;
    const language = config.get<string>('language') || 'en';

    // Find agit binary
    const agitPath = findAgitBinary();
    if (!agitPath) {
        vscode.window.showErrorMessage('agit binary not found. Please build the Rust project first.');
        return;
    }

    // Build command
    const args = [
        '--repo', workspaceFolder.uri.fsPath,
        '--threshold', threshold.toString(),
        '--interval', interval.toString(),
    ];

    if (autoPush) {
        args.push('--push');
    }

    if (sclEnabled) {
        args.push('--scl');
        args.push('--lang', language);
    }

    args.push('run');

    // Start agent
    agentProcess = child_process.spawn(agitPath, args, {
        cwd: workspaceFolder.uri.fsPath,
    });

    agentProcess.stdout?.on('data', (data) => {
        const output = data.toString();
        console.log('[Autonomous Git]', output);
        
        // Parse fitness from output
        const fitnessMatch = output.match(/Fitness: ([\d.]+)/);
        if (fitnessMatch) {
            const fitness = parseFloat(fitnessMatch[1]);
            updateFitnessDisplay(fitness);
        }

        // Parse SCL commit
        const sclMatch = output.match(/🔤 (⠀-⣿+)/);
        if (sclMatch) {
            const scl = sclMatch[1];
            vscode.window.showInformationMessage(`Committed: ${scl}`);
            
            // Store in Neo4j if connected
            if (neo4jDriver) {
                storeCommitInGraph(scl, output);
            }
        }
    });

    agentProcess.stderr?.on('data', (data) => {
        console.error('[Autonomous Git Error]', data.toString());
    });

    agentProcess.on('close', (code) => {
        console.log(`Agent exited with code ${code}`);
        agentProcess = null;
        statusBarItem.text = '$(robot) Autonomous Git: Inactive';
        statusBarItem.command = 'autonomousGit.start';
        fitnessStatusBarItem.hide();
    });

    statusBarItem.text = '$(robot) Autonomous Git: Active';
    statusBarItem.command = 'autonomousGit.stop';
    fitnessStatusBarItem.show();

    vscode.window.showInformationMessage('Autonomous Git agent started');
}

function stopAgent() {
    if (!agentProcess) {
        vscode.window.showWarningMessage('Agent is not running');
        return;
    }

    agentProcess.kill();
    agentProcess = null;
    statusBarItem.text = '$(robot) Autonomous Git: Inactive';
    statusBarItem.command = 'autonomousGit.start';
    fitnessStatusBarItem.hide();

    vscode.window.showInformationMessage('Autonomous Git agent stopped');
}

async function checkFitness() {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        vscode.window.showErrorMessage('No workspace folder open');
        return;
    }

    const agitPath = findAgitBinary();
    if (!agitPath) {
        vscode.window.showErrorMessage('agit binary not found');
        return;
    }

    // Run fitness check
    child_process.exec(
        `${agitPath} --repo ${workspaceFolder.uri.fsPath} check`,
        (error, stdout, stderr) => {
            if (error) {
                vscode.window.showErrorMessage(`Error: ${stderr}`);
                return;
            }

            // Parse fitness
            const fitnessMatch = stdout.match(/Fitness: ([\d.]+)/);
            if (fitnessMatch) {
                const fitness = parseFloat(fitnessMatch[1]);
                updateFitnessDisplay(fitness);
                
                // Show detailed breakdown
                vscode.window.showInformationMessage(
                    `Current Fitness: ${fitness.toFixed(2)}`,
                    'View Details'
                ).then(selection => {
                    if (selection === 'View Details') {
                        const panel = vscode.window.createWebviewPanel(
                            'fitnessDetails',
                            'Fitness Details',
                            vscode.ViewColumn.One,
                            {}
                        );
                        panel.webview.html = getFitnessDetailsHtml(stdout);
                    }
                });
            }
        }
    );
}

async function viewGraph() {
    if (!neo4jDriver) {
        vscode.window.showErrorMessage('Neo4j not connected');
        return;
    }

    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        return;
    }

    const repoName = path.basename(workspaceFolder.uri.fsPath);

    // Query fitness evolution
    const session = neo4jDriver.session();
    try {
        const result = await session.run(
            `MATCH (r:Repo {name: $repo})-[:CONTAINS]->(c:Commit)
             MATCH (c)-[:HAS_FITNESS]->(f:FitnessTopology)
             RETURN c.timestamp as timestamp,
                    c.scl as scl,
                    f.braille as braille,
                    f.kappa as kappa,
                    f.sigma as sigma,
                    f.delta as delta
             ORDER BY c.timestamp DESC
             LIMIT 50`,
            { repo: repoName }
        );

        const commits = result.records.map(record => ({
            timestamp: record.get('timestamp'),
            scl: record.get('scl'),
            braille: record.get('braille'),
            kappa: record.get('kappa'),
            sigma: record.get('sigma'),
            delta: record.get('delta'),
        }));

        // Show in webview
        const panel = vscode.window.createWebviewPanel(
            'bifmGraph',
            'BIFM Graph',
            vscode.ViewColumn.One,
            { enableScripts: true }
        );
        panel.webview.html = getGraphHtml(commits);

    } finally {
        await session.close();
    }
}

async function enableSCL() {
    const config = vscode.workspace.getConfiguration('autonomousGit');
    await config.update('sclEnabled', true, vscode.ConfigurationTarget.Workspace);
    vscode.window.showInformationMessage('SCL mode enabled');
}

function updateFitnessDisplay(fitness: number) {
    const icon = fitness >= 0.8 ? '$(check)' : fitness >= 0.6 ? '$(warning)' : '$(error)';
    const color = fitness >= 0.8 ? '#4ade80' : fitness >= 0.6 ? '#fbbf24' : '#f87171';
    
    fitnessStatusBarItem.text = `${icon} Fitness: ${fitness.toFixed(2)}`;
    fitnessStatusBarItem.tooltip = `Current fitness score: ${fitness.toFixed(2)}`;
    fitnessStatusBarItem.color = color;
}

async function storeCommitInGraph(scl: string, output: string) {
    if (!neo4jDriver) {
        return;
    }

    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        return;
    }

    const repoName = path.basename(workspaceFolder.uri.fsPath);

    // Parse fitness topology from output
    const kappaMatch = output.match(/κ=(\d+)/);
    const sigmaMatch = output.match(/σ=(\d+)/);
    const deltaMatch = output.match(/δ=(\d+)/);
    const brailleMatch = output.match(/🔤 ([⠀-⣿]+)/);

    if (!kappaMatch || !sigmaMatch || !deltaMatch || !brailleMatch) {
        return;
    }

    const kappa = parseInt(kappaMatch[1]);
    const sigma = parseInt(sigmaMatch[1]);
    const delta = parseInt(deltaMatch[1]);
    const braille = brailleMatch[1];

    const session = neo4jDriver.session();
    try {
        await session.run(
            `MERGE (f:FitnessTopology {braille: $braille})
             ON CREATE SET f.kappa = $kappa, f.sigma = $sigma, f.delta = $delta
             CREATE (c:Commit {scl: $scl, timestamp: datetime(), repo: $repo})
             CREATE (c)-[:HAS_FITNESS]->(f)
             MERGE (r:Repo {name: $repo})
             CREATE (r)-[:CONTAINS]->(c)`,
            { braille, kappa, sigma, delta, scl, repo: repoName }
        );
    } finally {
        await session.close();
    }
}

function findAgitBinary(): string | null {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        return null;
    }

    // Try local build first
    const localPath = path.join(workspaceFolder.uri.fsPath, 'rust/target/release/agit');
    if (require('fs').existsSync(localPath)) {
        return localPath;
    }

    // Try system PATH
    try {
        child_process.execSync('which agit');
        return 'agit';
    } catch {
        return null;
    }
}

function getFitnessDetailsHtml(output: string): string {
    return `
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px; }
                pre { background: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 5px; }
                .braille { font-size: 2em; color: #00d9ff; }
            </style>
        </head>
        <body>
            <h1>Fitness Details</h1>
            <pre>${output}</pre>
        </body>
        </html>
    `;
}

function getGraphHtml(commits: any[]): string {
    return `
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px; }
                .commit { background: #1e1e1e; padding: 15px; margin: 10px 0; border-radius: 5px; }
                .braille { font-size: 1.5em; color: #00d9ff; }
                .fitness { color: #8b5cf6; }
            </style>
        </head>
        <body>
            <h1>BIFM-64 Graph</h1>
            ${commits.map(c => `
                <div class="commit">
                    <div class="braille">${c.braille}</div>
                    <div>${c.scl}</div>
                    <div class="fitness">κ=${c.kappa} σ=${c.sigma} δ=${c.delta}</div>
                    <div style="color: #888; font-size: 0.9em;">${c.timestamp}</div>
                </div>
            `).join('')}
        </body>
        </html>
    `;
}

export function deactivate() {
    if (agentProcess) {
        agentProcess.kill();
    }
    if (neo4jDriver) {
        neo4jDriver.close();
    }
}
