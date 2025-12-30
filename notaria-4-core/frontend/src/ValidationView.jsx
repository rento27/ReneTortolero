import React, { useState } from 'react';

function ValidationView() {
  const [rfc, setRfc] = useState('');
  const [subtotal, setSubtotal] = useState(0);
  const [result, setResult] = useState(null);

  const validate = async () => {
    // This would call the backend API in a real scenario
    // For now, we simulate the fetch or use a placeholder
    console.log("Validating RFC:", rfc);

    // Simulating backend response for demo purposes (matching the Python logic)
    let retentions = null;
    if (rfc.length === 12) {
       const base = parseFloat(subtotal);
       const isr = base * 0.10;
       const iva_trasladado = base * 0.16;
       const iva_ret = (iva_trasladado * 2) / 3;

       retentions = {
         isr: isr.toFixed(2),
         iva_ret: iva_ret.toFixed(2),
         total: (isr + iva_ret).toFixed(2)
       };
    }

    setResult(retentions);
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial' }}>
      <h2>Validación Fiscal - Notaría 4</h2>
      <div style={{ display: 'flex', gap: '20px' }}>
        <div style={{ flex: 1, border: '1px solid #ccc', padding: '10px' }}>
          <h3>Visor de Escritura (PDF)</h3>
          <p>Placeholder for PDF Viewer</p>
        </div>
        <div style={{ flex: 1, border: '1px solid #ccc', padding: '10px' }}>
          <h3>Datos Fiscales</h3>
          <label>RFC Receptor: </label>
          <input
            type="text"
            value={rfc}
            onChange={(e) => setRfc(e.target.value.toUpperCase())}
            placeholder="RFC"
          />
          <br /><br />
          <label>Subtotal: </label>
          <input
            type="number"
            value={subtotal}
            onChange={(e) => setSubtotal(e.target.value)}
          />
          <br /><br />
          <button onClick={validate}>Validar Retenciones</button>

          {result && (
            <div style={{ marginTop: '20px', padding: '10px', backgroundColor: '#f0f0f0' }}>
              <h4>Cálculo de Retenciones (Persona Moral)</h4>
              <p>ISR (10%): ${result.isr}</p>
              <p>IVA Retenido (2/3): ${result.iva_ret}</p>
              <p><strong>Total Retenido: ${result.total}</strong></p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ValidationView;
