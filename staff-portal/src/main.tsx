import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';

// Set up online/offline listeners
window.addEventListener('online', () => {
  window.dispatchEvent(new CustomEvent('connection-change', { detail: { isOnline: true } }));
});

window.addEventListener('offline', () => {
  window.dispatchEvent(new CustomEvent('connection-change', { detail: { isOnline: false } }));
});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
