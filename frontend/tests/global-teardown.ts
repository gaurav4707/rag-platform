import { FullConfig } from '@playwright/test';

export default async function globalTeardown(config: FullConfig) {
  const backendProcess = (global as any).__BACKEND_PROCESS__;
  
  if (backendProcess) {
    console.log('Stopping backend server...');
    backendProcess.kill('SIGTERM');
    
    // Wait for process to exit
    await new Promise<void>((resolve) => {
      backendProcess.on('exit', () => {
        console.log('Backend stopped');
        resolve();
      });
      
      // Force kill after 5 seconds
      setTimeout(() => {
        backendProcess.kill('SIGKILL');
        resolve();
      }, 5000);
    });
  }
}