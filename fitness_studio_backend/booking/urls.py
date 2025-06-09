from django.urls import path

from booking.views import BookingCreateListView, FitnessClassCreateListView, FitnessClassRetrieveUpdateDestroyView

urlpatterns = [
    path('fitness_classes/', FitnessClassCreateListView.as_view(), name='fitness_classes'),
    path('fitness_class/<uuid:pk>/', FitnessClassRetrieveUpdateDestroyView.as_view(), name='fitness_class_detail'),
    path('bookings/', BookingCreateListView.as_view(), name='bookings'),
]
