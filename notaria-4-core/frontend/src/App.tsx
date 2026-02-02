import React from 'react';
import { Header } from './components/Header';
import { ValidationPage } from './components/ValidationPage';

function App() {
  return (
    <div className="min-h-screen bg-slate-50 font-sans">
      <Header />
      <main>
        <ValidationPage />
      </main>
    </div>
  );
}

export default App;
