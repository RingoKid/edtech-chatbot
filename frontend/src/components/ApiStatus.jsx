import React, { useEffect, useState } from 'react';
import { health, chat } from '../api';

export default function ApiStatus() {
  const [status, setStatus] = useState({ health: null, debug: null, chat: null, error: null });

  useEffect(() => {
    let mounted = true;

    async function fetchAll() {
      const results = await Promise.allSettled([health.get(), health.debug(), chat.status()]);
      if (!mounted) return;
      const [h, d, c] = results;
      let error = null;
      if (h.status === 'rejected' || d.status === 'rejected' || c.status === 'rejected') {
        const errors = [h, d, c].map((r, i) =>
          r.status === 'rejected'
            ? ['Health', 'Debug', 'Chat'][i] + ': ' + (r.reason?.message || r.reason || 'Network error')
            : null
        ).filter(Boolean);
        error = errors.join('; ');
      }
      setStatus({
        health: h.status === 'fulfilled' ? h.value : null,
        debug: d.status === 'fulfilled' ? d.value : null,
        chat: c.status === 'fulfilled' ? c.value : null,
        error,
      });
    }

    fetchAll();
    const id = setInterval(fetchAll, 10_000);
    return () => { mounted = false; clearInterval(id); };
  }, []);

  return (
    <div className="fixed bottom-4 right-4 z-50 max-w-sm bg-white/90 border rounded p-3 shadow-lg text-sm">
      <div className="font-semibold mb-2">API Status</div>
      <div className="flex gap-2 items-center mb-1">
        <span className="font-medium">Health:</span>
        <span className={`px-2 py-0.5 rounded text-xs ${status.health?.status === 'ok' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
          {status.health?.status ?? 'unknown'}
        </span>
      </div>

      <div className="flex gap-2 items-center mb-1">
        <span className="font-medium">Debug:</span>
        <span className="text-xs">{status.debug?.status ?? 'n/a'}</span>
      </div>

      <div className="flex gap-2 items-center mb-1">
        <span className="font-medium">Chat:</span>
        <span className="text-xs">{status.chat?.status ?? 'unknown'}</span>
      </div>

      {status.error && <div className="text-red-600 text-xs mt-2">Error: {status.error}</div>}
      <div className="text-xs text-gray-500 mt-2">Auto-refresh every 10s</div>
    </div>
  );
}
