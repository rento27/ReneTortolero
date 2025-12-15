import React from 'react';
import { Tab } from './Tab';

export const TopBar: React.FC = () => {
  return (
    <div className="h-[40px] w-full bg-[#050505] flex items-end drag-region pl-[80px] border-b border-[#1A1A1D]">
      <div className="flex flex-1 h-full items-end overflow-x-auto no-scrollbar">
        <Tab title="Inicio" active />
        <Tab title="Docs: Estructura" />
        <Tab title="Nueva Pestaña" />
      </div>
      <div className="no-drag flex items-center px-4 h-full">
         {/* Window Controls or extra tools could go here */}
      </div>
    </div>
  );
};
