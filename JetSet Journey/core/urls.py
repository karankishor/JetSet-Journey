from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('profile/', views.profile, name='profile'),
    path('register/', views.RegisterView, name='register'),
    path('login/', views.LoginView, name='login'),
    path('logout/', views.LogoutView, name='logout'),
    path('forgot-password/', views.ForgotPassword, name='forgot-password'),
    path('password-reset-sent/<str:reset_id>/', views.PasswordResetSent, name='password-reset-sent'),
    path('reset-password/<str:reset_id>/', views.ResetPassword, name='reset-password'),
    path('trip/<int:trip_id>/', views.trip_detail, name='trip_detail'),
    path('trip/<int:trip_id>/add-itinerary/', views.add_itinerary, name='add_itinerary'),  # Add this line
    path('trip/<int:trip_id>/update-itinerary/<int:itinerary_id>/', views.update_itinerary, name='update_itinerary'),
    path('trip/<int:trip_id>/delete-itinerary/<int:itinerary_id>/', views.delete_itinerary, name='delete_itinerary'),
    path('trip/<int:trip_id>/edit/', views.update_trip, name='update_trip'),
    path('trip/<int:trip_id>/delete/', views.delete_trip, name='delete_trip'),
    path('destinations/', views.destination_suggestions, name='destination_suggestions'),
    path('search-place/', views.search_place, name='search_place'),
    path('save-itinerary/', views.save_itinerary, name='save_itinerary'),
    path('map/', views.map_view, name='map'),
    path('trip/<int:trip_id>/send-notification/', views.send_trip_notification, name='send_trip_notification'),
    
]