import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import ObsPlayer from './ObsPlayer';

const Component = window.location.pathname.startsWith('/obs') ? ObsPlayer : App;

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Component />
  </React.StrictMode>,
);
