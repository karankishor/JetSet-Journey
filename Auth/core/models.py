from django.db import models
from django.contrib.auth.models import User
import uuid

class PasswordReset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reset_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_when = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Password reset for {self.user.username} at {self.created_when}"


class Trip(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    origin = models.CharField(max_length=200)
    destination = models.CharField(max_length=200)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class UserPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=50, blank=True, null=True)
    budget = models.CharField(max_length=10, blank=True, null=True)  # e.g., Low, Medium, High

    def __str__(self):
        return f"{self.user.username}'s Preferences"


class Itinerary(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='itineraries')
    destination = models.CharField(max_length=200)
    address = models.TextField(blank=True, null=True)  # Make address optional
    activity = models.CharField(max_length=100)
    budget = models.CharField(max_length=20, default='medium')
    types = models.TextField(blank=True)  # Store as comma-separated list
    rating = models.FloatField(null=True, blank=True)
    date = models.DateField()
    time = models.TimeField()
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    weather = models.JSONField(null=True, blank=True)  # Add weather field

    def __str__(self):
        return f"{self.destination} on {self.date}"


class Destination(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)  # e.g., Beach, Historical, Adventure
    budget_level = models.CharField(max_length=10)  # e.g., Low, Medium, High
    latitude = models.FloatField()
    longitude = models.FloatField()
    rating = models.FloatField(null=True, blank=True)  # Optional field for reviews

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
