import React, { useEffect, useState } from 'react';

export const Omnibox: React.FC = () => {
  const [url, setUrl] = useState('');

  useEffect(() => {
    // Listen for URL changes from the main process
    if (window.electron && window.electron.onUrlChange) {
      window.electron.onUrlChange((newUrl) => {
        setUrl(newUrl);
      });
    }
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      window.electron.navigate(url);
    }
  };

  return (
    <div className="h-[50px] bg-[#050505] flex items-center px-4 gap-4 border-b border-[#1A1A1D]">
      {/* Navigation Controls */}
      <div className="flex gap-2 text-[#E0E0E0]">
        <button
          onClick={() => window.electron.goBack()}
          className="p-2 hover:text-[#00F0FF] transition-colors rounded hover:bg-[#1A1A1D]"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m15 18-6-6 6-6"/></svg>
        </button>
        <button
          onClick={() => window.electron.goForward()}
          className="p-2 hover:text-[#00F0FF] transition-colors rounded hover:bg-[#1A1A1D]"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
        </button>
        <button
          onClick={() => window.electron.reload()}
          className="p-2 hover:text-[#00F0FF] transition-colors rounded hover:bg-[#1A1A1D]"
        >
           <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>
        </button>
      </div>

      {/* Input Field */}
      <div className="flex-1">
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ingresa coordenadas o URL..."
          className="w-full bg-[#111] border border-[#333] rounded px-4 py-1.5 text-sm text-[#E0E0E0] focus:outline-none focus:border-[#00F0FF] focus:shadow-[0_0_5px_rgba(0,240,255,0.2)] placeholder-gray-600 font-mono"
        />
      </div>

      {/* Extra Actions */}
      <div className="flex gap-2">
         <div className="text-xs text-gray-600 font-mono tracking-widest">SECURE_LINK</div>
      </div>
    </div>
  );
};
