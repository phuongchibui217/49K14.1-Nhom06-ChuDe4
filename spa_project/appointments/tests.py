"""
Tests cho Appointments app — covers models, APIs, views.
"""
import json
from datetime import date, time, timedelta, datetime

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.crypto import get_random_string

from customers.models import CustomerProfile
from spa_services.models import Service, ServiceCategory, ServiceVariant
from .models import Appointment, Room


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

    def test_admin_appointments_page_loads(self):
        client = Client()
        client.force_login(self.admin_user)
        response = client.get(reverse("appointments:admin_appointments"))
        self.assertEqual(response.status_code, 200)


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
