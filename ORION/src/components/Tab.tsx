import React from 'react';

interface TabProps {
  active?: boolean;
  title: string;
  onClick?: () => void;
}

export const Tab: React.FC<TabProps> = ({ active, title, onClick }) => {
  return (
    <div
      onClick={onClick}
      className={`
        no-drag
        relative px-4 py-1.5 min-w-[120px] max-w-[200px]
        text-xs tracking-wider cursor-pointer transition-all duration-200
        clip-path-angular
        ${active
          ? 'bg-[#1A1A1D] text-[#E0E0E0] border-t-2 border-[#00F0FF]'
          : 'bg-transparent text-gray-500 hover:text-gray-300 opacity-70 hover:opacity-100'}
      `}
    >
      <div className="flex items-center justify-between">
        <span className="truncate">{title}</span>
        {active && (
           <span className="w-1.5 h-1.5 rounded-full bg-[#00F0FF] shadow-[0_0_5px_#00F0FF]"></span>
        )}
      </div>

      {/* Separator for inactive tabs */}
      {!active && (
        <div className="absolute right-0 top-1/2 -translate-y-1/2 w-[1px] h-4 bg-[#333]"></div>
      )}
    </div>
  );
};
