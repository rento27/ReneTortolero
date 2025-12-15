import React from 'react';

export const SidePanel: React.FC = () => {
  return (
    <div className="w-[300px] h-full border-l border-[#333] bg-[#0A0A0A] flex flex-col">
      <div className="h-[40px] border-b border-[#333] flex items-center px-4 bg-[#050505]">
        <h2 className="text-sm font-bold tracking-widest text-[#00F0FF]">ORION AI</h2>
      </div>

      <div className="flex-1 p-4 font-mono text-xs text-gray-500 overflow-y-auto">
        <div className="mb-2 text-[#00F0FF] opacity-50">System initialized...</div>
        <div className="mb-2">Awaiting user input.</div>
        <div className="animate-pulse">_</div>
      </div>
    </div>
  );
};
