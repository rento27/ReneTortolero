import React from 'react';
import { Users, AlertCircle } from 'lucide-react';

const ADULT_PRICE = 1900;
const CHILD_PRICE = 900;

export const Stats = ({ reservations }) => {
    const totalExpected = reservations.reduce((acc, curr) => acc + curr.adultos + curr.ninos, 0);
    const totalArrived = reservations.filter(r => r.llego).reduce((acc, curr) => acc + curr.adultos + curr.ninos, 0);

    // Calculate progress percentage
    const progress = totalExpected > 0 ? (totalArrived / totalExpected) * 100 : 0;

    return React.createElement('div', { className: "bg-gray-900 border-b border-gold-400 p-4 sticky top-0 z-10 shadow-xl" },
        React.createElement('div', { className: "flex justify-between items-center mb-2" },
            React.createElement('h1', { className: "text-gold-400 font-bold text-lg tracking-widest" }, "LASAL PLAYA"),
            React.createElement('div', { className: "text-xs text-gray-400" }, new Date().toLocaleDateString())
        ),

        React.createElement('div', { className: "grid grid-cols-2 gap-4" },
            React.createElement('div', { className: "flex flex-col" },
                React.createElement('span', { className: "text-gray-400 text-xs uppercase" }, "Asistencia"),
                React.createElement('div', { className: "flex items-baseline space-x-1" },
                    React.createElement('span', { className: "text-2xl font-bold text-white" }, totalArrived),
                    React.createElement('span', { className: "text-sm text-gray-500" }, `/ ${totalExpected}`)
                )
            ),
            React.createElement('div', { className: "flex flex-col items-end" },
                React.createElement('span', { className: "text-gray-400 text-xs uppercase" }, "Pendiente Cobro"),
                 // Simple sum of pending amounts across all reservations
                React.createElement('span', { className: "text-xl font-bold text-red-400" },
                    `$${reservations.reduce((acc, r) => {
                        const total = (r.adultos * ADULT_PRICE) + (r.ninos * CHILD_PRICE);
                        const due = total - r.monto_pagado;
                        return acc + (due > 0 ? due : 0);
                    }, 0).toLocaleString()}`
                )
            )
        ),

        // Progress bar
        React.createElement('div', { className: "w-full bg-gray-800 h-1.5 mt-3 rounded-full overflow-hidden" },
            React.createElement('div', {
                className: "bg-gold-400 h-full transition-all duration-500",
                style: { width: `${progress}%` }
            })
        )
    );
};
