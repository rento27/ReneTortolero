import React, { useState, useEffect } from 'react';
import { HistoryItem } from '../types';
import { X, Clock, Trash2 } from 'lucide-react';

interface HistoryOverlayProps {
  onClose: () => void;
  onNavigate: (url: string) => void;
}

export const HistoryOverlay: React.FC<HistoryOverlayProps> = ({ onClose, onNavigate }) => {
  const [history, setHistory] = useState<HistoryItem[]>([]);

  useEffect(() => {
    const stored = localStorage.getItem('orion_history');
    if (stored) {
      try {
        setHistory(JSON.parse(stored));
      } catch (e) {
        console.error('Failed to parse history', e);
      }
    }
  }, []);

  const clearHistory = () => {
    localStorage.removeItem('orion_history');
    setHistory([]);
  };

  const formatTime = (ts: number) => {
    return new Date(ts).toLocaleString();
  };

  return (
    <div className="absolute inset-0 z-50 bg-[#050505]/90 backdrop-blur-sm flex items-center justify-center animate-in fade-in duration-200">
      <div className="w-[600px] h-[80%] bg-[#0A0A0A] border border-[#00F0FF] rounded-lg shadow-[0_0_50px_rgba(0,240,255,0.1)] flex flex-col">
        {/* Header */}
        <div className="h-[60px] border-b border-[#333] flex items-center justify-between px-6 bg-[#050505] rounded-t-lg">
          <div className="flex items-center gap-3 text-[#00F0FF]">
            <Clock size={20} />
            <h2 className="text-lg font-mono tracking-widest uppercase">Registro de Navegación</h2>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors">
            <X size={24} />
          </button>
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto p-4 scrollbar-thin scrollbar-thumb-[#333]">
          {history.length === 0 ? (
            <div className="text-gray-600 font-mono text-center mt-20">SIN REGISTROS DE VUELO</div>
          ) : (
            history.map((item, i) => (
              <div
                key={i}
                onClick={() => { onNavigate(item.url); onClose(); }}
                className="group flex items-center justify-between p-3 border-b border-[#1A1A1D] hover:bg-[#1A1A1D] cursor-pointer transition-colors"
              >
                <div className="flex flex-col gap-1 overflow-hidden">
                  <span className="text-[#E0E0E0] font-medium text-sm truncate group-hover:text-[#00F0FF] transition-colors">{item.title || item.url}</span>
                  <span className="text-gray-600 text-xs font-mono truncate">{item.url}</span>
                </div>
                <span className="text-gray-700 text-xs font-mono whitespace-nowrap ml-4">
                  {formatTime(item.timestamp)}
                </span>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-[#333] flex justify-end">
          <button
            onClick={clearHistory}
            className="flex items-center gap-2 px-4 py-2 text-red-500 hover:bg-red-500/10 rounded border border-transparent hover:border-red-500/50 transition-all font-mono text-xs"
          >
            <Trash2 size={14} />
            PURGAR DATOS
          </button>
        </div>
      </div>
    </div>
  );
};
