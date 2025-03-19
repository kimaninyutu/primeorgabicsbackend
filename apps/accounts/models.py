# apps/accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone  # Import Django's timezone utility
import uuid
from datetime import timedelta  # Remove datetime import


class User(AbstractUser):
    """
    Custom user model that extends Django's AbstractUser
    """
    # Override the username field to remove the unique constraint
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=False,  # Changed from True to False
        help_text=_('Required. 150 characters or fewer.'),
        error_messages={
            'max_length': _("Username must be 150 characters or fewer."),
        },
    )

    # Add custom related_name attributes to avoid clashes
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name='accounts_user_set',  # Custom related_name
        related_query_name='accounts_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='accounts_user_set',  # Custom related_name
        related_query_name='accounts_user',
    )

    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        db_table = 'users'

    def __str__(self):
        return self.email


class EmailVerification(models.Model):
    """
    Model to store email verification tokens
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_verifications')
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"{self.user.email} - {self.token}"

    @classmethod
    def create_verification(cls, user, expiry_hours=24):
        """Create a new verification token for a user"""
        # Use timezone.now() instead of datetime.now()
        expires_at = timezone.now() + timedelta(hours=expiry_hours)
        return cls.objects.create(user=user, expires_at=expires_at)

    @property
    def is_expired(self):
        """Check if the verification token has expired"""
        # Use timezone.now() instead of datetime.now()
        return timezone.now() > self.expires_at


class PasswordReset(models.Model):
    """
    Model to store password reset tokens
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_resets')
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.email} - {self.token}"

    @classmethod
    def create_reset_token(cls, user, expiry_hours=1):
        """Create a new password reset token for a user"""
        # Use timezone.now() instead of datetime.now()
        expires_at = timezone.now() + timedelta(hours=expiry_hours)
        return cls.objects.create(user=user, expires_at=expires_at)

    @property
    def is_expired(self):
        """Check if the reset token has expired"""
        # Use timezone.now() instead of datetime.now()
        return timezone.now() > self.expires_at or self.is_used


class UserSession(models.Model):
    """
    Model to track user sessions for security
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user_agent = models.TextField()
    ip_address = models.GenericIPAddressField()
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.email} - {self.session_id}"

