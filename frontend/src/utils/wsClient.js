// Simple WebSocket client with reconnection/backoff and subscribe API
// Usage:
// const client = createWsClient(url);
// client.connect();
// client.subscribe(msg => ...);
// client.send({ message, thread_id });
// client.close();

function wait(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export function createWsClient(wsUrl, { maxRetries = 10, baseDelay = 500 } = {}) {
  let ws = null;
  let connected = false;
  let listeners = new Set();
  let retries = 0;
  let shouldReconnect = true;

  function notify(data) {
    listeners.forEach(cb => {
      try { cb(data); } catch (e) { console.error('ws listener error', e); }
    });
  }

  async function connect() {
    shouldReconnect = true;
    if (connected || ws) return;
    while (shouldReconnect && retries <= maxRetries) {
      try {
        ws = new WebSocket(wsUrl);
        ws.onopen = () => {
          connected = true;
          retries = 0;
          console.info('ws connected', wsUrl);
          notify({ type: 'open' });
        };

        ws.onmessage = (evt) => {
          let parsed = null;
          try { parsed = JSON.parse(evt.data); } catch (e) { parsed = evt.data; }
          notify({ type: 'message', data: parsed });
        };

        ws.onclose = (ev) => {
          connected = false;
          ws = null;
          notify({ type: 'close', event: ev });
          if (shouldReconnect) {
            retries += 1;
            const delay = Math.min(30000, baseDelay * Math.pow(2, retries));
            console.info(`ws reconnect in ${delay}ms (attempt ${retries})`);
            wait(delay).then(() => connect());
          }
        };

        ws.onerror = (err) => {
          console.error('ws error', err);
          notify({ type: 'error', error: err });
        };

        // Wait for open or error
        await new Promise((resolve, reject) => {
          const to = setTimeout(() => reject(new Error('ws connect timeout')), 10000);
          const onOpen = (e) => { clearTimeout(to); resolve(e); };
          const onClose = (e) => { clearTimeout(to); reject(e); };
          ws.addEventListener('open', onOpen, { once: true });
          ws.addEventListener('close', onClose, { once: true });
        });

        // connected - break out of reconnect loop
        break;
      } catch (err) {
        console.warn('ws connect attempt failed', err);
        retries += 1;
        const delay = Math.min(30000, baseDelay * Math.pow(2, retries));
        await wait(delay);
      }
    }
  }

  function send(obj) {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket not connected');
    }
    ws.send(JSON.stringify(obj));
  }

  function subscribe(cb) {
    listeners.add(cb);
    return () => { listeners.delete(cb); };
  }

  function close() {
    shouldReconnect = false;
    if (ws) {
      try { ws.close(); } catch (e) { /* ignore */ }
      ws = null;
    }
  }

  return { connect, send, subscribe, close, isConnected: () => connected };
}

export default createWsClient;
