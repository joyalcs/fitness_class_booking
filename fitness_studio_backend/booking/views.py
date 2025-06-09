import logging
from datetime import datetime
from django.shortcuts import render
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from booking.serializers import BookingSerializer, FitnessClassSerializer
from .models import Booking, FitnessClass
# Create your views here.

logger = logging.getLogger(__name__)

class FitnessClassCreateListView(ListCreateAPIView):
    serializer_class = FitnessClassSerializer
    queryset = FitnessClass.objects.all()
    lookup_fields = ['name']
    
    
    def get_queryset(self):
        queryset = self.queryset.filter(available_slots__gt=0)

        date_str = self.request.query_params.get('date')
        if date_str:
            try:
                # Parse the date string (format: YYYY-MM-DD)
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                queryset = queryset.filter(date_time__date=date_obj)
                print("Filtered queryset:", queryset)
            except ValueError:
                logger.error(f"Invalid date format: {date_str}. Expected format: YYYY-MM-DD")
                raise ValueError("Invalid date format. Expected format: YYYY-MM-DD")
    
        return queryset

class FitnessClassRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    queryset = FitnessClass.objects.all()
    serializer_class = FitnessClassSerializer
    lookup_fields = ['pk']
    
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
    
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
    
    
class BookingCreateListView(ListCreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    lookup_fields = ['client_email']
    
    
    def get_queryset(self):
        queryset = super().get_queryset()
        email = self.request.query_params.get('query')

        if email:
            queryset = queryset.filter(client_email=email)
        return queryset
    
    
    def perform_create(self, serializer):
        fitness_class_id = serializer.validated_data['fitness_class_id']
        
        if fitness_class_id.available_slots > 0:
            fitness_class_id.available_slots -= 1
            fitness_class_id.save()
            serializer.save()
        else:
            raise ValueError("No available slots for this class.")