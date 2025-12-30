import React, { useState } from 'react';
import { FileText, Calculator, Send, Save } from 'lucide-react';

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [extractedData, setExtractedData] = useState(null);

  const handleFileChange = (event) => {
    if (event.target.files && event.target.files[0]) {
      setSelectedFile(event.target.files[0]);
      // Mock extraction trigger
      setTimeout(() => {
        setExtractedData({
            rfc: "AGI123456XYZ",
            nombre: "AGI BUILDING SYNERGY",
            monto: 6083.91
        });
      }, 1000);
    }
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar / Navigation */}
      <div className="w-64 bg-slate-900 text-white p-4">
        <h1 className="text-xl font-bold mb-8">Notaría 4 Core</h1>
        <nav className="space-y-4">
            <button className="flex items-center space-x-2 w-full p-2 bg-slate-800 rounded">
                <FileText size={18} /> <span>Facturación</span>
            </button>
            <button className="flex items-center space-x-2 w-full p-2 hover:bg-slate-800 rounded">
                <Calculator size={18} /> <span>Calculadora ISAI</span>
            </button>
        </nav>
      </div>

      {/* Main Content Area: Human-in-the-Loop Interface */}
      <div className="flex-1 flex flex-col">
        <header className="bg-white shadow p-4">
            <h2 className="text-lg font-semibold text-gray-700">Validación de Escritura / Generación CFDI</h2>
        </header>

        <div className="flex-1 flex overflow-hidden">
            {/* Left Panel: PDF Viewer (Mock) */}
            <div className="w-1/2 p-4 bg-gray-200 border-r border-gray-300 overflow-y-auto">
                <div className="bg-white h-[800px] shadow-lg p-8">
                    {selectedFile ? (
                        <div className="text-center mt-20">
                            <p className="text-gray-500">Visualizando: {selectedFile.name}</p>
                            <div className="mt-4 border-2 border-dashed border-yellow-400 p-4 bg-yellow-50">
                                <p className="text-xs text-gray-400 uppercase">Zona detectada por OCR</p>
                                <p className="font-mono text-sm">...COMPARECE LA PERSONA MORAL <strong>AGI BUILDING SYNERGY</strong> REPRESENTADA POR...</p>
                            </div>
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center h-full text-gray-400">
                            <FileText size={48} />
                            <p className="mt-4">Cargue una escritura (PDF) para comenzar</p>
                            <input type="file" onChange={handleFileChange} className="mt-4" />
                        </div>
                    )}
                </div>
            </div>

            {/* Right Panel: Data Validation Form */}
            <div className="w-1/2 p-4 bg-white overflow-y-auto">
                <h3 className="font-bold text-gray-800 mb-4">Datos Fiscales Extraídos</h3>

                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700">RFC Receptor</label>
                        <input
                            type="text"
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border"
                            defaultValue={extractedData?.rfc || ''}
                        />
                        {extractedData?.rfc?.length === 12 && (
                            <span className="text-xs text-blue-600 font-semibold">Persona Moral detectada - Aplicando Retenciones</span>
                        )}
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700">Razón Social (Sanitizada)</label>
                        <input
                            type="text"
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border"
                            defaultValue={extractedData?.nombre || ''}
                        />
                        <p className="text-xs text-gray-500">Se ha eliminado "S.A. de C.V." automáticamente.</p>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                         <div>
                            <label className="block text-sm font-medium text-gray-700">Monto Operación</label>
                            <input
                                type="number"
                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border"
                                defaultValue={extractedData?.monto || ''}
                            />
                        </div>
                        <div>
                             <label className="block text-sm font-medium text-gray-700">Uso CFDI</label>
                             <select className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 sm:text-sm p-2 border">
                                <option>G03 - Gastos en general</option>
                                <option>I01 - Construcciones</option>
                             </select>
                        </div>
                    </div>

                    <div className="border-t pt-4 mt-6">
                        <h4 className="font-medium text-gray-900">Desglose (Simulado)</h4>
                        <div className="flex justify-between text-sm mt-2">
                            <span>Subtotal:</span>
                            <span>$6,083.91</span>
                        </div>
                         <div className="flex justify-between text-sm text-red-600">
                            <span>Ret. ISR (10%):</span>
                            <span>-$608.39</span>
                        </div>
                         <div className="flex justify-between text-sm text-red-600">
                            <span>Ret. IVA (10.6667%):</span>
                            <span>-$648.95</span>
                        </div>
                        <div className="flex justify-between font-bold text-lg mt-2 border-t pt-2">
                            <span>Total:</span>
                            <span>$5,800.00</span>
                        </div>
                    </div>

                    <div className="mt-8 flex space-x-4">
                        <button className="flex-1 bg-indigo-600 text-white p-2 rounded hover:bg-indigo-700 flex justify-center items-center">
                            <Save size={18} className="mr-2"/> Guardar Borrador
                        </button>
                         <button className="flex-1 bg-green-600 text-white p-2 rounded hover:bg-green-700 flex justify-center items-center">
                            <Send size={18} className="mr-2"/> Timbrar CFDI 4.0
                        </button>
                    </div>
                </div>
            </div>
        </div>
      </div>
    </div>
  )
}

export default App
