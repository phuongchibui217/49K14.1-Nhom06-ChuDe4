(function () {
    const config = window.adminSidebarChatBadgeConfig;
    if (!config) {
        return;
    }

    const dom = {
        badge: document.getElementById("adminSidebarChatBadge"),
    };

    if (!dom.badge) {
        return;
    }

    const state = {
        stream: null,
        reconnectTimer: null,
    };

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
            `${normalizedCount} tin nhắn chat khách hàng chưa đọc`
        );
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

    async function fetchUnreadTotal() {
        try {
            const response = await fetch(config.sessionsUrl, {
                credentials: "same-origin",
            });
            const data = await parseJsonResponse(response);

            if (data && data.success) {
                renderBadge(data.unreadTotal);
            }
        } catch (error) {
            // Giữ badge hiện tại nếu request lỗi.
        }
    }

    function disconnectStream() {
        if (state.stream) {
            state.stream.close();
            state.stream = null;
        }

        if (state.reconnectTimer) {
            clearTimeout(state.reconnectTimer);
            state.reconnectTimer = null;
        }
    }

    function scheduleReconnect() {
        if (state.reconnectTimer) {
            return;
        }

        state.reconnectTimer = window.setTimeout(function () {
            state.reconnectTimer = null;
            connectStream();
        }, 3000);
    }

    function connectStream() {
        disconnectStream();

        if (!window.EventSource) {
            return;
        }

        const eventSource = new EventSource(config.sessionsStreamUrl);
        state.stream = eventSource;

        eventSource.addEventListener("sessions", function (event) {
            try {
                const data = JSON.parse(event.data);
                renderBadge(data.unreadTotal);
            } catch (error) {
                // Bỏ qua payload lỗi và chờ event tiếp theo.
            }
        });

        eventSource.onerror = function () {
            if (state.stream === eventSource) {
                eventSource.close();
                state.stream = null;
            }
            scheduleReconnect();
        };
    }

    document.addEventListener("DOMContentLoaded", function () {
        fetchUnreadTotal();
        connectStream();
    });

    window.addEventListener("beforeunload", disconnectStream);
})();
