import React, { useState } from 'react';
import { FileText, Calculator, Send, Save, Loader } from 'lucide-react';

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [extractedData, setExtractedData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = async (event) => {
    if (event.target.files && event.target.files[0]) {
      const file = event.target.files[0];
      setSelectedFile(file);
      setLoading(true);
      setError(null);
      setExtractedData(null);

      const formData = new FormData();
      formData.append('file', file);

      try {
        // In development, this connects to localhost:8080 or the forwarded port
        // Ensure backend is running.
        // If cors fails in preview, we might need a proxy, but for code structure this is correct.
        const response = await fetch('http://localhost:8080/api/v1/process-deed', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.statusText}`);
        }

        const result = await response.json();
        setExtractedData({
            rfc: result.extracted_data.rfc || "",
            nombre: result.extracted_data.razon_social || "",
            monto: result.extracted_data.monto || 0,
            escritura: result.extracted_data.escritura || ""
        });
      } catch (err) {
        console.error(err);
        setError("Error procesando la escritura. Asegúrate que el backend esté corriendo.");

        // Fallback for demo purposes if backend isn't reachable in this specific sandbox view
        // setExtractedData({
        //    rfc: "AGI123456XYZ",
        //    nombre: "AGI BUILDING SYNERGY (DEMO)",
        //    monto: 6083.91,
        //    escritura: "12345"
        // });
      } finally {
        setLoading(false);
      }
    }
  };

  const handleGenerateCFDI = async () => {
      if (!extractedData) return;

      try {
          const response = await fetch('http://localhost:8080/api/v1/generate-cfdi', {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                  receptor_rfc: extractedData.rfc,
                  razon_social: extractedData.nombre,
                  subtotal: parseFloat(extractedData.monto),
                  escritura: extractedData.escritura
              })
          });
          const result = await response.json();
          alert("CFDI Generado (Preview): \n" + JSON.stringify(result.calculations, null, 2));
      } catch (err) {
          alert("Error generando CFDI: " + err.message);
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
                <div className="bg-white h-[800px] shadow-lg p-8 relative">
                    {loading && (
                        <div className="absolute inset-0 bg-white/80 flex items-center justify-center z-10">
                            <Loader className="animate-spin text-indigo-600" size={48} />
                            <span className="ml-4 font-semibold text-indigo-600">Analizando escritura...</span>
                        </div>
                    )}

                    {selectedFile ? (
                        <div className="text-center mt-20">
                            <p className="text-gray-500">Visualizando: {selectedFile.name}</p>
                            <div className="mt-4 border-2 border-dashed border-yellow-400 p-4 bg-yellow-50">
                                <p className="text-xs text-gray-400 uppercase">Zona detectada por OCR</p>
                                <p className="font-mono text-sm">
                                    {extractedData ? `...${extractedData.nombre}...` : "Esperando extracción..."}
                                </p>
                            </div>
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center h-full text-gray-400">
                            <FileText size={48} />
                            <p className="mt-4">Cargue una escritura (PDF) para comenzar</p>
                            <input type="file" onChange={handleFileChange} className="mt-4" accept="application/pdf" />
                        </div>
                    )}
                    {error && (
                        <div className="mt-4 p-4 bg-red-100 text-red-700 rounded">
                            {error}
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
                            value={extractedData?.rfc || ''}
                            onChange={(e) => setExtractedData({...extractedData, rfc: e.target.value})}
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
                            value={extractedData?.nombre || ''}
                            onChange={(e) => setExtractedData({...extractedData, nombre: e.target.value})}
                        />
                        <p className="text-xs text-gray-500">Se ha eliminado "S.A. de C.V." automáticamente.</p>
                    </div>

                     <div>
                        <label className="block text-sm font-medium text-gray-700">No. Escritura</label>
                        <input
                            type="text"
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border"
                            value={extractedData?.escritura || ''}
                            onChange={(e) => setExtractedData({...extractedData, escritura: e.target.value})}
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                         <div>
                            <label className="block text-sm font-medium text-gray-700">Monto Operación</label>
                            <input
                                type="number"
                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border"
                                value={extractedData?.monto || ''}
                                onChange={(e) => setExtractedData({...extractedData, monto: e.target.value})}
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
                        <h4 className="font-medium text-gray-900">Desglose (Estimado)</h4>
                        {/* Note: In a real app, we would re-fetch calculations from backend on change. For now static or simple JS calc */}
                        <p className="text-xs text-gray-500 mb-2">Calculos finales se realizan al timbrar.</p>
                    </div>

                    <div className="mt-8 flex space-x-4">
                        <button className="flex-1 bg-indigo-600 text-white p-2 rounded hover:bg-indigo-700 flex justify-center items-center">
                            <Save size={18} className="mr-2"/> Guardar Borrador
                        </button>
                         <button
                            onClick={handleGenerateCFDI}
                            className="flex-1 bg-green-600 text-white p-2 rounded hover:bg-green-700 flex justify-center items-center"
                            disabled={!extractedData}
                         >
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
