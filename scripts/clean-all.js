#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const PROJECT_ROOT = path.join(__dirname, '..');

function removePath(p) {
  const fullPath = path.join(PROJECT_ROOT, p);
  if (fs.existsSync(fullPath)) {
    fs.rmSync(fullPath, { recursive: true, force: true });
    console.log(`Removed: ${p}`);
  }
}

console.log('Cleaning generated files...\n');

// Backend outputs
const backendOutputsDir = path.join(PROJECT_ROOT, 'backend', 'outputs');
if (fs.existsSync(backendOutputsDir)) {
  const files = fs.readdirSync(backendOutputsDir);
  files.forEach(file => {
    const fullPath = path.join(backendOutputsDir, file);
    if (file.endsWith('.csv') || file.endsWith('.json')) {
      fs.rmSync(fullPath, { recursive: true, force: true });
      console.log(`Removed: backend/outputs/${file}`);
    }
  });
  
  // Remove jobs directory
  const jobsDir = path.join(backendOutputsDir, 'jobs');
  if (fs.existsSync(jobsDir)) {
    fs.rmSync(jobsDir, { recursive: true, force: true });
    console.log('Removed: backend/outputs/jobs');
  }
}

// Backend models
const backendModelsDir = path.join(PROJECT_ROOT, 'backend', 'models');
if (fs.existsSync(backendModelsDir)) {
  const files = fs.readdirSync(backendModelsDir);
  files.forEach(file => {
    if (file.endsWith('.pkl')) {
      fs.rmSync(path.join(backendModelsDir, file), { force: true });
      console.log(`Removed: backend/models/${file}`);
    }
  });
}

// Frontend dist
const frontendDistDir = path.join(PROJECT_ROOT, 'frontend', 'dist');
if (fs.existsSync(frontendDistDir)) {
  fs.rmSync(frontendDistDir, { recursive: true, force: true });
  console.log('Removed: frontend/dist');
}

console.log('\nClean completed.');