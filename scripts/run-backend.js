#!/usr/bin/env node
const { spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const PROJECT_ROOT = path.join(__dirname, '..');

function runCommand(command, args, cwd = PROJECT_ROOT) {
  const result = spawnSync(command, args, { cwd, stdio: 'inherit', shell: true });
  if (result.status !== 0) {
    process.exit(result.status || 1);
  }
}

// Check virtual environment
const venvPath = path.join(PROJECT_ROOT, '.venv');
if (!fs.existsSync(venvPath)) {
  console.error('Error: Virtual environment not found. Run "npm run install:all" first.');
  process.exit(1);
}

const isWindows = process.platform === 'win32';
const venvBin = isWindows ? path.join(PROJECT_ROOT, '.venv', 'Scripts') : path.join(PROJECT_ROOT, '.venv', 'bin');
const pythonExe = path.join(venvBin, isWindows ? 'python.exe' : 'python');

console.log('Starting LatentGuard AI backend on port 8000...');
runCommand(pythonExe, ['-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '8000', '--reload'], path.join(PROJECT_ROOT, 'backend'));