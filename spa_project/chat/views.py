import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from core.api_response import ApiResponse, get_or_404, safe_api, staff_api

from .models import ChatSession
from .services import (
    can_customer_access_session,
    create_chat_message,
    ensure_staff_session_participation,
    get_admin_chat_sessions_data,
    get_attachment_accept_string,
    get_customer_sender_name,
    get_existing_customer_chat_session,
    get_or_create_customer_chat_session,
    mark_session_read_by_admin,
    mark_session_read_by_customer,
    serialize_customer_chat_message,
    serialize_chat_message,
    serialize_chat_messages,
    serialize_chat_session,
)


def _parse_json_body(request):
    if not request.body:
        return {}

    try:
        return json.loads(request.body)
    except json.JSONDecodeError:
        return {}


def _get_guest_key(request, payload=None):
    payload = payload or {}
    return (
        payload.get("guestKey")
        or request.GET.get("guestKey")
        or request.headers.get("X-Guest-Session-Key")
        or ""
    ).strip()


def _get_customer_session_or_error(request, chat_code, payload=None):
    try:
        session = ChatSession.objects.select_related("customer", "customer__user").get(chat_code=chat_code)
    except ChatSession.DoesNotExist:
        return None, ApiResponse.not_found("Khong tim thay phien chat.")

    guest_key = _get_guest_key(request, payload)
    if not can_customer_access_session(request, session, guest_key):
        if request.user.is_authenticated:
            return None, ApiResponse.forbidden("Ban khong co quyen truy cap phien chat nay.")
        return None, ApiResponse.forbidden("Phien chat khong hop le hoac da het han.")

    return session, None


def _serialize_session_messages(session, customer_safe=False):
    messages_qs = session.messages.select_related("sender", "session").order_by("created_at", "id")
    return serialize_chat_messages(messages_qs, customer_safe=customer_safe)


@login_required(login_url="accounts:login")
def admin_live_chat(request):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Ban khong co quyen truy cap trang nay.")
        return redirect("pages:home")

    return render(
        request,
        "chat/admin_live_chat.html",
        {
            "chat_attachment_accept": get_attachment_accept_string(),
        },
    )


@require_http_methods(["GET"])
def api_customer_chat_bootstrap(request):
    guest_key = _get_guest_key(request)
    session = get_existing_customer_chat_session(request, guest_key=guest_key)

    if session:
        mark_session_read_by_customer(session)
        return ApiResponse.success(
            data={
                "session": serialize_chat_session(session),
                "messages": _serialize_session_messages(session, customer_safe=True),
                "guestKey": session.guest_session_key or "",
                "historyPreserved": session.customer_type == "authenticated",
                "isNewSession": False,
                "warningMessage": (
                    "Lich su chat se khong duoc luu khi ban roi khoi website."
                    if session.customer_type == "guest"
                    else ""
                ),
            }
        )

    return ApiResponse.success(
        data={
            "session": None,
            "messages": [],
            "guestKey": guest_key or "",
            "historyPreserved": False,
            "isNewSession": True,
            "warningMessage": (
                "Lich su chat se khong duoc luu khi ban roi khoi website."
                if not request.user.is_authenticated
                else ""
            ),
        }
    )


@require_http_methods(["POST"])
@safe_api
def api_customer_chat_send_new(request):
    if request.content_type and "multipart/form-data" in request.content_type:
        return ApiResponse.bad_request("Khach hang chi duoc gui tin nhan van ban.")

    data = _parse_json_body(request)
    guest_key = _get_guest_key(request, data)
    source_page = (data.get("sourcePage") or "").strip()[:255]
    session, _ = get_or_create_customer_chat_session(
        request,
        guest_key=guest_key,
        source_page=source_page,
    )

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
            "message": serialize_customer_chat_message(message),
            "session": serialize_chat_session(session),
            "guestKey": session.guest_session_key or "",
        }
    )


@require_http_methods(["POST"])
@safe_api
def api_customer_chat_send(request, chat_code):
    if request.content_type and "multipart/form-data" in request.content_type:
        return ApiResponse.bad_request("Khach hang chi duoc gui tin nhan van ban.")

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
            "message": serialize_customer_chat_message(message),
            "session": serialize_chat_session(session),
        }
    )


@require_http_methods(["POST"])
@safe_api
def api_customer_chat_mark_read(request, chat_code):
    data = _parse_json_body(request)
    session, error = _get_customer_session_or_error(request, chat_code, data)
    if error:
        return error

    mark_session_read_by_customer(session)
    return ApiResponse.success(data={"session": serialize_chat_session(session)})


@require_http_methods(["GET"])
@staff_api
def api_admin_chat_sessions(request):
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
    session, error = get_or_404(ChatSession, chat_code=chat_code)
    if error:
        return error

    ensure_staff_session_participation(session, request.user)
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
    session, error = get_or_404(ChatSession, chat_code=chat_code)
    if error:
        return error

    ensure_staff_session_participation(session, request.user)

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
    session, error = get_or_404(ChatSession, chat_code=chat_code)
    if error:
        return error

    ensure_staff_session_participation(session, request.user)
    mark_session_read_by_admin(session)
    return ApiResponse.success(data={"session": serialize_chat_session(session)})
