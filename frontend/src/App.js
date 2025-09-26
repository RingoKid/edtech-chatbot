import { useState } from 'react';
import logo from './logo.svg';
import './App.css';

function App() {
  const [healthStatus, setHealthStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleHealthCheck = async () => {
    setLoading(true);
    setError(null);
    setHealthStatus(null);

    try {
      const response = await fetch('https://mkbifgscip.us-east-1.awsapprunner.com//api/v1/health');

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setHealthStatus(data);
    } catch (error) {
      console.error('Health check failed:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        
        <button
          onClick={handleHealthCheck}
          disabled={loading}
          style={{
            padding: '12px 24px',
            fontSize: '16px',
            fontWeight: '600',
            backgroundColor: loading ? '#ccc' : '#61dafb',
            color: '#282c34',
            border: 'none',
            borderRadius: '8px',
            cursor: loading ? 'not-allowed' : 'pointer',
            transition: 'all 0.3s ease',
            boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
            marginBottom: '20px'
          }}
          onMouseOver={(e) => {
            if (!loading) {
              e.target.style.backgroundColor = '#4fa8c5';
              e.target.style.transform = 'translateY(-2px)';
              e.target.style.boxShadow = '0 4px 8px rgba(0,0,0,0.3)';
            }
          }}
          onMouseOut={(e) => {
            if (!loading) {
              e.target.style.backgroundColor = '#61dafb';
              e.target.style.transform = 'translateY(0)';
              e.target.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
            }
          }}
        >
          {loading ? 'Checking...' : 'Check API Health'}
        </button>

        {error && (
          <div style={{ color: '#ff6b6b', marginBottom: '20px' }}>
            Error: {error}
          </div>
        )}

        {healthStatus && (
          <pre style={{
            backgroundColor: 'rgba(255,255,255,0.1)',
            padding: '15px',
            borderRadius: '8px',
            textAlign: 'left',
            maxWidth: '400px'
          }}>
            {JSON.stringify(healthStatus, null, 2)}
          </pre>
        )}
      </header>
    </div>
  );
}

export default App;
