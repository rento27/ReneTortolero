import React, { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import { Search, Filter } from 'lucide-react';
import { supabase } from './lib/supabase.js';
import { ReservationCard } from './components/ReservationCard.js';
import { Stats } from './components/Stats.js';

// Dummy data for initial load / offline fallback
const DUMMY_DATA = [
    { id: 1, nombre: 'Juan Pérez', adultos: 4, ninos: 2, mesa: 'A1', monto_pagado: 5000, llego: false, notas: 'Alergia nueces' },
    { id: 2, nombre: 'Maria Garcia', adultos: 2, ninos: 0, mesa: 'B3', monto_pagado: 3800, llego: true, notas: '' },
    { id: 3, nombre: 'Carlos Slim', adultos: 10, ninos: 5, mesa: 'VIP1', monto_pagado: 10000, llego: false, notas: 'Champagne lista' },
    { id: 4, nombre: 'Ana Torre', adultos: 2, ninos: 1, mesa: 'C4', monto_pagado: 0, llego: false, notas: '' },
];

const App = () => {
    const [reservations, setReservations] = useState(DUMMY_DATA);
    const [filter, setFilter] = useState('all'); // all, pending_payment, arrived
    const [search, setSearch] = useState('');
    const [loading, setLoading] = useState(false); // Set to true when real data fetching is implemented

    useEffect(() => {
        // Real-time subscription setup
        // Note: This relies on Supabase being configured.
        // For this demo, we just log connection attempts.

        const fetchReservations = async () => {
            // Uncomment when connected to real DB
            // const { data, error } = await supabase.from('reservaciones').select('*');
            // if (data) setReservations(data);
        };

        fetchReservations();

        const channel = supabase
            .channel('public:reservaciones')
            .on('postgres_changes', { event: '*', schema: 'public', table: 'reservaciones' }, (payload) => {
                console.log('Change received!', payload);
                // Handle INSERT, UPDATE, DELETE logic here
                // Simple strategy: re-fetch or optimistically update
            })
            .subscribe();

        return () => {
            supabase.removeChannel(channel);
        };
    }, []);

    const handleCheckIn = async (id) => {
        // Optimistic update
        setReservations(prev => prev.map(r => r.id === id ? { ...r, llego: true } : r));

        // Supabase update
        // await supabase.from('reservaciones').update({ llego: true }).eq('id', id);
    };

    const filteredReservations = reservations.filter(r => {
        const matchesSearch = r.nombre.toLowerCase().includes(search.toLowerCase()) || r.mesa.toLowerCase().includes(search.toLowerCase());

        if (!matchesSearch) return false;

        if (filter === 'all') return true;
        if (filter === 'arrived') return r.llego;
        if (filter === 'pending_payment') {
             const totalDue = (r.adultos * 1900) + (r.ninos * 900);
             return r.monto_pagado < totalDue;
        }
        return true;
    });

    return React.createElement('div', { className: "pb-20" },
        // Top Stats
        React.createElement(Stats, { reservations: reservations }),

        // Search & Filter Bar
        React.createElement('div', { className: "p-4 space-y-3" },
            // Search
            React.createElement('div', { className: "relative" },
                React.createElement(Search, { className: "absolute left-3 top-3 text-gray-500", size: 20 }),
                React.createElement('input', {
                    type: "text",
                    placeholder: "Buscar por nombre o mesa...",
                    value: search,
                    onChange: (e) => setSearch(e.target.value),
                    className: "w-full bg-gray-900 border border-gray-700 rounded-lg py-3 pl-10 pr-4 text-white focus:outline-none focus:border-gold-400 transition-colors"
                })
            ),

            // Filters
            React.createElement('div', { className: "flex space-x-2 overflow-x-auto pb-2" },
                [
                    { id: 'all', label: 'Todos' },
                    { id: 'pending_payment', label: 'Falta Pago' },
                    { id: 'arrived', label: 'Ya llegaron' }
                ].map(f =>
                    React.createElement('button', {
                        key: f.id,
                        onClick: () => setFilter(f.id),
                        className: `px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${
                            filter === f.id
                            ? 'bg-gold-400 text-black'
                            : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                        }`
                    }, f.label)
                )
            )
        ),

        // List
        React.createElement('div', { className: "px-4" },
            filteredReservations.length > 0 ? filteredReservations.map(r =>
                React.createElement(ReservationCard, {
                    key: r.id,
                    reservation: r,
                    onCheckIn: handleCheckIn
                })
            ) : React.createElement('div', { className: "text-center py-10 text-gray-500" },
                "No se encontraron reservaciones."
            )
        )
    );
};

const root = createRoot(document.getElementById('root'));
root.render(React.createElement(App));
