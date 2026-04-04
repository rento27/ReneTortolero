import React from 'react';

export const Viewport: React.FC = () => {
  return (
    <div className="flex-1 h-full bg-[#050505] relative flex items-center justify-center overflow-hidden">
      {/* Grid Pattern Background */}
      <div className="absolute inset-0 opacity-10 pointer-events-none"
           style={{ backgroundImage: 'linear-gradient(#333 1px, transparent 1px), linear-gradient(90deg, #333 1px, transparent 1px)', backgroundSize: '40px 40px' }}>
      </div>

      <div className="text-center z-10">
         <div className="text-[#333] mb-4">
            <svg className="w-24 h-24 mx-auto animate-pulse" fill="currentColor" viewBox="0 0 24 24">
               <path d="M12 2L2 22h20L12 2zm0 4l6 14H6l6-14z"/>
            </svg>
         </div>
         <h1 className="text-xl font-light tracking-[0.2em] text-[#E0E0E0] opacity-50">SISTEMAS DE NAVEGACIÓN</h1>
         <p className="text-sm font-mono text-[#00F0FF] mt-2 tracking-widest">EN ESPERA</p>
      </div>
    </div>
  );
};
