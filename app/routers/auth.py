import hashlib
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.database import get_db
from app.models.refresh_tokens import RefreshToken
from app.models.users import User
from app.schemas.token import TokenRefresh
from app.schemas.user import UserCreate, UserLogin, UserUpdate
from app.services.auth import generate_access_token, generate_refresh_token
from app.services.users import get_current_user

router = APIRouter(tags=["auth"])


@router.post("/register")
async def register(
    user_create: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    # check duplicate email
    result = await db.execute(select(User).where(User.email == user_create.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    new_user = User(
        email=user_create.email,
        hashed_password=get_password_hash(user_create.password),
        full_name=user_create.full_name,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return {"message": "User registered successfully"}


@router.post("/login")
async def login(user_login: UserLogin, db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(User).where(User.email == user_login.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = generate_access_token(data={"sub": str(user.user_id)})

    raw_token, token_hash, expires_at = generate_refresh_token()

    db.add(
        RefreshToken(
            user_id=user.user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
    )
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": raw_token,
        "token_type": "bearer",
    }


@router.post("/refresh")
async def refresh_token(
    refresh_token: TokenRefresh,
    db: AsyncSession = Depends(get_db),
):
    import hashlib
    from datetime import datetime

    from sqlalchemy import select

    token_hash = hashlib.sha256(refresh_token.refresh_token.encode()).hexdigest()

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False,
        )
    )
    stored_token = result.scalar_one_or_none()

    if not stored_token or stored_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token",
        )

    result = await db.execute(select(User).where(User.user_id == stored_token.user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    stored_token.revoked = True

    new_access_token = generate_access_token(data={"sub": str(user.user_id)})

    raw_token, new_hash, expires_at = generate_refresh_token()

    new_refresh_token = RefreshToken(
        user_id=user.user_id,
        token_hash=new_hash,
        expires_at=expires_at,
    )

    db.add(new_refresh_token)
    await db.commit()

    return {
        "access_token": new_access_token,
        "refresh_token": raw_token,
        "token_type": "bearer",
    }


@router.post("/logout")
async def logout(
    refresh_token: TokenRefresh,
    db: AsyncSession = Depends(get_db),
):
    token_hash = hashlib.sha256(refresh_token.refresh_token.encode()).hexdigest()

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False,
        )
    )
    stored_token = result.scalar_one_or_none()

    if not stored_token or stored_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Invalid token")

    stored_token.revoked = True
    await db.commit()

    return {"message": "Logged out successfully"}


@router.put("/me")
async def update_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):

    update_data = data.model_dump(exclude_unset=True)

    if "email" in update_data:
        result = await db.execute(
            select(User).where(User.email == update_data["email"])
        )
        existing_user = result.scalar_one_or_none()

        if existing_user and existing_user.user_id != current_user.user_id:
            raise HTTPException(status_code=400, detail="Email already in use")

        current_user.email = update_data["email"]

    if "full_name" in update_data:
        current_user.full_name = update_data["full_name"]

    if "password" in update_data:
        current_user.hashed_password = get_password_hash(update_data["password"])

    try:
        await db.commit()
        await db.refresh(current_user)
    except Exception:
        await db.rollback()
        raise

    return {"message": "Profile updated successfully"}


@router.get("/me")
async def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "email": current_user.email,
        "full_name": current_user.full_name,
        "created_at": current_user.created_at,
    }
