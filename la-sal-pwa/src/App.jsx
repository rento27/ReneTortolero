import React, { useState, useEffect } from 'react';
import { createClient } from '@supabase/supabase-js';
import {
  Users, Clock, DollarSign, MapPin, Sparkles,
  ChefHat, Music, Wine, Utensils, Baby, AlertCircle, CheckCircle, Search, Filter
} from 'lucide-react';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

const PRICE_ADULT = 1900;
const PRICE_KID = 900;

export default function App() {
  const [reservations, setReservations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all'); // all, pending_payment, arrived

  useEffect(() => {
    fetchReservations();
    const channel = supabase
      .channel('schema-db-changes')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'reservaciones' }, () => fetchReservations())
      .subscribe();
    return () => supabase.removeChannel(channel);
  }, []);

  async function fetchReservations() {
    // If connected to real DB, this works. For now, if empty, we can seed dummy data?
    // But user provided code assumes real DB. I will keep it as is.
    const { data } = await supabase.from('reservaciones').select('*').order('created_at', { ascending: false });
    if (data) setReservations(data);
    setLoading(false);
  }

  const handleCheckIn = async (id) => {
    // Optimistic update
    setReservations(prev => prev.map(r => r.id === id ? { ...r, llego: true } : r));
    await supabase.from('reservaciones').update({ llego: true }).eq('id', id);
  };

  const filteredReservations = reservations.filter(r => {
    const matchesSearch = (r.nombre || '').toLowerCase().includes(search.toLowerCase()) || (r.mesa || '').toLowerCase().includes(search.toLowerCase());
    if (!matchesSearch) return false;

    if (filter === 'all') return true;
    if (filter === 'arrived') return r.llego;
    if (filter === 'pending_payment') {
         const totalDue = (r.adultos * PRICE_ADULT) + (r.ninos * PRICE_KID);
         return r.monto_pagado < totalDue;
    }
    return true;
  });

  const formatCurr = (n) => new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(n);

  // Cálculos Globales
  const totalAdults = reservations.reduce((acc, r) => acc + (r.adultos || 0), 0);
  const totalKids = reservations.reduce((acc, r) => acc + (r.ninos || 0), 0);
  const totalRecaudado = reservations.reduce((acc, r) => acc + (r.monto_pagado || 0), 0);
  const totalEventValue = reservations.reduce((acc, r) => acc + (r.adultos * PRICE_ADULT) + (r.ninos * PRICE_KID), 0);
  const totalFalta = totalEventValue - totalRecaudado;

  return (
    <div className="min-h-screen bg-[#F8F9FA] font-sans pb-20">

      {/* HEADER / LOGO SECTION */}
      <header className="pt-12 pb-8 px-4 text-center bg-white border-b border-slate-100">
        <div className="flex justify-center mb-4">
          <div className="w-24 h-24 rounded-full border border-slate-200 flex items-center justify-center p-4 relative">
             <img src="https://cdn-icons-png.flaticon.com/512/3655/3655682.png" className="w-10 opacity-20 absolute" alt="" />
             <span className="text-xs font-serif font-light leading-tight">laSal playa</span>
          </div>
        </div>
        <h1 className="text-6xl font-serif tracking-tighter mb-1">la<span className="font-bold text-[#EAB308]">Sal</span></h1>
        <p className="text-[10px] tracking-[0.6em] uppercase text-slate-400 mb-8">P L A Y A</p>

        <p className="text-slate-400 text-xs uppercase tracking-[0.3em] mb-2">BIENVENIDO 2026</p>
        <h2 className="text-4xl font-serif italic text-slate-800 mb-6">Fiesta de Año Nuevo</h2>

        <div className="flex justify-center gap-3">
          <span className="bg-white border border-slate-100 px-4 py-1.5 rounded-full text-[10px] font-bold text-slate-500 flex items-center gap-2 shadow-sm">
            <Music size={12} className="text-amber-500" /> DJ Bob
          </span>
          <span className="bg-white border border-slate-100 px-4 py-1.5 rounded-full text-[10px] font-bold text-slate-500 flex items-center gap-2 shadow-sm">
            <Wine size={12} className="text-amber-500" /> Kit de Celebración
          </span>
        </div>
      </header>

      {/* MENU & INFO SECTION */}
      <div className="max-w-6xl mx-auto p-4 md:p-8">
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden flex flex-col md:row flex-wrap lg:flex-nowrap">
          {/* Menú */}
          <div className="p-8 flex-1 border-b md:border-b-0 md:border-r border-slate-100">
            <h3 className="flex items-center gap-3 text-lg font-bold text-slate-800 mb-6">
              <ChefHat size={20} className="text-amber-500" /> Menú Degustación
            </h3>
            <div className="space-y-6">
              <div>
                <p className="text-[10px] font-black text-amber-500 uppercase tracking-widest mb-1">Entrada</p>
                <p className="text-sm font-bold text-slate-800">Amouse bouche: <span className="font-normal text-slate-600 uppercase text-xs tracking-tight">Crema de langosta en pan de hogaza, manzana con trufa negra.</span></p>
                <p className="text-[10px] italic text-slate-400 mt-1">o Lechuga asada, frutos secos, queso azul y panal de miel.</p>
              </div>
              <div>
                <p className="text-[10px] font-black text-amber-500 uppercase tracking-widest mb-2">Plato Fuerte</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                    <p className="text-xs font-bold mb-1 uppercase">Tierra</p>
                    <p className="text-[11px] text-slate-500 leading-relaxed">Short rib y gratin de papa con salsa de frutos rojos y setas.</p>
                  </div>
                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                    <p className="text-xs font-bold mb-1 uppercase">Mar</p>
                    <p className="text-[11px] text-slate-500 leading-relaxed">Pescado al vapor con uvas, alcachofas y salsa de mejillones.</p>
                  </div>
                </div>
              </div>
              <div>
                <p className="text-[10px] font-black text-amber-500 uppercase tracking-widest mb-1">Postre</p>
                <p className="text-xs text-slate-600 font-medium">Tarta de queso con salsa de frutos rojos y helado de yogurt.</p>
              </div>
            </div>
          </div>

          {/* Lateral Info */}
          <div className="p-8 w-full lg:w-80 bg-slate-50/50 space-y-8">
            <div>
              <h4 className="flex items-center gap-2 text-xs font-bold text-slate-800 mb-3 uppercase">
                <DollarSign size={14} className="text-amber-500" /> Precios
              </h4>
              <div className="space-y-2">
                <div className="bg-white p-3 rounded-lg border border-slate-200 flex justify-between items-center shadow-sm">
                  <span className="text-xs text-slate-500">Adultos</span>
                  <span className="text-xs font-black tracking-tight">$1,900</span>
                </div>
                <div className="bg-white p-3 rounded-lg border border-slate-200 flex justify-between items-center shadow-sm">
                  <span className="text-xs text-slate-500">Niños</span>
                  <span className="text-xs font-black tracking-tight">$900</span>
                </div>
              </div>
            </div>
            <div>
              <h4 className="flex items-center gap-2 text-xs font-bold text-slate-800 mb-2 uppercase">
                <MapPin size={14} className="text-amber-500" /> Ubicación
              </h4>
              <p className="text-[10px] leading-relaxed text-slate-500">
                Av. Lázaro Cárdenas #797<br/>
                Col. Las brisas (frente al estadio)
              </p>
            </div>
            <button className="w-full bg-[#222] text-white py-4 rounded-xl font-bold text-[10px] uppercase tracking-widest flex items-center justify-center gap-2 hover:bg-black transition-all shadow-lg">
              <Sparkles size={14} /> Agregar Nueva Reserva
            </button>
          </div>
        </div>
      </div>

      {/* STATS BAR */}
      <div className="max-w-7xl mx-auto px-4 grid grid-cols-2 md:grid-cols-5 gap-3 mb-10">
        {[
          { label: 'Total', value: totalAdults + totalKids, color: 'border-blue-500', icon: <Utensils size={14}/> },
          { label: 'Adultos', value: totalAdults, color: 'border-amber-400', icon: <Users size={14}/> },
          { label: 'Niños', value: totalKids, color: 'border-purple-400', icon: <Baby size={14}/> },
          { label: 'Recaudado', value: formatCurr(totalRecaudado), color: 'border-emerald-500', icon: <DollarSign size={14}/>, valColor: 'text-emerald-500' },
          { label: 'Falta', value: formatCurr(totalFalta), color: 'border-rose-500', icon: <AlertCircle size={14}/>, valColor: 'text-rose-500' },
        ].map((stat, i) => (
          <div key={i} className={`bg-white p-5 rounded-xl border-l-[3px] shadow-sm ${stat.color} flex flex-col justify-center`}>
            <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1 flex items-center gap-2">{stat.icon} {stat.label}</p>
            <p className={`text-xl font-black tracking-tighter ${stat.valColor || 'text-slate-800'}`}>{stat.value}</p>
          </div>
        ))}
      </div>

      {/* SEARCH & FILTERS */}
      <div className="max-w-7xl mx-auto px-4 mb-6">
        <div className="flex flex-col md:flex-row gap-4 justify-between items-center bg-white p-4 rounded-xl shadow-sm border border-slate-100">
           {/* Search */}
           <div className="relative w-full md:w-96">
                <Search className="absolute left-3 top-3 text-slate-400" size={18} />
                <input
                    type="text"
                    placeholder="Buscar por nombre o mesa..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg py-2.5 pl-10 pr-4 text-sm focus:outline-none focus:border-amber-400 transition-colors"
                />
            </div>

            {/* Filters */}
            <div className="flex gap-2 w-full md:w-auto overflow-x-auto">
                {[
                    { id: 'all', label: 'Todos' },
                    { id: 'pending_payment', label: 'Falta Pago' },
                    { id: 'arrived', label: 'Ya llegaron' }
                ].map(f => (
                    <button
                        key={f.id}
                        onClick={() => setFilter(f.id)}
                        className={`px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-colors whitespace-nowrap ${
                            filter === f.id
                            ? 'bg-amber-400 text-black shadow-md'
                            : 'bg-slate-50 text-slate-500 hover:bg-slate-100'
                        }`}
                    >
                        {f.label}
                    </button>
                ))}
            </div>
        </div>
      </div>

      {/* LISTADO DE ASISTENTES */}
      <div className="max-w-7xl mx-auto px-4">
        <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.3em] mb-6">Listado de Asistentes ({filteredReservations.length})</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredReservations.length === 0 && (
             <div className="col-span-full text-center py-10 text-slate-400 text-sm">No se encontraron reservaciones.</div>
          )}
          {filteredReservations.map((res) => {
            const totalMesa = (res.adultos * PRICE_ADULT) + (res.ninos * PRICE_KID);
            const faltaMesa = totalMesa - res.monto_pagado;

            return (
              <div key={res.id} className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden relative">
                <div className="h-1.5 w-full bg-amber-400/20 absolute top-0"></div>
                <div className="p-6">
                  <div className="flex justify-between items-start mb-6">
                    <div>
                      <h4 className="text-lg font-bold text-slate-800">{res.nombre}</h4>
                      <div className="flex items-center gap-1 text-[10px] text-slate-400 mt-1">
                        <Clock size={10} /> {res.hora || '8:00pm'}
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3 mb-6">
                    <div className="flex justify-between items-center text-xs">
                      <span className="flex items-center gap-2 text-slate-500"><Users size={14} className="text-slate-300"/> {res.adultos} Adultos</span>
                      <span className="font-mono text-slate-400 tracking-tighter">${(res.adultos * PRICE_ADULT).toLocaleString()}</span>
                    </div>
                    {res.ninos > 0 && (
                      <div className="flex justify-between items-center text-xs">
                        <span className="flex items-center gap-2 text-slate-500"><Baby size={14} className="text-purple-300"/> {res.ninos} Niños</span>
                        <span className="font-mono text-slate-400 tracking-tighter">${(res.ninos * PRICE_KID).toLocaleString()}</span>
                      </div>
                    )}
                    <div className="flex justify-between items-center pt-2 border-t border-slate-50 font-black uppercase text-[10px] tracking-widest text-slate-800">
                      <span>Total Mesa</span>
                      <span>${totalMesa.toLocaleString()}</span>
                    </div>
                  </div>

                  <div className="flex justify-between items-end border-t border-slate-100 pt-5 mt-4">
                    {/* Check In Button */}
                    {!res.llego ? (
                        <button
                            onClick={() => handleCheckIn(res.id)}
                            className="bg-slate-800 text-white px-4 py-2 rounded-lg text-[10px] font-bold uppercase tracking-widest hover:bg-black transition-all shadow-lg flex items-center gap-2"
                        >
                            <CheckCircle size={14} className="text-emerald-400"/> Check-in
                        </button>
                    ) : (
                        <div className="bg-emerald-50 text-emerald-700 px-4 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest flex items-center gap-2 border border-emerald-100">
                            <CheckCircle size={14} /> Ya en Mesa
                        </div>
                    )}

                    <div className="text-right space-y-1">
                      <div className="bg-emerald-50 px-3 py-2 rounded-lg border border-emerald-100 min-w-[100px]">
                        <p className="text-[8px] font-black text-emerald-600 uppercase mb-0.5">Pagado</p>
                        <p className="text-sm font-black text-emerald-600 tracking-tighter">${res.monto_pagado.toLocaleString()}.00</p>
                      </div>
                      {faltaMesa > 0 && (
                        <div className="bg-orange-50 px-3 py-2 rounded-lg border border-orange-100 min-w-[100px]">
                          <p className="text-[8px] font-black text-amber-600 uppercase mb-0.5">Falta</p>
                          <p className="text-sm font-black text-rose-600 tracking-tighter">${faltaMesa.toLocaleString()}.00</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
