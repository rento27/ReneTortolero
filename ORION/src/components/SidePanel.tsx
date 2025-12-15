import React, { useState } from 'react';

export const SidePanel: React.FC = () => {
  const [logs, setLogs] = useState<string[]>([
    "System initialized...",
    "Awaiting user input."
  ]);
  const [isScanning, setIsScanning] = useState(false);

  const handleScan = async () => {
    setIsScanning(true);
    setLogs(prev => [...prev, "> INICIANDO ESCANEO..."]);

    try {
      const data = await window.electron.scanPage();

      if (data) {
        setLogs(prev => [
          ...prev,
          `> OBJETIVO: ${data.title || 'Desconocido'}`,
          `> ELEMENTOS CLAVE: ${data.headings.length > 0 ? data.headings.join(', ') : 'Ninguno detectado'}`,
          `> INTERACTIVOS: ${data.interactive.length} elementos detectados.`,
          "> DATOS EXTRACTADOS CON ÉXITO."
        ]);
      } else {
        setLogs(prev => [...prev, "> ERROR: No se pudo escanear la página."]);
      }
    } catch (error) {
      setLogs(prev => [...prev, "> ERROR CRÍTICO EN ESCANEO."]);
      console.error(error);
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <div className="w-[300px] h-full border-l border-[#333] bg-[#0A0A0A] flex flex-col">
      <div className="h-[40px] border-b border-[#333] flex items-center justify-between px-4 bg-[#050505]">
        <h2 className="text-sm font-bold tracking-widest text-[#00F0FF]">ORION AI</h2>
        <div className="w-2 h-2 rounded-full bg-[#00F0FF] animate-pulse"></div>
      </div>

      <div className="flex-1 p-4 font-mono text-xs text-gray-400 overflow-y-auto scrollbar-thin scrollbar-thumb-[#333]">
        {logs.map((log, i) => (
          <div key={i} className={`mb-2 ${log.startsWith('>') ? 'text-[#E0E0E0]' : 'text-[#00F0FF] opacity-70'}`}>
            {log}
          </div>
        ))}
        {isScanning && <div className="animate-pulse text-[#00F0FF]">{'>'} PROCESANDO...</div>}
      </div>

      <div className="p-4 border-t border-[#333] bg-[#050505]">
        <button
          onClick={handleScan}
          disabled={isScanning}
          className="w-full py-2 px-4 bg-[#1A1A1D] border border-[#00F0FF] text-[#00F0FF]
                     font-mono text-xs tracking-widest uppercase
                     hover:bg-[#00F0FF] hover:text-[#000] transition-all duration-300
                     disabled:opacity-50 disabled:cursor-not-allowed
                     shadow-[0_0_10px_rgba(0,240,255,0.1)] hover:shadow-[0_0_20px_rgba(0,240,255,0.4)]"
        >
          {isScanning ? 'ESCANEANDO...' : 'ANALIZAR SECTOR'}
        </button>
      </div>
    </div>
  );
};
