import { TopBar } from './components/TopBar';
import { Omnibox } from './components/Omnibox';
import { Viewport } from './components/Viewport';
import { SidePanel } from './components/SidePanel';

function App() {
  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#050505]">
      {/* Header Section */}
      <TopBar />
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
