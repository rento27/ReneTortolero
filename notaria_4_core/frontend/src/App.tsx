import { useState } from 'react'
import './App.css'

function App() {
  const [file, setFile] = useState<File | null>(null)
  const [status, setStatus] = useState<string>('Esperando archivo...')

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(e.target.files[0])
      setStatus('Archivo seleccionado. Listo para procesar.')
    }
  }

  const handleUpload = async () => {
    if (!file) return
    setStatus('Subiendo y procesando...')
    // Simulation of upload to Cloud Functions / Cloud Run
    setTimeout(() => {
      setStatus('Procesamiento completado via Cloud Run (Simulado)')
    }, 2000)
  }

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-4">
      <div className="bg-white p-8 rounded-lg shadow-xl w-full max-w-2xl">
        <header className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold text-gray-800">Notaría 4 Digital Core</h1>
          <div className="text-sm text-gray-500">Manzanillo, Colima</div>
        </header>

        <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center hover:border-blue-500 transition-colors">
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            className="block w-full text-sm text-gray-500
              file:mr-4 file:py-2 file:px-4
              file:rounded-full file:border-0
              file:text-sm file:font-semibold
              file:bg-blue-50 file:text-blue-700
              hover:file:bg-blue-100"
          />
          <p className="mt-4 text-gray-600">Sube la escritura (PDF) para extracción automática</p>
        </div>

        <div className="mt-8">
          <h2 className="text-xl font-semibold mb-4">Estado del Sistema</h2>
          <div className="p-4 bg-gray-50 rounded border border-gray-200">
            <p className="font-mono text-sm">{status}</p>
          </div>
        </div>

        <button
          onClick={handleUpload}
          disabled={!file}
          className="mt-6 w-full bg-blue-600 text-white py-3 rounded-lg font-semibold disabled:opacity-50 hover:bg-blue-700 transition"
        >
          Iniciar Procesamiento (OCR + NLP)
        </button>
      </div>
    </div>
  )
}

export default App
