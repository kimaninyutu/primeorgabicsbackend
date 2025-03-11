# apps/accounts/api.py
from ninja import Router, File
from ninja.files import UploadedFile
from ninja.security import HttpBearer
from django.core.exceptions import ValidationError
from django.http import HttpRequest
from typing import Dict, List
from .schemas import (
    LoginSchema, RegisterSchema, TokenSchema, UserProfileSchema,
    UserProfileUpdateSchema, PasswordResetRequestSchema,
    PasswordResetConfirmSchema, RefreshTokenSchema,
    EmailVerificationSchema, ChangePasswordSchema,
    MessageResponseSchema, ErrorResponseSchema,
    SessionSchema, SessionListSchema
)
from .services import AuthService, UserService
from .models import User


# Authentication middleware
class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        user = AuthService.get_user_from_token(token)
        if user:
            request.user = user
            return token
        return None


router = Router()


# Authentication endpoints
@router.post("/login", response={200: TokenSchema, 401: ErrorResponseSchema})
def login(request, payload: LoginSchema):
    try:
        # Get user agent and IP for session tracking
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        ip_address = request.META.get('REMOTE_ADDR')

        result = AuthService.login(
            payload.email,
            payload.password,
            user_agent=user_agent,
            ip_address=ip_address
        )

        return 200, {
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": "bearer"
        }
    except ValidationError as e:
        return 401, {"detail": str(e)}


@router.post("/register", response={201: TokenSchema, 400: ErrorResponseSchema})
def register(request, payload: RegisterSchema):
    try:
        result = AuthService.register(payload.dict())

        return 201, {
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": "bearer"
        }
    except ValidationError as e:
        return 400, {"detail": str(e)}


@router.post("/verify-email", response={200: MessageResponseSchema, 400: ErrorResponseSchema})
def verify_email(request, payload: EmailVerificationSchema):
    if AuthService.verify_email(payload.token):
        return 200, {"message": "Email verified successfully"}
    return 400, {"detail": "Invalid or expired token"}


@router.post("/password-reset/request", response={200: MessageResponseSchema})
def request_password_reset(request, payload: PasswordResetRequestSchema):
    AuthService.request_password_reset(payload.email)
    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/password-reset/confirm", response={200: MessageResponseSchema, 400: ErrorResponseSchema})
def confirm_password_reset(request, payload: PasswordResetConfirmSchema):
    if AuthService.reset_password(payload.token, payload.new_password):
        return {"message": "Password reset successfully"}
    return 400, {"detail": "Invalid or expired token"}


@router.post("/refresh-token", response={200: TokenSchema, 401: ErrorResponseSchema})
def refresh_token(request, payload: RefreshTokenSchema):
    try:
        result = AuthService.refresh_token(payload.refresh_token)
        return 200, {
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": "bearer"
        }
    except ValidationError as e:
        return 401, {"detail": str(e)}


@router.post("/logout", response={200: MessageResponseSchema}, auth=AuthBearer())
def logout(request):
    # Get the current session ID from the request if available
    session_id = request.META.get('HTTP_X_SESSION_ID')

    if session_id:
        # Revoke only this session
        UserService.revoke_session(request.user, session_id)

    return {"message": "Logged out successfully"}


# User profile endpoints
@router.get("/me", response={200: UserProfileSchema, 401: ErrorResponseSchema}, auth=AuthBearer())
def get_profile(request):
    return request.user


@router.put("/me", response={200: UserProfileSchema, 400: ErrorResponseSchema}, auth=AuthBearer())
def update_profile(request, payload: UserProfileUpdateSchema):
    try:
        updated_user = UserService.update_profile(request.user, payload.dict(exclude_unset=True))
        return updated_user
    except ValidationError as e:
        return 400, {"detail": str(e)}


@router.post("/me/change-password", response={200: MessageResponseSchema, 400: ErrorResponseSchema}, auth=AuthBearer())
def change_password(request, payload: ChangePasswordSchema):
    try:
        UserService.change_password(
            request.user,
            payload.current_password,
            payload.new_password
        )
        return {"message": "Password changed successfully"}
    except ValidationError as e:
        return 400, {"detail": str(e)}


@router.post("/me/profile-picture", response={200: MessageResponseSchema, 400: ErrorResponseSchema}, auth=AuthBearer())
def upload_profile_picture(request, file: UploadedFile = File(...)):
    try:
        request.user.profile_picture.save(
            file.name,
            file.file,
            save=True
        )
        return {"message": "Profile picture uploaded successfully"}
    except Exception as e:
        return 400, {"detail": str(e)}


# Session management endpoints
@router.get("/sessions", response=SessionListSchema, auth=AuthBearer())
def get_sessions(request):
    sessions = UserService.get_sessions(request.user)
    return {"sessions": sessions}


@router.delete("/sessions/{session_id}", response={200: MessageResponseSchema, 404: ErrorResponseSchema},
               auth=AuthBearer())
def revoke_session(request, session_id: str):
    if UserService.revoke_session(request.user, session_id):
        return {"message": "Session revoked successfully"}
    return 404, {"detail": "Session not found"}


@router.delete("/sessions", response=MessageResponseSchema, auth=AuthBearer())
def revoke_all_sessions(request):
    # Get the current session ID to keep it active
    current_session_id = request.META.get('HTTP_X_SESSION_ID')

    UserService.revoke_all_sessions(request.user, except_session_id=current_session_id)
    return {"message": "All other sessions revoked successfully"}