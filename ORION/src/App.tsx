import { useState } from 'react';
import { TopBar } from './components/TopBar';
import { Omnibox } from './components/Omnibox';
import { Viewport } from './components/Viewport';
import { SidePanel } from './components/SidePanel';

export interface TabData {
  id: string;
  title: string;
  url: string;
}

function App() {
  const [tabs, setTabs] = useState<TabData[]>([
    { id: '1', title: 'Inicio', url: 'https://google.com' },
    { id: '2', title: 'Docs: Estructura', url: 'about:blank' }
  ]);
  const [activeTabId, setActiveTabId] = useState<string>('1');

  const handleTabChange = (id: string) => {
    setActiveTabId(id);
    // Here we would tell Electron to switch views if we supported multi-view
    // For now, it just updates the UI active state
  };

  const handleNewTab = () => {
    const newId = Math.random().toString(36).substring(7);
    const newTab: TabData = {
      id: newId,
      title: 'Nueva Pestaña',
      url: ''
    };
    setTabs(prev => [...prev, newTab]);
    setActiveTabId(newId);
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#050505]">
      {/* Header Section */}
      <TopBar
        tabs={tabs}
        activeTabId={activeTabId}
        onTabChange={handleTabChange}
        onNewTab={handleNewTab}
      />
      <Omnibox />

      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden">
        <Viewport />
        <SidePanel />
      </div>
    </div>
  );
}

export default App;
