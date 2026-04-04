import React, { useState, useEffect } from 'react';
import { Tab } from './Tab';
import { TabData } from '../App';
import { MoreVertical, Download } from 'lucide-react';
import { AppMenu } from './AppMenu';
import { FindBar } from './FindBar';
import { DownloadsBubble } from './DownloadsBubble';
import { DownloadItem } from '../types';

interface TopBarProps {
  tabs: TabData[];
  activeTabId: string;
  onTabChange: (id: string) => void;
  onNewTab: () => void;
  onOpenHistory: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({ tabs, activeTabId, onTabChange, onNewTab, onOpenHistory }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isFindOpen, setIsFindOpen] = useState(false);
  const [isDownloadsOpen, setIsDownloadsOpen] = useState(false);
  const [downloads, setDownloads] = useState<DownloadItem[]>([]);
  const [showDownloadBtn, setShowDownloadBtn] = useState(false);

  useEffect(() => {
    if (window.electron) {
       window.electron.onDownloadStart((data: any) => {
         setDownloads(prev => [{ ...data, receivedBytes: 0, state: 'progressing' }, ...prev]);
         setShowDownloadBtn(true);
         setIsDownloadsOpen(true); // Auto-open on start
       });

       window.electron.onDownloadProgress((data: any) => {
         setDownloads(prev => prev.map(d => d.id === data.id ? { ...d, ...data, state: 'progressing' } : d));
       });

       window.electron.onDownloadComplete((data: any) => {
         setDownloads(prev => prev.map(d => d.id === data.id ? { ...d, state: data.state, path: data.path } : d));
       });
    }
  }, []);

  const toggleMenu = () => setIsMenuOpen(!isMenuOpen);
  const toggleFind = () => {
      setIsFindOpen(!isFindOpen);
      if (isFindOpen) window.electron.stopFind();
  };
  const toggleDownloads = () => setIsDownloadsOpen(!isDownloadsOpen);

  const activeDownloadsCount = downloads.filter(d => d.state === 'progressing').length;

  return (
    <div className="h-[40px] w-full bg-[#050505] flex items-end drag-region pl-[80px] border-b border-[#1A1A1D] relative">
      <div className="flex flex-1 h-full items-end overflow-x-auto no-scrollbar">
        {tabs.map(tab => (
          <Tab
            key={tab.id}
            title={tab.title}
            active={tab.id === activeTabId}
            onClick={() => onTabChange(tab.id)}
          />
        ))}

        {/* New Tab Button */}
        <button
          onClick={onNewTab}
          className="no-drag h-full px-3 flex items-center justify-center text-[#E0E0E0] hover:text-[#00F0FF] hover:bg-[#1A1A1D] transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
        </button>
      </div>

      <div className="no-drag flex items-center px-2 h-full gap-1">
         {showDownloadBtn && (
           <button
             onClick={toggleDownloads}
             className={`p-2 rounded hover:bg-[#1A1A1D] transition-all relative ${activeDownloadsCount > 0 ? 'text-[#00F0FF] animate-pulse' : 'text-gray-400'}`}
           >
             <Download size={18} />
             {activeDownloadsCount > 0 && (
               <span className="absolute top-1 right-1 w-2 h-2 bg-[#00F0FF] rounded-full"></span>
             )}
           </button>
         )}

         <button
           onClick={toggleMenu}
           className={`p-2 rounded hover:bg-[#1A1A1D] transition-colors ${isMenuOpen ? 'text-[#00F0FF]' : 'text-[#E0E0E0]'}`}
         >
           <MoreVertical size={18} />
         </button>
      </div>

      {isMenuOpen && (
        <AppMenu
          onClose={() => setIsMenuOpen(false)}
          onNewTab={onNewTab}
          onToggleFind={toggleFind}
          onOpenHistory={onOpenHistory}
        />
      )}

      {isFindOpen && (
        <FindBar onClose={toggleFind} />
      )}

      {isDownloadsOpen && (
        <DownloadsBubble downloads={downloads} onClose={() => setIsDownloadsOpen(false)} />
      )}
    </div>
  );
};
