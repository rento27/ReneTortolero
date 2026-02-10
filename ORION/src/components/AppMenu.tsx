import React, { useState, useEffect } from 'react';
import {
  Plus, Maximize, Printer, Search, History, Download, Settings,
  Minus, Shield
} from 'lucide-react';

interface AppMenuProps {
  onClose: () => void;
  onNewTab: () => void;
  onToggleFind: () => void;
  onOpenHistory: () => void;
}

export const AppMenu: React.FC<AppMenuProps> = ({ onClose, onNewTab, onToggleFind, onOpenHistory }) => {
  const [shieldsActive, setShieldsActive] = useState(true);

  useEffect(() => {
    if (window.electron && window.electron.getShieldsStatus) {
      window.electron.getShieldsStatus().then(setShieldsActive);
    }
  }, []);

  const toggleShields = () => {
    if (window.electron && window.electron.toggleShields) {
      window.electron.toggleShields();
      setShieldsActive(!shieldsActive);
    }
  };

  return (
    <div className="absolute right-4 top-[50px] w-[280px] bg-[#0A0A0A] border border-[#00F0FF] rounded-lg shadow-[0_0_20px_rgba(0,240,255,0.2)] z-50 text-[#E0E0E0] font-mono text-sm">
      {/* Menu Header (Optional) */}

      <div className="py-2">
        <MenuItem icon={<Plus size={16} />} label="Nueva Pestaña" onClick={() => { onNewTab(); onClose(); }} shortcut="Ctrl+T" />
        <MenuItem icon={<Maximize size={16} />} label="Nueva Ventana" onClick={onClose} shortcut="Ctrl+N" />

        <div className="h-[1px] bg-[#333] my-2 mx-2" />

        {/* Zoom Controls */}
        <div className="px-4 py-2 flex items-center justify-between hover:bg-[#1A1A1D]">
          <span className="flex items-center gap-3">
             <span className="w-4"></span>
             <span>Zoom</span>
          </span>
          <div className="flex items-center gap-2 border border-[#333] rounded overflow-hidden">
             <button onClick={() => window.electron.zoomOut()} className="p-1 hover:bg-[#333]"><Minus size={14} /></button>
             <button onClick={() => window.electron.zoomReset()} className="px-2 text-xs">100%</button>
             <button onClick={() => window.electron.zoomIn()} className="p-1 hover:bg-[#333]"><Plus size={14} /></button>
          </div>
        </div>

        <MenuItem icon={<Printer size={16} />} label="Imprimir..." onClick={() => { window.electron.printPage(); onClose(); }} shortcut="Ctrl+P" />
        <MenuItem icon={<Search size={16} />} label="Buscar en página..." onClick={() => { onToggleFind(); onClose(); }} shortcut="Ctrl+F" />

        <div className="h-[1px] bg-[#333] my-2 mx-2" />

        {/* Shield Toggle */}
        <button
          onClick={toggleShields}
          className="w-full text-left px-4 py-2 flex items-center justify-between hover:bg-[#1A1A1D] transition-colors"
        >
           <span className="flex items-center gap-3">
              <Shield size={16} className={shieldsActive ? "text-[#00F0FF]" : "text-gray-500"} />
              <span className={shieldsActive ? "text-[#00F0FF]" : "text-gray-500"}>Escudos de Defensa</span>
           </span>
           <div className={`w-8 h-4 rounded-full flex items-center px-0.5 transition-colors ${shieldsActive ? 'bg-[#00F0FF]' : 'bg-[#333]'}`}>
              <div className={`w-3 h-3 bg-black rounded-full transition-transform ${shieldsActive ? 'translate-x-4' : 'translate-x-0'}`}></div>
           </div>
        </button>

        <div className="h-[1px] bg-[#333] my-2 mx-2" />

        <MenuItem icon={<History size={16} />} label="Historial" onClick={() => { onOpenHistory(); onClose(); }} />
        <MenuItem icon={<Download size={16} />} label="Descargas" onClick={onClose} />
        <MenuItem icon={<Settings size={16} />} label="Configuración" onClick={onClose} />
      </div>
    </div>
  );
};

interface MenuItemProps {
  icon: React.ReactNode;
  label: string;
  shortcut?: string;
  onClick: () => void;
}

const MenuItem: React.FC<MenuItemProps> = ({ icon, label, shortcut, onClick }) => {
  return (
    <button onClick={onClick} className="w-full text-left px-4 py-2 flex items-center justify-between hover:bg-[#1A1A1D] hover:text-[#00F0FF] transition-colors">
       <span className="flex items-center gap-3">
          {icon}
          <span>{label}</span>
       </span>
       {shortcut && <span className="text-xs text-gray-500">{shortcut}</span>}
    </button>
  );
};
