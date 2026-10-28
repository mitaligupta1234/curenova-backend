import logging
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.models import User
from ..services.auth_service import decode_jwt_token

logger = logging.getLogger("curenova.auth")

# HTTP Bearer token extractor for Swagger UI and API requests
http_bearer = HTTPBearer(
    auto_error=False,
    description="Enter the JWT access token returned by POST /api/auth/login"
)
# Backwards-compatibility alias
oauth2_scheme = http_bearer

def get_current_user(
    auth: HTTPAuthorizationCredentials | None = Depends(http_bearer),
    db: Session = Depends(get_db)
) -> User:
    """
    Extracts and validates the Bearer access token from Authorization header.
    Returns the authenticated User instance.
    """
    if not auth or not auth.credentials:
        logger.warning("Auth failure: Authorization Bearer header missing or empty")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = auth.credentials.strip()
    try:
        payload = decode_jwt_token(token, expected_type="access")
    except jwt.ExpiredSignatureError:
        logger.warning("Auth failure: Access token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.PyJWTError as jwt_err:
        logger.warning("Auth failure: Invalid token signature or claims: %s", str(jwt_err))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user

def get_optional_current_user(
    auth: HTTPAuthorizationCredentials | None = Depends(http_bearer),
    db: Session = Depends(get_db)
) -> User | None:
    """
    Returns the authenticated user if Bearer token is provided and valid,
    or None if no authentication was supplied.
    """
    if not auth or not auth.credentials:
        return None
    try:
        payload = decode_jwt_token(auth.credentials, expected_type="access")
        user_id = int(payload.get("sub", 0))
        return db.query(User).filter(User.id == user_id, User.is_active == True).first()
    except Exception:
        return None

def get_current_active_user(

    current_user: User = Depends(get_current_user)
) -> User:
    """Ensures the authenticated user account is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    return current_user

def require_role(*allowed_roles: str):
    """
    Dependency factory enforcing role-based authorization and verification status.
    Denies access to non-approved privileged accounts.
    """
    def role_dependency(user: User = Depends(get_current_active_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Action requires one of roles: {', '.join(allowed_roles)}"
            )
        # Ensure doctor or researcher cannot act until approved
        if user.role in ("researcher", "doctor") and user.approval_status != "approved":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Account status is '{user.approval_status}'. Approval required for {user.role} role."
            )
        return user
    return role_dependency

# Convenience role dependencies
require_researcher = require_role("researcher", "admin")
require_doctor = require_role("doctor", "admin")
require_admin = require_role("admin")
