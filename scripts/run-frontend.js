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

// Check frontend dependencies
const frontendNodeModules = path.join(PROJECT_ROOT, 'frontend', 'node_modules');
if (!fs.existsSync(frontendNodeModules)) {
  console.error('Error: Frontend dependencies not found. Run "npm run install:all" first.');
  process.exit(1);
}

console.log('Starting LatentGuard AI frontend on port 3000...');
runCommand('npm', ['run', 'dev'], path.join(PROJECT_ROOT, 'frontend'));