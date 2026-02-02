import { useState } from 'react'
import { FileText, Check, AlertCircle, Upload } from 'lucide-react'

function App() {
  const [file, setFile] = useState(null)
  const [extractedData, setExtractedData] = useState(null)

  const handleFileUpload = (e) => {
    const uploadedFile = e.target.files[0]
    setFile(uploadedFile)
    // Simulate extraction trigger
    setTimeout(() => {
      setExtractedData({
        escritura: "23674",
        cliente: "INMOBILIARIA DEL PACIFICO",
        monto: 1000000.00,
        isai: 30000.00
      })
    }, 1500)
  }

  return (
    <div className="flex h-screen bg-gray-50 text-slate-900">
      {/* Sidebar / Navigation */}
      <aside className="w-64 bg-navy-900 text-white flex flex-col p-4 border-r border-navy-800">
        <h1 className="text-xl font-bold text-gold-500 mb-8">Notaría 4 Core</h1>
        <nav className="space-y-2">
          <a href="#" className="block p-2 rounded bg-navy-800 text-white">Facturación</a>
          <a href="#" className="block p-2 rounded text-gray-400 hover:text-white">Expedientes</a>
        </nav>
      </aside>

      {/* Main Content: Split View */}
      <main className="flex-1 flex overflow-hidden">
        {/* Left: Document Viewer */}
        <div className="w-1/2 bg-gray-200 border-r border-gray-300 flex items-center justify-center relative">
          {file ? (
            <div className="text-center">
              <FileText className="w-16 h-16 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-600 font-medium">{file.name}</p>
              <p className="text-xs text-gray-500">Visualizador de PDF (Mock)</p>
            </div>
          ) : (
             <div className="text-center p-8 border-2 border-dashed border-gray-400 rounded-lg">
                <Upload className="w-12 h-12 text-gray-400 mx-auto mb-2" />
                <p className="text-gray-500">Arrastra tu escritura aquí</p>
                <input type="file" className="mt-4" onChange={handleFileUpload} />
             </div>
          )}
        </div>

        {/* Right: Data Validation Form */}
        <div className="w-1/2 p-8 overflow-y-auto bg-white">
          <div className="mb-6 flex justify-between items-center">
            <h2 className="text-2xl font-serif font-bold text-navy-900">Validación de Escritura</h2>
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-gold-100 text-gold-700 uppercase tracking-wide">
              {extractedData ? 'Revisión' : 'Esperando Documento'}
            </span>
          </div>

          {extractedData && (
            <form className="space-y-6">
              {/* Section: Datos Generales */}
              <div className="bg-sand-50 p-4 rounded-lg border border-sand-200">
                <h3 className="text-sm font-bold text-navy-700 uppercase mb-4 border-b border-sand-200 pb-2">
                  Datos del Instrumento
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-gray-500 uppercase">Num. Escritura</label>
                    <input type="text" defaultValue={extractedData.escritura} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-gold-500 focus:ring-gold-500 bg-white p-2 border" />
                  </div>
                   <div>
                    <label className="block text-xs font-bold text-gray-500 uppercase">Fecha</label>
                    <input type="date" className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-gold-500 focus:ring-gold-500 bg-white p-2 border" />
                  </div>
                </div>
              </div>

              {/* Section: Fiscal */}
              <div className="bg-sand-50 p-4 rounded-lg border border-sand-200">
                <h3 className="text-sm font-bold text-navy-700 uppercase mb-4 border-b border-sand-200 pb-2">
                  Datos Fiscales
                </h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-xs font-bold text-gray-500 uppercase">Receptor (Razón Social)</label>
                    <div className="flex gap-2">
                      <input type="text" defaultValue={extractedData.cliente} className="flex-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-gold-500 focus:ring-gold-500 bg-white p-2 border" />
                      <button type="button" className="text-xs bg-navy-100 text-navy-700 px-2 py-1 rounded hover:bg-navy-200">
                        Sanitizar
                      </button>
                    </div>
                     <p className="text-xs text-red-500 mt-1 flex items-center">
                        <AlertCircle className="w-3 h-3 mr-1" />
                        Verificar Régimen Fiscal
                     </p>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                     <div>
                        <label className="block text-xs font-bold text-gray-500 uppercase">Monto Operación</label>
                        <input type="number" defaultValue={extractedData.monto} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-gold-500 focus:ring-gold-500 bg-white p-2 border" />
                     </div>
                     <div>
                        <label className="block text-xs font-bold text-gray-500 uppercase">ISAI Calculado (3%)</label>
                        <input type="number" defaultValue={extractedData.isai} readOnly className="mt-1 block w-full rounded-md border-gray-300 bg-gray-100 p-2 border text-gray-600" />
                     </div>
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-4 pt-4">
                 <button type="button" className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">
                    Cancelar
                 </button>
                 <button type="submit" className="px-4 py-2 text-sm font-medium text-white bg-navy-600 rounded-md hover:bg-navy-700 flex items-center shadow-lg shadow-navy-600/20">
                    <Check className="w-4 h-4 mr-2" />
                    Validar y Timbrar
                 </button>
              </div>
            </form>
          )}
        </div>
      </main>
    </div>
  )
}

export default App
