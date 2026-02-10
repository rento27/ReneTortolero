import React from 'react';
import { FileText, AlertCircle, CheckCircle } from 'lucide-react';

export const ValidationPage: React.FC = () => {
  return (
    <div className="flex h-[calc(100vh-80px)]">
      {/* Left Panel: PDF Viewer Stub */}
      <div className="w-1/2 bg-slate-200 border-r border-slate-300 p-4 flex flex-col">
        <div className="bg-white rounded-t-lg p-2 border-b border-slate-200 flex justify-between items-center">
          <h2 className="font-semibold text-slate-700 flex items-center gap-2">
            <FileText size={18} />
            Escritura 23674.pdf
          </h2>
          <span className="text-xs text-slate-500">Página 1 de 45</span>
        </div>
        <div className="flex-1 bg-slate-100 flex items-center justify-center border border-slate-300 rounded-b-lg overflow-hidden relative">
          {/* Placeholder for PDF rendering */}
          <div className="text-center p-8">
            <p className="text-slate-400 mb-2">Visor de PDF</p>
            <div className="w-64 h-80 bg-white shadow-lg mx-auto border border-slate-200 p-8 text-xs text-justify text-slate-300 select-none">
              Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
              <br/><br/>
              <span className="bg-yellow-200 text-slate-800 px-1">Precio de Operación: $1,500,000.00</span>
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel: Validation Form */}
      <div className="w-1/2 bg-white p-6 overflow-y-auto">
        <div className="mb-6 flex justify-between items-center">
          <h2 className="text-2xl font-serif text-notaria-navy font-bold">Validación Fiscal</h2>
          <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded border border-blue-200">
            Estatus: Borrador
          </span>
        </div>

        <form className="space-y-6">
          {/* Receptor Section */}
          <section className="space-y-4">
            <h3 className="text-lg font-semibold text-slate-700 border-b pb-2">Receptor</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-600">RFC</label>
                <input type="text" className="mt-1 block w-full rounded-md border-slate-300 shadow-sm focus:border-notaria-navy focus:ring focus:ring-notaria-navy focus:ring-opacity-50 border p-2" defaultValue="ISP880920K20" />
                <p className="text-xs text-green-600 mt-1 flex items-center gap-1"><CheckCircle size={12}/> Válido (Persona Moral)</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-600">Razón Social</label>
                <input type="text" className="mt-1 block w-full rounded-md border-slate-300 shadow-sm border p-2" defaultValue="INMOBILIARIA DEL SUR DEL PACIFICO" />
                <p className="text-xs text-orange-500 mt-1 flex items-center gap-1"><AlertCircle size={12}/> Sufijo "S.A. DE C.V." eliminado automáticamente</p>
              </div>
            </div>
          </section>

          {/* Totals Section with Auto-Calc */}
          <section className="space-y-4 bg-slate-50 p-4 rounded-lg border border-slate-200">
            <h3 className="text-lg font-semibold text-slate-700">Cálculo</h3>

            <div className="flex justify-between items-center text-sm">
              <span className="text-slate-600">Subtotal Honorarios:</span>
              <span className="font-mono">$ 15,000.00</span>
            </div>

            <div className="flex justify-between items-center text-sm">
              <span className="text-slate-600">IVA (16%):</span>
              <span className="font-mono">$ 2,400.00</span>
            </div>

            <div className="border-t border-slate-200 my-2 pt-2">
              <div className="flex justify-between items-center text-sm text-red-600">
                <span className="flex items-center gap-1"><AlertCircle size={14}/> Retención ISR (10%):</span>
                <span className="font-mono">- $ 1,500.00</span>
              </div>
              <div className="flex justify-between items-center text-sm text-red-600">
                <span className="flex items-center gap-1"><AlertCircle size={14}/> Retención IVA (10.6667%):</span>
                <span className="font-mono">- $ 1,600.00</span>
              </div>
            </div>

            <div className="flex justify-between items-center font-bold text-lg pt-2 border-t border-slate-300 text-notaria-navy">
              <span>Total a Pagar:</span>
              <span>$ 14,300.00</span>
            </div>
          </section>

          <div className="pt-4 flex gap-3">
             <button type="button" className="flex-1 bg-notaria-navy text-white py-2 px-4 rounded hover:bg-opacity-90 transition shadow-lg">
               Validar y Timbrar
             </button>
             <button type="button" className="bg-white border border-slate-300 text-slate-600 py-2 px-4 rounded hover:bg-slate-50 transition">
               Guardar Borrador
             </button>
          </div>
        </form>
      </div>
    </div>
  );
};
