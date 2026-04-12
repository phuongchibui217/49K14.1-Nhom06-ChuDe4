from django.contrib import admin

from .models import ChatMessage, ChatSession


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = [
        "sender_type",
        "sender",
        "sender_name",
        "message_type",
        "content",
        "attachment",
        "created_at",
    ]
    fields = [
        "sender_type",
        "sender_name",
        "message_type",
        "content",
        "attachment",
        "created_at",
    ]


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = [
        "chat_code",
        "customer_type",
        "customer",
        "status",
        "admin_unread_count",
        "customer_unread_count",
        "last_message_at",
    ]
    list_filter = ["customer_type", "status", "created_at"]
    search_fields = [
        "chat_code",
        "customer__full_name",
        "customer__phone",
        "guest_session_key",
        "last_message_preview",
    ]
    readonly_fields = [
        "chat_code",
        "guest_session_key",
        "last_message_preview",
        "last_sender_type",
        "last_message_at",
        "created_at",
        "updated_at",
        "closed_at",
    ]
    list_select_related = ["customer", "customer__user"]
    inlines = [ChatMessageInline]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = [
        "session",
        "sender_name",
        "sender_type",
        "message_type",
        "status",
        "created_at",
    ]
    list_filter = ["sender_type", "message_type", "status", "created_at"]
    search_fields = ["session__chat_code", "sender_name", "content", "attachment_name"]
    readonly_fields = [
        "session",
        "sender",
        "sender_name",
        "message_type",
        "content",
        "attachment",
        "attachment_name",
        "attachment_size",
        "attachment_content_type",
        "client_message_id",
        "status",
        "created_at",
        "updated_at",
    ]
