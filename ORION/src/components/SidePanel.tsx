import React, { useState, useEffect, useRef } from 'react';
import { Bug, Send } from 'lucide-react';

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
  const [userInput, setUserInput] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Debug State
  const [debugMode, setDebugMode] = useState(false);

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

  const resetKey = () => {
    localStorage.removeItem('orion_gemini_key');
    window.location.reload();
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

  const executeAgentAction = async (actionJson: string) => {
    try {
      const action = JSON.parse(actionJson);
      // Map AI 'action' property to IPC 'type' property
      const mappedAction = {
        ...action,
        type: action.action
      };

      addMessage('system', `> INICIANDO SECUENCIA MOTOR: ${action.action.toUpperCase()}`);

      if (window.electron && window.electron.performAction) {
        window.electron.performAction(mappedAction);
        addMessage('system', '> EJECUCIÓN EXITOSA.');
      } else {
        addMessage('system', '> ERROR: MOTOR NO DISPONIBLE.');
      }
    } catch (e) {
      addMessage('system', '> ERROR DE PARSEO DE COMANDO.');
    }
  };

  const askOrion = async (pageData: any, userPrompt: string) => {
    try {
      const systemPrompt = `
Eres ORION, un Agente de Navegación Autónomo.
Tienes capacidad para interactuar con la web actual.

HERRAMIENTAS DISPONIBLES (Usa estas acciones en tu respuesta si se solicita):
- { "action": "click", "selector": "css_selector" }
- { "action": "type", "selector": "css_selector", "value": "texto" }
- { "action": "scroll", "selector": "css_selector" }

CONTEXTO VISUAL (Elementos interactivos detectados):
${JSON.stringify(pageData.interactive)}

REGLAS DE RESPUESTA:
1. Si el usuario pide una acción (ej: 'Busca X', 'Entra en el primer link'), TU RESPUESTA DEBE SER ÚNICAMENTE UN BLOQUE JSON VÁLIDO con la acción.
2. Si el usuario solo charla, responde con texto normal.
3. Sé preciso con los selectores del contexto visual.
`;

      const response = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            contents: [{
              parts: [{
                text: `${systemPrompt}\n\nDATOS DEL SECTOR: ${JSON.stringify(pageData)}\nPREGUNTA DEL COMANDANTE: ${userPrompt}`
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
        // Check for JSON action
        const jsonMatch = aiText.match(/\{[\s\S]*"action"[\s\S]*\}/);
        if (jsonMatch) {
          await executeAgentAction(jsonMatch[0]);
        } else {
          await typeWriterEffect(aiText);
        }
      } else {
        addMessage('system', 'Error: No tactical response received.');
      }

    } catch (error) {
      console.error(error);
      addMessage('system', 'Communication link failed. Check credentials.');
    }
  };

  const handleScan = async (customPrompt?: string) => {
    if (!apiKey) return;

    const promptToUse = customPrompt || 'Genera un informe de situación de este sitio web. Identifica el propósito y riesgos potenciales.';

    setIsScanning(true);
    addMessage('system', '> INICIANDO ESCANEO DE DOM...');

    try {
      const data = await window.electron.scanPage();

      if (data) {
        addMessage('system', '> DATOS EXTRACTADOS CON ÉXITO.');
        if (!customPrompt) addMessage('user', promptToUse); // Show default prompt if not typed

        await askOrion(data, promptToUse);
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

  const handleSendMessage = () => {
    if (!userInput.trim() || isScanning) return;
    addMessage('user', userInput);
    handleScan(userInput); // Pass user input as the prompt
    setUserInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const runTestClick = async () => {
    addMessage('system', '> EJECUTANDO PROTOCOLO DE PRUEBA MOTOR...');
    try {
      const data = await window.electron.scanPage();
      if (data && data.interactive && data.interactive.length > 0) {
        const target = data.interactive[0]; // First element
        addMessage('system', `> OBJETIVO LOCALIZADO: ${target.text || target.tag} (${target.selector})`);
        addMessage('system', '> INICIANDO SECUENCIA DE CLIC...');

        window.electron.performAction({ type: 'click', selector: target.selector });
        addMessage('system', '> ACCIÓN ENVIADA.');
      } else {
        addMessage('system', '> NO SE ENCONTRARON OBJETIVOS INTERACTIVOS.');
      }
    } catch (e) {
      addMessage('system', '> FALLO EN SISTEMA DE MOTORES.');
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
        <div className="flex items-center gap-3">
           <button
             onClick={() => setDebugMode(!debugMode)}
             className={`text-[10px] font-mono tracking-wider px-1 transition-colors ${debugMode ? 'text-[#00F0FF]' : 'text-gray-600'}`}
             title="Toggle Debug Mode"
           >
             <Bug size={14} />
           </button>
           <button
             onClick={resetKey}
             className="text-[10px] text-red-500 hover:text-red-400 font-mono tracking-wider border border-red-900 px-1 hover:bg-red-900/20 transition-colors"
             title="Reset Connection"
           >
             RESET
           </button>
           <div className="w-2 h-2 rounded-full bg-[#00F0FF] animate-pulse"></div>
        </div>
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

      <div className="p-4 border-t border-[#333] bg-[#050505] space-y-2">
        {/* Chat Input */}
        <div className="flex gap-2 mb-2">
          <input
            type="text"
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Enviar comando..."
            className="flex-1 bg-[#111] border border-[#333] text-[#E0E0E0] text-xs px-2 py-2 rounded focus:outline-none focus:border-[#00F0FF] font-mono placeholder-gray-600"
            disabled={isScanning}
          />
          <button
            onClick={handleSendMessage}
            disabled={isScanning || !userInput.trim()}
            className="bg-[#1A1A1D] border border-[#333] text-[#00F0FF] px-2 rounded hover:bg-[#00F0FF] hover:text-black transition-colors disabled:opacity-50"
          >
            <Send size={14} />
          </button>
        </div>

        <button
          onClick={() => handleScan()} // No arg = default prompt
          disabled={isScanning}
          className="w-full py-2 px-4 bg-[#1A1A1D] border border-[#00F0FF] text-[#00F0FF]
                     font-mono text-xs tracking-widest uppercase
                     hover:bg-[#00F0FF] hover:text-[#000] transition-all duration-300
                     disabled:opacity-50 disabled:cursor-not-allowed
                     shadow-[0_0_10px_rgba(0,240,255,0.1)] hover:shadow-[0_0_20px_rgba(0,240,255,0.4)]"
        >
          {isScanning ? 'ANALIZANDO...' : 'ANALIZAR SECTOR'}
        </button>

        {debugMode && (
          <button
            onClick={runTestClick}
            className="w-full py-2 px-4 bg-[#111] border border-orange-500 text-orange-500
                       font-mono text-xs tracking-widest uppercase
                       hover:bg-orange-500 hover:text-black transition-all duration-300"
          >
            TEST MOTOR: CLIC
          </button>
        )}
      </div>
    </div>
  );
};
