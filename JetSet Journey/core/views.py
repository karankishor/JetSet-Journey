from django.shortcuts import render, redirect, get_object_or_404
from django.test import Client
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone
from django.urls import reverse
from django.http import JsonResponse
from .models import Trip, Itinerary, Destination, UserPreference, PasswordReset
from .forms import TripForm, UserPreferenceForm
import json
import requests
from .twilio_utils import send_sms
from .models import UserProfile






@login_required
def home(request):
    if request.method == 'POST':
        form = TripForm(request.POST)
        if form.is_valid():
            trip = form.save(commit=False)
            trip.user = request.user
            trip.save()
            
            # Send SMS notif
            # 
            # 
            # ication if user has phone number
            if hasattr(request.user, 'profile') and request.user.profile.phone_number:
                try:
                    # Get weather data
                    geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={trip.destination}&key={settings.GOOGLE_MAPS_API_KEY}"
                    geocode_response = requests.get(geocode_url)
                    
                    if geocode_response.status_code == 200:
                        geocode_data = geocode_response.json()
                        if geocode_data['results']:
                            location = geocode_data['results'][0]['geometry']['location']
                            
                            # Get weather data
                            weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={location['lat']}&lon={location['lng']}&appid={settings.OPENWEATHER_API_KEY}&units=metric"
                            weather_response = requests.get(weather_url)
                            
                            if weather_response.status_code == 200:
                                weather_data = weather_response.json()
                                weather_info = {
                                    'temp': weather_data['main']['temp'],
                                    'desc': weather_data['weather'][0]['description']
                                }
                                
                                # Construct message
                                message = f"New Trip Created!\n\n"
                                message += f"Title: {trip.title}\n"
                                message += f"From: {trip.origin}\n"
                                message += f"To: {trip.destination}\n"
                                message += f"Start: {trip.start_date}\n"
                                message += f"End: {trip.end_date}\n"
                                if trip.description:
                                    message += f"Description: {trip.description}\n"
                                message += f"\nCurrent Weather in {trip.destination}:\n"
                                message += f"Temperature: {weather_info['temp']}°C\n"
                                message += f"Conditions: {weather_info['desc']}"
                                
                                # Send SMS
                                send_sms(request.user.profile.phone_number, message)
                except Exception as e:
                    print(f"Error sending SMS notification: {str(e)}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            messages.success(request, 'Trip created successfully!')
            return redirect('home')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': form.errors})
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TripForm()
    
    trips = Trip.objects.filter(user=request.user)
    return render(request, 'core/home.html', {
        'form': form,
        'trips': trips,
        'GOOGLE_MAPS_API_KEY': settings.GOOGLE_MAPS_API_KEY
    })

def RegisterView(request):
    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        user_data_has_error = False

        if User.objects.filter(username=username).exists():
            user_data_has_error = True
            messages.error(request, "Username already exists")

        if User.objects.filter(email=email).exists():
            user_data_has_error = True
            messages.error(request, "Email already exists")

        if len(password) < 5:
            user_data_has_error = True
            messages.error(request, "Password must be at least 5 characters")

        if user_data_has_error:
            return redirect('register')
        else:
            new_user = User.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                email=email, 
                username=username,
                password=password
            )
            messages.success(request, "Account created. Login now")
            return redirect('login')

    return render(request, 'register.html')

def LoginView(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid login credentials")
            return redirect('login')

    return render(request, 'registration/login.html')

@login_required
def LogoutView(request):
    logout(request)
    return redirect('login')

def ForgotPassword(request):
    if request.method == "POST":
        email = request.POST.get('email')

        try:
            user = User.objects.get(email=email)

            new_password_reset = PasswordReset(user=user)
            new_password_reset.save()

            password_reset_url = reverse('reset-password', kwargs={'reset_id': new_password_reset.reset_id})
            full_password_reset_url = f'{request.scheme}://{request.get_host()}{password_reset_url}'

            email_body = f'Reset your password using the link below:\n\n\n{full_password_reset_url}'
        
            email_message = EmailMessage(
                'Reset your password',
                email_body,
                settings.EMAIL_HOST_USER,
                [email]
            )

            email_message.fail_silently = True
            email_message.send()

            return redirect('password-reset-sent', reset_id=new_password_reset.reset_id)

        except User.DoesNotExist:
            messages.error(request, f"No user with email '{email}' found")
            return redirect('forgot-password')

    return render(request, 'forgot_password.html')

def PasswordResetSent(request, reset_id):
    if PasswordReset.objects.filter(reset_id=reset_id).exists():
        return render(request, 'password_reset_sent.html')
    else:
        messages.error(request, 'Invalid reset id')
        return redirect('forgot-password')

def ResetPassword(request, reset_id):
    try:
        password_reset_id = PasswordReset.objects.get(reset_id=reset_id)

        if request.method == "POST":
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')

            passwords_have_error = False

            if password != confirm_password:
                passwords_have_error = True
                messages.error(request, 'Passwords do not match')

            if len(password) < 5:
                passwords_have_error = True
                messages.error(request, 'Password must be at least 5 characters long')

            expiration_time = password_reset_id.created_when + timezone.timedelta(minutes=10)

            if timezone.now() > expiration_time:
                passwords_have_error = True
                messages.error(request, 'Reset link has expired')
                password_reset_id.delete()

            if not passwords_have_error:
                user = password_reset_id.user
                user.set_password(password)
                user.save()

                password_reset_id.delete()

                messages.success(request, 'Password reset. Proceed to login')
                return redirect('login')
            else:
                return redirect('reset-password', reset_id=reset_id)

    except PasswordReset.DoesNotExist:
        messages.error(request, 'Invalid reset id')
        return redirect('forgot-password')

    return render(request, 'reset_password.html')


@login_required
def create_trip(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        description = request.POST.get('description')
        cover_image = request.FILES.get('cover_image')

        trip = Trip.objects.create(
            user=request.user,
            title=title,
            start_date=start_date,
            end_date=end_date,
            description=description,
            cover_image=cover_image
        )

        # ✅ Construct and send SMS
        if request.user.phone_number:
            message = f"Trip Created: {trip.title}\nStart: {trip.start_date}\nEnd: {trip.end_date}"
            sms_sent = send_sms(request.user.phone_number, message)

            if not sms_sent:
                print("SMS sending failed.")
            else:
                print("SMS sent successfully.")

        return redirect('trip_detail', trip_id=trip.id)
    
    return render(request, 'core/create_trip.html')



def update_trip(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)

    if request.method == 'POST':
        form = TripForm(request.POST, instance=trip)
        if form.is_valid():
            form.save()
            return redirect('trip_detail', trip_id=trip.id)
    else:
        form = TripForm(instance=trip)

    return render(request, 'update_trip.html', {'form': form})

def delete_trip(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)

    if request.method == 'POST':
        trip.delete()
        return redirect('home')

    return render(request, 'delete_trip.html', {'trip': trip})

@login_required
def trip_detail(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)
    itineraries = Itinerary.objects.filter(trip=trip).order_by('date', 'time')
    
    if request.method == 'POST':
        if 'add_itinerary' in request.POST:
            destination = request.POST.get('destination')
            activity = request.POST.get('activity')
            date = request.POST.get('date')
            time = request.POST.get('time')
            
            try:
                # Get location data from Google Places API
                geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={destination}&key={settings.GOOGLE_MAPS_API_KEY}"
                geocode_response = requests.get(geocode_url)
                geocode_data = geocode_response.json()
                
                if geocode_data['results']:
                    location = geocode_data['results'][0]['geometry']['location']
                    latitude = location['lat']
                    longitude = location['lng']
                    
                    # Get weather data
                    weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={settings.OPENWEATHER_API_KEY}&units=metric"
                    weather_response = requests.get(weather_url)
                    weather_data = weather_response.json()
                    
                    weather_info = {
                        'temp': weather_data['main']['temp'],
                        'desc': weather_data['weather'][0]['description'],
                        'icon': weather_data['weather'][0]['icon']
                    }
                    
                    # Create itinerary item
                    itinerary = Itinerary.objects.create(
                        trip=trip,
                        destination=destination,
                        activity=activity,
                        date=date,
                        time=time,
                        latitude=float(latitude),
                        longitude=float(longitude),
                        weather=weather_info
                    )
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Itinerary item added successfully',
                        'id': itinerary.id
                    })
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Could not find location'
                    }, status=400)
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=500)
    
    # Prepare itinerary data for the template
    itinerary_data = []
    for itinerary in itineraries:
        itinerary_data.append({
            'id': itinerary.id,
            'destination': itinerary.destination,
            'activity': itinerary.activity,
            'date': itinerary.date.strftime('%Y-%m-%d'),  # Convert date to string
            'time': itinerary.time.strftime('%H:%M'),  # Convert time to string
            'latitude': itinerary.latitude,
            'longitude': itinerary.longitude,
            'weather': getattr(itinerary, 'weather', None)
        })
    
    # Get filter parameters
    activity_filter = request.GET.get('activity')
    budget_filter = request.GET.get('budget')
    distance_filter = request.GET.get('distance', 10)
    
    # Apply filters if provided
    if activity_filter:
        itineraries = itineraries.filter(activity=activity_filter)
    if budget_filter:
        # Implement budget filtering logic here
        pass
    
    return render(request, 'core/trip_detail.html', {
        'trip': trip,
        'itineraries': itineraries,
        'itinerary_data': json.dumps(itinerary_data),
        'GOOGLE_MAPS_API_KEY': settings.GOOGLE_MAPS_API_KEY
    })

@login_required
def destination_suggestions(request):
    form = UserPreferenceForm(request.GET or None)
    destinations = Destination.objects.all()

    if form.is_valid():
        activity_type = form.cleaned_data.get('activity_type')
        budget = form.cleaned_data.get('budget')
        if activity_type:
            destinations = destinations.filter(category__iexact=activity_type)
        if budget:
            destinations = destinations.filter(budget_level__iexact=budget)

        # Optionally, save/update the user's preferences
        UserPreference.objects.update_or_create(
            user=request.user,
            defaults={'activity_type': activity_type, 'budget': budget}
        )

    context = {
        'form': form,
        'destinations': destinations,
    }
    return render(request, 'core/destination_suggestions.html', context)

def get_weather(lat, lon):
    api_key = settings.OPENWEATHER_API_KEY
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

@login_required
def search_place(request):
    query = request.GET.get('q', '')
    if not query:
        return JsonResponse({'error': 'No search query provided'}, status=400)

    try:
        # Use Google Places API to search for the location
        places_url = (
            f'https://maps.googleapis.com/maps/api/place/textsearch/json'
            f'?query={query}&key={settings.GOOGLE_MAPS_API_KEY}'
        )
        response = requests.get(places_url).json()

        if response['status'] == 'OK':
            # Get details for each place
            places = []
            for place in response['results']:
                # Get place details
                details_url = (
                    f'https://maps.googleapis.com/maps/api/place/details/json'
                    f'?place_id={place["place_id"]}&fields=name,formatted_address,geometry,rating,photos,types'
                    f'&key={settings.GOOGLE_MAPS_API_KEY}'
                )
                details_response = requests.get(details_url).json()
                
                if details_response['status'] == 'OK':
                    place_details = details_response['result']
                    # Fetch Yelp data for the place using RapidAPI
                    yelp_url = f'https://yelp-com.p.rapidapi.com/business/search?term={place_details["name"]}&location={place_details["formatted_address"]}'
                    yelp_headers = {
                        'X-RapidAPI-Key': settings.YELP_API_KEY,
                        'X-RapidAPI-Host': 'yelp-com.p.rapidapi.com'
                    }
                    yelp_response = requests.get(yelp_url, headers=yelp_headers).json()
                    
                    yelp_data = None
                    if 'businesses' in yelp_response and yelp_response['businesses']:
                        yelp_data = yelp_response['businesses'][0]
                    
                    places.append({
                        'name': place_details.get('name', ''),
                        'formatted_address': place_details.get('formatted_address', ''),
                        'geometry': place_details.get('geometry', {}),
                        'rating': place_details.get('rating', None),
                        'types': place_details.get('types', []),
                        'photos': place_details.get('photos', []),
                        'yelp_data': yelp_data
                    })

            return JsonResponse({
                'results': places
            })
        else:
            return JsonResponse({
                'error': f'Places search failed: {response["status"]}'
            }, status=400)

    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)

@login_required
@csrf_exempt
def save_itinerary(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            items = data.get('items', [])
            
            # Create a new trip for the itinerary
            trip = Trip.objects.create(
                user=request.user,
                title=f"Itinerary - {timezone.now().strftime('%Y-%m-%d %H:%M')}"
            )
            
            # Add each item to the itinerary
            for item in items:
                # Get coordinates for the destination
                geocode_url = (
                    f'https://maps.googleapis.com/maps/api/geocode/json'
                    f'?address={item["address"]}&key={settings.GOOGLE_MAPS_API_KEY}'
                )
                geocode_response = requests.get(geocode_url).json()
                
                latitude = None
                longitude = None
                
                if geocode_response['status'] == 'OK':
                    location = geocode_response['results'][0]['geometry']['location']
                    latitude = location['lat']
                    longitude = location['lng']
                
                Itinerary.objects.create(
                    trip=trip,
                    destination=item['name'],
                    address=item['address'],
                    activity=item['activity'],
                    budget=item['budget'],
                    types=','.join(item.get('types', [])),
                    rating=item.get('rating'),
                    date=timezone.now().date(),  # Default to today
                    time=timezone.now().time(),  # Default to current time
                    latitude=float(latitude),
                    longitude=float(longitude)
                )
            
            return JsonResponse({'status': 'success', 'trip_id': trip.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@login_required
def map_view(request):
    return render(request, 'map.html', {
        'GOOGLE_MAPS_API_KEY': settings.GOOGLE_MAPS_API_KEY
    })

@login_required
def add_itinerary(request, trip_id):
    print("add_itinerary view called")  # Debug log
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)
    
    if request.method == 'POST':
        print("POST request received")  # Debug log
        try:
            # Get all form data
            destination = request.POST.get('destination')
            activity = request.POST.get('activity')
            date = request.POST.get('date')
            time = request.POST.get('time')
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            address = request.POST.get('address', '')
            
            # Log received data for debugging
            print("Received form data:")
            print(f"Destination: {destination}")
            print(f"Activity: {activity}")
            print(f"Date: {date}")
            print(f"Time: {time}")
            print(f"Latitude: {latitude}")
            print(f"Longitude: {longitude}")
            print(f"Address: {address}")
            
            # Validate required fields
            missing_fields = []
            if not destination: missing_fields.append('destination')
            if not activity: missing_fields.append('activity')
            if not date: missing_fields.append('date')
            if not time: missing_fields.append('time')
            
            if missing_fields:
                print(f"Missing fields: {missing_fields}")  # Debug log
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required fields: {", ".join(missing_fields)}'
                }, status=400)
            
            # Get weather data if coordinates are available
            weather_info = None
            if latitude and longitude:
                try:
                    print("Fetching weather data...")  # Debug log
                    weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={settings.OPENWEATHER_API_KEY}&units=metric"
                    weather_response = requests.get(weather_url)
                    if weather_response.status_code == 200:
                        weather_data = weather_response.json()
                        weather_info = {
                            'temp': weather_data['main']['temp'],
                            'desc': weather_data['weather'][0]['description'],
                            'icon': weather_data['weather'][0]['icon']
                        }
                        print("Weather data fetched successfully")  # Debug log
                except Exception as e:
                    print(f"Error getting weather data: {str(e)}")
                    # Continue without weather data
            
            # Create itinerary item
            print("Creating itinerary item...")  # Debug log
            itinerary = Itinerary.objects.create(
                trip=trip,
                destination=destination,
                address=address,
                activity=activity,
                date=date,
                time=time,
                latitude=float(latitude) if latitude else None,
                longitude=float(longitude) if longitude else None,
                weather=weather_info,
                budget='medium',  # Default value
                types=''  # Empty string as default
            )
            print(f"Itinerary created with ID: {itinerary.id}")  # Debug log
            
            return JsonResponse({
                'success': True,
                'message': 'Itinerary item added successfully',
                'id': itinerary.id
            })
            
        except Exception as e:
            print(f"Error in add_itinerary: {str(e)}")
            import traceback
            print(traceback.format_exc())  # Print full traceback
            return JsonResponse({
                'success': False,
                'error': f'Error saving itinerary: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    }, status=405)

@login_required
def update_itinerary(request, trip_id, itinerary_id):
    try:
        itinerary = Itinerary.objects.get(id=itinerary_id, trip_id=trip_id, trip__user=request.user)
        
        # Get form data
        destination = request.POST.get('destination')
        activity = request.POST.get('activity')
        date = request.POST.get('date')
        time = request.POST.get('time')
        
        # Validate required fields
        if not all([destination, activity, date, time]):
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields'
            })
        
        # Update the itinerary item
        itinerary.destination = destination
        itinerary.activity = activity
        itinerary.date = date
        itinerary.time = time
        itinerary.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Itinerary item updated successfully'
        })
        
    except Itinerary.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Itinerary item not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def delete_itinerary(request, trip_id, itinerary_id):
    try:
        itinerary = Itinerary.objects.get(id=itinerary_id, trip_id=trip_id, trip__user=request.user)
        itinerary.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Itinerary item deleted successfully'
        })
        
    except Itinerary.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Itinerary item not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

  # Make sure this import is present

@login_required
def send_trip_notification(request, trip_id):
    """
    Send an SMS notification about a trip
    """
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)
    
    try:
        profile = request.user.userprofile  # Access related UserProfile
    except UserProfile.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'User profile not found'
        }, status=400)
    
    if not profile.phone_number:
        return JsonResponse({
            'status': 'error',
            'message': 'Phone number not set'
        }, status=400)

    # Optional: also check if phone is verified
    if not profile.phone_verified:
        return JsonResponse({
            'status': 'error',
            'message': 'Phone number not verified'
        }, status=400)
    
    message = f"Trip Reminder: {trip.title}\n"
    message += f"Start Date: {trip.start_date}\n"
    message += f"End Date: {trip.end_date}\n"
    
    if send_sms(profile.phone_number, message):
        return JsonResponse({
            'status': 'success',
            'message': 'Notification sent successfully'
        })
    else:
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to send notification'
        }, status=500)





@login_required
def test_twilio_credentials(request):
    """
    Test view to verify Twilio credentials and send a test message
    """
    try:
        # Check if Twilio settings are configured
        if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_PHONE_NUMBER]):
            return JsonResponse({
                'status': 'error',
                'message': 'Twilio settings are not properly configured in .env file'
            }, status=400)

        # Initialize Twilio client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        # Try to send a test message
        test_message = "This is a test message from your Travel Planner app!"
        test_number = "+919876543210"  # Replace with your test number
        
        message = client.messages.create(
            body=test_message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=test_number
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Test message sent successfully',
            'message_sid': message.sid
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error sending test message: {str(e)}'
        }, status=500)


@login_required
def profile(request):
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number', '').strip()
        
        # Validate phone number format
        if phone_number and not phone_number.startswith('+'):
            messages.error(request, 'Phone number must start with country code (e.g., +1 for US)')
            return redirect('profile')
            
        # Update user's phone number
        profile.phone_number = phone_number
        profile.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    
    context = {
        'user': request.user,
        'profile': profile
    }
    return render(request, 'core/profile.html', context)