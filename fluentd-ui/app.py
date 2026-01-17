#!/usr/bin/env python3
import os

import requests
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Fluentd Log Viewer</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: 'Courier New', monospace;
            margin: 0;
            padding: 20px;
            background: #1e1e1e;
            color: #d4d4d4;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        h1 {
            color: #4ec9b0;
            border-bottom: 2px solid #4ec9b0;
            padding-bottom: 10px;
        }
        .controls {
            margin: 20px 0;
            padding: 15px;
            background: #252526;
            border-radius: 5px;
        }
        button {
            background: #007acc;
            color: white;
            border: none;
            padding: 10px 20px;
            margin: 5px;
            border-radius: 3px;
            cursor: pointer;
        }
        button:hover {
            background: #005a9e;
        }
        .log-container {
            background: #252526;
            border: 1px solid #3e3e42;
            border-radius: 5px;
            padding: 15px;
            max-height: 600px;
            overflow-y: auto;
        }
        .log-entry {
            padding: 5px;
            margin: 2px 0;
            border-left: 3px solid #007acc;
            padding-left: 10px;
            word-wrap: break-word;
        }
        .log-entry.error {
            border-left-color: #f48771;
        }
        .log-entry.warn {
            border-left-color: #dcdcaa;
        }
        .log-entry.info {
            border-left-color: #4ec9b0;
        }
        .timestamp {
            color: #808080;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Fluentd Log Viewer</h1>
        <div class="controls">
            <button onclick="refreshLogs()">Refresh Logs</button>
            <button onclick="clearLogs()">Clear</button>
            <button onclick="toggleAutoRefresh()">Auto Refresh: <span id="autoRefreshStatus">Off</span></button>
            <span style="margin-left: 20px;">Fluentd Status: <span id="fluentdStatus">Checking...</span></span>
        </div>
        <div class="log-container" id="logContainer">
            <div class="log-entry">Waiting for logs...</div>
        </div>
    </div>

    <script>
        let autoRefresh = false;
        let refreshInterval = null;

        function getLogLevelClass(level) {
            if (level.includes('error') || level.includes('ERROR')) return 'error';
            if (level.includes('warn') || level.includes('WARN')) return 'warn';
            if (level.includes('info') || level.includes('INFO')) return 'info';
            return '';
        }

        function formatLogEntry(log) {
            const level = log.level || 'info';
            const time = log.time || new Date().toISOString();
            const message = log.message || JSON.stringify(log);
            return `
                <div class="log-entry ${getLogLevelClass(level)}">
                    <span class="timestamp">[${time}]</span>
                    <strong>[${level.toUpperCase()}]</strong>
                    ${message}
                </div>
            `;
        }

        async function refreshLogs() {
            try {
                const response = await fetch('/api/logs');
                const data = await response.json();
                const container = document.getElementById('logContainer');
                
                if (data.logs && data.logs.length > 0) {
                    container.innerHTML = data.logs.map(formatLogEntry).join('');
                    container.scrollTop = container.scrollHeight;
                } else {
                    container.innerHTML = '<div class="log-entry">No logs available</div>';
                }
                
                document.getElementById('fluentdStatus').textContent = data.fluentd_status || 'Unknown';
            } catch (error) {
                document.getElementById('logContainer').innerHTML = 
                    `<div class="log-entry error">Error fetching logs: ${error.message}</div>`;
            }
        }

        function clearLogs() {
            document.getElementById('logContainer').innerHTML = '<div class="log-entry">Logs cleared</div>';
        }

        function toggleAutoRefresh() {
            autoRefresh = !autoRefresh;
            document.getElementById('autoRefreshStatus').textContent = autoRefresh ? 'On (5s)' : 'Off';
            
            if (autoRefresh) {
                refreshInterval = setInterval(refreshLogs, 5000);
            } else {
                if (refreshInterval) {
                    clearInterval(refreshInterval);
                    refreshInterval = null;
                }
            }
        }

        refreshLogs();
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/logs')
def get_logs():
    try:
        fluentd_host = os.getenv('FLUENTD_HOST', 'fluentd')
        response = requests.get(f'http://{fluentd_host}:9880/logs', timeout=2)
        if response.status_code == 200:
            return jsonify({
                'logs': response.json() if response.headers.get('content-type') == 'application/json' else [],
                'fluentd_status': 'Connected'
            })
    except Exception as e:
        pass

    try:
        import subprocess
        result = subprocess.run(
            ['docker', 'logs', '--tail', '50', 'api-scheduler-fluentd'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            logs = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    try:
                        import json
                        log_entry = json.loads(line)
                        logs.append(log_entry)
                    except:
                        logs.append(
                            {'level': 'info', 'time': '', 'message': line})

            return jsonify({
                'logs': logs[-50:],
                'fluentd_status': 'Connected (via Docker)'
            })
    except Exception as e:
        pass

    return jsonify({
        'logs': [{'level': 'warn', 'time': '', 'message': 'Unable to fetch logs from Fluentd'}],
        'fluentd_status': 'Disconnected'
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
