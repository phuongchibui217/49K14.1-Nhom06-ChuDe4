/**
 * Notification Badge: Khiếu nại mới chưa xử lý
 *
 * Hiển thị số lượng khiếu nại có status='NEW'
 * Auto-update real-time qua SSE stream (polling fallback nếu SSE lỗi)
 */
(function () {
    const config = window.adminSidebarComplaintsBadgeConfig;
    if (!config) return;

    const dom = {
        badge: document.getElementById('adminSidebarComplaintsBadge'),
    };
    if (!dom.badge) return;

    const state = {
        stream: null,
        reconnectTimer: null,
        pollingTimer: null,
        usePolling: false,
        reconnectAttempts: 0,
        maxReconnectAttempts: 3,
    };

    function normalizeCount(value) {
        const count = Number(value);
        return Number.isFinite(count) && count > 0 ? Math.floor(count) : 0;
    }

    function renderBadge(count) {
        const n = normalizeCount(count);
        if (!n) {
            dom.badge.textContent = '';
            dom.badge.classList.add('d-none');
            return;
        }
        dom.badge.textContent = n > 99 ? '99+' : String(n);
        dom.badge.classList.remove('d-none');
        dom.badge.setAttribute('aria-label', `${n} khiếu nại chưa giải quyết`);
        dom.badge.classList.add('badge-pulse');
        setTimeout(() => dom.badge.classList.remove('badge-pulse'), 500);
    }

    async function fetchCount() {
        try {
            const res = await fetch(config.countUrl, { credentials: 'same-origin' });
            const ct = res.headers.get('content-type') || '';
            if (!ct.includes('application/json')) return;
            const data = await res.json();
            if (data && data.success) renderBadge(data.count);
        } catch (_) {}
    }

    function disconnect() {
        if (state.stream) { state.stream.close(); state.stream = null; }
        if (state.reconnectTimer) { clearTimeout(state.reconnectTimer); state.reconnectTimer = null; }
        if (state.pollingTimer) { clearInterval(state.pollingTimer); state.pollingTimer = null; }
    }

    function startPolling() {
        if (state.pollingTimer) return;
        state.usePolling = true;
        fetchCount();
        state.pollingTimer = setInterval(fetchCount, 15000);
    }

    function scheduleReconnect() {
        if (state.reconnectTimer) return;
        state.reconnectAttempts++;
        if (state.reconnectAttempts > state.maxReconnectAttempts) { startPolling(); return; }
        const delay = Math.min(3000 * state.reconnectAttempts, 10000);
        state.reconnectTimer = setTimeout(() => { state.reconnectTimer = null; connectStream(); }, delay);
    }

    function connectStream() {
        if (state.usePolling) return;
        disconnect();
        if (!window.EventSource) { startPolling(); return; }
        try {
            const es = new EventSource(config.countStreamUrl);
            state.stream = es;
            state.reconnectAttempts = 0;
            es.addEventListener('message', (e) => {
                try { renderBadge(JSON.parse(e.data).count); } catch (_) {}
            });
            es.onerror = () => {
                if (state.stream === es) { es.close(); state.stream = null; }
                scheduleReconnect();
            };
        } catch (_) { startPolling(); }
    }

    document.addEventListener('DOMContentLoaded', () => { fetchCount(); connectStream(); });
    window.addEventListener('beforeunload', disconnect);
})();
