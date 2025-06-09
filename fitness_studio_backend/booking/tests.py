from datetime import timedelta, datetime
import uuid

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from booking.models import FitnessClass, Booking


class FitnessClassAPITest(APITestCase):
    def setUp(self):
        # Create a fitness class scheduled in the future (tomorrow)
        self.future_datetime = timezone.now() + timedelta(days=1)
        self.fitness_class = FitnessClass.objects.create(
            name="Yoga",
            date_time=self.future_datetime,
            instructor="Alex",
            available_slots=5
        )
        # URL for list and create
        self.fitness_class_list_url = reverse('fitness_classes')
        # URL for retrieve/update/delete (lookup by pk)
        self.fitness_class_detail_url = reverse('fitness_class_detail', kwargs={'pk': self.fitness_class.pk})

    def test_get_fitness_classes_without_date_filter(self):
        """
        GET /fitness_classes/ should return classes with available_slots > 0.
        """
        response = self.client.get(self.fitness_class_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # We expect at least one class (the one we created)
        self.assertGreaterEqual(len(response.data), 1)

    def test_get_fitness_classes_with_date_filter(self):
        """
        GET /fitness_classes/?date=YYYY-MM-DD should return classes on that date.
        """
        date_str = self.future_datetime.strftime('%Y-%m-%d')
        url = f"{self.fitness_class_list_url}?date={date_str}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.data:
            # Make sure the returned date matches the query date.
            returned_date = datetime.fromisoformat(item['date_time']).date()
            self.assertEqual(returned_date.strftime('%Y-%m-%d'), date_str)

    def test_create_fitness_class(self):
        """
        POST /fitness_classes/ should create a new fitness class.
        """
        payload = {
            "name": "Zumba",
            "date_time": (timezone.now() + timedelta(days=2)).isoformat(),
            "instructor": "Beth",
            "available_slots": 10
        }
        response = self.client.post(self.fitness_class_list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], payload['name'])

    def test_retrieve_update_destroy_fitness_class(self):
        """
        Test GET, PUT, and DELETE on /fitness_classes/<id>/.
        """
        # Retrieve
        response = self.client.get(self.fitness_class_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.fitness_class.name)

        # Update
        update_payload = {
            "name": "Yoga Updated",
            "date_time": self.fitness_class.date_time.isoformat(),
            "instructor": "Alex",
            "available_slots": 3
        }
        response = self.client.put(self.fitness_class_detail_url, update_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Yoga Updated")

        # Delete
        response = self.client.delete(self.fitness_class_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Verify the instance is deleted
        self.assertFalse(FitnessClass.objects.filter(pk=self.fitness_class.pk).exists())


class BookingAPITest(APITestCase):
    def setUp(self):
        # Create a fitness class for booking
        self.future_datetime = timezone.now() + timedelta(days=1)
        self.fitness_class = FitnessClass.objects.create(
            name="HIIT",
            date_time=self.future_datetime,
            instructor="Chris",
            available_slots=2  # Start with 2 available slots
        )
        # URL for creating and listing bookings
        self.booking_list_url = reverse('bookings')

    def test_create_booking_success(self):
        """
        POST /bookings/ creates a booking when there are available slots.
        """
        payload = {
            # Depending on your serializer field name, we use "fitness_class"
            # (if you are using a PrimaryKeyRelatedField mapping to FitnessClass)
            "fitness_class_id": str(self.fitness_class.pk),
            "client_name": "John Doe",
            "client_email": "john@example.com"
        }
        response = self.client.post(self.booking_list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # After the booking is successful, available_slots should be decremented
        self.fitness_class.refresh_from_db()
        self.assertEqual(self.fitness_class.available_slots, 1)
        # Verify the booking exists in the database
        self.assertTrue(Booking.objects.filter(client_email="john@example.com",
                                               fitness_class_id=self.fitness_class).exists())

    def test_create_booking_no_slots(self):
        """
        POST /bookings/ should fail if there are no available slots.
        """
        # Deplete slots for this fitness class
        self.fitness_class.available_slots = 0
        self.fitness_class.save()
        payload = {
            "fitness_class_id": str(self.fitness_class.pk),
            "client_name": "John Doe",
            "client_email": "john@example.com"
        }
        response = self.client.post(self.booking_list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("No available slots", str(response.data))

    def test_create_duplicate_booking(self):
        """
        A second booking with the same fitness class and client details should be disallowed.
        """
        payload = {
            "fitness_class_id": str(self.fitness_class.pk),
            "client_name": "Jane Doe",
            "client_email": "jane@example.com"
        }
        # First booking 
        response1 = self.client.post(self.booking_list_url, payload, format="json")
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        # Second booking 
        response2 = self.client.post(self.booking_list_url, payload, format="json")
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already booked", str(response2.data))

    def test_get_bookings_by_email(self):
        """
        GET /bookings/?email=... should list bookings for that client.
        """
        # Create two bookings for a specific email
        payload_1 = {
            "fitness_class_id": str(self.fitness_class.pk),
            "client_name": "User One",
            "client_email": "user@example.com"
        }
        self.client.post(self.booking_list_url, payload_1, format="json")

        # You might add another booking if your view supports filtering by email.
        # The view in our current setup uses get_queryset to filter by a query parameter "email".
        url = f"{self.booking_list_url}?email=user@example.com"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that at least one booking is returned
        self.assertGreaterEqual(len(response.data), 1)