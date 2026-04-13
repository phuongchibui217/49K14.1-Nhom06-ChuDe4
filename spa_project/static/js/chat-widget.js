(function () {
    const config = window.chatWidgetConfig;
    if (!config) {
        return;
    }

    const STORAGE_KEYS = {
        guestKey: "spa_ana_guest_chat_key",
        chatCode: "spa_ana_guest_chat_code",
    };

    const state = {
        isOpen: false,
        isBootstrapped: false,
        session: null,
        guestKey: sessionStorage.getItem(STORAGE_KEYS.guestKey) || "",
        messageIds: new Set(),
        unreadCount: 0,
        stream: null,
    };

    const dom = {
        widget: document.getElementById("chatWidgetContainer"),
        statusLabel: document.getElementById("chatStatusLabel"),
        warning: document.getElementById("chatGuestWarning"),
        messages: document.getElementById("chatMessages"),
        emptyState: document.getElementById("chatEmptyState"),
        form: document.getElementById("chatForm"),
        input: document.getElementById("chatInput"),
        sendBtn: document.getElementById("chatSendBtn"),
        error: document.getElementById("chatErrorMessage"),
        floatingBadge: document.getElementById("chatFloatingBadge"),
    };

    function buildChatUrl(template, chatCode) {
        return template.replace("__CHAT_CODE__", chatCode);
    }

    function getCsrfToken() {
        const tokenInput = dom.form.querySelector('input[name="csrfmiddlewaretoken"]');
        return config.csrfToken || (tokenInput ? tokenInput.value : "");
    }

    function escapeHtml(value) {
        const div = document.createElement("div");
        div.textContent = value || "";
        return div.innerHTML;
    }

    function formatTime(value) {
        if (!value) {
            return "";
        }

        const date = new Date(value);
        if (Number.isNaN(date.getTime())) {
            return "";
        }

        return date.toLocaleTimeString("vi-VN", {
            hour: "2-digit",
            minute: "2-digit",
        });
    }

    function formatFileSize(size) {
        const value = Number(size || 0);
        if (!value) {
            return "";
        }

        if (value >= 1024 * 1024) {
            return `${(value / (1024 * 1024)).toFixed(1)} MB`;
        }

        return `${Math.ceil(value / 1024)} KB`;
    }

    function getBootstrapUrl() {
        const params = new URLSearchParams({
            source: window.location.pathname,
        });

        if (!config.isAuthenticated && state.guestKey) {
            params.set("guestKey", state.guestKey);
        }

        return `${config.bootstrapUrl}?${params.toString()}`;
    }

    async function parseJsonResponse(response) {
        const contentType = response.headers.get("content-type") || "";

        if (!contentType.includes("application/json")) {
            return {
                success: false,
                error: config.sendErrorMessage,
            };
        }

        try {
            return await response.json();
        } catch (error) {
            return {
                success: false,
                error: config.sendErrorMessage,
            };
        }
    }

    async function apiGet(url) {
        try {
            const response = await fetch(url, {
                credentials: "same-origin",
            });
            return await parseJsonResponse(response);
        } catch (error) {
            return {
                success: false,
                error: config.sendErrorMessage,
            };
        }
    }

    async function apiPostJson(url, payload) {
        try {
            const response = await fetch(url, {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCsrfToken(),
                },
                body: JSON.stringify(payload || {}),
            });
            return await parseJsonResponse(response);
        } catch (error) {
            return {
                success: false,
                error: config.sendErrorMessage,
            };
        }
    }

    function setErrorMessage(message) {
        if (!message) {
            dom.error.classList.add("d-none");
            dom.error.textContent = config.sendErrorMessage;
            return;
        }

        dom.error.textContent = message;
        dom.error.classList.remove("d-none");
    }

    function autoResizeInput() {
        dom.input.style.height = "52px";
        dom.input.style.height = `${Math.min(dom.input.scrollHeight, 132)}px`;
    }

    function updateSendButtonState() {
        dom.sendBtn.disabled = !dom.input.value.trim();
    }

    function clearGuestStorage() {
        sessionStorage.removeItem(STORAGE_KEYS.guestKey);
        sessionStorage.removeItem(STORAGE_KEYS.chatCode);
        state.guestKey = "";
    }

    function persistGuestStorage() {
        if (config.isAuthenticated || !state.session) {
            clearGuestStorage();
            return;
        }

        state.guestKey = state.guestKey || "";
        sessionStorage.setItem(STORAGE_KEYS.guestKey, state.guestKey);
        sessionStorage.setItem(STORAGE_KEYS.chatCode, state.session.chatCode);
    }

    function updateFloatingBadge() {
        if (!dom.floatingBadge) {
            return;
        }

        if (state.unreadCount > 0) {
            dom.floatingBadge.textContent = state.unreadCount > 9 ? "9+" : String(state.unreadCount);
            dom.floatingBadge.classList.remove("d-none");
        } else {
            dom.floatingBadge.textContent = "";
            dom.floatingBadge.classList.add("d-none");
        }
    }

    function renderWarning() {
        if (!config.isAuthenticated) {
            dom.warning.querySelector("span").textContent = config.guestWarningMessage;
            dom.warning.classList.remove("d-none");
        } else {
            dom.warning.classList.add("d-none");
        }
    }

    function buildAttachmentHtml(message) {
        if (!message.attachmentUrl) {
            return "";
        }

        if (message.isImage) {
            return `
                <div class="chat-attachment">
                    <a href="${message.attachmentUrl}" target="_blank" rel="noopener noreferrer">
                        <img src="${message.attachmentUrl}" alt="${escapeHtml(message.attachmentName || "Hình ảnh")}">
                    </a>
                </div>
            `;
        }

        return `
            <div class="chat-attachment">
                <a
                    class="chat-attachment-file"
                    href="${message.attachmentUrl}"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    <i class="fas fa-file-alt"></i>
                    <span>${escapeHtml(message.attachmentName || "Tệp đính kèm")}</span>
                    <small>${escapeHtml(formatFileSize(message.attachmentSize))}</small>
                </a>
            </div>
        `;
    }

    function buildMessageHtml(message, deliveryState) {
        const senderClass = message.senderType === "customer"
            ? "customer"
            : message.senderType === "system"
                ? "system"
                : "admin";

        const displayName = message.senderType === "customer"
            ? "Bạn"
            : message.senderName || "Spa ANA";

        const headerHtml = senderClass === "system"
            ? ""
            : `
                <div class="chat-message-header">
                    <span class="chat-message-name">${escapeHtml(displayName)}</span>
                    <span class="chat-message-time">${escapeHtml(message.timeLabel || formatTime(message.createdAt))}</span>
                </div>
            `;

        let deliveryHtml = "";
        if (message.senderType === "customer" && deliveryState) {
            deliveryHtml = `<div class="chat-message-status">${escapeHtml(deliveryState)}</div>`;
        }

        return `
            <div class="chat-message ${senderClass}" data-message-id="${message.id}">
                ${headerHtml}
                ${message.content ? `<div class="chat-message-body">${escapeHtml(message.content)}</div>` : ""}
                ${buildAttachmentHtml(message)}
                ${deliveryHtml}
            </div>
        `;
    }

    function scrollMessagesToBottom() {
        dom.messages.scrollTop = dom.messages.scrollHeight;
    }

    function renderMessages(messages) {
        state.messageIds = new Set(messages.map((message) => Number(message.id)));

        if (!messages.length) {
            dom.messages.innerHTML = "";
            dom.messages.appendChild(dom.emptyState);
            dom.emptyState.classList.remove("d-none");
            return;
        }

        dom.messages.innerHTML = messages
            .map((message) => buildMessageHtml(message, message.senderType === "customer" ? "Đã gửi" : ""))
            .join("");
        scrollMessagesToBottom();
    }

    function appendMessage(message, deliveryState) {
        if (message.id && state.messageIds.has(Number(message.id))) {
            return;
        }

        if (message.id) {
            state.messageIds.add(Number(message.id));
        }

        if (dom.emptyState.parentNode === dom.messages) {
            dom.messages.innerHTML = "";
        }

        dom.messages.insertAdjacentHTML("beforeend", buildMessageHtml(message, deliveryState));
        scrollMessagesToBottom();
    }

    function updatePendingMessage(clientMessageId, message, deliveryState, failed) {
        const element = dom.messages.querySelector(`[data-message-id="${clientMessageId}"]`);
        if (!element) {
            appendMessage(message, deliveryState);
            return;
        }

        const wrapper = document.createElement("div");
        wrapper.innerHTML = buildMessageHtml(message, deliveryState);
        const nextElement = wrapper.firstElementChild;
        if (failed) {
            nextElement.classList.add("failed");
        }
        element.replaceWith(nextElement);
        if (message.id) {
            state.messageIds.add(Number(message.id));
        }
        scrollMessagesToBottom();
    }

    async function markCurrentSessionRead() {
        if (!state.session) {
            return;
        }

        const payload = config.isAuthenticated ? {} : { guestKey: state.guestKey };
        await apiPostJson(buildChatUrl(config.readUrlTemplate, state.session.chatCode), payload);
        state.unreadCount = 0;
        updateFloatingBadge();
    }

    function disconnectStream() {
        if (state.stream) {
            state.stream.close();
            state.stream = null;
        }
    }

    function connectStream(lastMessageId) {
        disconnectStream();
        if (!state.session) {
            return;
        }

        const params = new URLSearchParams({
            lastMessageId: String(lastMessageId || 0),
        });

        if (!config.isAuthenticated && state.guestKey) {
            params.set("guestKey", state.guestKey);
        }

        const streamUrl = `${buildChatUrl(config.streamUrlTemplate, state.session.chatCode)}?${params.toString()}`;
        const eventSource = new EventSource(streamUrl);
        state.stream = eventSource;

        eventSource.addEventListener("message", async (event) => {
            const data = JSON.parse(event.data);
            if (!data.message) {
                return;
            }

            appendMessage(
                data.message,
                data.message.senderType === "customer" ? "Đã gửi" : ""
            );

            if (data.session) {
                state.session = data.session;
            }

            if (data.message.senderType === "admin") {
                if (state.isOpen) {
                    await markCurrentSessionRead();
                } else {
                    state.unreadCount += 1;
                    updateFloatingBadge();
                }
            }
        });

        eventSource.onerror = function () {
            eventSource.close();
            if (state.session) {
                const currentLastId = [...state.messageIds].length ? Math.max(...state.messageIds) : 0;
                setTimeout(() => connectStream(currentLastId), 3000);
            }
        };
    }

    async function bootstrapChat() {
        const data = await apiGet(getBootstrapUrl());
        if (!data.success) {
            setErrorMessage(config.sendErrorMessage);
            return;
        }

        state.session = data.session;
        state.isBootstrapped = true;

        if (config.isAuthenticated) {
            clearGuestStorage();
        } else {
            state.guestKey = data.guestKey || state.guestKey;
            persistGuestStorage();
        }

        renderWarning();
        renderMessages(data.messages || []);
        const lastMessage = (data.messages || []).length ? data.messages[data.messages.length - 1] : null;
        connectStream(lastMessage ? lastMessage.id : 0);
        state.unreadCount = 0;
        updateFloatingBadge();
        await markCurrentSessionRead();
    }

    async function ensureChatReady() {
        if (!state.isBootstrapped) {
            await bootstrapChat();
        }
    }

    async function handleSend(event) {
        event.preventDefault();
        const content = dom.input.value.trim();
        if (!content) {
            return;
        }

        await ensureChatReady();
        if (!state.session) {
            setErrorMessage(config.sendErrorMessage);
            return;
        }

        const clientMessageId = `temp-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
        const tempMessage = {
            id: clientMessageId,
            senderType: "customer",
            senderName: "Bạn",
            messageType: "text",
            content: content,
            createdAt: new Date().toISOString(),
            timeLabel: formatTime(new Date().toISOString()),
        };

        appendMessage(tempMessage, "Đang gửi...");
        dom.input.value = "";
        autoResizeInput();
        updateSendButtonState();
        setErrorMessage("");

        const payload = {
            content: content,
            clientMessageId: clientMessageId,
        };

        if (!config.isAuthenticated) {
            payload.guestKey = state.guestKey;
        }

        const data = await apiPostJson(buildChatUrl(config.sendUrlTemplate, state.session.chatCode), payload);
        if (!data.success) {
            updatePendingMessage(
                clientMessageId,
                tempMessage,
                "Lỗi gửi",
                true
            );
            setErrorMessage(data.error || config.sendErrorMessage);
            return;
        }

        if (data.session) {
            state.session = data.session;
            if (!config.isAuthenticated) {
                persistGuestStorage();
            }
        }

        if (data.message) {
            updatePendingMessage(clientMessageId, data.message, "Đã gửi", false);
        }
    }

    function openChat() {
        state.isOpen = true;
        dom.widget.classList.add("active");
        setTimeout(() => {
            dom.input.focus();
            scrollMessagesToBottom();
        }, 120);

        ensureChatReady();
        markCurrentSessionRead();
    }

    function closeChat() {
        state.isOpen = false;
        dom.widget.classList.remove("active");
    }

    function toggleChat() {
        if (state.isOpen) {
            closeChat();
        } else {
            openChat();
        }
    }

    function initialize() {
        renderWarning();
        autoResizeInput();
        updateSendButtonState();
        updateFloatingBadge();

        dom.input.addEventListener("input", function () {
            autoResizeInput();
            updateSendButtonState();
        });

        dom.input.addEventListener("keydown", function (event) {
            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                if (!dom.sendBtn.disabled) {
                    dom.form.requestSubmit();
                }
            }
        });

        dom.form.addEventListener("submit", handleSend);
    }

    window.toggleChat = toggleChat;
    document.addEventListener("DOMContentLoaded", initialize);
    window.addEventListener("beforeunload", disconnectStream);
})();
