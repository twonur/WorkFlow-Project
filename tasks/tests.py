from django.test import TestCase
from django.conf import settings
from unittest.mock import patch, MagicMock
import unittest

class FirebaseIntegrationTest(TestCase):
    """Test class for testing Firebase integration"""
    
    @patch('firebase_admin.initialize_app')
    @patch('firebase_admin.get_app')
    @patch('firebase_admin.credentials.Certificate')
    @patch('firebase_admin.messaging.send')
    def test_firebase_notification(self, mock_send, mock_certificate, mock_get_app, mock_initialize_app):
        """Tests if Firebase notifications work properly"""
        
        # Set up mocks to prevent actual connection to Firebase service
        mock_get_app.side_effect = ValueError("App not found") 
        mock_certificate.return_value = "Mocked Certificate"
        mock_initialize_app.return_value = MagicMock()
        mock_send.return_value = "message-id-123"
        
        # Import Firebase module
        import firebase_admin
        from firebase_admin import credentials, messaging
        
        # Check environment variables - use FIREBASE_CONFIG dictionary
        self.assertTrue(hasattr(settings, 'FIREBASE_CONFIG'), 
                        "FIREBASE_CONFIG settings içinde tanımlanmamış")
        self.assertIn('private_key', settings.FIREBASE_CONFIG, 
                     "private_key FIREBASE_CONFIG içinde tanımlanmamış")
        self.assertIn('client_email', settings.FIREBASE_CONFIG, 
                     "client_email FIREBASE_CONFIG içinde tanımlanmamış")
        
        # Check private key start and end
        self.assertTrue(settings.FIREBASE_CONFIG['private_key'].startswith("-----BEGIN PRIVATE KEY-----"), 
                        "Private key doğru formatta değil")
        self.assertTrue(settings.FIREBASE_CONFIG['private_key'].endswith("-----END PRIVATE KEY-----"), 
                        "Private key doğru formatta değil")
        
        # Initialize Firebase
        try:
            default_app = firebase_admin.get_app()
        except ValueError:
            cred = credentials.Certificate(settings.FIREBASE_CONFIG)
            default_app = firebase_admin.initialize_app(cred)
        
        # Check mock function calls
        mock_get_app.assert_called_once()
        mock_certificate.assert_called_once()
        mock_initialize_app.assert_called_once()
        
        # Create and send test message
        message = messaging.Message(
            data={
                'title': 'Test Bildirimi',
                'body': 'Bu bir test bildirimidir',
            },
            topic='test_topic'
        )
        
        response = messaging.send(message)
        
        # Check mock send function call
        mock_send.assert_called_once()
        self.assertEqual(response, "message-id-123")
        
    def test_firebase_settings_existence(self):
        """Tests that Firebase settings exist in settings.py"""
        self.assertTrue(hasattr(settings, 'FIREBASE_CONFIG'), 
                        "FIREBASE_CONFIG settings içinde tanımlanmamış")
        
        # Check FIREBASE_CONFIG content
        if hasattr(settings, 'FIREBASE_CONFIG'):
            config = settings.FIREBASE_CONFIG
            self.assertIn('private_key', config, "private_key FIREBASE_CONFIG içinde tanımlanmamış")
            self.assertIn('client_email', config, "client_email FIREBASE_CONFIG içinde tanımlanmamış")
            
            # Check private key format
            private_key = config['private_key']
            self.assertTrue("PRIVATE KEY" in private_key, 
                           "Private key doğru formatı içermiyor")
            self.assertTrue(private_key.startswith("-----BEGIN PRIVATE KEY-----"), 
                           "Private key doğru başlangıca sahip değil")
            self.assertTrue(private_key.endswith("-----END PRIVATE KEY-----"), 
                           "Private key doğru sonlanmaya sahip değil")

# Separate test class for real Firebase integration
class FirebaseRealIntegrationTest(TestCase):
    """Class that tests integration with real Firebase service."""
    
    @unittest.skip("This test sends real Firebase message, skipped in normal test process")
    def test_real_firebase_message(self):
        """Sends a test message by connecting to real Firebase service.
        This test should be run manually and is skipped in normal test process."""
        
        try:
            import firebase_admin
            from firebase_admin import credentials, messaging
            
            # Initialize Firebase application
            try:
                app = firebase_admin.get_app()
                print("Firebase already initialized")
            except ValueError:
                # Load Firebase credentials
                cred = credentials.Certificate(settings.FIREBASE_CONFIG)
                app = firebase_admin.initialize_app(cred)
                print("Firebase initialized successfully")
            
            # Create test message
            message = messaging.Message(
                notification=messaging.Notification(
                    title='Gerçek Test Bildirimi',
                    body='Bu test.py tarafından gönderilen gerçek bir test bildirimidir',
                ),
                topic='test_topic'
            )
            
            # Send message
            response = messaging.send(message)
            print(f"Real message sent, response: {response}")
            
            # Consider this test as passed
            self.assertTrue(True, "Mesaj başarıyla gönderildi")
            
        except Exception as e:
            self.fail(f"Firebase mesaj gönderimi sırasında hata oluştu: {e}")
