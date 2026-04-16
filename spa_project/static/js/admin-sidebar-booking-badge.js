/**
 * Notification badge cho yêu cầu đặt lịch chờ xác nhận.
 *
 * Ưu tiên WebSocket để nhận update realtime.
 * Nếu WebSocket không khả dụng thì fallback sang polling nhẹ.
 */
(function () {
    const config = window.adminSidebarBookingBadgeConfig;
    if (!config) {
        return;
    }

    const dom = {
        badge: document.getElementById("adminSidebarBookingBadge"),
    };

    if (!dom.badge) {
        return;
    }

    const state = {
        stream: null,
        reconnectTimer: null,
        pollingTimer: null,
        usePolling: false,
        reconnectAttempts: 0,
        maxReconnectAttempts: 3,
    };

    function buildWebSocketUrl(path) {
        const protocol = window.location.protocol === "https:" ? "wss" : "ws";
        return `${protocol}://${window.location.host}${path}`;
    }

    function normalizeCount(value) {
        const count = Number(value);
        if (!Number.isFinite(count) || count <= 0) {
            return 0;
        }
        return Math.floor(count);
    }

    function formatCount(count) {
        return count > 99 ? "99+" : String(count);
    }

    function dispatchCountUpdate(count) {
        window.dispatchEvent(
            new CustomEvent("booking-pending-count:update", {
                detail: { count },
            })
        );
    }

    function renderBadge(count) {
        const normalizedCount = normalizeCount(count);

        if (!normalizedCount) {
            dom.badge.textContent = "";
            dom.badge.classList.add("d-none");
            dispatchCountUpdate(0);
            return;
        }

        dom.badge.textContent = formatCount(normalizedCount);
        dom.badge.classList.remove("d-none");
        dom.badge.setAttribute(
            "aria-label",
            `${normalizedCount} yêu cầu đặt lịch online chưa xử lý`
        );

        dom.badge.classList.add("badge-pulse");
        setTimeout(function () {
            dom.badge.classList.remove("badge-pulse");
        }, 500);

        dispatchCountUpdate(normalizedCount);
    }

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
            console.error("Failed to fetch pending count:", error);
        }
    }

    function disconnectStream() {
        if (state.stream) {
            state.stream.onclose = null;
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

    function startPolling() {
        if (state.pollingTimer) {
            return;
        }

        state.usePolling = true;
        fetchPendingCount();

        state.pollingTimer = setInterval(function () {
            fetchPendingCount();
        }, 15000);
    }

    function scheduleReconnect() {
        if (state.reconnectTimer) {
            return;
        }

        state.reconnectAttempts += 1;
        if (state.reconnectAttempts > state.maxReconnectAttempts) {
            startPolling();
            return;
        }

        const delay = Math.min(3000 * state.reconnectAttempts, 10000);
        state.reconnectTimer = window.setTimeout(function () {
            state.reconnectTimer = null;
            connectStream();
        }, delay);
    }

    function connectStream() {
        if (state.usePolling) {
            return;
        }

        disconnectStream();

        if (!window.WebSocket) {
            startPolling();
            return;
        }

        try {
            const socket = new WebSocket(buildWebSocketUrl(config.countSocketPath));
            state.stream = socket;

            socket.addEventListener("open", function () {
                state.reconnectAttempts = 0;
            });

            socket.addEventListener("message", function (event) {
                try {
                    const data = JSON.parse(event.data || "{}");
                    if (data.event !== "pending_count") {
                        return;
                    }
                    renderBadge(data.count);
                } catch (error) {
                    console.error("Failed to parse booking badge payload:", error);
                }
            });

            socket.addEventListener("close", function () {
                if (state.stream === socket) {
                    state.stream = null;
                }
                scheduleReconnect();
            });
        } catch (error) {
            console.error("Failed to create booking badge WebSocket:", error);
            startPolling();
        }
    }

    document.addEventListener("DOMContentLoaded", function () {
        fetchPendingCount();
        connectStream();
    });

    window.addEventListener("beforeunload", disconnectStream);
})();
