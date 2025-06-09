from rest_framework import serializers
from .models import FitnessClass, Booking
from django.utils import timezone

class FitnessClassSerializer(serializers.ModelSerializer):
    date_time_view = serializers.DateTimeField(source='date_time', format="%Y-%m-%d %H:%M:%S", read_only=True)
    booking_count = serializers.SerializerMethodField()
    class Meta:
        model = FitnessClass
        fields = [
            'id',
            'name', 
            'date_time', 
            'instructor', 
            'available_slots',
            'date_time_view',
            'booking_count',
        ]
        read_only_fields = ['booking_count', 'id']
        
    def get_booking_count(self, obj):
        return Booking.objects.filter(fitness_class_id=obj).select_related('fitness_class').count()
        
    def validate(self, attrs):
        instructor = attrs.get('instructor')
        date_time = attrs.get('date_time')

        if self.instance:
            conflicts = FitnessClass.objects.filter(
                instructor=instructor,
                date_time=date_time
            ).exclude(id=self.instance.id)
        else:
            conflicts = FitnessClass.objects.filter(
                instructor=instructor,
                date_time=date_time
            )

        if conflicts.exists():
            raise serializers.ValidationError(
                {"instructor": "Instructor already has a class scheduled at this time."}
            )
        if date_time < timezone.now():
            raise serializers.ValidationError(
                {"date_time": "Cannot schedule a class in the past."}
            )

        return attrs


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['fitness_class_id', 'client_name', 'client_email']
        
    def validate(self, attrs):
        print("Validating booking data:", attrs)
        fitness_class_id = attrs.get('fitness_class_id')

        if fitness_class_id.available_slots <= 0:
            raise serializers.ValidationError(
                {"fitness_class_id": "No available slots for this class."}
            )

        if fitness_class_id.date_time < timezone.now():
            raise serializers.ValidationError(
                {"fitness_class_id": "Cannot book a class in the past."}
            )
            
        if Booking.objects.filter(
            fitness_class_id=fitness_class_id,
            client_email=attrs.get('client_email'),
        ).exists():
            raise serializers.ValidationError(
                {"client_email": "You have already booked this class."}
            )
    
        return attrs
        
    