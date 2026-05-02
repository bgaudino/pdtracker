from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from .models import MedicationLog, TypingTest, CheckIn


User = get_user_model()


def make_user(email="test@example.com", password="password"):
    return User.objects.create_user(email=email, password=password)


class TypingTestModelTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.test = TypingTest.objects.create(
            user=self.user,
            prompt="hello world",
            typed="hallo w0rld",
            time_seconds=5,
            timestamp=timezone.now(),
        )

    def test_correct_chars(self):
        self.assertEqual(self.test.correct_chars, 9)

    def test_errors(self):
        self.assertEqual(self.test.errors, 2)

    def test_accuracy(self):
        self.assertEqual(self.test.accuracy, Decimal("81.82"))

    def test_wpm(self):
        self.assertEqual(self.test.wpm, Decimal("21.60"))


class ReportsTestCase(TestCase):
    def setUp(self):
        self.user = make_user()
        self.medication = self.user.medication_set.create(name="TestMed")
        MedicationLog.objects.create(
            user=self.user, medication=self.medication, timestamp=timezone.now()
        )

    def test_checkin_report(self):
        self.user.checkin_set.create(
            bradykinesia=2,
            rigidity=1,
            timestamp=timezone.now() + timezone.timedelta(hours=1),
        )
        self.user.checkin_set.create(
            bradykinesia=4,
            rigidity=2,
            timestamp=timezone.now() + timezone.timedelta(hours=1),
        )
        self.user.checkin_set.create(
            bradykinesia=5,
            rigidity=3,
            timestamp=timezone.now() + timezone.timedelta(hours=2),
        )
        self.user.checkin_set.create(
            bradykinesia=4,
            rigidity=5,
            timestamp=timezone.now() + timezone.timedelta(hours=2),
        )
        report = self.user.checkin_set.report(fields=["bradykinesia", "rigidity"])
        self.assertEqual(report[1]["bradykinesia"], 3)
        self.assertEqual(report[1]["rigidity"], 1.5)
        self.assertEqual(report[1]["count"], 2)
        self.assertEqual(report[2]["bradykinesia"], 4.5)
        self.assertEqual(report[2]["rigidity"], 4)
        self.assertEqual(report[2]["count"], 2)


class LogQuerySetTestCase(TestCase):
    def setUp(self):
        self.user = make_user(email="log@example.com")
        self.medication = self.user.medication_set.create(name="TestMed")

    def test_time_since_last_dose(self):
        now = timezone.now()
        MedicationLog.objects.create(
            user=self.user,
            medication=self.medication,
            timestamp=now - timezone.timedelta(hours=3),
        )
        MedicationLog.objects.create(
            user=self.user,
            medication=self.medication,
            timestamp=now - timezone.timedelta(hours=1),
        )
        a = CheckIn.objects.create(user=self.user, timestamp=now)
        a = CheckIn.objects.filter(pk=a.pk).with_time_since_dose().get()
        self.assertEqual(a.time_since_dose, timezone.timedelta(hours=1))

        b = CheckIn.objects.create(
            user=self.user, timestamp=now - timezone.timedelta(hours=1, minutes=30)
        )
        b = CheckIn.objects.filter(pk=b.pk).with_time_since_dose().get()
        self.assertEqual(b.time_since_dose, timezone.timedelta(hours=1, minutes=30))
