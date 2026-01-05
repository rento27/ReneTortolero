// Removed unused React import
import './index.css';

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-notaria-navy text-white p-4 shadow-lg">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-serif font-bold">Notaría 4 Digital Core</h1>
          <div className="text-notaria-gold text-sm font-semibold">Soberanía Tecnológica</div>
        </div>
      </header>

      <main className="container mx-auto p-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Section 1: Dashboard */}
          <section className="bg-white p-6 rounded-lg shadow-md border-t-4 border-notaria-gold">
            <h2 className="text-xl font-bold text-notaria-navy mb-4">Gestión Fiscal</h2>
            <div className="space-y-4">
              <button className="w-full bg-notaria-navy text-white py-2 px-4 rounded hover:bg-opacity-90 transition">
                Nueva Factura (CFDI 4.0)
              </button>
              <button className="w-full border border-notaria-navy text-notaria-navy py-2 px-4 rounded hover:bg-gray-50 transition">
                Consultar Expedientes
              </button>
            </div>
          </section>

          {/* Section 2: Upload & Extraction */}
          <section className="bg-white p-6 rounded-lg shadow-md border-t-4 border-notaria-navy">
            <h2 className="text-xl font-bold text-notaria-navy mb-4">Inteligencia Artificial</h2>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:bg-gray-50 cursor-pointer">
              <p className="text-gray-500">Arrastra tu escritura (PDF) aquí para extracción automática</p>
              <p className="text-xs text-gray-400 mt-2">Soporta OCR y Análisis NLP</p>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}

export default App;
