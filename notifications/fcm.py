import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Firebase Admin SDK initialization
def initialize_firebase():
    if not firebase_admin._apps:  # If not already initialized
        try:
            # If FIREBASE_CONFIG is a dict, use it directly
            firebase_config = settings.FIREBASE_CONFIG
            if isinstance(firebase_config, dict):
                cred = credentials.Certificate(firebase_config)
            else:
                # If it's a file path, read the file
                cred = credentials.Certificate(firebase_config)
                
            firebase_admin.initialize_app(cred)
            return True
        except Exception as e:
            logger.error(f"Error initializing Firebase Admin SDK: {e}")
            # Detailed error information
            import traceback
            logger.error(f"Detailed error: {traceback.format_exc()}")
            return False
    return True

# Sends push notification to a specific device
def send_push_notification(token, title, body, data=None):
    if not initialize_firebase():
        return False
    
    try:
        # Notification settings
        notification = messaging.Notification(
            title=title,
            body=body
        )
        
        # Create message - in V1 API format
        message = messaging.Message(
            notification=notification,
            data=data or {},
            token=token
        )
        
        # Send notification
        response = messaging.send(message)
        return True
    except Exception as e:
        logger.error(f"Error occurred while sending notification: {e}")
        return False

# Send notification to multiple devices
def send_multicast_notification(tokens, title, body, data=None):
    if not initialize_firebase():
        logger.error("Firebase could not be initialized!")
        return {"success": 0, "failure": len(tokens) if tokens else 0}
        
    if not tokens:
        logger.warning("No token found to send!")
        return {"success": 0, "failure": 0}
    
    try:
        success_count = 0
        failure_count = 0
        
        # Make separate V1 API call for each token
        for token in tokens:
            try:
                # Create notification
                notification = messaging.Notification(
                    title=title,
                    body=body
                )
                
                # Create message
                message = messaging.Message(
                    notification=notification,
                    data=data or {},
                    token=token
                )
                
                # Send with V1 API
                response = messaging.send(message)
                success_count += 1
            except Exception as e:
                logger.error(f"Token send failed: {token[:10]}... Error: {e}")
                failure_count += 1
        
        return {
            "success": success_count,
            "failure": failure_count
        }
    except Exception as e:
        logger.error(f"Error occurred while sending notification with V1 API: {e}")
        import traceback
        logger.error(f"Detailed error: {traceback.format_exc()}")
        return {"success": 0, "failure": len(tokens) if tokens else 0} 