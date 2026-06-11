import uuid
from sqlmodel import select
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_db_session 
from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.user import UserCreate
# Make sure to import your User model!
from app.models.user import User 

router = APIRouter(tags=["Authentication"])

# ==========================================
# CREATE NEW USER (SIGNUP)
# ==========================================
@router.post(
    "/signup", 
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user"
)
async def create_user(
    request: UserCreate, 
    db: AsyncSession = Depends(get_db_session)
):
    # 1. Check if the email already exists
    query = select(User).where(User.email == request.email)
    result = await db.execute(query)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )

    # 2. Create the new user
    new_user = User(
        id=uuid.uuid4(), # Generates a brand new secure UUID!
        name=request.name,
        email=request.email,
        phone_no=request.phone_no,
        # TODO: We need to hash this password later!
        password_hash=request.password, 
        is_active=True
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return {
        "message": "User created successfully!",
        "user_id": new_user.id,
        "email": new_user.email
    }

# ==========================================
# DEVELOPMENT LOGIN (CONNECTS TO DATABASE)
# ==========================================
@router.post(
    "/login", 
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Development login: authenticates against real DB users"
)
async def db_login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db_session)
):
    # 1. Look up the user by email
    query = select(User).where(User.email == request.email)
    result = await db.execute(query)
    db_user = result.scalar_one_or_none()

    # 2. Verify the user exists AND the password matches
    # NOTE: We are doing a direct string comparison here because you 
    # haven't added password hashing yet. This is perfect for testing!
    if not db_user or db_user.password_hash != request.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
        
    # 3. Check if the account was soft-deleted or deactivated
    if not db_user.is_active or db_user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated."
        )

    # 4. Return the REAL database user details!
    return {
        "access_token": f"fake-jwt-token-for-{db_user.id}", # Still fake, but unique to them
        "token_type": "bearer",
        "user_id": str(db_user.id),
        "name": db_user.name,
        "email": db_user.email
    }


# Later, when you are ready to secure the application for production, you only have to change db_user.password_hash != request.password to a secure hash checker (like verify_password(request.password, db_user.password_hash)), and the frontend won't have to change a single line of code!