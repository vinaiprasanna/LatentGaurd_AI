#!/usr/bin/env node
const { spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const PROJECT_ROOT = path.join(__dirname, '..');

function runCommand(command, args, cwd = PROJECT_ROOT) {
  console.log(`Running: ${command} ${args.join(' ')}`);
  const result = spawnSync(command, args, { cwd, stdio: 'inherit', shell: true });
  if (result.status !== 0) {
    console.error(`Command failed: ${command} ${args.join(' ')}`);
    process.exit(result.status || 1);
  }
}

console.log('=== LatentGuard AI - Dependency Installer ===\n');

// [1/4] Install frontend dependencies
const frontendNodeModules = path.join(PROJECT_ROOT, 'frontend', 'node_modules');
if (fs.existsSync(frontendNodeModules)) {
  console.log('[1/4] Frontend dependencies already installed. Skipping.\n');
} else {
  console.log('[1/4] Installing frontend dependencies...\n');
  runCommand('npm', ['install', '--prefer-offline', '--no-audit'], path.join(PROJECT_ROOT, 'frontend'));
  console.log('');
}

// [2/4] Create virtual environment
const venvPath = path.join(PROJECT_ROOT, '.venv');
if (fs.existsSync(venvPath)) {
  console.log('[2/4] Virtual environment already exists. Skipping.\n');
} else {
  console.log('[2/4] Creating Python virtual environment...\n');
  runCommand('python3', ['-m', 'venv', '.venv']);
  console.log('');
}

// Determine python/pip path based on platform (use absolute paths)
const isWindows = process.platform === 'win32';
const venvBin = isWindows ? path.join(PROJECT_ROOT, '.venv', 'Scripts') : path.join(PROJECT_ROOT, '.venv', 'bin');
const pythonExe = path.join(venvBin, isWindows ? 'python.exe' : 'python');
const pipExe = path.join(venvBin, isWindows ? 'pip.exe' : 'pip');

// [3/4] Install backend dependencies
const backendEnvInstalled = path.join(PROJECT_ROOT, 'backend', 'env_installed.txt');
if (fs.existsSync(backendEnvInstalled)) {
  console.log('[3/4] Backend dependencies already installed. Skipping.\n');
} else {
  console.log('[3/4] Installing backend dependencies...\n');
  runCommand(pipExe, ['install', '-r', 'requirements.txt'], path.join(PROJECT_ROOT, 'backend'));
  fs.writeFileSync(backendEnvInstalled, 'ready');
  console.log('');
}

// [4/4] Install model training dependencies
const modelTrainingEnvInstalled = path.join(PROJECT_ROOT, 'model-training', 'env_installed.txt');
if (fs.existsSync(modelTrainingEnvInstalled)) {
  console.log('[4/4] Model training dependencies already installed. Skipping.\n');
} else {
  console.log('[4/4] Installing model training dependencies...\n');
  runCommand(pipExe, ['install', '-r', 'requirements.txt'], path.join(PROJECT_ROOT, 'model-training'));
  fs.writeFileSync(modelTrainingEnvInstalled, 'ready');
  console.log('');
}

console.log('All dependencies installed successfully.');