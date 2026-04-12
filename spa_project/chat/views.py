import json
import time

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import close_old_connections
from django.http import StreamingHttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from core.api_response import ApiResponse, get_or_404, safe_api, staff_api

from .models import ChatMessage, ChatSession
from .services import (
    build_sse_payload,
    can_customer_access_session,
    create_chat_message,
    get_admin_chat_sessions_data,
    get_attachment_accept_string,
    get_customer_sender_name,
    get_or_create_customer_chat_session,
    mark_session_read_by_admin,
    mark_session_read_by_customer,
    serialize_chat_message,
    serialize_chat_messages,
    serialize_chat_session,
)


def _parse_json_body(request):
    """Đọc JSON body một cách an toàn."""
    if not request.body:
        return {}

    try:
        return json.loads(request.body)
    except json.JSONDecodeError:
        return {}


def _get_guest_key(request, payload=None):
    """Lấy guestKey từ query/body/header."""
    payload = payload or {}
    return (
        payload.get("guestKey")
        or request.GET.get("guestKey")
        or request.headers.get("X-Guest-Session-Key")
        or ""
    ).strip()


def _streaming_response(generator):
    """Tạo StreamingHttpResponse cho SSE."""
    response = StreamingHttpResponse(generator, content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


def _get_customer_session_or_error(request, chat_code, payload=None):
    """Lấy phiên chat và kiểm tra quyền truy cập phía khách."""
    try:
        session = ChatSession.objects.select_related("customer", "customer__user").get(chat_code=chat_code)
    except ChatSession.DoesNotExist:
        return None, ApiResponse.not_found("Không tìm thấy phiên chat.")

    guest_key = _get_guest_key(request, payload)
    if not can_customer_access_session(request, session, guest_key):
        if request.user.is_authenticated:
            return None, ApiResponse.forbidden("Bạn không có quyền truy cập phiên chat này.")
        return None, ApiResponse.forbidden("Phiên chat không hợp lệ hoặc đã hết hạn.")

    return session, None


def _serialize_session_messages(session):
    messages_qs = session.messages.select_related("sender", "session").order_by("created_at", "id")
    return serialize_chat_messages(messages_qs)


# =====================================================
# ADMIN PAGE
# =====================================================


@login_required(login_url="accounts:login")
def admin_live_chat(request):
    """Trang chat trực tuyến trong admin panel."""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Bạn không có quyền truy cập trang này.")
        return redirect("pages:home")

    return render(
        request,
        "chat/admin_live_chat.html",
        {
            "chat_attachment_accept": get_attachment_accept_string(),
        },
    )


# =====================================================
# CUSTOMER CHAT API
# =====================================================


@require_http_methods(["GET"])
def api_customer_chat_bootstrap(request):
    """Lấy hoặc tạo phiên chat cho widget phía khách."""
    guest_key = _get_guest_key(request)
    source_page = (request.GET.get("source") or "").strip()
    session, created = get_or_create_customer_chat_session(
        request,
        guest_key=guest_key,
        source_page=source_page,
    )
    mark_session_read_by_customer(session)

    return ApiResponse.success(
        data={
            "session": serialize_chat_session(session),
            "messages": _serialize_session_messages(session),
            "guestKey": session.guest_session_key or "",
            "historyPreserved": session.customer_type == "authenticated",
            "isNewSession": created,
            "warningMessage": (
                "Lịch sử chat sẽ không được lưu khi bạn rời khỏi website."
                if session.customer_type == "guest"
                else ""
            ),
        }
    )


@require_http_methods(["POST"])
@safe_api
def api_customer_chat_send(request, chat_code):
    """Khách hàng gửi tin nhắn text."""
    if request.content_type and "multipart/form-data" in request.content_type:
        return ApiResponse.bad_request("Khách hàng chỉ được gửi tin nhắn văn bản.")

    data = _parse_json_body(request)
    session, error = _get_customer_session_or_error(request, chat_code, data)
    if error:
        return error

    try:
        message, _ = create_chat_message(
            session=session,
            sender_type="customer",
            sender_user=request.user if request.user.is_authenticated else None,
            sender_name=get_customer_sender_name(request),
            content=data.get("content", ""),
            client_message_id=data.get("clientMessageId", ""),
        )
    except Exception as exc:
        return ApiResponse.from_exception(exc)

    return ApiResponse.success(
        data={
            "message": serialize_chat_message(message),
            "session": serialize_chat_session(session),
        }
    )


@require_http_methods(["POST"])
@safe_api
def api_customer_chat_mark_read(request, chat_code):
    """Đánh dấu admin messages đã được khách xem."""
    data = _parse_json_body(request)
    session, error = _get_customer_session_or_error(request, chat_code, data)
    if error:
        return error

    mark_session_read_by_customer(session)
    return ApiResponse.success(data={"session": serialize_chat_session(session)})


@require_http_methods(["GET"])
def api_customer_chat_stream(request, chat_code):
    """SSE stream cho một phiên chat phía khách."""
    session, error = _get_customer_session_or_error(request, chat_code)
    if error:
        return error

    try:
        last_message_id = int(request.GET.get("lastMessageId", "0") or 0)
    except ValueError:
        last_message_id = 0

    def event_stream():
        nonlocal last_message_id
        idle_loops = 0

        try:
            close_old_connections()
            yield build_sse_payload(
                "ready",
                {"chatCode": session.chat_code, "lastMessageId": last_message_id},
            )

            while True:
                close_old_connections()
                new_messages = list(
                    ChatMessage.objects.select_related("session", "sender")
                    .filter(session=session, id__gt=last_message_id)
                    .order_by("id")
                )

                if new_messages:
                    for message in new_messages:
                        last_message_id = message.id
                        yield build_sse_payload(
                            "message",
                            {
                                "message": serialize_chat_message(message),
                                "session": serialize_chat_session(message.session),
                            },
                        )
                    idle_loops = 0
                else:
                    idle_loops += 1
                    if idle_loops >= 5:
                        yield build_sse_payload("ping", {"timestamp": time.time()})
                        idle_loops = 0

                close_old_connections()
                time.sleep(2)
        except GeneratorExit:
            close_old_connections()
            return

    return _streaming_response(event_stream())


# =====================================================
# ADMIN CHAT API
# =====================================================


@require_http_methods(["GET"])
@staff_api
def api_admin_chat_sessions(request):
    """Danh sách phiên chat cho admin."""
    search = (request.GET.get("search") or "").strip()
    status = (request.GET.get("status") or "").strip()
    sessions, unread_total = get_admin_chat_sessions_data(search=search, status=status)

    return ApiResponse.success(
        data={
            "sessions": [serialize_chat_session(session) for session in sessions],
            "unreadTotal": unread_total,
        }
    )


@require_http_methods(["GET"])
@staff_api
def api_admin_chat_messages(request, chat_code):
    """Chi tiết lịch sử tin nhắn của một phiên chat."""
    session, error = get_or_404(ChatSession, chat_code=chat_code)
    if error:
        return error

    mark_session_read_by_admin(session)
    return ApiResponse.success(
        data={
            "session": serialize_chat_session(session),
            "messages": _serialize_session_messages(session),
        }
    )


@require_http_methods(["POST"])
@staff_api
def api_admin_chat_send(request, chat_code):
    """Admin gửi tin nhắn text/file/image."""
    session, error = get_or_404(ChatSession, chat_code=chat_code)
    if error:
        return error

    if request.content_type and "multipart/form-data" in request.content_type:
        payload = request.POST
        content = payload.get("content", "")
        client_message_id = payload.get("clientMessageId", "")
        attachment = request.FILES.get("attachment")
    else:
        payload = _parse_json_body(request)
        content = payload.get("content", "")
        client_message_id = payload.get("clientMessageId", "")
        attachment = None

    try:
        message, _ = create_chat_message(
            session=session,
            sender_type="admin",
            sender_user=request.user,
            sender_name=request.user.get_full_name() or request.user.username,
            content=content,
            attachment=attachment,
            client_message_id=client_message_id,
        )
    except Exception as exc:
        return ApiResponse.from_exception(exc)

    return ApiResponse.success(
        data={
            "message": serialize_chat_message(message),
            "session": serialize_chat_session(session),
        }
    )


@require_http_methods(["POST"])
@staff_api
def api_admin_chat_mark_read(request, chat_code):
    """Đánh dấu khách message đã được admin xem."""
    session, error = get_or_404(ChatSession, chat_code=chat_code)
    if error:
        return error

    mark_session_read_by_admin(session)
    return ApiResponse.success(data={"session": serialize_chat_session(session)})


@require_http_methods(["GET"])
@staff_api
def api_admin_chat_sessions_stream(request):
    """SSE stream cập nhật danh sách phiên chat cho admin."""
    search = (request.GET.get("search") or "").strip()
    status = (request.GET.get("status") or "").strip()

    def event_stream():
        last_signature = None
        idle_loops = 0

        try:
            while True:
                close_old_connections()
                sessions, unread_total = get_admin_chat_sessions_data(search=search, status=status)
                signature = (
                    unread_total,
                    tuple(
                        (
                            session.id,
                            session.updated_at.isoformat(),
                            session.admin_unread_count,
                            session.customer_unread_count,
                            session.last_message_preview,
                        )
                        for session in sessions
                    ),
                )

                if signature != last_signature:
                    yield build_sse_payload(
                        "sessions",
                        {
                            "sessions": [serialize_chat_session(session) for session in sessions],
                            "unreadTotal": unread_total,
                        },
                    )
                    last_signature = signature
                    idle_loops = 0
                else:
                    idle_loops += 1
                    if idle_loops >= 5:
                        yield build_sse_payload("ping", {"timestamp": time.time()})
                        idle_loops = 0

                close_old_connections()
                time.sleep(2)
        except GeneratorExit:
            close_old_connections()
            return

    return _streaming_response(event_stream())


@require_http_methods(["GET"])
@staff_api
def api_admin_chat_stream(request, chat_code):
    """SSE stream cập nhật tin nhắn cho một phiên chat admin đang mở."""
    session, error = get_or_404(ChatSession, chat_code=chat_code)
    if error:
        return error

    try:
        last_message_id = int(request.GET.get("lastMessageId", "0") or 0)
    except ValueError:
        last_message_id = 0

    def event_stream():
        nonlocal last_message_id
        idle_loops = 0

        try:
            close_old_connections()
            yield build_sse_payload(
                "ready",
                {"chatCode": session.chat_code, "lastMessageId": last_message_id},
            )

            while True:
                close_old_connections()
                new_messages = list(
                    ChatMessage.objects.select_related("session", "sender")
                    .filter(session=session, id__gt=last_message_id)
                    .order_by("id")
                )

                if new_messages:
                    for message in new_messages:
                        last_message_id = message.id
                        yield build_sse_payload(
                            "message",
                            {
                                "message": serialize_chat_message(message),
                                "session": serialize_chat_session(message.session),
                            },
                        )
                    idle_loops = 0
                else:
                    idle_loops += 1
                    if idle_loops >= 5:
                        yield build_sse_payload("ping", {"timestamp": time.time()})
                        idle_loops = 0

                close_old_connections()
                time.sleep(2)
        except GeneratorExit:
            close_old_connections()
            return

    return _streaming_response(event_stream())
