from django import forms
from .models import Trip

class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = ['title', 'origin', 'destination', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

class UserPreferenceForm(forms.Form):
    ACTIVITY_CHOICES = [
        ('beach', 'Beach'),
        ('historical', 'Historical'),
        ('adventure', 'Adventure'),
        # Add more options as needed
    ]
    BUDGET_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    activity_type = forms.ChoiceField(choices=ACTIVITY_CHOICES, required=False)
    budget = forms.ChoiceField(choices=BUDGET_CHOICES, required=False)
