import React from 'react';
import logo from '../assets/notaria_logo.jpg';

export const Header: React.FC = () => {
  return (
    <header className="bg-notaria-navy text-white shadow-md">
      <div className="container mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <img src={logo} alt="Notaría 4 Logo" className="h-12 w-12 rounded-full object-cover border-2 border-notaria-gold" />
          <div>
            <h1 className="text-xl font-serif font-bold tracking-wide text-notaria-gold">NOTARÍA 4 DIGITAL CORE</h1>
            <p className="text-xs text-slate-300">Lic. René Manuel Tortolero Santillana</p>
          </div>
        </div>
        <div className="text-sm">
          <span className="px-3 py-1 bg-notaria-gold text-notaria-navy font-bold rounded-full">
            Manzanillo, Colima
          </span>
        </div>
      </div>
    </header>
  );
};
