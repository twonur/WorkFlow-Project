from django.template.loader import render_to_string
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
from django.core.mail import send_mail

_firebase_app = None

def initialize_firebase():
    """Initialize Firebase (if not already initialized)"""
    global _firebase_app
    if _firebase_app is None and hasattr(settings, 'FIREBASE_CONFIG'):
        try:
            cred = credentials.Certificate(settings.FIREBASE_CONFIG)
            _firebase_app = firebase_admin.initialize_app(cred)
            print("Firebase başarıyla başlatıldı!")
        except Exception as e:
            print(f"Firebase başlatılamadı: {e}")

def send_push_notification(token, title, body, data=None):
    if _firebase_app is None:
        initialize_firebase()
        if _firebase_app is None:
            return False, "Firebase başlatılamadı"

    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data=data or {},
            token=token,
        )
        
        response = messaging.send(message)
        return True, response
    except Exception as e:
        return False, str(e)

def send_invitation_email(email, code):
    subject = 'WorkFlow - Davet Kodunuz'
    html_message = render_to_string('invitation_email.html', {'code': code})
    text_message = render_to_string('invitation_email.txt', {'code': code})
    
    send_mail(
        subject=subject,
        message=text_message,  # Plain text version
        html_message=html_message,  # HTML version
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=False,
    ) 