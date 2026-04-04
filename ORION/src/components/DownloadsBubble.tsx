import React from 'react';
import { DownloadItem } from '../types';
import { File, FolderOpen, X } from 'lucide-react';

interface DownloadsBubbleProps {
  downloads: DownloadItem[];
  onClose: () => void;
}

export const DownloadsBubble: React.FC<DownloadsBubbleProps> = ({ downloads, onClose }) => {
  return (
    <div className="absolute right-[50px] top-[50px] w-[320px] bg-[#0A0A0A] border border-[#00F0FF] rounded-lg shadow-[0_0_20px_rgba(0,240,255,0.2)] z-50 text-[#E0E0E0] font-mono text-sm flex flex-col max-h-[400px]">
      <div className="px-4 py-2 border-b border-[#333] flex items-center justify-between bg-[#050505] rounded-t-lg">
        <h3 className="text-[#00F0FF] text-xs tracking-widest uppercase">Descargas Activas</h3>
        <button onClick={onClose} className="text-gray-500 hover:text-white"><X size={14}/></button>
      </div>

      <div className="flex-1 overflow-y-auto p-2 scrollbar-thin scrollbar-thumb-[#333]">
        {downloads.length === 0 ? (
          <div className="text-center py-4 text-gray-600 text-xs">No hay descargas recientes</div>
        ) : (
          downloads.map(item => (
            <div key={item.id} className="mb-2 p-2 bg-[#111] rounded border border-[#333] hover:border-[#00F0FF]/30 transition-colors">
              <div className="flex items-center gap-3 mb-2">
                 <File size={20} className="text-[#00F0FF]" />
                 <div className="flex-1 overflow-hidden">
                   <div className="truncate text-xs font-bold text-[#E0E0E0]">{item.filename}</div>
                   <div className="flex justify-between text-[10px] text-gray-500">
                      <span>{(item.receivedBytes / 1024 / 1024).toFixed(1)} MB / {(item.totalBytes / 1024 / 1024).toFixed(1)} MB</span>
                      <span className={item.state === 'completed' ? 'text-green-400' : item.state === 'progressing' ? 'text-yellow-400' : 'text-red-400'}>
                        {item.state.toUpperCase()}
                      </span>
                   </div>
                 </div>
              </div>

              {item.state === 'progressing' && (
                <div className="h-1 w-full bg-[#333] rounded-full overflow-hidden mb-2">
                   <div
                     className="h-full bg-[#00F0FF] transition-all duration-300"
                     style={{ width: `${(item.receivedBytes / item.totalBytes) * 100}%` }}
                   ></div>
                </div>
              )}

              <div className="flex justify-end gap-2">
                 {item.state === 'progressing' && (
                   <button
                     onClick={() => window.electron.cancelDownload(item.id)}
                     className="p-1 hover:bg-red-900/30 text-gray-500 hover:text-red-400 rounded"
                     title="Cancelar"
                   >
                     <X size={14} />
                   </button>
                 )}
                 {item.state === 'completed' && item.path && (
                   <button
                     onClick={() => window.electron.showItemInFolder(item.path!)}
                     className="p-1 hover:bg-[#333] text-gray-500 hover:text-[#00F0FF] rounded"
                     title="Mostrar en carpeta"
                   >
                     <FolderOpen size={14} />
                   </button>
                 )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
