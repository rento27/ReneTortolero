import React, { useState, useEffect, useRef } from 'react';

interface Message {
  id: string;
  sender: 'user' | 'ai' | 'system';
  text: string;
}

export const SidePanel: React.FC = () => {
  const [apiKey, setApiKey] = useState<string>('');
  const [inputKey, setInputKey] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    { id: 'init', sender: 'system', text: "System initialized..." },
    { id: 'await', sender: 'system', text: "Awaiting authentication..." }
  ]);
  const [isScanning, setIsScanning] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load API Key on mount
  useEffect(() => {
    const storedKey = localStorage.getItem('orion_gemini_key');
    if (storedKey) {
      setApiKey(storedKey);
      addMessage('system', 'Authentication successful. Neural link established.');
    }
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const addMessage = (sender: 'user' | 'ai' | 'system', text: string) => {
    const id = Math.random().toString(36).substring(7);
    setMessages(prev => [...prev, { id, sender, text }]);
    return id; // Return ID for updates if needed
  };

  const saveKey = () => {
    if (inputKey.trim()) {
      localStorage.setItem('orion_gemini_key', inputKey.trim());
      setApiKey(inputKey.trim());
      addMessage('system', 'Identity verified. Access granted.');
    }
  };

  const typeWriterEffect = async (text: string) => {
    const id = Math.random().toString(36).substring(7);
    // Initialize empty message
    setMessages(prev => [...prev, { id, sender: 'ai', text: '' }]);

    for (let i = 0; i < text.length; i++) {
      setMessages(prev => prev.map(msg =>
        msg.id === id ? { ...msg, text: msg.text + text[i] } : msg
      ));
      await new Promise(resolve => setTimeout(resolve, 15)); // Typing speed
    }
  };

  const askOrion = async (pageData: any, userPrompt: string) => {
    try {
      const response = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            contents: [{
              parts: [{
                text: `Eres ORION, una IA de navegación táctica. Analiza los siguientes datos extraídos de una web. Sé conciso, militar y útil.
DATOS DEL SECTOR: ${JSON.stringify(pageData)}
PREGUNTA DEL COMANDANTE: ${userPrompt}`
              }]
            }]
          })
        }
      );

      const data = await response.json();

      if (data.error) {
        throw new Error(data.error.message || 'API Error');
      }

      const aiText = data.candidates?.[0]?.content?.parts?.[0]?.text;

      if (aiText) {
        await typeWriterEffect(aiText);
      } else {
        addMessage('system', 'Error: No tactical response received.');
      }

    } catch (error) {
      console.error(error);
      addMessage('system', 'Communication link failed. Check credentials.');
    }
  };

  const handleScan = async () => {
    if (!apiKey) return;

    setIsScanning(true);
    addMessage('system', '> INICIANDO ESCANEO DE DOM...');

    try {
      const data = await window.electron.scanPage();

      if (data) {
        addMessage('system', '> DATOS EXTRACTADOS CON ÉXITO.');
        addMessage('user', 'Genera un informe de situación.');

        await askOrion(data, 'Genera un informe de situación de este sitio web. Identifica el propósito y riesgos potenciales.');
      } else {
        addMessage('system', '> ERROR: Escaneo fallido.');
      }
    } catch (error) {
      addMessage('system', '> ERROR CRÍTICO.');
      console.error(error);
    } finally {
      setIsScanning(false);
    }
  };

  // --- RENDER: LOGIN VIEW ---
  if (!apiKey) {
    return (
      <div className="w-[300px] h-full border-l border-[#333] bg-[#0A0A0A] flex flex-col items-center justify-center p-6">
         <div className="mb-4 text-[#00F0FF] animate-pulse">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="m2 17 10 5 10-5"/><path d="m2 12 10 5 10-5"/></svg>
         </div>
         <h2 className="text-[#00F0FF] font-mono text-sm tracking-[0.2em] mb-6">ACCESO DENEGADO</h2>

         <div className="w-full space-y-2">
            <label className="text-[10px] text-[#E0E0E0] font-mono tracking-widest">CÓDIGO DE ACCESO (GEMINI KEY)</label>
            <input
              type="password"
              value={inputKey}
              onChange={(e) => setInputKey(e.target.value)}
              className="w-full bg-[#111] border border-[#333] text-[#00F0FF] p-2 text-xs font-mono focus:border-[#00F0FF] focus:outline-none"
              placeholder="••••••••••••••••"
            />
            <button
               onClick={saveKey}
               className="w-full bg-[#1A1A1D] text-[#E0E0E0] border border-[#00F0FF] py-2 text-xs font-mono hover:bg-[#00F0FF] hover:text-black transition-colors"
            >
               ESTABLECER ENLACE
            </button>
         </div>
      </div>
    );
  }

  // --- RENDER: CHAT VIEW ---
  return (
    <div className="w-[300px] h-full border-l border-[#333] bg-[#0A0A0A] flex flex-col">
      <div className="h-[40px] border-b border-[#333] flex items-center justify-between px-4 bg-[#050505]">
        <h2 className="text-sm font-bold tracking-widest text-[#00F0FF]">ORION AI</h2>
        <div className="w-2 h-2 rounded-full bg-[#00F0FF] animate-pulse"></div>
      </div>

      <div className="flex-1 p-4 overflow-y-auto scrollbar-thin scrollbar-thumb-[#333]">
        {messages.map((msg) => (
          <div key={msg.id} className="mb-4 font-mono text-xs">
            {msg.sender === 'system' && (
               <div className="text-[#00F0FF] opacity-50 uppercase tracking-wider mb-1 text-[10px]">{'>'} SYSTEM</div>
            )}
            {msg.sender === 'user' && (
               <div className="text-[#E0E0E0] text-right mb-1 text-[10px]">CMD</div>
            )}
            {msg.sender === 'ai' && (
               <div className="text-[#00F0FF] font-bold mb-1 text-[10px]">ORION</div>
            )}

            <div className={`
               ${msg.sender === 'system' ? 'text-gray-500 italic' : ''}
               ${msg.sender === 'user' ? 'text-[#E0E0E0] bg-[#1A1A1D] p-2 rounded-l-lg rounded-br-lg ml-8 border border-[#333]' : ''}
               ${msg.sender === 'ai' ? 'text-[#00F0FF] leading-relaxed' : ''}
            `}>
               {msg.text}
            </div>
          </div>
        ))}
        {isScanning && <div className="animate-pulse text-[#00F0FF] text-xs font-mono">{'>'} PROCESANDO DATOS...</div>}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 border-t border-[#333] bg-[#050505]">
        <button
          onClick={handleScan}
          disabled={isScanning}
          className="w-full py-2 px-4 bg-[#1A1A1D] border border-[#00F0FF] text-[#00F0FF]
                     font-mono text-xs tracking-widest uppercase
                     hover:bg-[#00F0FF] hover:text-[#000] transition-all duration-300
                     disabled:opacity-50 disabled:cursor-not-allowed
                     shadow-[0_0_10px_rgba(0,240,255,0.1)] hover:shadow-[0_0_20px_rgba(0,240,255,0.4)]"
        >
          {isScanning ? 'ANALIZANDO...' : 'ANALIZAR SECTOR'}
        </button>
      </div>
    </div>
  );
};
