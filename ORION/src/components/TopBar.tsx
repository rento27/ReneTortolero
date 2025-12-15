import React from 'react';
import { Tab } from './Tab';
import { TabData } from '../App';

interface TopBarProps {
  tabs: TabData[];
  activeTabId: string;
  onTabChange: (id: string) => void;
  onNewTab: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({ tabs, activeTabId, onTabChange, onNewTab }) => {
  return (
    <div className="h-[40px] w-full bg-[#050505] flex items-end drag-region pl-[80px] border-b border-[#1A1A1D]">
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
      <div className="no-drag flex items-center px-4 h-full">
         {/* Window Controls or extra tools could go here */}
      </div>
    </div>
  );
};
