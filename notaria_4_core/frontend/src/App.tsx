import React, { useState } from 'react';

function App() {
  const [rfc, setRfc] = useState('');
  const [subtotal, setSubtotal] = useState(0);
  const [result, setResult] = useState<any>(null);

  const calculateFiscal = async () => {
    try {
      const response = await fetch('/api/calculate-fiscal', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          rfc_receptor: rfc,
          subtotal: subtotal,
          is_persona_moral: rfc.length === 12
        }),
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error("Error calculating fiscal", error);
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial' }}>
      <h1>Notaría 4 Digital Core</h1>
      <div style={{ marginBottom: '20px', border: '1px solid #ccc', padding: '10px' }}>
        <h2>Calculadora Fiscal Rápida</h2>
        <div>
          <label>RFC Receptor: </label>
          <input
            type="text"
            value={rfc}
            onChange={(e) => setRfc(e.target.value)}
            placeholder="XAXX010101000"
          />
        </div>
        <div>
          <label>Subtotal: </label>
          <input
            type="number"
            value={subtotal}
            onChange={(e) => setSubtotal(Number(e.target.value))}
          />
        </div>
        <button onClick={calculateFiscal} style={{ marginTop: '10px' }}>Calcular Impuestos</button>
      </div>

      {result && (
        <div style={{ backgroundColor: '#f0f0f0', padding: '15px' }}>
          <h3>Resultado:</h3>
          <p>Subtotal: ${result.subtotal}</p>
          <p>IVA Trasladado (16%): ${result.iva_trasladado}</p>
          <p>Retención ISR: -${result.retenciones.isr_retention}</p>
          <p>Retención IVA: -${result.retenciones.iva_retention}</p>
          <hr/>
          <strong>Total Neto: ${result.total}</strong>
        </div>
      )}
    </div>
  );
}

export default App;
