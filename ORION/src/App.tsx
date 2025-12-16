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
    const tab = tabs.find(t => t.id === id);
    if (tab && window.electron && window.electron.navigate) {
      window.electron.navigate(tab.url);
    }
  };

  const handleNewTab = () => {
    const newId = Math.random().toString(36).substring(7);
    const newTab: TabData = {
      id: newId,
      title: 'Nueva Pestaña',
      url: 'about:blank'
    };
    setTabs(prev => [...prev, newTab]);
    setActiveTabId(newId);
    if (window.electron && window.electron.navigate) {
        window.electron.navigate(newTab.url);
    }
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
