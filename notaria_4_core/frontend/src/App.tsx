import { FileText, Shield, DollarSign } from 'lucide-react';

function App() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
      <header className="bg-brand-navy w-full p-4 text-white text-center shadow-md">
        <h1 className="text-2xl font-serif">Notaría Pública No. 4</h1>
        <p className="text-sm text-brand-gold">Manzanillo, Colima - Lic. René Manuel Tortolero Santillana</p>
      </header>

      <main className="w-full max-w-4xl p-6 grid gap-6">
        <div className="bg-white p-6 rounded-lg shadow-lg border-l-4 border-brand-gold">
          <h2 className="text-xl font-bold flex items-center gap-2 mb-4">
            <Shield className="text-brand-navy" />
            Digital Core Sovereignty
          </h2>
          <p className="text-gray-600 mb-4">
            Sistema propietario de gestión notarial. Validación estricta CFDI 4.0 y cálculo automatizado de ISAI Manzanillo.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button className="bg-brand-navy text-white px-4 py-2 rounded hover:bg-opacity-90 flex items-center justify-center gap-2">
              <FileText size={18} />
              Generar Escritura
            </button>
            <button className="border border-brand-navy text-brand-navy px-4 py-2 rounded hover:bg-gray-50 flex items-center justify-center gap-2">
               <DollarSign size={18} />
               Cálculo Fiscal
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
