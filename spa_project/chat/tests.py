import json
import shutil
import tempfile

from asgiref.sync import async_to_sync, sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, TransactionTestCase, override_settings
from django.urls import reverse

from customers.models import CustomerProfile
from spa_project.asgi import application

from .models import ChatMessage, ChatSession, SessionStaff
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

    def send_new_customer_message(
        self,
        client,
        csrf_token,
        *,
        content,
        guest_key="",
        source_page="/",
        client_message_id="customer-msg-001",
    ):
        payload = {
            "content": content,
            "sourcePage": source_page,
            "clientMessageId": client_message_id,
        }
        if guest_key:
            payload["guestKey"] = guest_key

        return self.post_json(
            client,
            reverse("chat:api_customer_chat_send_new"),
            payload,
            csrf_token,
        )


class CustomerChatApiTests(BaseChatTestCase):
    def test_guest_bootstrap_returns_empty_state_until_first_message(self):
        client = Client()

        payload = self.bootstrap_guest(client, source="/about/")

        self.assertIsNone(payload["session"])
        self.assertEqual(payload["messages"], [])
        self.assertEqual(payload["guestKey"], "")
        self.assertTrue(payload["isNewSession"])
        self.assertFalse(payload["historyPreserved"])

    def test_guest_can_send_first_message_then_duplicate_protection_still_works(self):
        client = Client()
        guest_bootstrap = self.bootstrap_guest(client, source="/about/")
        self.assertIsNone(guest_bootstrap["session"])

        csrf_token = self.prime_csrf(client, reverse("pages:index"))
        first_send = self.send_new_customer_message(
            client,
            csrf_token,
            content="Xin chào Spa ANA",
            source_page="/about/",
            client_message_id="guest-msg-001",
        )

        self.assertEqual(first_send.status_code, 200)
        first_payload = first_send.json()
        self.assertTrue(first_payload["success"])
        self.assertEqual(first_payload["message"]["content"], "Xin chào Spa ANA")
        self.assertEqual(first_payload["message"]["messageType"], "text")
        self.assertTrue(first_payload["guestKey"])

        chat_code = first_payload["session"]["chatCode"]
        guest_key = first_payload["guestKey"]

        duplicate_send = self.post_json(
            client,
            reverse("chat:api_customer_chat_send", args=[chat_code]),
            {
                "content": "Xin chào Spa ANA",
                "guestKey": guest_key,
                "clientMessageId": "guest-msg-001",
            },
            csrf_token,
        )
        self.assertEqual(duplicate_send.status_code, 200)
        duplicate_payload = duplicate_send.json()
        self.assertEqual(duplicate_payload["message"]["id"], first_payload["message"]["id"])
        self.assertEqual(ChatMessage.objects.filter(session__chat_code=chat_code).count(), 1)

        session = ChatSession.objects.get(chat_code=chat_code)
        self.assertEqual(session.customer_type, "guest")
        self.assertEqual(session.source_page, "/about/")
        self.assertEqual(session.admin_unread_count, 1)
        self.assertEqual(session.customer_unread_count, 0)

    def test_customer_bootstrap_masks_admin_sender_name(self):
        session = ChatSession.objects.create(
            customer_type="guest",
            guest_session_key="guest-session-mask-admin",
            source_page="/",
        )
        create_chat_message(
            session=session,
            sender_type="admin",
            sender_user=self.admin_user,
            sender_name=self.admin_user.get_full_name() or self.admin_user.username,
            content="Spa ANA xin chào bạn.",
            client_message_id="admin-mask-bootstrap-001",
        )

        client = Client()
        response = client.get(
            reverse("chat:api_customer_chat_bootstrap"),
            {
                "source": "/",
                "guestKey": session.guest_session_key,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(len(payload["messages"]), 1)
        self.assertEqual(payload["messages"][0]["senderType"], "admin")
        self.assertEqual(payload["messages"][0]["senderName"], "Nhân viên")

    def test_guest_history_is_not_restored_without_guest_key(self):
        first_client = Client()
        csrf_token = self.prime_csrf(first_client, reverse("pages:index"))

        first_send = self.send_new_customer_message(
            first_client,
            csrf_token,
            content="Tôi cần tư vấn",
            source_page="/",
            client_message_id="guest-msg-restore",
        ).json()

        self.assertTrue(first_send["success"])

        second_client = Client()
        new_bootstrap = self.bootstrap_guest(second_client, source="/")

        self.assertIsNone(new_bootstrap["session"])
        self.assertEqual(new_bootstrap["messages"], [])
        self.assertTrue(new_bootstrap["isNewSession"])
        self.assertFalse(new_bootstrap["historyPreserved"])

    def test_guest_history_is_restored_when_guest_key_is_reused(self):
        client = Client()
        csrf_token = self.prime_csrf(client, reverse("pages:index"))

        first_send_response = self.send_new_customer_message(
            client,
            csrf_token,
            content="Giữ lại lịch sử chat guest",
            source_page="/",
            client_message_id="guest-msg-reuse",
        )
        first_send = first_send_response.json()
        self.assertEqual(first_send_response.status_code, 200)

        second_bootstrap_response = client.get(
            reverse("chat:api_customer_chat_bootstrap"),
            {
                "source": "/",
                "guestKey": first_send["guestKey"],
            },
        )

        self.assertEqual(second_bootstrap_response.status_code, 200)
        second_bootstrap = second_bootstrap_response.json()
        self.assertTrue(second_bootstrap["success"])
        self.assertEqual(second_bootstrap["session"]["chatCode"], first_send["session"]["chatCode"])
        self.assertEqual(second_bootstrap["guestKey"], first_send["guestKey"])
        self.assertFalse(second_bootstrap["isNewSession"])
        self.assertEqual(len(second_bootstrap["messages"]), 1)
        self.assertEqual(second_bootstrap["messages"][0]["content"], "Giữ lại lịch sử chat guest")

    def test_authenticated_customer_history_is_preserved_between_logins(self):
        first_client = Client()
        first_client.force_login(self.customer_user)
        csrf_token = self.prime_csrf(first_client, reverse("pages:index"))

        first_bootstrap = self.bootstrap_authenticated_customer(first_client, source="/home/")
        self.assertIsNone(first_bootstrap["session"])

        send_response = self.send_new_customer_message(
            first_client,
            csrf_token,
            content="Tôi muốn đặt lịch chăm sóc da",
            source_page="/home/",
            client_message_id="auth-msg-001",
        )
        self.assertEqual(send_response.status_code, 200)
        first_chat_code = send_response.json()["session"]["chatCode"]

        second_client = Client()
        second_client.force_login(self.customer_user)
        second_bootstrap = self.bootstrap_authenticated_customer(second_client, source="/home/")

        self.assertEqual(second_bootstrap["session"]["chatCode"], first_chat_code)
        self.assertTrue(second_bootstrap["historyPreserved"])
        self.assertEqual(len(second_bootstrap["messages"]), 1)
        self.assertEqual(second_bootstrap["messages"][0]["content"], "Tôi muốn đặt lịch chăm sóc da")
        self.assertEqual(ChatSession.objects.filter(customer=self.customer_profile).count(), 1)

    def test_authenticated_customer_cannot_access_another_customers_chat(self):
        owner_client = Client()
        owner_client.force_login(self.customer_user)
        owner_csrf = self.prime_csrf(owner_client, reverse("pages:index"))

        owner_send = self.send_new_customer_message(
            owner_client,
            owner_csrf,
            content="Đây là phiên của tôi",
            source_page="/",
            client_message_id="owner-msg-001",
        ).json()

        intruder_client = Client()
        intruder_client.force_login(self.other_customer_user)
        intruder_csrf = self.prime_csrf(intruder_client, reverse("pages:index"))

        forbidden_response = self.post_json(
            intruder_client,
            reverse("chat:api_customer_chat_send", args=[owner_send["session"]["chatCode"]]),
            {
                "content": "Tôi không nên vào được phiên này",
                "clientMessageId": "intruder-msg-001",
            },
            intruder_csrf,
        )

        self.assertEqual(forbidden_response.status_code, 403)
        self.assertFalse(forbidden_response.json()["success"])
        self.assertEqual(
            ChatMessage.objects.filter(session__chat_code=owner_send["session"]["chatCode"]).count(),
            1,
        )

    def test_guest_customer_cannot_upload_attachments(self):
        client = Client()
        csrf_token = self.prime_csrf(client, reverse("pages:index"))
        attachment = SimpleUploadedFile(
            "ghi-chu.txt",
            b"noi dung",
            content_type="text/plain",
        )

        response = client.post(
            reverse("chat:api_customer_chat_send_new"),
            data={
                "content": "Co file",
                "sourcePage": "/",
                "attachment": attachment,
            },
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])
        self.assertIn("van ban", response.json()["error"].lower())
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
        self.assertEqual(payload["message"]["senderName"], self.admin_user.get_full_name() or self.admin_user.username)
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
        response = client.get(reverse("chat:api_admin_chat_messages", args=[self.guest_session.chat_code]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["session"]["chatCode"], self.guest_session.chat_code)
        self.assertEqual(len(payload["messages"]), 1)

        self.guest_session.refresh_from_db()
        self.assertEqual(self.guest_session.admin_unread_count, 0)
        SessionStaff.objects.get(session=self.guest_session, staff=self.admin_user)

    def test_admin_session_staff_membership_is_created_once_per_session(self):
        client = Client()
        client.force_login(self.admin_user)
        csrf_token = self.prime_csrf(client, reverse("chat:admin_live_chat"))

        first_open = client.get(reverse("chat:api_admin_chat_messages", args=[self.guest_session.chat_code]))
        self.assertEqual(first_open.status_code, 200)
        self.assertEqual(
            SessionStaff.objects.filter(session=self.guest_session, staff=self.admin_user).count(),
            1,
        )

        send_response = self.post_json(
            client,
            reverse("chat:api_admin_chat_send", args=[self.guest_session.chat_code]),
            {
                "content": "Admin đã tham gia phiên chat.",
                "clientMessageId": "admin-msg-session-staff",
            },
            csrf_token,
        )
        self.assertEqual(send_response.status_code, 200)
        self.assertEqual(
            SessionStaff.objects.filter(session=self.guest_session, staff=self.admin_user).count(),
            1,
        )

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
        self.assertIn("/ws/admin/chat/sessions/", content)

    def test_admin_live_chat_template_includes_websocket_paths(self):
        client = Client()
        client.force_login(self.admin_user)

        response = client.get(reverse("chat:admin_live_chat"))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn("/ws/admin/chat/sessions/", content)
        self.assertIn("/ws/admin/chat/sessions/__CHAT_CODE__/", content)

    def test_non_staff_user_cannot_access_admin_chat_api(self):
        client = Client()
        client.force_login(self.customer_user)

        response = client.get(reverse("chat:api_admin_chat_sessions"))
        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json()["success"])


class BaseChatWebSocketTestCase(TransactionTestCase):
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

    def build_cookie_header(self, client):
        cookies = [f"{key}={morsel.value}" for key, morsel in client.cookies.items()]
        return "; ".join(cookies)

    def get_websocket_headers(self, client=None):
        headers = [(b"origin", b"http://localhost")]
        if client:
            cookie_header = self.build_cookie_header(client)
            if cookie_header:
                headers.append((b"cookie", cookie_header.encode("utf-8")))
        return headers

    async def connect_websocket(self, path, client=None):
        communicator = WebsocketCommunicator(
            application,
            path,
            headers=self.get_websocket_headers(client),
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        return communicator

    async def receive_ws_json(self, communicator, timeout=5):
        return await communicator.receive_json_from(timeout=timeout)

    async def disconnect_ws(self, communicator):
        await communicator.disconnect()


class ChatWebSocketTests(BaseChatWebSocketTestCase):
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

    def test_guest_websocket_receives_new_message_event(self):
        async def scenario():
            guest_client = Client(HTTP_HOST="localhost")
            csrf_token = await sync_to_async(self.prime_csrf, thread_sensitive=True)(
                guest_client,
                reverse("pages:index"),
            )

            communicator = await self.connect_websocket(
                f"/ws/chat/session/{self.guest_session.chat_code}/?guestKey={self.guest_session.guest_session_key}&lastMessageId={self.customer_message.id}"
            )

            try:
                ready_event = await self.receive_ws_json(communicator)
                self.assertEqual(ready_event["event"], "ready")

                send_response = await sync_to_async(self.post_json, thread_sensitive=True)(
                    guest_client,
                    reverse("chat:api_customer_chat_send", args=[self.guest_session.chat_code]),
                    {
                        "content": "Xin chào Spa ANA",
                        "guestKey": self.guest_session.guest_session_key,
                        "clientMessageId": "guest-ws-msg-001",
                    },
                    csrf_token,
                )
                self.assertEqual(send_response.status_code, 200)

                message_event = await self.receive_ws_json(communicator)
                self.assertEqual(message_event["event"], "message")
                self.assertEqual(message_event["message"]["content"], "Xin chào Spa ANA")
            finally:
                await self.disconnect_ws(communicator)

        async_to_sync(scenario)()

    def test_customer_websocket_masks_admin_sender_name(self):
        async def scenario():
            communicator = await self.connect_websocket(
                f"/ws/chat/session/{self.guest_session.chat_code}/?guestKey={self.guest_session.guest_session_key}&lastMessageId={self.customer_message.id}"
            )

            try:
                ready_event = await self.receive_ws_json(communicator)
                self.assertEqual(ready_event["event"], "ready")

                admin_client = Client(HTTP_HOST="localhost")
                await sync_to_async(admin_client.force_login, thread_sensitive=True)(self.admin_user)
                csrf_token = await sync_to_async(self.prime_csrf, thread_sensitive=True)(
                    admin_client,
                    reverse("chat:admin_live_chat"),
                )

                send_response = await sync_to_async(self.post_json, thread_sensitive=True)(
                    admin_client,
                    reverse("chat:api_admin_chat_send", args=[self.guest_session.chat_code]),
                    {
                        "content": "Nhân viên sẽ hỗ trợ bạn ngay.",
                        "clientMessageId": "admin-ws-mask-customer-001",
                    },
                    csrf_token,
                )
                self.assertEqual(send_response.status_code, 200)
                self.assertEqual(
                    send_response.json()["message"]["senderName"],
                    self.admin_user.get_full_name() or self.admin_user.username,
                )

                message_event = await self.receive_ws_json(communicator)
                self.assertEqual(message_event["event"], "message")
                self.assertEqual(message_event["message"]["senderType"], "admin")
                self.assertEqual(message_event["message"]["senderName"], "Nhân viên")
            finally:
                await self.disconnect_ws(communicator)

        async_to_sync(scenario)()

    def test_admin_sessions_websocket_sends_initial_snapshot(self):
        async def scenario():
            admin_client = Client(HTTP_HOST="localhost")
            await sync_to_async(admin_client.force_login, thread_sensitive=True)(self.admin_user)

            communicator = await self.connect_websocket("/ws/admin/chat/sessions/", admin_client)
            try:
                sessions_event = await self.receive_ws_json(communicator)

                self.assertEqual(sessions_event["event"], "sessions")
                self.assertEqual(sessions_event["unreadTotal"], 1)
                self.assertTrue(
                    any(item["chatCode"] == self.guest_session.chat_code for item in sessions_event["sessions"])
                )
            finally:
                await self.disconnect_ws(communicator)

        async_to_sync(scenario)()

    def test_admin_session_websocket_receives_customer_message(self):
        async def scenario():
            admin_client = Client(HTTP_HOST="localhost")
            await sync_to_async(admin_client.force_login, thread_sensitive=True)(self.admin_user)
            communicator = await self.connect_websocket(
                f"/ws/admin/chat/sessions/{self.guest_session.chat_code}/?lastMessageId={self.customer_message.id}",
                admin_client,
            )
            try:
                ready_event = await self.receive_ws_json(communicator)
                self.assertEqual(ready_event["event"], "ready")

                guest_client = Client(HTTP_HOST="localhost")
                csrf_token = await sync_to_async(self.prime_csrf, thread_sensitive=True)(
                    guest_client,
                    reverse("pages:index"),
                )
                send_response = await sync_to_async(self.post_json, thread_sensitive=True)(
                    guest_client,
                    reverse("chat:api_customer_chat_send", args=[self.guest_session.chat_code]),
                    {
                        "content": "Khách vừa gửi thêm tin nhắn",
                        "guestKey": self.guest_session.guest_session_key,
                        "clientMessageId": "guest-ws-admin-msg-002",
                    },
                    csrf_token,
                )
                self.assertEqual(send_response.status_code, 200)

                message_event = await self.receive_ws_json(communicator)
                self.assertEqual(message_event["event"], "message")
                self.assertEqual(message_event["message"]["content"], "Khách vừa gửi thêm tin nhắn")
            finally:
                await self.disconnect_ws(communicator)

        async_to_sync(scenario)()
