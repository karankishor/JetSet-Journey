from twilio.rest import Client
from django.conf import settings
import logging
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def send_sms(to_number, message):
    """
    Send an SMS message using Twilio
    
    Args:
        to_number (str): The recipient's phone number (must include country code)
        message (str): The message to send
        
    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    try:
        # Log the credentials being used (without sensitive data)
        logger.info("Checking Twilio credentials...")
        logger.info(f"Using Twilio phone number: {settings.TWILIO_PHONE_NUMBER}")
        
        # Validate Twilio credentials
        if not settings.TWILIO_ACCOUNT_SID:
            logger.error("TWILIO_ACCOUNT_SID is not set")
            return False
        if not settings.TWILIO_AUTH_TOKEN:
            logger.error("TWILIO_AUTH_TOKEN is not set")
            return False
        if not settings.TWILIO_PHONE_NUMBER:
            logger.error("TWILIO_PHONE_NUMBER is not set")
            return False
            
        logger.info("Initializing Twilio client...")
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        # Log the attempt
        logger.info(f"Attempting to send SMS to {to_number}")
        logger.info(f"Message content: {message}")
        
        message = client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to_number
        )
        
        # Log success
        logger.info(f"SMS sent successfully to {to_number}. Message SID: {message.sid}")
        return True
        
    except Exception as e:
        # Log the full error details
        logger.error(f"Error sending SMS to {to_number}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error(f"Full error details: {e}")
        return False