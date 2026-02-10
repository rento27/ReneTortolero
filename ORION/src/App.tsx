import { useState, useEffect } from 'react';
import { TopBar } from './components/TopBar';
import { Omnibox } from './components/Omnibox';
import { Viewport } from './components/Viewport';
import { SidePanel } from './components/SidePanel';
import { HistoryOverlay } from './components/HistoryOverlay';
import { BookmarksBar } from './components/BookmarksBar';
import { HistoryItem } from './types';

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
  const [showHistory, setShowHistory] = useState(false);
  const [bookmarksRefresh, setBookmarksRefresh] = useState(0);

  // History Listener
  useEffect(() => {
    if (window.electron && window.electron.onUrlChange) {
      window.electron.onUrlChange((newUrl) => {
        // Basic history logic: add to top
        const stored = localStorage.getItem('orion_history');
        const history: HistoryItem[] = stored ? JSON.parse(stored) : [];

        // Avoid duplicate consecutive entries
        if (history.length > 0 && history[0].url === newUrl) return;

        const newItem: HistoryItem = {
          url: newUrl,
          title: newUrl, // Title would ideally come from another IPC event
          timestamp: Date.now()
        };

        const newHistory = [newItem, ...history].slice(0, 100); // Limit to 100 items
        localStorage.setItem('orion_history', JSON.stringify(newHistory));
      });
    }
  }, []);

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

  const handleNavigate = (url: string) => {
    if (window.electron && window.electron.navigate) {
      window.electron.navigate(url);
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
        onOpenHistory={() => setShowHistory(true)}
      />

      <div className="flex flex-col">
        <Omnibox onBookmarkUpdate={() => setBookmarksRefresh(prev => prev + 1)} />
        <BookmarksBar onNavigate={handleNavigate} refreshTrigger={bookmarksRefresh} />
      </div>

      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden relative">
        <Viewport />
        <SidePanel />

        {showHistory && (
          <HistoryOverlay
            onClose={() => setShowHistory(false)}
            onNavigate={handleNavigate}
          />
        )}
      </div>
    </div>
  );
}

export default App;
