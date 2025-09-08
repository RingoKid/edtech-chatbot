import { useState, useEffect } from 'react';
import logo from './logo.svg';
import './App.css';

function App() {
  // State variables - great places to set breakpoints!
  const [message, setMessage] = useState('Loading...');
  const [debugData, setDebugData] = useState(null);
  const [counter, setCounter] = useState(0);
  const [apiStatus, setApiStatus] = useState('unknown');

  // useEffect hook - excellent debugging spot for component lifecycle
  useEffect(() => {
    console.log('Component mounted - set breakpoint here!');
    checkApiHealth();
  }, []);

  // API call function - perfect for debugging HTTP requests
  const checkApiHealth = async () => {
    try {
      console.log('Checking API health...');
      const response = await fetch('http://localhost:8000/api/v1/health');
      const data = await response.json();
      
      // Set breakpoint here to inspect API response
      setApiStatus(data.status);
      setMessage('Backend API is connected!');
    } catch (error) {
      // Set breakpoint here to debug API errors
      console.error('API Error:', error);
      setApiStatus('error');
      setMessage('Backend API not available');
    }
  };

  // Event handler - great for debugging user interactions
  const handleCounterClick = () => {
    // Set breakpoint here to debug button clicks
    console.log('Button clicked! Current counter:', counter);
    setCounter(prevCounter => {
      const newCounter = prevCounter + 1;
      console.log('Counter updated to:', newCounter);
      return newCounter;
    });
  };

  // Debug API test function
  const testDebugEndpoint = async () => {
    try {
      console.log('Testing debug endpoint...');
      // Set breakpoint here to debug the debug endpoint call
      const response = await fetch('http://localhost:8000/api/v1/debug-test');
      const data = await response.json();
      
      // Set breakpoint here to inspect debug data
      console.log('Debug endpoint response:', data);
      setDebugData(data);
    } catch (error) {
      console.error('Debug endpoint error:', error);
      setDebugData({ error: 'Failed to call debug endpoint' });
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        
        {/* Status indicators - set breakpoints in render logic */}
        <div style={{ marginBottom: '20px' }}>
          <p>API Status: <span style={{ color: apiStatus === 'ok' ? 'green' : 'red' }}>
            {apiStatus}
          </span></p>
          <p>{message}</p>
        </div>

        {/* Interactive counter - great for debugging state changes */}
        <div style={{ marginBottom: '20px' }}>
          <h3>Counter: {counter}</h3>
          <button 
            onClick={handleCounterClick}
            style={{
              padding: '10px 20px',
              fontSize: '16px',
              backgroundColor: '#61dafb',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer'
            }}
          >
            Click me! (Set breakpoint in handler)
          </button>
        </div>

        {/* Debug API test button */}
        <div style={{ marginBottom: '20px' }}>
          <button 
            onClick={testDebugEndpoint}
            style={{
              padding: '10px 20px',
              fontSize: '16px',
              backgroundColor: '#ff6b6b',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer'
            }}
          >
            Test Backend Debug Endpoint
          </button>
        </div>

        {/* Debug data display */}
        {debugData && (
          <div style={{ 
            backgroundColor: 'rgba(255,255,255,0.1)', 
            padding: '15px', 
            borderRadius: '5px',
            maxWidth: '600px',
            textAlign: 'left'
          }}>
            <h4>Debug Response:</h4>
            <pre style={{ fontSize: '12px', overflow: 'auto' }}>
              {JSON.stringify(debugData, null, 2)}
            </pre>
          </div>
        )}

        <p style={{ marginTop: '20px', fontSize: '14px' }}>
          🎯 <strong>Frontend Debug Tips:</strong><br/>
          Set breakpoints in React DevTools or VS Code on the lines marked with console.log!
        </p>
      </header>
    </div>
  );
}

export default App;
