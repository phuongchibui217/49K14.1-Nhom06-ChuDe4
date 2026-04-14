import json
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from customers.models import CustomerProfile

from .models import ChatMessage, ChatSession
from .services import create_chat_message


class BaseChatTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._temp_media = tempfile.mkdtemp(prefix="spa-chat-test-")
        cls._media_override = override_settings(MEDIA_ROOT=cls._temp_media)
        cls._media_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls._media_override.disable()
        shutil.rmtree(cls._temp_media, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.customer_user = User.objects.create_user(
            username="0912345678",
            password="testpass123",
            first_name="Lan",
            last_name="Nguyen",
            email="lan@example.com",
        )
        self.customer_profile = CustomerProfile.objects.create(
            user=self.customer_user,
            phone="0912345678",
            full_name="Lan Nguyen",
        )

        self.other_customer_user = User.objects.create_user(
            username="0988888888",
            password="testpass123",
            first_name="Minh",
            last_name="Tran",
            email="minh@example.com",
        )
        self.other_customer_profile = CustomerProfile.objects.create(
            user=self.other_customer_user,
            phone="0988888888",
            full_name="Minh Tran",
        )

        self.admin_user = User.objects.create_user(
            username="receptionist",
            password="testpass123",
            first_name="Le",
            last_name="Reception",
            email="admin@example.com",
            is_staff=True,
        )

    def prime_csrf(self, client, url):
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("csrftoken", client.cookies)
        return client.cookies["csrftoken"].value

    def post_json(self, client, url, payload, csrf_token):
        return client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

    def bootstrap_guest(self, client, source="/"):
        response = client.get(
            reverse("chat:api_customer_chat_bootstrap"),
            {"source": source},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        return payload

    def bootstrap_authenticated_customer(self, client, source="/"):
        response = client.get(
            reverse("chat:api_customer_chat_bootstrap"),
            {"source": source},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        return payload


class CustomerChatApiTests(BaseChatTestCase):
    def test_guest_can_send_text_message_with_duplicate_protection_and_stream(self):
        client = Client()
        guest_bootstrap = self.bootstrap_guest(client, source="/about/")
        csrf_token = self.prime_csrf(client, reverse("pages:index"))

        chat_code = guest_bootstrap["session"]["chatCode"]
        guest_key = guest_bootstrap["guestKey"]
        send_url = reverse("chat:api_customer_chat_send", args=[chat_code])

        payload = {
            "content": "Xin chào Spa ANA",
            "guestKey": guest_key,
            "clientMessageId": "guest-msg-001",
        }
        first_send = self.post_json(client, send_url, payload, csrf_token)
        self.assertEqual(first_send.status_code, 200)
        first_data = first_send.json()
        self.assertTrue(first_data["success"])
        self.assertEqual(first_data["message"]["content"], "Xin chào Spa ANA")
        self.assertEqual(first_data["message"]["messageType"], "text")

        duplicate_send = self.post_json(client, send_url, payload, csrf_token)
        self.assertEqual(duplicate_send.status_code, 200)
        duplicate_data = duplicate_send.json()
        self.assertEqual(duplicate_data["message"]["id"], first_data["message"]["id"])
        self.assertEqual(ChatMessage.objects.filter(session__chat_code=chat_code).count(), 1)

        session = ChatSession.objects.get(chat_code=chat_code)
        self.assertEqual(session.customer_type, "guest")
        self.assertEqual(session.source_page, "/about/")
        self.assertEqual(session.admin_unread_count, 1)
        self.assertEqual(session.customer_unread_count, 0)

        stream_response = client.get(
            reverse("chat:api_customer_chat_stream", args=[chat_code]),
            {"guestKey": guest_key, "lastMessageId": 0},
        )
        self.assertEqual(stream_response.status_code, 200)
        self.assertEqual(stream_response["Content-Type"], "text/event-stream")

        stream_iter = iter(stream_response.streaming_content)
        ready_chunk = next(stream_iter)
        message_chunk = next(stream_iter)
        stream_response.close()

        ready_text = ready_chunk.decode() if isinstance(ready_chunk, bytes) else ready_chunk
        message_text = message_chunk.decode() if isinstance(message_chunk, bytes) else message_chunk
        self.assertIn("event: ready", ready_text)
        self.assertIn("event: message", message_text)
        self.assertIn("Xin chào Spa ANA", message_text)

    def test_guest_history_is_not_restored_without_guest_key(self):
        first_client = Client()
        guest_bootstrap = self.bootstrap_guest(first_client, source="/")
        csrf_token = self.prime_csrf(first_client, reverse("pages:index"))

        self.post_json(
            first_client,
            reverse("chat:api_customer_chat_send", args=[guest_bootstrap["session"]["chatCode"]]),
            {
                "content": "Tôi cần tư vấn",
                "guestKey": guest_bootstrap["guestKey"],
                "clientMessageId": "guest-msg-restore",
            },
            csrf_token,
        )

        second_client = Client()
        new_bootstrap = self.bootstrap_guest(second_client, source="/")

        self.assertNotEqual(
            new_bootstrap["session"]["chatCode"],
            guest_bootstrap["session"]["chatCode"],
        )
        self.assertEqual(new_bootstrap["messages"], [])
        self.assertTrue(new_bootstrap["isNewSession"])
        self.assertFalse(new_bootstrap["historyPreserved"])

    def test_authenticated_customer_history_is_preserved_between_logins(self):
        first_client = Client()
        first_client.force_login(self.customer_user)
        csrf_token = self.prime_csrf(first_client, reverse("pages:index"))

        first_bootstrap = self.bootstrap_authenticated_customer(first_client, source="/home/")
        first_chat_code = first_bootstrap["session"]["chatCode"]

        send_response = self.post_json(
            first_client,
            reverse("chat:api_customer_chat_send", args=[first_chat_code]),
            {
                "content": "Tôi muốn đặt lịch chăm sóc da",
                "clientMessageId": "auth-msg-001",
            },
            csrf_token,
        )
        self.assertEqual(send_response.status_code, 200)

        second_client = Client()
        second_client.force_login(self.customer_user)
        second_bootstrap = self.bootstrap_authenticated_customer(second_client, source="/home/")

        self.assertEqual(second_bootstrap["session"]["chatCode"], first_chat_code)
        self.assertTrue(second_bootstrap["historyPreserved"])
        self.assertEqual(len(second_bootstrap["messages"]), 1)
        self.assertEqual(
            second_bootstrap["messages"][0]["content"],
            "Tôi muốn đặt lịch chăm sóc da",
        )
        self.assertEqual(ChatSession.objects.filter(customer=self.customer_profile).count(), 1)

    def test_authenticated_customer_cannot_access_another_customers_chat(self):
        owner_client = Client()
        owner_client.force_login(self.customer_user)
        owner_csrf = self.prime_csrf(owner_client, reverse("pages:index"))
        owner_bootstrap = self.bootstrap_authenticated_customer(owner_client, source="/")

        self.post_json(
            owner_client,
            reverse("chat:api_customer_chat_send", args=[owner_bootstrap["session"]["chatCode"]]),
            {
                "content": "Đây là phiên của tôi",
                "clientMessageId": "owner-msg-001",
            },
            owner_csrf,
        )

        intruder_client = Client()
        intruder_client.force_login(self.other_customer_user)
        intruder_csrf = self.prime_csrf(intruder_client, reverse("pages:index"))

        forbidden_response = self.post_json(
            intruder_client,
            reverse("chat:api_customer_chat_send", args=[owner_bootstrap["session"]["chatCode"]]),
            {
                "content": "Tôi không nên vào được phiên này",
                "clientMessageId": "intruder-msg-001",
            },
            intruder_csrf,
        )

        self.assertEqual(forbidden_response.status_code, 403)
        self.assertFalse(forbidden_response.json()["success"])
        self.assertEqual(
            ChatMessage.objects.filter(session__chat_code=owner_bootstrap["session"]["chatCode"]).count(),
            1,
        )

    def test_guest_customer_cannot_upload_attachments(self):
        client = Client()
        guest_bootstrap = self.bootstrap_guest(client, source="/")
        csrf_token = self.prime_csrf(client, reverse("pages:index"))
        attachment = SimpleUploadedFile(
            "ghi-chu.txt",
            b"noi dung",
            content_type="text/plain",
        )

        response = client.post(
            reverse("chat:api_customer_chat_send", args=[guest_bootstrap["session"]["chatCode"]]),
            data={
                "guestKey": guest_bootstrap["guestKey"],
                "attachment": attachment,
            },
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])
        self.assertIn("văn bản", response.json()["error"])
        self.assertEqual(ChatMessage.objects.count(), 0)


class AdminChatApiTests(BaseChatTestCase):
    def setUp(self):
        super().setUp()
        self.guest_session = ChatSession.objects.create(
            customer_type="guest",
            guest_session_key="guest-session-001",
            source_page="/",
        )
        self.customer_message, _ = create_chat_message(
            session=self.guest_session,
            sender_type="customer",
            sender_name="Khách vãng lai",
            content="Tôi cần gặp lễ tân",
            client_message_id="guest-seed-msg",
        )

    def test_admin_can_reply_with_attachment_and_updates_unread_state(self):
        client = Client()
        client.force_login(self.admin_user)
        csrf_token = self.prime_csrf(client, reverse("chat:admin_live_chat"))

        attachment = SimpleUploadedFile(
            "quy-trinh.pdf",
            b"%PDF-1.4\nchat attachment\n",
            content_type="application/pdf",
        )

        response = client.post(
            reverse("chat:api_admin_chat_send", args=[self.guest_session.chat_code]),
            data={
                "content": "Spa gửi bạn tài liệu tham khảo.",
                "clientMessageId": "admin-msg-001",
                "attachment": attachment,
            },
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["message"]["senderType"], "admin")
        self.assertEqual(payload["message"]["messageType"], "file")
        self.assertTrue(payload["message"]["attachmentUrl"])
        self.assertEqual(payload["message"]["attachmentName"], "quy-trinh.pdf")

        self.guest_session.refresh_from_db()
        self.assertEqual(self.guest_session.admin_unread_count, 0)
        self.assertEqual(self.guest_session.customer_unread_count, 1)
        self.assertEqual(ChatMessage.objects.filter(session=self.guest_session).count(), 2)

    def test_admin_loading_messages_marks_session_as_read(self):
        self.assertEqual(self.guest_session.admin_unread_count, 1)

        client = Client()
        client.force_login(self.admin_user)
        response = client.get(
            reverse("chat:api_admin_chat_messages", args=[self.guest_session.chat_code])
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["session"]["chatCode"], self.guest_session.chat_code)
        self.assertEqual(len(payload["messages"]), 1)

        self.guest_session.refresh_from_db()
        self.assertEqual(self.guest_session.admin_unread_count, 0)

    def test_admin_sessions_api_returns_unread_total_and_chat_identifier(self):
        client = Client()
        client.force_login(self.admin_user)

        response = client.get(reverse("chat:api_admin_chat_sessions"))
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertTrue(payload["success"])
        self.assertEqual(payload["unreadTotal"], 1)
        self.assertEqual(len(payload["sessions"]), 1)
        self.assertEqual(payload["sessions"][0]["chatCode"], self.guest_session.chat_code)

    def test_admin_sidebar_includes_realtime_chat_badge(self):
        client = Client()
        client.force_login(self.admin_user)

        response = client.get(reverse("appointments:admin_appointments"))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn('id="adminSidebarChatBadge"', content)
        self.assertIn(reverse("chat:api_admin_chat_sessions"), content)
        self.assertIn(reverse("chat:api_admin_chat_sessions_stream"), content)

    def test_non_staff_user_cannot_access_admin_chat_api(self):
        client = Client()
        client.force_login(self.customer_user)

        response = client.get(reverse("chat:api_admin_chat_sessions"))
        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json()["success"])
