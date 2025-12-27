import React from 'react';
import { User, CheckCircle, Clock, DollarSign, Users, Table as TableIcon } from 'lucide-react';

const ADULT_PRICE = 1900;
const CHILD_PRICE = 900;

export const ReservationCard = ({ reservation, onCheckIn }) => {
    const totalDue = (reservation.adultos * ADULT_PRICE) + (reservation.ninos * CHILD_PRICE);
    const remaining = totalDue - reservation.monto_pagado;
    const isFullyPaid = remaining <= 0;

    return React.createElement('div', { className: `p-4 mb-4 rounded-xl border ${reservation.llego ? 'border-green-500 bg-gray-900' : 'border-gold-400 bg-gray-900'} shadow-lg relative` },
        // Header: Name and Table
        React.createElement('div', { className: "flex justify-between items-start mb-2" },
            React.createElement('h3', { className: "text-xl font-bold text-white truncate w-3/4" }, reservation.nombre),
            React.createElement('div', { className: "flex items-center space-x-1 bg-gold-400 text-black px-2 py-1 rounded-lg font-bold" },
                React.createElement(TableIcon, { size: 16 }),
                React.createElement('span', null, reservation.mesa)
            )
        ),

        // People Count
        React.createElement('div', { className: "flex space-x-4 mb-3 text-gray-300" },
            React.createElement('div', { className: "flex items-center space-x-1" },
                React.createElement(User, { size: 18 }),
                React.createElement('span', null, `${reservation.adultos} Adl`)
            ),
            reservation.ninos > 0 && React.createElement('div', { className: "flex items-center space-x-1" },
                React.createElement(Users, { size: 18, className: "text-sm" }),
                React.createElement('span', null, `${reservation.ninos} Niñ`)
            )
        ),

        // Financials
        React.createElement('div', { className: "bg-black/50 p-2 rounded-lg mb-3" },
            React.createElement('div', { className: "flex justify-between text-sm mb-1" },
                React.createElement('span', { className: "text-gray-400" }, "Total:"),
                React.createElement('span', { className: "font-semibold" }, `$${totalDue.toLocaleString()}`)
            ),
            React.createElement('div', { className: "flex justify-between text-sm mb-1" },
                React.createElement('span', { className: "text-gray-400" }, "Pagado:"),
                React.createElement('span', { className: "text-green-400" }, `$${reservation.monto_pagado.toLocaleString()}`)
            ),
            !isFullyPaid && React.createElement('div', { className: "flex justify-between text-base font-bold border-t border-gray-700 pt-1 mt-1" },
                React.createElement('span', { className: "text-red-400" }, "Falta:"),
                React.createElement('span', { className: "text-red-400" }, `$${remaining.toLocaleString()}`)
            )
        ),

        // Notes if any
        reservation.notas && React.createElement('div', { className: "text-xs text-gray-400 italic mb-3" },
            `Nota: ${reservation.notas}`
        ),

        // Action Button
        !reservation.llego ? React.createElement('button', {
            onClick: () => onCheckIn(reservation.id),
            className: "w-full py-3 bg-gold-400 hover:bg-gold-500 text-black font-bold rounded-lg flex items-center justify-center space-x-2 touch-action-manipulation transition-colors"
        },
            React.createElement(CheckCircle, { size: 20 }),
            React.createElement('span', null, "CHECK-IN (LLEGÓ)")
        ) : React.createElement('div', { className: "w-full py-2 bg-green-600/20 text-green-400 border border-green-600 rounded-lg flex items-center justify-center font-bold" },
            "YA EN MESA"
        )
    );
};
