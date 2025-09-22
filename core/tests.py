from datetime import timedelta

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from . import models


class ClaimProfitViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="password123")
        self.earnings = models.UserEarnings.objects.create(
            user=self.user,
            profit_per_hour=100,
            last_claimed=timezone.now() - timedelta(hours=2),
            total_collected=50,
        )

    def test_get_pending_profit_for_authenticated_user(self):
        expected_pending = self.earnings.calculate_pending_profit()
        self.client.force_authenticate(user=self.user)

        response = self.client.get(reverse("profit"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("pending_profit"), expected_pending)

    def test_claim_profit_updates_totals(self):
        expected_pending = self.earnings.calculate_pending_profit()
        self.client.force_authenticate(user=self.user)

        response = self.client.post(reverse("profit"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        claimed = response.data.get("claimed")
        self.assertEqual(claimed, expected_pending)

        self.earnings.refresh_from_db()
        self.assertEqual(self.earnings.total_collected, 50 + expected_pending)

    def test_earnings_created_for_user_without_record(self):
        other_user = User.objects.create_user(username="newuser", password="password123")
        self.client.force_authenticate(user=other_user)

        response = self.client.get(reverse("profit"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(models.UserEarnings.objects.filter(user=other_user).exists())
