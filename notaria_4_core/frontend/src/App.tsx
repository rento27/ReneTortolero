import { useState } from 'react'
import { Upload, FileText, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import { cn } from './lib/utils'
import logo from '../../assets/logo.jpg'

function App() {
  const [file, setFile] = useState<File | null>(null)
  const [status, setStatus] = useState<'idle' | 'uploading' | 'processing' | 'success' | 'error'>('idle')
  const [data, setData] = useState<any>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setStatus('idle')
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setStatus('uploading')

    // Simulate upload and processing
    setTimeout(() => {
        setStatus('processing')
        setTimeout(() => {
            setStatus('success')
            setData({
                escritura: "12345",
                cliente: "INMOBILIARIA DEL PACIFICO",
                monto: "$1,500,000.00"
            })
        }, 1500)
    }, 1000)
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-notaria-navy text-white p-4 shadow-lg">
        <div className="container mx-auto flex items-center justify-between">
            <div className="flex items-center space-x-4">
                <img src={logo} alt="Notaria 4 Logo" className="h-12 w-auto rounded bg-white p-1" />
                <div>
                    <h1 className="text-xl font-bold font-serif">Notaría Pública No. 4</h1>
                    <p className="text-xs text-notaria-gold uppercase tracking-wider">Manzanillo, Colima • Lic. René M. Tortolero</p>
                </div>
            </div>
            <div className="text-sm font-medium bg-notaria-gold text-notaria-navy px-3 py-1 rounded-full">
                Digital Core v1.0
            </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-grow container mx-auto p-8">
        <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-8">

            {/* Upload Section */}
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                <h2 className="text-lg font-semibold mb-4 text-gray-800 flex items-center">
                    <Upload className="w-5 h-5 mr-2 text-notaria-navy" />
                    Cargar Escritura (PDF)
                </h2>

                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-notaria-gold transition-colors">
                    <input
                        type="file"
                        accept=".pdf"
                        onChange={handleFileChange}
                        className="hidden"
                        id="file-upload"
                    />
                    <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center">
                        <FileText className="w-12 h-12 text-gray-400 mb-2" />
                        <span className="text-sm text-gray-600 font-medium">Click para seleccionar PDF</span>
                        <span className="text-xs text-gray-400 mt-1">Soporta texto digital y escaneado (OCR)</span>
                    </label>
                </div>

                {file && (
                    <div className="mt-4 p-3 bg-blue-50 rounded-lg flex items-center justify-between">
                        <span className="text-sm text-blue-800 font-medium truncate max-w-[200px]">{file.name}</span>
                        <button
                            onClick={handleUpload}
                            disabled={status !== 'idle'}
                            className={cn(
                                "px-4 py-2 rounded-lg text-sm font-bold transition-all",
                                status === 'idle'
                                    ? "bg-notaria-navy text-white hover:bg-blue-900"
                                    : "bg-gray-200 text-gray-500 cursor-not-allowed"
                            )}
                        >
                            {status === 'uploading' ? 'Subiendo...' :
                             status === 'processing' ? 'Procesando...' :
                             status === 'success' ? 'Procesado' : 'Procesar'}
                        </button>
                    </div>
                )}
            </div>

            {/* Results Section */}
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 relative overflow-hidden">
                <h2 className="text-lg font-semibold mb-4 text-gray-800 flex items-center">
                    <CheckCircle className="w-5 h-5 mr-2 text-green-600" />
                    Validación Fiscal
                </h2>

                {status === 'processing' && (
                    <div className="absolute inset-0 bg-white/80 flex flex-col items-center justify-center z-10">
                        <Loader2 className="w-10 h-10 text-notaria-navy animate-spin mb-2" />
                        <p className="text-sm text-gray-600 font-medium">Analizando con spaCy & Tesseract...</p>
                    </div>
                )}

                {status === 'success' && data ? (
                    <div className="space-y-4">
                        <div className="p-4 bg-green-50 rounded-lg border border-green-100">
                            <p className="text-xs text-green-600 uppercase font-bold tracking-wider mb-1">Estatus</p>
                            <div className="flex items-center text-green-800 font-medium">
                                <CheckCircle className="w-4 h-4 mr-2" />
                                Datos Extraídos Correctamente
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-xs text-gray-500 mb-1">Escritura No.</label>
                                <input readOnly value={data.escritura} className="w-full bg-gray-50 border border-gray-200 rounded p-2 text-sm font-mono" />
                            </div>
                            <div>
                                <label className="block text-xs text-gray-500 mb-1">Monto Operación</label>
                                <input readOnly value={data.monto} className="w-full bg-gray-50 border border-gray-200 rounded p-2 text-sm font-bold text-gray-800" />
                            </div>
                        </div>

                        <div>
                            <label className="block text-xs text-gray-500 mb-1">Receptor (Sanitizado)</label>
                            <input readOnly value={data.cliente} className="w-full bg-gray-50 border border-gray-200 rounded p-2 text-sm" />
                            <p className="text-[10px] text-orange-500 mt-1 flex items-center">
                                <AlertCircle className="w-3 h-3 mr-1" />
                                Se eliminó "S.A. DE C.V." automáticamente.
                            </p>
                        </div>
                    </div>
                ) : (
                    <div className="h-full flex flex-col items-center justify-center text-gray-400 opacity-50">
                        <FileText className="w-16 h-16 mb-4" />
                        <p className="text-sm">Esperando documento...</p>
                    </div>
                )}
            </div>

        </div>
      </main>
    </div>
  )
}

export default App
