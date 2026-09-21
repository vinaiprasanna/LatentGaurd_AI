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

// Check virtual environment
const venvPath = path.join(PROJECT_ROOT, '.venv');
if (!fs.existsSync(venvPath)) {
  console.error('Error: Virtual environment not found. Run "npm run install:all" first.');
  process.exit(1);
}

// Check model training dependencies
const modelTrainingEnvInstalled = path.join(PROJECT_ROOT, 'model-training', 'env_installed.txt');
if (!fs.existsSync(modelTrainingEnvInstalled)) {
  console.error('Error: Model dependencies not installed. Run "npm run install:all" first.');
  process.exit(1);
}

const isWindows = process.platform === 'win32';
const venvBin = isWindows ? path.join(PROJECT_ROOT, '.venv', 'Scripts') : path.join(PROJECT_ROOT, '.venv', 'bin');
const pythonExe = path.join(venvBin, isWindows ? 'python.exe' : 'python');

console.log('Training models...\n');

console.log('Training anomaly ensemble model...');
runCommand(pythonExe, ['anomaly_ensemble/train.py'], path.join(PROJECT_ROOT, 'model-training'));

console.log('\nTraining drift model...');
runCommand(pythonExe, ['drift_model/train.py'], path.join(PROJECT_ROOT, 'model-training'));

console.log('\nAll models trained and exported successfully.');