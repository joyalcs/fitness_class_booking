import uuid
from django.db import models

# Create your models here.

class FitnessClass(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    date_time = models.DateTimeField()
    instructor = models.CharField(max_length=100)
    available_slots = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.name} ({self.date_time})"
    

class Booking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fitness_class_id = models.ForeignKey(FitnessClass, on_delete=models.CASCADE)
    client_name = models.CharField(max_length=100)
    client_email = models.EmailField()

    def __str__(self):
        return f"{self.client_name} - {self.fitness_class_id.name}"