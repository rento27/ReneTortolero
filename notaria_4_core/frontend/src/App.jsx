import React from 'react';

function App() {
  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-8">
        <h1 className="text-3xl font-bold text-center text-blue-900 mb-4">
          Notaría 4 Digital Core
        </h1>
        <p className="text-gray-600 text-center mb-6">
          Plataforma de Soberanía Tecnológica
        </p>
        <div className="border-t border-gray-200 pt-4">
          <div className="flex justify-between items-center mb-2">
            <span className="font-semibold text-sm">Estado del Sistema:</span>
            <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">Activo</span>
          </div>
          <p className="text-xs text-gray-500 mt-2 text-center">
            Gestión de CFDI 4.0, OCR y Protocolos Notariales.
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;
