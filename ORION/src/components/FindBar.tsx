import React, { useState, useEffect } from 'react';
import { X, ArrowUp, ArrowDown } from 'lucide-react';

interface FindBarProps {
  onClose: () => void;
}

export const FindBar: React.FC<FindBarProps> = ({ onClose }) => {
  const [text, setText] = useState('');

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setText(e.target.value);
    if (e.target.value) {
      window.electron.findInPage(e.target.value);
    } else {
      window.electron.stopFind();
    }
  };

  return (
    <div className="absolute right-[80px] top-[50px] bg-[#0A0A0A] border border-[#00F0FF] rounded shadow-lg p-2 z-40 flex items-center gap-2 animate-in fade-in slide-in-from-top-2">
      <input
        autoFocus
        type="text"
        value={text}
        onChange={handleChange}
        placeholder="Buscar..."
        className="bg-[#111] border border-[#333] text-[#E0E0E0] text-xs px-2 py-1 rounded w-[150px] focus:outline-none focus:border-[#00F0FF]"
      />
      <div className="h-4 w-[1px] bg-[#333]"></div>
      {/* Navigation buttons could be hooked up if electron supports findNext */}
      <button className="text-gray-400 hover:text-[#00F0FF]"><ArrowUp size={14}/></button>
      <button className="text-gray-400 hover:text-[#00F0FF]"><ArrowDown size={14}/></button>
      <button onClick={onClose} className="text-gray-400 hover:text-red-500"><X size={14}/></button>
    </div>
  );
};
