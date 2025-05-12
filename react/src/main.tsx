import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App.tsx';
import { BrowserRouter } from 'react-router-dom';

import { ThemeProvider, CssBaseline } from '@mui/material';
import getAppTheme from './assets/Theme';  // ✅ Fixed

const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
const resolvedMode = prefersDark ? 'dark' : 'light';

console.log('prefersDark:', prefersDark);
console.log('resolvedMode:', resolvedMode);
console.log('typeof getAppTheme:', typeof getAppTheme);

const theme = getAppTheme(resolvedMode); // <- NOW guaranteed to be 'light' or 'dark'

console.log('theme.palette.mode:', theme.palette.mode); // should log 'light' or 'dark'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ThemeProvider>
  </StrictMode>
);