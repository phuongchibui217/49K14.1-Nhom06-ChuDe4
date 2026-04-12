import json
import os
import secrets

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F, Q, Sum
from django.utils import timezone

from accounts.models import CustomerProfile
from core.validators import validate_length, validate_required

from .models import ChatMessage, ChatSession


CHAT_TEXT_MAX_LENGTH = 1000
CHAT_ATTACHMENT_MAX_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/gif",
}
ALLOWED_FILE_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain",
    "application/zip",
    "application/x-zip-compressed",
}
ALLOWED_FILE_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".txt",
    ".zip",
}


def ensure_customer_profile(user):
    """Lấy hoặc tạo CustomerProfile theo cùng pattern các app hiện có."""
    if hasattr(user, "customer_profile"):
        return user.customer_profile

    return CustomerProfile.objects.create(
        user=user,
        phone=user.username,
        full_name=user.get_full_name() or user.username,
        email=user.email or "",
    )


def generate_guest_session_key():
    """Sinh khóa tạm thời cho khách vãng lai."""
    return secrets.token_urlsafe(24)


def normalize_text_message(content):
    """Chuẩn hóa và validate nội dung chat text."""
    content = validate_required(content, "Tin nhắn")
    return validate_length(
        content,
        min_len=1,
        max_len=CHAT_TEXT_MAX_LENGTH,
        field_name="Tin nhắn",
    )


def validate_admin_attachment(attachment):
    """Validate file/image đính kèm phía admin."""
    if not attachment:
        return "text"

    if attachment.size > CHAT_ATTACHMENT_MAX_SIZE:
        raise ValidationError("Tệp đính kèm không được vượt quá 10MB.")

    content_type = getattr(attachment, "content_type", "").lower()
    extension = os.path.splitext(attachment.name or "")[1].lower()

    if content_type in ALLOWED_IMAGE_TYPES:
        return "image"

    if content_type in ALLOWED_FILE_TYPES or extension in ALLOWED_FILE_EXTENSIONS:
        return "file"

    raise ValidationError("Định dạng tệp không được hỗ trợ.")


def get_or_create_customer_chat_session(request, guest_key=None, source_page=""):
    """
    Lấy hoặc tạo phiên chat cho khách hàng.

    - Khách đăng nhập: luôn tái sử dụng phiên open gần nhất.
    - Khách vãng lai: tái sử dụng theo guest_key đang giữ trong sessionStorage.
    """
    source_page = (source_page or "")[:255]

    if request.user.is_authenticated:
        customer = ensure_customer_profile(request.user)
        session = ChatSession.objects.filter(
            customer=customer,
            customer_type="authenticated",
            status="open",
        ).order_by("-last_message_at", "-created_at").first()

        if session:
            if source_page and not session.source_page:
                session.source_page = source_page
                session.save(update_fields=["source_page", "updated_at"])
            return session, False

        session = ChatSession.objects.create(
            customer_type="authenticated",
            customer=customer,
            source_page=source_page,
        )
        return session, True

    if guest_key:
        session = ChatSession.objects.filter(
            customer_type="guest",
            guest_session_key=guest_key,
            status="open",
        ).first()
        if session:
            if source_page and not session.source_page:
                session.source_page = source_page
                session.save(update_fields=["source_page", "updated_at"])
            return session, False

    session = ChatSession.objects.create(
        customer_type="guest",
        guest_session_key=generate_guest_session_key(),
        source_page=source_page,
    )
    return session, True


def can_customer_access_session(request, session, guest_key=None):
    """Kiểm tra khách hàng hiện tại có quyền truy cập phiên chat không."""
    if session.customer_type == "authenticated":
        return (
            request.user.is_authenticated
            and session.customer_id
            and hasattr(request.user, "customer_profile")
            and session.customer_id == request.user.customer_profile.id
        )

    return bool(guest_key and session.guest_session_key == guest_key)


def get_customer_sender_name(request):
    """Tên người gửi phía khách."""
    if request.user.is_authenticated:
        profile = ensure_customer_profile(request.user)
        return profile.full_name or profile.phone or request.user.username
    return "Khách vãng lai"


def touch_session_from_message(session, message):
    """Cập nhật activity và unread counters của phiên chat."""
    update_kwargs = {
        "last_message_at": message.created_at,
        "last_message_preview": message.get_preview_text()[:255],
        "last_sender_type": message.sender_type,
        "updated_at": timezone.now(),
    }
    if message.sender_type == "customer":
        update_kwargs["admin_unread_count"] = F("admin_unread_count") + 1
        update_kwargs["customer_unread_count"] = 0
    elif message.sender_type == "admin":
        update_kwargs["customer_unread_count"] = F("customer_unread_count") + 1
        update_kwargs["admin_unread_count"] = 0

    ChatSession.objects.filter(pk=session.pk).update(**update_kwargs)
    session.refresh_from_db(
        fields=[
            "last_message_at",
            "last_message_preview",
            "last_sender_type",
            "admin_unread_count",
            "customer_unread_count",
            "updated_at",
        ]
    )


def create_chat_message(
    session,
    sender_type,
    sender_user=None,
    sender_name="",
    content="",
    attachment=None,
    client_message_id=None,
):
    """Tạo tin nhắn mới, có chống duplicate theo client_message_id."""
    sender_name = (sender_name or "").strip()
    content = (content or "").strip()
    client_message_id = (client_message_id or "").strip() or None

    if sender_type == "customer" and attachment:
        raise ValidationError("Khách hàng chỉ được gửi tin nhắn văn bản.")

    message_type = validate_admin_attachment(attachment)

    if content:
        content = normalize_text_message(content)

    if not content and not attachment:
        raise ValidationError("Vui lòng nhập nội dung tin nhắn.")

    with transaction.atomic():
        locked_session = ChatSession.objects.select_for_update().get(pk=session.pk)

        if client_message_id:
            existing = ChatMessage.objects.filter(
                session=locked_session,
                client_message_id=client_message_id,
            ).first()
            if existing:
                session.refresh_from_db()
                return existing, False

        message = ChatMessage(
            session=locked_session,
            sender_type=sender_type,
            sender=sender_user,
            sender_name=sender_name,
            message_type=message_type if attachment else "text",
            content=content,
            client_message_id=client_message_id,
        )

        if attachment:
            message.attachment = attachment
            message.attachment_name = attachment.name
            message.attachment_size = getattr(attachment, "size", 0) or 0
            message.attachment_content_type = getattr(attachment, "content_type", "") or ""

        message.save()
        touch_session_from_message(locked_session, message)
        session.refresh_from_db()
        return message, True


def mark_session_read_by_admin(session):
    """Reset unread phía admin khi một admin đã xem phiên."""
    if session.admin_unread_count:
        session.admin_unread_count = 0
        session.updated_at = timezone.now()
        ChatSession.objects.filter(pk=session.pk).update(
            admin_unread_count=0,
            updated_at=session.updated_at,
        )


def mark_session_read_by_customer(session):
    """Reset unread phía khách khi khách mở chat."""
    if session.customer_unread_count:
        session.customer_unread_count = 0
        session.updated_at = timezone.now()
        ChatSession.objects.filter(pk=session.pk).update(
            customer_unread_count=0,
            updated_at=session.updated_at,
        )


def get_chat_sessions_queryset(search="", status=""):
    """Queryset danh sách phiên chat cho admin."""
    sessions = ChatSession.objects.select_related("customer", "customer__user")

    if status:
        sessions = sessions.filter(status=status)

    search = (search or "").strip()
    if search:
        sessions = sessions.filter(
            Q(chat_code__icontains=search)
            | Q(customer__full_name__icontains=search)
            | Q(customer__phone__icontains=search)
            | Q(last_message_preview__icontains=search)
            | Q(source_page__icontains=search)
        )

    return sessions.order_by("-last_message_at", "-created_at")


def get_admin_chat_sessions_data(search="", status="", limit=200):
    """
    Trả về danh sách phiên chat cho admin cùng tổng unread phía admin.

    unreadTotal được tính trên toàn bộ queryset đã filter,
    không chỉ phần sessions đang hiển thị.
    """
    sessions_qs = get_chat_sessions_queryset(search=search, status=status)
    unread_total = sessions_qs.order_by().aggregate(total=Sum("admin_unread_count"))["total"] or 0
    return list(sessions_qs[:limit]), unread_total


def serialize_chat_message(message):
    """Serialize tin nhắn cho frontend."""
    return {
        "id": message.id,
        "sessionCode": message.session.chat_code,
        "senderType": message.sender_type,
        "senderName": message.sender_name or "",
        "messageType": message.message_type,
        "content": message.content or "",
        "status": message.status,
        "createdAt": message.created_at.isoformat(),
        "timeLabel": timezone.localtime(message.created_at).strftime("%H:%M"),
        "attachmentUrl": message.attachment.url if message.attachment else "",
        "attachmentName": message.attachment_name or "",
        "attachmentSize": message.attachment_size or 0,
        "attachmentContentType": message.attachment_content_type or "",
        "isImage": message.is_image(),
    }


def serialize_chat_session(session):
    """Serialize phiên chat cho danh sách admin và widget khách."""
    return {
        "id": session.id,
        "chatCode": session.chat_code,
        "customerType": session.customer_type,
        "customerName": session.get_customer_display_name(),
        "customerPhone": session.get_customer_contact(),
        "status": session.status,
        "sourcePage": session.source_page or "",
        "lastMessagePreview": session.get_last_message_label(),
        "lastSenderType": session.last_sender_type or "",
        "lastMessageAt": session.last_message_at.isoformat() if session.last_message_at else "",
        "lastMessageTimeLabel": timezone.localtime(session.last_message_at).strftime("%H:%M")
        if session.last_message_at
        else "",
        "adminUnreadCount": session.admin_unread_count,
        "customerUnreadCount": session.customer_unread_count,
        "isGuest": session.customer_type == "guest",
    }


def serialize_chat_messages(messages):
    return [serialize_chat_message(message) for message in messages]


def build_sse_payload(event, data):
    """Chuẩn hóa SSE payload."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def get_attachment_accept_string():
    """Chuỗi accept cho input file phía admin."""
    return ",".join(sorted(ALLOWED_IMAGE_TYPES | ALLOWED_FILE_TYPES | ALLOWED_FILE_EXTENSIONS))
