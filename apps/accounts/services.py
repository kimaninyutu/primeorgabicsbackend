# apps/accounts/services.py
from django.utils import timezone  # Import Django's timezone utility
from datetime import timedelta
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.conf import settings
import jwt as pyjwt  # Renamed to avoid conflicts
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import User, EmailVerification, PasswordReset, UserSession
import logging

# Set up logging
logger = logging.getLogger(__name__)

class AuthService:
    @staticmethod
    def create_token(user_id, expiry=None):
        """Create a JWT token for a user"""
        if expiry is None:
            expiry = timedelta(minutes=60)  # Default to 1 hour

        payload = {
            'user_id': user_id,
            'exp': timezone.now() + expiry,
            'iat': timezone.now(),
        }

        return pyjwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

    @staticmethod
    def create_refresh_token(user_id):
        """Create a refresh token for a user"""
        return AuthService.create_token(user_id, expiry=timedelta(days=7))  # 7 days refresh token

    @staticmethod
    def get_user_from_token(token):
        """Get user from a JWT token"""
        try:
            payload = pyjwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user = User.objects.get(id=payload['user_id'])
            return user
        except (pyjwt.ExpiredSignatureError, pyjwt.InvalidTokenError, User.DoesNotExist):
            return None

    @staticmethod
    def login(email, password, user_agent=None, ip_address=None):
        """Authenticate a user and return tokens"""
        user = authenticate(username=email, password=password)
        if not user:
            raise ValidationError("Invalid credentials")

        # Temporarily comment out email verification check for testing
        # if not user.is_email_verified:
        #     raise ValidationError("Please verify your email first")

        # Create session if user_agent and ip_address are provided
        if user_agent and ip_address:
            UserSession.objects.create(
                user=user,
                user_agent=user_agent,
                ip_address=ip_address
            )

        return {
            'access_token': AuthService.create_token(user.id),
            'refresh_token': AuthService.create_refresh_token(user.id),
            'user': user
        }

    @staticmethod
    def register(data, send_verification=True):
        """Register a new user"""
        try:
            if User.objects.filter(email=data['email']).exists():
                raise ValidationError("Email already registered")

            # Ensure first_name and last_name are never null
            first_name = data.get('first_name', '')
            if first_name is None:
                first_name = ''

            last_name = data.get('last_name', '')
            if last_name is None:
                last_name = ''

            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                first_name=first_name,
                last_name=last_name,
                phone_number=data.get('phone_number', '')
            )

            # Create email verification if requested
            if send_verification:
                try:
                    verification = EmailVerification.create_verification(user)
                    EmailService.send_verification_email(user, verification)
                except Exception as e:
                    # Log the error but don't fail registration
                    logger.error(f"Error sending verification email: {e}")
                    # For testing, automatically verify the user
                    user.is_email_verified = True
                    user.save()

            return {
                'access_token': AuthService.create_token(user.id),
                'refresh_token': AuthService.create_refresh_token(user.id),
                'user': user
            }
        except Exception as e:
            logger.error(f"Registration error: {e}")
            raise

    @staticmethod
    def verify_email(token):
        """Verify a user's email with a token"""
        try:
            verification = EmailVerification.objects.get(token=token)

            if verification.is_expired:
                return False

            user = verification.user
            user.is_email_verified = True
            user.save()

            # Delete the verification token
            verification.delete()

            return True
        except EmailVerification.DoesNotExist:
            return False

    @staticmethod
    def request_password_reset(email):
        """Request a password reset for a user"""
        try:
            user = User.objects.get(email=email)

            # Delete any existing reset tokens
            PasswordReset.objects.filter(user=user, is_used=False).delete()

            # Create a new reset token
            reset = PasswordReset.create_reset_token(user)

            # Send email
            EmailService.send_password_reset_email(user, reset)

            return True
        except User.DoesNotExist:
            # We don't want to reveal if an email exists or not
            return False

    @staticmethod
    def reset_password(token, new_password):
        """Reset a user's password with a token"""
        try:
            reset = PasswordReset.objects.get(token=token, is_used=False)

            if reset.is_expired:
                return False

            user = reset.user
            user.set_password(new_password)
            user.save()

            # Mark the token as used
            reset.is_used = True
            reset.save()

            # Invalidate all sessions
            UserSession.objects.filter(user=user).update(is_active=False)

            return True
        except PasswordReset.DoesNotExist:
            return False

    @staticmethod
    def refresh_token(refresh_token):
        """Get a new access token using a refresh token"""
        user = AuthService.get_user_from_token(refresh_token)
        if not user:
            raise ValidationError("Invalid refresh token")

        return {
            'access_token': AuthService.create_token(user.id),
            'refresh_token': AuthService.create_refresh_token(user.id)
        }


class UserService:
    @staticmethod
    def get_profile(user_id):
        """Get a user's profile"""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise ValidationError("User not found")

    @staticmethod
    def update_profile(user, data):
        """Update a user's profile"""
        for field, value in data.items():
            if hasattr(user, field) and value is not None:
                setattr(user, field, value)

        user.save()
        return user

    @staticmethod
    def change_password(user, current_password, new_password):
        """Change a user's password"""
        if not user.check_password(current_password):
            raise ValidationError("Current password is incorrect")

        user.set_password(new_password)
        user.save()

        # Invalidate all sessions except the current one
        UserSession.objects.filter(user=user).update(is_active=False)

        return True

    @staticmethod
    def get_sessions(user):
        """Get all sessions for a user"""
        return UserSession.objects.filter(user=user).order_by('-last_activity')

    @staticmethod
    def revoke_session(user, session_id):
        """Revoke a specific session"""
        try:
            session = UserSession.objects.get(user=user, session_id=session_id)
            session.is_active = False
            session.save()
            return True
        except UserSession.DoesNotExist:
            return False

    @staticmethod
    def revoke_all_sessions(user, except_session_id=None):
        """Revoke all sessions for a user, optionally except one"""
        sessions = UserSession.objects.filter(user=user)
        if except_session_id:
            sessions = sessions.exclude(session_id=except_session_id)

        sessions.update(is_active=False)
        return True


class EmailService:
    @staticmethod
    def send_verification_email(user, verification):
        """Send an email verification email"""
        try:
            subject = 'Verify your email address'

            # Get FRONTEND_URL from settings or use a default
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            verification_url = f"{frontend_url}/verify-email?token={verification.token}"

            # You can use a template here
            message = f"""
            Hi {user.first_name or user.username},

            Please verify your email address by clicking the link below:   

            {verification_url}

            This link will expire in 24 hours.

            Thanks,
            The Team
            """

            send_mail(
                subject,
                message,
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                [user.email]
            )
            return True
        except Exception as e:
            logger.error(f"Error sending verification email: {e}")
            return False

    @staticmethod
    def send_password_reset_email(user, reset):
        """Send a password reset email"""
        try:
            subject = 'Reset your password'

            # Get FRONTEND_URL from settings or use a default
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            reset_url = f"{frontend_url}/reset-password?token={reset.token}"

            # You can use a template here
            message = f"""
            Hi {user.first_name or user.username},

            You requested to reset your password. Click the link below to set a new password:

            {reset_url}

            This link will expire in 1 hour.

            If you didn't request this, please ignore this email.

            Thanks,
            The Team
            """

            send_mail(
                subject,
                message,
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                [user.email]
            )
            return True
        except Exception as e:
            logger.error(f"Error sending password reset email: {e}")
            return False

