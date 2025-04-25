from django.contrib import admin
from .models import PasswordReset
from .models import Trip, Itinerary

admin.site.register(PasswordReset)
admin.site.register(Trip)
admin.site.register(Itinerary)
