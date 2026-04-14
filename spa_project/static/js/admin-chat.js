(function () {
    const config = window.adminChatConfig;
    if (!config) {
        return;
    }

    const state = {
        sessions: [],
        selectedSession: null,
        selectedFile: null,
        sessionStream: null,
        messageStream: null,
        messageIds: new Set(),
        search: "",
    };

    const dom = {
        emptyState: document.getElementById("adminChatEmptyState"),
        panel: document.getElementById("adminChatPanel"),
        sessionList: document.getElementById("adminChatSessionList"),
        unreadTotal: document.getElementById("adminChatUnreadTotal"),
        searchInput: document.getElementById("adminChatSearch"),
        sessionName: document.getElementById("adminChatSessionName"),
        sessionCode: document.getElementById("adminChatSessionCode"),
        sessionContact: document.getElementById("adminChatSessionContact"),
        sessionStatus: document.getElementById("adminChatSessionStatus"),
        messages: document.getElementById("adminChatMessages"),
        form: document.getElementById("adminChatComposerForm"),
        input: document.getElementById("adminChatInput"),
        sendBtn: document.getElementById("adminChatSendBtn"),
        error: document.getElementById("adminChatErrorMessage"),
        attachBtn: document.getElementById("adminChatAttachBtn"),
        attachmentInput: document.getElementById("adminChatAttachmentInput"),
        selectedFile: document.getElementById("adminChatSelectedFile"),
        selectedFileName: document.getElementById("adminChatSelectedFileName"),
        removeFileBtn: document.getElementById("adminChatRemoveFile"),
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

    function formatDateTime(value) {
        if (!value) {
            return "";
        }

        const date = new Date(value);
        if (Number.isNaN(date.getTime())) {
            return "";
        }

        return date.toLocaleString("vi-VN", {
            hour: "2-digit",
            minute: "2-digit",
            day: "2-digit",
            month: "2-digit",
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

    function getSessionStatusLabel(status) {
        const normalized = String(status || "").trim().toUpperCase();
        return normalized === "CLOSED" ? "Đã đóng" : "Đang mở";
    }

    function debounce(fn, delay) {
        let timeoutId = null;
        return function (...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => fn.apply(this, args), delay);
        };
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

    async function apiPost(url, body, headers) {
        try {
            const response = await fetch(url, {
                method: "POST",
                credentials: "same-origin",
                headers: Object.assign(
                    {
                        "X-CSRFToken": getCsrfToken(),
                    },
                    headers || {}
                ),
                body: body,
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
        dom.input.style.height = `${Math.min(dom.input.scrollHeight, 180)}px`;
    }

    function updateSendButtonState() {
        const hasText = dom.input.value.trim().length > 0;
        const hasFile = !!state.selectedFile;
        dom.sendBtn.disabled = !state.selectedSession || (!hasText && !hasFile);
    }

    function setSelectedFile(file) {
        state.selectedFile = file || null;

        if (state.selectedFile) {
            dom.selectedFileName.textContent = state.selectedFile.name;
            dom.selectedFile.classList.remove("d-none");
        } else {
            dom.attachmentInput.value = "";
            dom.selectedFile.classList.add("d-none");
            dom.selectedFileName.textContent = "";
        }

        updateSendButtonState();
    }

    function renderSessions() {
        dom.unreadTotal.textContent = `${state.sessions.reduce((sum, item) => sum + (item.adminUnreadCount || 0), 0)} chưa đọc`;

        if (!state.sessions.length) {
            dom.sessionList.innerHTML = `
                <div class="admin-chat-list-empty">
                    <i class="fas fa-comments"></i>
                    <p>Chưa có phiên chat nào.</p>
                </div>
            `;
            return;
        }

        dom.sessionList.innerHTML = state.sessions
            .map((session) => {
                const isActive = state.selectedSession && state.selectedSession.chatCode === session.chatCode;
                const unreadBadge = session.adminUnreadCount
                    ? `<span class="admin-chat-unread-badge">${session.adminUnreadCount}</span>`
                    : "";
                const contactLabel = session.customerPhone || (session.isGuest ? "Khách vãng lai" : "Khách hàng");

                return `
                    <button
                        type="button"
                        class="admin-chat-session-item ${isActive ? "active" : ""}"
                        data-chat-code="${escapeHtml(session.chatCode)}"
                    >
                        <div class="admin-chat-session-top">
                            <div>
                                <p class="admin-chat-session-name">${escapeHtml(session.customerName || "Khách hàng")}</p>
                                <span class="admin-chat-session-code">${escapeHtml(session.chatCode)}</span>
                            </div>
                            <span class="admin-chat-session-time">${escapeHtml(session.lastMessageTimeLabel || "Mới tạo")}</span>
                        </div>
                        <div class="admin-chat-session-preview">${escapeHtml(session.lastMessagePreview || "Chưa có tin nhắn")}</div>
                        <div class="admin-chat-session-bottom">
                            <span class="admin-chat-session-contact">${escapeHtml(contactLabel)}</span>
                            ${unreadBadge}
                        </div>
                    </button>
                `;
            })
            .join("");

        dom.sessionList.querySelectorAll(".admin-chat-session-item").forEach((item) => {
            item.addEventListener("click", function () {
                selectSession(this.dataset.chatCode);
            });
        });
    }

    function renderMessageAttachment(message) {
        if (!message.attachmentUrl) {
            return "";
        }

        if (message.isImage) {
            return `
                <div class="admin-chat-attachment">
                    <a href="${message.attachmentUrl}" target="_blank" rel="noopener noreferrer">
                        <img
                            src="${message.attachmentUrl}"
                            alt="${escapeHtml(message.attachmentName || "Hình ảnh chat")}"
                            class="admin-chat-attachment-image"
                        >
                    </a>
                </div>
            `;
        }

        return `
            <div class="admin-chat-attachment">
                <a
                    href="${message.attachmentUrl}"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="admin-chat-attachment-file"
                >
                    <i class="fas fa-file-alt"></i>
                    <span>${escapeHtml(message.attachmentName || "Tệp đính kèm")}</span>
                    <small>${escapeHtml(formatFileSize(message.attachmentSize))}</small>
                </a>
            </div>
        `;
    }

    function buildMessageHtml(message) {
        const messageClass = message.senderType === "admin"
            ? "admin"
            : message.senderType === "system"
                ? "system"
                : "customer";

        // Phía admin: hiện tên thật staff (staffName) hoặc tên khách (senderName)
        const displayName = message.senderType === "admin"
            ? (message.staffName || message.senderName || "Nhân viên")
            : (message.senderName || "Khách hàng");

        return `
            <div class="admin-chat-message ${messageClass}" data-message-id="${message.id}">
                <div class="admin-chat-message-header">
                    <span class="admin-chat-message-name">${escapeHtml(displayName)}</span>
                    <span class="admin-chat-message-time">${escapeHtml(message.timeLabel || formatDateTime(message.createdAt))}</span>
                </div>
                ${message.content ? `<div class="admin-chat-message-content">${escapeHtml(message.content)}</div>` : ""}
                ${renderMessageAttachment(message)}
            </div>
        `;
    }

    function scrollMessagesToBottom() {
        dom.messages.scrollTop = dom.messages.scrollHeight;
    }

    function renderMessages(messages) {
        state.messageIds = new Set(messages.map((message) => Number(message.id)));
        dom.messages.innerHTML = messages.length
            ? messages.map(buildMessageHtml).join("")
            : `
                <div class="admin-chat-empty">
                    <i class="fas fa-comment-slash"></i>
                    <p>Phiên chat này chưa có tin nhắn nào.</p>
                </div>
            `;

        scrollMessagesToBottom();
    }

    function appendMessage(message) {
        if (state.messageIds.has(Number(message.id))) {
            return;
        }

        state.messageIds.add(Number(message.id));

        const emptyState = dom.messages.querySelector(".admin-chat-empty");
        if (emptyState) {
            dom.messages.innerHTML = "";
        }

        dom.messages.insertAdjacentHTML("beforeend", buildMessageHtml(message));
        scrollMessagesToBottom();
    }

    function updateSelectedSession(session) {
        state.selectedSession = session;
        dom.emptyState.classList.add("d-none");
        dom.panel.classList.remove("d-none");
        dom.sessionName.textContent = session.customerName || "Khách hàng";
        dom.sessionCode.textContent = session.chatCode || "";
        dom.sessionContact.textContent = session.customerPhone || (session.isGuest ? "Khách vãng lai" : "");
        dom.sessionStatus.textContent = getSessionStatusLabel(session.status);
        updateSendButtonState();
        renderSessions();
    }

    async function loadSessions() {
        const search = dom.searchInput.value.trim();
        const query = search ? `?search=${encodeURIComponent(search)}` : "";
        const data = await apiGet(`${config.sessionsUrl}${query}`);

        if (!data.success) {
            return;
        }

        state.sessions = data.sessions || [];
        renderSessions();

        if (state.selectedSession) {
            const refreshed = state.sessions.find((item) => item.chatCode === state.selectedSession.chatCode);
            if (refreshed) {
                state.selectedSession = refreshed;
                dom.sessionContact.textContent = refreshed.customerPhone || (refreshed.isGuest ? "Khách vãng lai" : "");
                dom.sessionStatus.textContent = getSessionStatusLabel(refreshed.status);
            }
        }
    }

    async function markCurrentSessionRead() {
        if (!state.selectedSession) {
            return;
        }

        await apiPost(buildChatUrl(config.readUrlTemplate, state.selectedSession.chatCode), new FormData(), {});
    }

    function disconnectMessageStream() {
        if (state.messageStream) {
            state.messageStream.close();
            state.messageStream = null;
        }
    }

    function disconnectSessionStream() {
        if (state.sessionStream) {
            state.sessionStream.close();
            state.sessionStream = null;
        }
    }

    function connectSessionStream() {
        disconnectSessionStream();

        const search = dom.searchInput.value.trim();
        const query = search ? `?search=${encodeURIComponent(search)}` : "";
        const eventSource = new EventSource(`${config.sessionsStreamUrl}${query}`);
        state.sessionStream = eventSource;

        eventSource.addEventListener("sessions", (event) => {
            const data = JSON.parse(event.data);
            state.sessions = data.sessions || [];
            renderSessions();

            if (state.selectedSession) {
                const refreshed = state.sessions.find((item) => item.chatCode === state.selectedSession.chatCode);
                if (refreshed) {
                    state.selectedSession = refreshed;
                    dom.sessionContact.textContent = refreshed.customerPhone || (refreshed.isGuest ? "Khách vãng lai" : "");
                    dom.sessionStatus.textContent = getSessionStatusLabel(refreshed.status);
                }
            }
        });

        eventSource.onerror = function () {
            eventSource.close();
            setTimeout(connectSessionStream, 3000);
        };
    }

    function connectMessageStream(chatCode, lastMessageId) {
        disconnectMessageStream();

        const streamUrl = `${buildChatUrl(config.streamUrlTemplate, chatCode)}?lastMessageId=${lastMessageId || 0}`;
        const eventSource = new EventSource(streamUrl);
        state.messageStream = eventSource;

        eventSource.addEventListener("message", async (event) => {
            const data = JSON.parse(event.data);
            if (!data.message) {
                return;
            }

            lastMessageId = data.message.id || lastMessageId;

            appendMessage(data.message);

            if (data.session && state.selectedSession && data.session.chatCode === state.selectedSession.chatCode) {
                updateSelectedSession(data.session);
            }

            if (data.message.senderType === "customer") {
                await markCurrentSessionRead();
                await loadSessions();
            }
        });

        eventSource.onerror = function () {
            eventSource.close();
            if (state.selectedSession && state.selectedSession.chatCode === chatCode) {
                setTimeout(() => connectMessageStream(chatCode, lastMessageId), 3000);
            }
        };
    }

    async function selectSession(chatCode) {
        const data = await apiGet(buildChatUrl(config.messagesUrlTemplate, chatCode));
        if (!data.success) {
            return;
        }

        updateSelectedSession(data.session);
        renderMessages(data.messages || []);

        const lastMessage = (data.messages || []).length ? data.messages[data.messages.length - 1] : null;
        connectMessageStream(chatCode, lastMessage ? lastMessage.id : 0);
        await loadSessions();
    }

    async function sendMessage(event) {
        event.preventDefault();
        if (!state.selectedSession) {
            return;
        }

        const content = dom.input.value.trim();
        if (!content && !state.selectedFile) {
            return;
        }

        dom.sendBtn.disabled = true;
        setErrorMessage("");

        const formData = new FormData();
        formData.append("content", content);
        formData.append("clientMessageId", `admin-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`);

        if (state.selectedFile) {
            formData.append("attachment", state.selectedFile);
        }

        const data = await apiPost(
            buildChatUrl(config.sendUrlTemplate, state.selectedSession.chatCode),
            formData,
            {}
        );

        if (!data.success) {
            setErrorMessage(data.error || config.sendErrorMessage);
            updateSendButtonState();
            return;
        }

        if (data.message) {
            appendMessage(data.message);
        }

        if (data.session) {
            updateSelectedSession(data.session);
        }

        dom.input.value = "";
        autoResizeInput();
        setSelectedFile(null);
        updateSendButtonState();
        await loadSessions();
    }

    function handleSearchInput() {
        state.search = dom.searchInput.value.trim();
        loadSessions();
        connectSessionStream();
    }

    function initialize() {
        loadSessions();
        connectSessionStream();

        dom.searchInput.addEventListener("input", debounce(handleSearchInput, 350));
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

        dom.form.addEventListener("submit", sendMessage);
        dom.attachBtn.addEventListener("click", () => dom.attachmentInput.click());
        dom.attachmentInput.addEventListener("change", function () {
            const file = this.files && this.files.length ? this.files[0] : null;
            setSelectedFile(file);
        });
        dom.removeFileBtn.addEventListener("click", function () {
            setSelectedFile(null);
        });

        autoResizeInput();
        updateSendButtonState();
    }

    document.addEventListener("DOMContentLoaded", initialize);
    window.addEventListener("beforeunload", function () {
        disconnectMessageStream();
        disconnectSessionStream();
    });
})();
