import { FullConfig } from '@playwright/test';
import { spawn } from 'child_process';
import http from 'http';

let backendProcess: ReturnType<typeof spawn> | null = null;

function waitForBackend(): Promise<void> {
  return new Promise((resolve, reject) => {
    const maxRetries = 30;
    let retries = 0;
    
    const checkHealth = () => {
      http.get('http://localhost:8000/health', (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          if (res.statusCode === 200 && data.includes('healthy')) {
            console.log('Backend is ready');
            resolve();
          } else {
            retry();
          }
        });
      }).on('error', () => {
        retry();
      });
    };
    
    const retry = () => {
      if (retries >= maxRetries) {
        reject(new Error('Backend failed to start within timeout'));
        return;
      }
      retries++;
      setTimeout(checkHealth, 1000);
    };
    
    checkHealth();
  });
}

export default async function globalSetup(config: FullConfig) {
  console.log('Starting backend server...');
  
  backendProcess = spawn('python3', ['-m', 'uvicorn', 'backend.app:app', '--host', '0.0.0.0', '--port', '8000'], {
    cwd: '/Users/gauravkumarverma/Desktop/Agentic_Engg/RAG_agent',
    stdio: 'pipe',
  });
  
  backendProcess.stdout?.on('data', (data) => {
    console.log(`Backend: ${data}`);
  });
  
  backendProcess.stderr?.on('data', (data) => {
    console.error(`Backend error: ${data}`);
  });
  
  try {
    await waitForBackend();
    console.log('Backend started successfully');
  } catch (e) {
    console.error('Failed to start backend:', e);
    process.exit(1);
  }
  
  // Store the process so we can clean up later
  (global as any).__BACKEND_PROCESS__ = backendProcess;
}