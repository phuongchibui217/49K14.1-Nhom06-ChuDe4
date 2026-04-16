from urllib.parse import parse_qs

from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model

from channels.generic.websocket import JsonWebsocketConsumer

from .models import ChatMessage, ChatSession
from .services import (
    ADMIN_CHAT_SESSIONS_GROUP,
    ensure_staff_session_participation,
    get_admin_chat_group,
    get_admin_chat_sessions_data,
    get_customer_chat_group,
    serialize_customer_chat_message,
    serialize_chat_message,
    serialize_chat_session,
)

User = get_user_model()


def get_customer_session_access(chat_code, user_id, guest_key):
    session = ChatSession.objects.select_related("customer", "customer__user").get(chat_code=chat_code)
    if session.customer_type == "authenticated":
        allowed = bool(user_id and session.customer and session.customer.user_id == user_id)
    else:
        allowed = bool(guest_key and session.guest_session_key == guest_key)
    return {
        "allowed": allowed,
        "session_id": session.id,
        "chat_code": session.chat_code,
    }


def get_admin_session_meta(chat_code):
    session = ChatSession.objects.only("id", "chat_code").get(chat_code=chat_code)
    return {
        "session_id": session.id,
        "chat_code": session.chat_code,
    }


def record_staff_participation(session_id, user_id):
    if not user_id:
        return

    session = ChatSession.objects.get(pk=session_id)
    user = User.objects.get(pk=user_id)
    ensure_staff_session_participation(session, user)


def get_pending_messages_payload(session_id, last_message_id, customer_safe=False):
    messages = (
        ChatMessage.objects.select_related("session", "sender")
        .filter(session_id=session_id, id__gt=last_message_id)
        .order_by("id")
    )
    return [
        {
            "message": (
                serialize_customer_chat_message(message)
                if customer_safe
                else serialize_chat_message(message)
            ),
            "session": serialize_chat_session(message.session),
        }
        for message in messages
    ]


def get_admin_sessions_snapshot(search, status):
    sessions, unread_total = get_admin_chat_sessions_data(search=search, status=status)
    return [serialize_chat_session(session) for session in sessions], unread_total


class BaseChatConsumer(JsonWebsocketConsumer):
    def get_query_params(self):
        raw_query = self.scope.get("query_string", b"").decode("utf-8")
        return parse_qs(raw_query)

    def get_query_param(self, key, default=""):
        values = self.get_query_params().get(key)
        if not values:
            return default
        return values[0]

    def get_last_message_id(self):
        try:
            return int(self.get_query_param("lastMessageId", "0") or 0)
        except (TypeError, ValueError):
            return 0

    def send_event(self, event, **payload):
        data = {"event": event}
        data.update(payload)
        self.send_json(data)

    def chat_message(self, event):
        self.send_event(
            "message",
            message=event.get("message"),
            session=event.get("session"),
        )

    def chat_session(self, event):
        self.send_event("session", session=event.get("session"))

    def chat_sessions_refresh(self, event):
        return None

    def disconnect_group(self):
        group_name = getattr(self, "group_name", "")
        if group_name:
            async_to_sync(self.channel_layer.group_discard)(group_name, self.channel_name)
            self.group_name = ""

    def disconnect(self, close_code):
        self.disconnect_group()


class CustomerChatConsumer(BaseChatConsumer):
    def connect(self):
        chat_code = self.scope["url_route"]["kwargs"]["chat_code"]
        guest_key = (self.get_query_param("guestKey", "") or "").strip()
        last_message_id = self.get_last_message_id()
        user = self.scope.get("user")
        user_id = getattr(user, "id", None) if getattr(user, "is_authenticated", False) else None

        try:
            access = get_customer_session_access(chat_code, user_id, guest_key)
        except ChatSession.DoesNotExist:
            self.close(code=4404)
            return

        if not access["allowed"]:
            self.close(code=4403)
            return

        self.chat_code = access["chat_code"]
        self.session_id = access["session_id"]
        self.group_name = get_customer_chat_group(self.chat_code)
        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
        self.accept()
        self.send_event("ready", chatCode=self.chat_code, lastMessageId=last_message_id)

        for item in get_pending_messages_payload(self.session_id, last_message_id, customer_safe=True):
            self.send_event("message", **item)


class AdminChatSessionsConsumer(BaseChatConsumer):
    def connect(self):
        user = self.scope.get("user")
        if not user or not getattr(user, "is_authenticated", False) or not (user.is_staff or user.is_superuser):
            self.close(code=4403)
            return

        self.search = (self.get_query_param("search", "") or "").strip()
        self.status = (self.get_query_param("status", "") or "").strip()
        self.group_name = ADMIN_CHAT_SESSIONS_GROUP
        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
        self.accept()
        self.send_sessions_snapshot()

    def send_sessions_snapshot(self):
        sessions, unread_total = get_admin_sessions_snapshot(self.search, self.status)
        self.send_event(
            "sessions",
            sessions=sessions,
            unreadTotal=unread_total,
        )

    def chat_sessions_refresh(self, event):
        self.send_sessions_snapshot()


class AdminChatSessionConsumer(BaseChatConsumer):
    def connect(self):
        user = self.scope.get("user")
        if not user or not getattr(user, "is_authenticated", False) or not (user.is_staff or user.is_superuser):
            self.close(code=4403)
            return

        chat_code = self.scope["url_route"]["kwargs"]["chat_code"]
        last_message_id = self.get_last_message_id()

        try:
            session_meta = get_admin_session_meta(chat_code)
        except ChatSession.DoesNotExist:
            self.close(code=4404)
            return

        self.chat_code = session_meta["chat_code"]
        self.session_id = session_meta["session_id"]
        record_staff_participation(self.session_id, getattr(user, "id", None))

        self.group_name = get_admin_chat_group(self.chat_code)
        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
        self.accept()
        self.send_event("ready", chatCode=self.chat_code, lastMessageId=last_message_id)

        for item in get_pending_messages_payload(self.session_id, last_message_id):
            self.send_event("message", **item)
