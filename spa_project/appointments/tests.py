"""
Tests cho Appointments app — covers models, APIs, views.
"""
import json
from datetime import date, time, timedelta, datetime

from asgiref.sync import async_to_sync, sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import User
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse
from django.utils.crypto import get_random_string

from customers.models import CustomerProfile
from spa_project.asgi import application
from spa_services.models import Service, ServiceCategory, ServiceVariant
from .models import Appointment, Room
from .realtime import get_pending_booking_count


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def make_staff(username="staff1"):
    return User.objects.create_user(username=username, password="pass1234", is_staff=True)


def make_customer_user(username="cust1", phone="0911111111"):
    user = User.objects.create_user(username=username, password="pass1234")
    profile = CustomerProfile.objects.create(user=user, phone=phone, full_name="Khach Hang")
    return user, profile


def make_room(code="P01", capacity=2):
    return Room.objects.create(code=code, name=f"Phong {code}", capacity=capacity)


def make_category():
    cat, _ = ServiceCategory.objects.get_or_create(code="MS", defaults={"name": "Massage", "status": "ACTIVE"})
    return cat


def make_service(category, created_by):
    svc = Service.objects.create(
        category=category, name="Massage Body", status="ACTIVE",
        image="", created_by=created_by,
    )
    ServiceVariant.objects.create(service=svc, label="60 phut", duration_minutes=60, price=200000)
    return svc


def make_appointment(customer, service, room, created_by, appt_date=None, appt_time=None, status="NOT_ARRIVED"):
    appt_date = appt_date or date.today()
    appt_time = appt_time or time(10, 0)
    end = (datetime.combine(date.today(), appt_time) + timedelta(minutes=60)).time()
    return Appointment.objects.create(
        customer=customer,
        service=service,
        room=room,
        appointment_date=appt_date,
        appointment_time=appt_time,
        end_time=end,
        duration_minutes=60,
        guests=1,
        status=status,
        payment_status="UNPAID",
        source="DIRECT",
        customer_name_snapshot=customer.full_name,
        customer_phone_snapshot=customer.phone,
        created_by=created_by,
    )


# ─────────────────────────────────────────────
# MODEL TESTS
# ─────────────────────────────────────────────

class AppointmentModelTests(TestCase):
    def setUp(self):
        self.staff = make_staff()
        self.cat = make_category()
        self.svc = make_service(self.cat, self.staff)
        self.room = make_room()
        _, self.profile = make_customer_user()

    def test_appointment_code_auto_generated(self):
        appt = make_appointment(self.profile, self.svc, self.room, self.staff)
        self.assertTrue(appt.appointment_code.startswith("APP"))

    def test_snapshot_fields_filled(self):
        appt = make_appointment(self.profile, self.svc, self.room, self.staff)
        self.assertEqual(appt.customer_name_snapshot, self.profile.full_name)
        self.assertEqual(appt.customer_phone_snapshot, self.profile.phone)

    def test_status_choices_valid(self):
        for status in ["PENDING", "NOT_ARRIVED", "ARRIVED", "COMPLETED", "CANCELLED"]:
            appt = make_appointment(self.profile, self.svc, self.room, self.staff, status=status)
            self.assertEqual(appt.status, status)

    def test_invalid_status_raises(self):
        from django.db import IntegrityError
        with self.assertRaises(Exception):
            make_appointment(self.profile, self.svc, self.room, self.staff, status="INVALID")

    def test_room_str(self):
        self.assertIn("P01", str(self.room))


# ─────────────────────────────────────────────
# API TESTS
# ─────────────────────────────────────────────

class AppointmentAPITests(TestCase):
    def setUp(self):
        self.staff = make_staff()
        self.cat = make_category()
        self.svc = make_service(self.cat, self.staff)
        self.room = make_room()
        _, self.profile = make_customer_user()
        self.appt = make_appointment(self.profile, self.svc, self.room, self.staff)
        self.client = Client(enforce_csrf_checks=False)
        self.client.force_login(self.staff)
        self.client.get("/")

    def _csrf(self):
        self.client.get("/")
        return self.client.cookies.get("csrftoken", type("",(object,),{"value":""})()).value if hasattr(self.client.cookies.get("csrftoken",""), "value") else ""

    def post_json(self, url, data):
        csrf_token = getattr(self.client.cookies.get("csrftoken"), "value", "")
        return self.client.post(
            url, json.dumps(data), content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

    # --- Rooms ---
    def test_api_rooms_list_staff(self):
        resp = self.client.get("/api/rooms/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertGreaterEqual(len(data["rooms"]), 1)

    def test_api_rooms_list_anonymous_denied(self):
        c = Client()
        resp = c.get("/api/rooms/")
        self.assertEqual(resp.status_code, 403)

    # --- Appointments list ---
    def test_api_appointments_list(self):
        resp = self.client.get("/api/appointments/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])

    def test_api_appointments_filter_status(self):
        resp = self.client.get("/api/appointments/?status=NOT_ARRIVED")
        self.assertEqual(resp.status_code, 200)
        appts = resp.json()["appointments"]
        for a in appts:
            self.assertEqual(a["apptStatus"], "NOT_ARRIVED")

    def test_api_appointments_search_by_name(self):
        resp = self.client.get("/api/appointments/?q=Khach")
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(len(resp.json()["appointments"]), 1)

    def test_api_appointments_search_no_result(self):
        resp = self.client.get("/api/appointments/?q=XYZNOTEXIST")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()["appointments"]), 0)

    # --- Appointment detail ---
    def test_api_appointment_detail(self):
        resp = self.client.get(f"/api/appointments/{self.appt.appointment_code}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["appointment"]["id"], self.appt.appointment_code)

    def test_api_appointment_detail_not_found(self):
        resp = self.client.get("/api/appointments/NOTEXIST/")
        self.assertEqual(resp.status_code, 404)

    # --- Status update ---
    def test_api_appointment_status_update(self):
        resp = self.post_json(
            f"/api/appointments/{self.appt.appointment_code}/status/",
            {"status": "ARRIVED"}
        )
        self.assertEqual(resp.status_code, 200)
        self.appt.refresh_from_db()
        self.assertEqual(self.appt.status, "ARRIVED")

    def test_api_appointment_status_invalid(self):
        resp = self.post_json(
            f"/api/appointments/{self.appt.appointment_code}/status/",
            {"status": "INVALID_STATUS"}
        )
        self.assertEqual(resp.status_code, 400)

    # --- Delete ---
    def test_api_appointment_delete(self):
        code = self.appt.appointment_code
        resp = self.post_json(f"/api/appointments/{code}/delete/", {})
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Appointment.objects.filter(appointment_code=code).exists())

    # --- Pending count ---
    def test_api_pending_count(self):
        resp = self.client.get("/api/booking/pending-count/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("count", resp.json())


class BookingBadgeTemplateTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="booking-admin",
            password="testpass123",
            is_staff=True,
        )

    def test_admin_base_uses_booking_websocket_config(self):
        client = Client()
        client.force_login(self.admin_user)

        response = client.get(reverse("appointments:admin_appointments"))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn("/ws/admin/booking/pending-count/", content)
        self.assertNotIn("/api/booking/pending-count/stream/", content)


class BookingPendingCountApiTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="booking-admin",
            password="testpass123",
            is_staff=True,
        )
        self.customer_user = User.objects.create_user(
            username="0900000001",
            password="testpass123",
        )
        self.customer = CustomerProfile.objects.create(
            user=self.customer_user,
            phone="0900000001",
            full_name="Khach Hang 1",
        )
        self.room = Room.objects.create(code="R01", name="Phong 1", capacity=2)
        self.category = ServiceCategory.objects.order_by("id").first()
        if not self.category:
            self.category = ServiceCategory.objects.create(
                code=f"CAT-{get_random_string(6)}",
                name=f"Category {get_random_string(6)}",
                status="ACTIVE",
            )
        self.service = Service.objects.create(
            category=self.category,
            name=f"Tri lieu da {get_random_string(6)}",
            status="ACTIVE",
            image="/media/services/test.jpg",
            created_by=self.admin_user,
        )
        ServiceVariant.objects.create(
            service=self.service,
            label="60 phut",
            duration_minutes=60,
            price=100000,
        )

    def create_appointment(self, *, source="ONLINE", status="PENDING"):
        return Appointment.objects.create(
            customer=self.customer,
            service=self.service,
            room=self.room,
            customer_name_snapshot=self.customer.full_name,
            customer_phone_snapshot=self.customer.phone,
            appointment_date=date(2026, 4, 15),
            appointment_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            guests=1,
            status=status,
            source=source,
            created_by=self.admin_user,
        )

    def test_pending_count_only_includes_online_pending_appointments(self):
        self.create_appointment(source="ONLINE", status="PENDING")
        self.create_appointment(source="DIRECT", status="PENDING")
        self.create_appointment(source="ONLINE", status="CANCELLED")

        client = Client()
        client.force_login(self.admin_user)

        response = client.get(reverse("appointments:api_booking_pending_count"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["count"], 1)
        self.assertEqual(get_pending_booking_count(), 1)


class BookingPendingCountWebSocketTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="booking-admin",
            password="testpass123",
            is_staff=True,
        )
        self.customer_user = User.objects.create_user(
            username="0900000002",
            password="testpass123",
        )
        self.customer = CustomerProfile.objects.create(
            user=self.customer_user,
            phone="0900000002",
            full_name="Khach Hang 2",
        )
        self.room = Room.objects.create(code="R02", name="Phong 2", capacity=2)
        self.category = ServiceCategory.objects.order_by("id").first()
        if not self.category:
            self.category = ServiceCategory.objects.create(
                code=f"CAT-{get_random_string(6)}",
                name=f"Category {get_random_string(6)}",
                status="ACTIVE",
            )
        self.service = Service.objects.create(
            category=self.category,
            name=f"Massage body {get_random_string(6)}",
            status="ACTIVE",
            image="/media/services/test-2.jpg",
            created_by=self.admin_user,
        )
        ServiceVariant.objects.create(
            service=self.service,
            label="60 phut",
            duration_minutes=60,
            price=200000,
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

    def create_appointment(self, *, source="ONLINE", status="PENDING"):
        return Appointment.objects.create(
            customer=self.customer,
            service=self.service,
            room=self.room,
            customer_name_snapshot=self.customer.full_name,
            customer_phone_snapshot=self.customer.phone,
            appointment_date=date(2026, 4, 15),
            appointment_time=time(11, 0),
            end_time=time(12, 0),
            duration_minutes=60,
            guests=1,
            status=status,
            source=source,
            created_by=self.admin_user,
        )

    def test_booking_pending_count_websocket_pushes_updates(self):
        async def scenario():
            admin_client = Client(HTTP_HOST="localhost")
            await sync_to_async(admin_client.force_login, thread_sensitive=True)(self.admin_user)

            communicator = await self.connect_websocket(
                "/ws/admin/booking/pending-count/",
                admin_client,
            )

            try:
                initial_event = await self.receive_ws_json(communicator)
                self.assertEqual(initial_event["event"], "pending_count")
                self.assertEqual(initial_event["count"], 0)

                appointment = await sync_to_async(self.create_appointment, thread_sensitive=True)()

                created_event = await self.receive_ws_json(communicator)
                self.assertEqual(created_event["event"], "pending_count")
                self.assertEqual(created_event["count"], 1)

                appointment.status = "CANCELLED"
                await sync_to_async(appointment.save, thread_sensitive=True)()

                updated_event = await self.receive_ws_json(communicator)
                self.assertEqual(updated_event["event"], "pending_count")
                self.assertEqual(updated_event["count"], 0)
            finally:
                await self.disconnect_ws(communicator)

        async_to_sync(scenario)()

    def test_non_staff_user_cannot_connect_booking_pending_count_websocket(self):
        async def scenario():
            customer_client = Client(HTTP_HOST="localhost")
            await sync_to_async(customer_client.force_login, thread_sensitive=True)(self.customer_user)

            communicator = WebsocketCommunicator(
                application,
                "/ws/admin/booking/pending-count/",
                headers=self.get_websocket_headers(customer_client),
            )
            connected, _ = await communicator.connect()
            self.assertFalse(connected)

        async_to_sync(scenario)()


# ─────────────────────────────────────────────
# VIEW TESTS (HTML pages)
# ─────────────────────────────────────────────

class AppointmentViewTests(TestCase):
    def setUp(self):
        self.staff = make_staff()
        self.cat = make_category()
        self.svc = make_service(self.cat, self.staff)
        self.room = make_room()
        self.user, self.profile = make_customer_user()
        self.client = Client()

    def test_admin_appointments_requires_staff(self):
        self.client.force_login(self.user)
        resp = self.client.get(reverse("appointments:admin_appointments"))
        self.assertEqual(resp.status_code, 302)  # redirect to home

    def test_admin_appointments_staff_ok(self):
        self.client.force_login(self.staff)
        resp = self.client.get(reverse("appointments:admin_appointments"))
        self.assertEqual(resp.status_code, 200)

    def test_my_appointments_requires_login(self):
        resp = self.client.get(reverse("appointments:my_appointments"))
        self.assertEqual(resp.status_code, 302)

    def test_my_appointments_customer_ok(self):
        self.client.force_login(self.user)
        resp = self.client.get(reverse("appointments:my_appointments"))
        self.assertEqual(resp.status_code, 200)

    def test_booking_page_customer_ok(self):
        self.client.force_login(self.user)
        resp = self.client.get(reverse("appointments:booking"))
        self.assertEqual(resp.status_code, 200)

    def test_cancel_appointment_wrong_owner(self):
        appt = make_appointment(self.profile, self.svc, self.room, self.staff)
        other_user, _ = make_customer_user(username="other", phone="0922222222")
        self.client.force_login(other_user)
        resp = self.client.post(reverse("appointments:cancel_appointment", args=[appt.id]))
        self.assertEqual(resp.status_code, 302)
        appt.refresh_from_db()
        self.assertNotEqual(appt.status, "CANCELLED")

    def test_cancel_appointment_success(self):
        appt = make_appointment(self.profile, self.svc, self.room, self.staff, status="PENDING")
        self.client.force_login(self.user)
        resp = self.client.post(reverse("appointments:cancel_appointment", args=[appt.id]))
        self.assertEqual(resp.status_code, 302)
        appt.refresh_from_db()
        self.assertEqual(appt.status, "CANCELLED")
