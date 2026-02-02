import React, { useState, useEffect } from 'react';
import { BookmarkItem } from '../types';
import { Globe, Trash } from 'lucide-react';

interface BookmarksBarProps {
  onNavigate: (url: string) => void;
  refreshTrigger: number; // Prop to force re-render when bookmark added externally
}

export const BookmarksBar: React.FC<BookmarksBarProps> = ({ onNavigate, refreshTrigger }) => {
  const [bookmarks, setBookmarks] = useState<BookmarkItem[]>([]);
  const [contextMenu, setContextMenu] = useState<{ x: number, y: number, id: string } | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem('orion_bookmarks');
    if (stored) {
      try {
        setBookmarks(JSON.parse(stored));
      } catch (e) {
        console.error('Failed to parse bookmarks', e);
      }
    }
  }, [refreshTrigger]);

  const handleContextMenu = (e: React.MouseEvent, id: string) => {
    e.preventDefault();
    setContextMenu({ x: e.clientX, y: e.clientY, id });
  };

  const deleteBookmark = () => {
    if (!contextMenu) return;
    const newBookmarks = bookmarks.filter(b => b.id !== contextMenu.id);
    setBookmarks(newBookmarks);
    localStorage.setItem('orion_bookmarks', JSON.stringify(newBookmarks));
    setContextMenu(null);
    // Dispatch storage event manually for other components if needed, though refreshTrigger handles parent updates
    window.dispatchEvent(new Event('storage'));
  };

  // Close context menu on click elsewhere
  useEffect(() => {
    const handleClick = () => setContextMenu(null);
    window.addEventListener('click', handleClick);
    return () => window.removeEventListener('click', handleClick);
  }, []);

  if (bookmarks.length === 0) return null;

  return (
    <div className="h-[28px] bg-[#050505] border-b border-[#1A1A1D] flex items-center px-2 gap-1 overflow-x-auto scrollbar-none z-30 relative">
      {bookmarks.map(b => (
        <div
          key={b.id}
          onClick={() => onNavigate(b.url)}
          onContextMenu={(e) => handleContextMenu(e, b.id)}
          className="flex items-center gap-2 px-2 py-1 max-w-[150px] hover:bg-[#1A1A1D] rounded cursor-pointer group"
          title={b.url}
        >
          {/* Simple favicon fallback: generic globe icon */}
          <Globe size={12} className="text-gray-500 group-hover:text-[#00F0FF]" />
          <span className="text-[10px] text-gray-400 group-hover:text-[#E0E0E0] truncate font-mono">{b.title || b.url}</span>
        </div>
      ))}

      {contextMenu && (
        <div
          className="fixed bg-[#1A1A1D] border border-[#333] shadow-xl rounded py-1 z-50 text-gray-300 text-xs font-mono"
          style={{ top: contextMenu.y, left: contextMenu.x }}
        >
          <button
            onClick={deleteBookmark}
            className="flex items-center gap-2 px-3 py-1.5 hover:bg-red-900/20 hover:text-red-400 w-full text-left"
          >
            <Trash size={12} />
            Eliminar
          </button>
        </div>
      )}
    </div>
  );
};
