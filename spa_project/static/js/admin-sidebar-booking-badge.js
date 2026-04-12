/**
 * Notification Badge: Yêu cầu đặt lịch chờ xác nhận
 *
 * Hiển thị số lượng booking requests có status='pending'
 * Auto-update real-time qua SSE stream (hoặc polling fallback)
 *
 * Pattern: Similar to chat badge
 */
(function () {
    const config = window.adminSidebarBookingBadgeConfig;
    if (!config) {
        console.warn('Booking badge config not found');
        return;
    }

    const dom = {
        badge: document.getElementById("adminSidebarBookingBadge"),
    };

    if (!dom.badge) {
        console.warn('Booking badge element not found');
        return;
    }

    const state = {
        stream: null,
        reconnectTimer: null,
        pollingTimer: null,
        usePolling: false,
        reconnectAttempts: 0,
        maxReconnectAttempts: 3
    };

    /**
     * Normalize count value
     * Returns 0 if invalid, otherwise returns floor of value
     */
    function normalizeCount(value) {
        const count = Number(value);
        if (!Number.isFinite(count) || count <= 0) {
            return 0;
        }
        return Math.floor(count);
    }

    /**
     * Format count for display
     * Shows "99+" for counts over 99
     */
    function formatCount(count) {
        return count > 99 ? "99+" : String(count);
    }

    /**
     * Render badge with count
     * Hides badge if count is 0
     */
    function renderBadge(count) {
        const normalizedCount = normalizeCount(count);

        if (!normalizedCount) {
            dom.badge.textContent = "";
            dom.badge.classList.add("d-none");
            return;
        }

        dom.badge.textContent = formatCount(normalizedCount);
        dom.badge.classList.remove("d-none");
        dom.badge.setAttribute(
            "aria-label",
            `${normalizedCount} yêu cầu đặt lịch chờ xác nhận`
        );

        // Thêm animation nhỏ khi badge thay đổi
        dom.badge.classList.add("badge-pulse");
        setTimeout(() => {
            dom.badge.classList.remove("badge-pulse");
        }, 500);
    }

    /**
     * Parse JSON response from API
     */
    async function parseJsonResponse(response) {
        const contentType = response.headers.get("content-type") || "";
        if (!contentType.includes("application/json")) {
            return null;
        }

        try {
            return await response.json();
        } catch (error) {
            return null;
        }
    }

    /**
     * Fetch initial pending count from API
     */
    async function fetchPendingCount() {
        try {
            const response = await fetch(config.countUrl, {
                credentials: "same-origin",
            });
            const data = await parseJsonResponse(response);

            if (data && data.success) {
                renderBadge(data.count);
            }
        } catch (error) {
            console.error('Failed to fetch pending count:', error);
            // Giữ badge hiện tại nếu request lỗi
        }
    }

    /**
     * Disconnect SSE stream và polling
     */
    function disconnectStream() {
        if (state.stream) {
            state.stream.close();
            state.stream = null;
        }

        if (state.reconnectTimer) {
            clearTimeout(state.reconnectTimer);
            state.reconnectTimer = null;
        }

        if (state.pollingTimer) {
            clearInterval(state.pollingTimer);
            state.pollingTimer = null;
        }
    }

    /**
     * Start polling fallback
     * Poll mỗi 15 giây nếu SSE không hoạt động
     */
    function startPolling() {
        if (state.pollingTimer) {
            return;
        }

        console.log('Booking badge: Switching to polling mode (15s interval)');
        state.usePolling = true;

        // Fetch immediately
        fetchPendingCount();

        // Then poll every 15 seconds
        state.pollingTimer = setInterval(function () {
            fetchPendingCount();
        }, 15000);
    }

    /**
     * Schedule reconnection after delay
     */
    function scheduleReconnect() {
        if (state.reconnectTimer) {
            return;
        }

        state.reconnectAttempts++;

        if (state.reconnectAttempts > state.maxReconnectAttempts) {
            console.warn('Booking badge: Max reconnect attempts reached, switching to polling');
            startPolling();
            return;
        }

        const delay = Math.min(3000 * state.reconnectAttempts, 10000); // Max 10s delay

        state.reconnectTimer = window.setTimeout(function () {
            state.reconnectTimer = null;
            connectStream();
        }, delay);
    }

    /**
     * Connect to SSE stream for real-time updates
     */
    function connectStream() {
        // Nếu đang dùng polling, không thử kết nối SSE
        if (state.usePolling) {
            return;
        }

        disconnectStream();

        if (!window.EventSource) {
            console.warn('EventSource not supported, using polling fallback');
            startPolling();
            return;
        }

        try {
            const eventSource = new EventSource(config.countStreamUrl);
            state.stream = eventSource;

            // Reset reconnect attempts on successful connection
            state.reconnectAttempts = 0;

            // Lắng nghe message từ SSE stream
            eventSource.addEventListener("message", function (event) {
                try {
                    const data = JSON.parse(event.data);
                    renderBadge(data.count);
                } catch (error) {
                    console.error('Failed to parse SSE data:', error);
                }
            });

            // Xử lý lỗi kết nối
            eventSource.onerror = function (error) {
                console.error('SSE connection error:', error);

                if (state.stream === eventSource) {
                    eventSource.close();
                    state.stream = null;
                }
                scheduleReconnect();
            };

            console.log('Booking badge: SSE connection established');

        } catch (error) {
            console.error('Failed to create EventSource:', error);
            startPolling();
        }
    }

    /**
     * Initialize badge on page load
     */
    document.addEventListener("DOMContentLoaded", function () {
        console.log('Initializing booking badge...');
        fetchPendingCount();
        connectStream();
    });

    /**
     * Cleanup on page unload
     */
    window.addEventListener("beforeunload", disconnectStream);

    console.log('Booking badge script loaded');
})();
