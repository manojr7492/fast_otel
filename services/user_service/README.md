# 🛒 E-Commerce User & Authentication Microservice

An enterprise-grade, production-ready User & Authentication microservice built with **Python 3.11**, **FastAPI**, **SQLAlchemy 2.0 (Async)**, **Alembic**, and **MySQL**.

This microservice handles user registration, authentication (JWT access and rotating refresh tokens), role-based access control (RBAC), user profiles, and customer address management. It connects to the dedicated MySQL database `fastapi_user_db` running on port `3306`.

---

## 📑 Table of Contents
1. [Architecture Overview](#-architecture-overview)
2. [Project Directory Layout](#-project-directory-layout)
3. [Component, File & Function Reference](#-component-file--function-reference)
   - [Core Module (`app/core/`)](#1-core-module-appcore)
   - [Database Layer (`app/db/`)](#2-database-layer-appdb)
   - [Domain Models (`app/models/`)](#3-domain-models-appmodels)
   - [Pydantic v2 Schemas (`app/schemas/`)](#4-pydantic-v2-schemas-appschemas)
   - [Repository Pattern (`app/repositories/`)](#5-repository-pattern-apprepositories)
   - [Business Logic Services (`app/services/`)](#6-business-logic-services-appservices)
   - [Dependencies & Guards (`app/api/deps.py`)](#7-dependencies--guards-appapidepspy)
   - [API Endpoints (`app/api/v1/endpoints/`)](#8-api-endpoints-appapiv1endpoints)
   - [Application Entry Point (`app/main.py`)](#9-application-entry-point-appmainpy)
4. [Performance & Complexity Optimizations](#-performance--complexity-optimizations)
5. [Database Migrations (Alembic)](#-database-migrations-alembic)
6. [API Endpoints Reference](#-api-endpoints-reference)
7. [Setup & Running Locally](#-setup--running-locally)
8. [Automated Verification Tests](#-automated-verification-tests)

---

## 🏛 Architecture Overview

This microservice is designed following **Clean Layered Architecture** principles:

```
┌────────────────────────────────────────────────────────┐
│             HTTP Client / API Gateway                  │
└──────────────────────────┬─────────────────────────────┘
                           │ (HTTP / JSON)
┌──────────────────────────▼─────────────────────────────┐
│ API Layer (Routers, Middleware, Dependencies, RBAC)    │
│  - app/api/v1/endpoints/auth.py                        │
│  - app/api/v1/endpoints/users.py                       │
│  - app/api/v1/endpoints/addresses.py                   │
│  - app/api/deps.py (JWT verification & Role Guards)    │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ Service Layer (Business Logic & Orchestration)         │
│  - AuthService                                         │
│  - UserService                                         │
│  - AddressService                                      │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ Repository Layer (Database Access & Query Optimization)│
│  - UserRepository                                      │
│  - AddressRepository                                   │
│  - BaseRepository                                      │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ Database Layer (Async Engine, Pooling, Models)         │
│  - MySQL (`fastapi_user_db`) on port 3306              │
│  - SQLAlchemy 2.0 Async (`asyncmy` driver)             │
│  - Alembic Migrations (`pymysql` driver)               │
└────────────────────────────────────────────────────────┘
```

---

## 📂 Project Directory Layout

```
services/user_service/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── addresses.py     # Shipping/billing address CRUD endpoints
│   │   │   │   ├── auth.py          # Register, login, refresh, password endpoints
│   │   │   │   └── users.py         # User profile and admin management endpoints
│   │   │   └── router.py            # API V1 router aggregation
│   │   └── deps.py                  # Database session, JWT decoding & RBAC dependencies
│   ├── core/
│   │   ├── config.py                # Pydantic Settings, environment variables, DB URLs
│   │   ├── exceptions.py            # Centralized domain exception hierarchy
│   │   ├── logging.py               # Structured application logger
│   │   └── security.py              # Bcrypt password hashing & PyJWT token utilities
│   ├── db/
│   │   ├── base.py                  # Model registry for Alembic discovery
│   │   └── session.py               # Async engine, connection pooling, session factory
│   ├── models/
│   │   ├── __init__.py              # Export models
│   │   ├── address.py               # SQLAlchemy Address table model
│   │   ├── base.py                  # DeclarativeBase and TimestampMixin
│   │   └── user.py                  # SQLAlchemy User table model
│   ├── repositories/
│   │   ├── address_repository.py    # Address database queries and default resets
│   │   ├── base.py                  # Generic async CRUD repository base class
│   │   └── user_repository.py       # Optimized user queries with B-Tree index lookups
│   ├── schemas/
│   │   ├── address.py               # Address Pydantic v2 validation models
│   │   ├── common.py                # Standard API response envelope & pagination schemas
│   │   ├── token.py                 # JWT Token response & payload models
│   │   └── user.py                  # User registration, login, update, and profile schemas
│   ├── services/
│   │   ├── address_service.py       # Address business rules and default toggling
│   │   ├── auth_service.py          # Registration, login, token rotation, password updates
│   │   └── user_service.py          # Profile management, RBAC updates, user pagination
│   └── main.py                      # FastAPI app, lifespan, CORS, middleware, global error handlers
├── alembic/                         # Database migration scripts & history
├── alembic.ini                      # Alembic configuration
├── .env                             # Active environment variable settings
├── .env.example                     # Environment template
├── requirements.txt                 # Pinned dependencies
├── run.py                           # Local server launcher (Port 8001)
└── verify_service.py                # Automated 11-step end-to-end integration test suite
```

---

## 🔍 Component, File & Function Reference

### 1. Core Module (`app/core/`)

#### `app/core/config.py`
Manages application configuration via `pydantic_settings.BaseSettings`, parsing environment variables from `.env`.
- **`Settings`**:
  - `PROJECT_NAME`, `SERVICE_NAME`, `ENVIRONMENT`, `DEBUG`: Metadata and operational mode.
  - `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DB`: MySQL connectivity.
  - `DB_POOL_SIZE` (default 20), `DB_MAX_OVERFLOW` (default 10), `DB_POOL_TIMEOUT` (30s), `DB_POOL_RECYCLE` (1800s), `DB_POOL_PRE_PING` (True): Connection pool controls.
  - `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`: JWT parameters.
  - `async_database_url`: Returns formatted async URI: `mysql+asyncmy://root:...@127.0.0.1:3306/fastapi_user_db?charset=utf8mb4`.
  - `sync_database_url`: Returns sync URI used by Alembic: `mysql+pymysql://root:...@127.0.0.1:3306/fastapi_user_db?charset=utf8mb4`.
  - `assemble_cors_origins(cls, v)`: Parses comma-delimited strings or JSON lists into Python list of allowed origins.

#### `app/core/security.py`
Provides cryptographic operations and token management without deprecated libraries.
- **`hash_password(password: str) -> str`**: Hashes plaintext password using `bcrypt.hashpw` with salt (cost factor 12). Space: $O(1)$.
- **`verify_password(plain_password: str, hashed_password: str) -> bool`**: Verifies password in constant time using `bcrypt.checkpw` to prevent timing attacks.
- **`create_token(subject, role, token_type, expires_delta, additional_claims) -> str`**: Creates a signed JWT containing claims: `sub`, `role`, `type`, `iat`, `exp`, and a unique `jti` (UUID4).
- **`create_access_token(subject, role, expires_delta, additional_claims) -> str`**: Creates short-lived access token (default 30 min).
- **`create_refresh_token(subject, role, expires_delta) -> str`**: Creates rotating refresh token (default 7 days).
- **`decode_jwt_token(token: str) -> Dict[str, Any]`**: Decodes token, verifies cryptographic signature, checks expiration. Raises `TokenExpiredException` or `TokenInvalidException` on failure.

#### `app/core/exceptions.py`
Defines an object-oriented domain exception hierarchy:
- **`AppException`**: Base exception with `message`, `status_code`, `error_code`, and optional `details`.
- **`EntityNotFoundException`** (HTTP 404): Raised when user or address cannot be found.
- **`EntityAlreadyExistsException`** (HTTP 409): Raised on duplicate email or username.
- **`InvalidCredentialsException`** (HTTP 401): Raised when login credentials fail verification.
- **`UnauthorizedException`** (HTTP 401): Raised when token is missing or invalid.
- **`ForbiddenException`** (HTTP 403): Raised when role fails RBAC requirements.
- **`UserInactiveException`** (HTTP 403): Raised when deactivated user attempts access.
- **`TokenExpiredException`** (HTTP 401): Raised when JWT expired.
- **`TokenInvalidException`** (HTTP 401): Raised when JWT malformed.
- **`BadRequestException`** (HTTP 400): Raised on invalid business parameters.

#### `app/core/logging.py`
Configures structured console logging.
- **`setup_logging()`**: Sets timestamped, process-aware log format, adjusts log levels, and suppresses verbose third-party log noise in development.

---

### 2. Database Layer (`app/db/`)

#### `app/db/session.py`
Manages asynchronous database connection pooling and lifecycle.
- **`engine`**: SQLAlchemy `AsyncEngine` initialized with connection pool settings (`pool_size=20`, `max_overflow=10`, `pool_recycle=1800`, `pool_pre_ping=True`).
- **`AsyncSessionFactory`**: Thread-safe `async_sessionmaker[AsyncSession]` with `expire_on_commit=False`.
- **`get_db_session() -> AsyncGenerator[AsyncSession, None]`**: FastAPI dependency yielding an isolated async session per request. Automatically calls `rollback()` on exceptions and guarantees `session.close()` in `finally`.

#### `app/db/base.py`
Aggregates `Base.metadata` and all models (`User`, `Address`) so Alembic can discover tables for autogenerating migrations.

---

### 3. Domain Models (`app/models/`)

#### `app/models/base.py`
- **`Base(DeclarativeBase)`**: SQLAlchemy 2.0 DeclarativeBase.
- **`TimestampMixin`**: Reusable mixin adding:
  - `created_at`: DateTime with server default `func.now()`, indexed for time-range filtering.
  - `updated_at`: DateTime with server default and `onupdate=func.now()`.

#### `app/models/user.py`
- **`UserRole(str, enum.Enum)`**: `CUSTOMER`, `ADMIN`, `SUPER_ADMIN`.
- **`User(Base, TimestampMixin)`**:
  - `id`: BigInteger primary key, auto-incrementing.
  - `uuid`: String(36), unique, indexed (used for public and cross-service IDs).
  - `email`: String(255), unique, indexed ($O(\log N)$ lookup).
  - `username`: String(50), unique, indexed.
  - `hashed_password`: String(255).
  - `first_name`, `last_name`, `phone_number` (indexed).
  - `role`: Enum `UserRole`, indexed.
  - `is_active`: Boolean, default `True`, indexed.
  - `is_verified`: Boolean, default `False`.
  - `addresses`: Relationship to `Address` (`cascade="all, delete-orphan"`, `lazy="selectin"` to prevent N+1 queries).
  - **Compound Indexes**: `ix_users_email_active` on `(email, is_active)` and `ix_users_username_active` on `(username, is_active)`.

#### `app/models/address.py`
- **`AddressType(str, enum.Enum)`**: `SHIPPING`, `BILLING`.
- **`Address(Base, TimestampMixin)`**:
  - `id`: BigInteger primary key.
  - `uuid`: String(36), unique, indexed.
  - `user_id`: BigInteger, ForeignKey to `users.id` with `ondelete="CASCADE"`.
  - `address_type`: Enum `AddressType`.
  - `street_address`, `apartment`, `city` (indexed), `state`, `country`, `postal_code` (indexed).
  - `is_default`: Boolean.
  - `user`: Many-to-one relationship back to `User`.
  - **Compound Index**: `ix_addresses_user_default` on `(user_id, is_default)`.

---

### 4. Pydantic v2 Schemas (`app/schemas/`)

#### `app/schemas/common.py`
- **`APIResponse[T]`**: Uniform enterprise response envelope:
  ```json
  {
    "success": true,
    "status_code": 200,
    "message": "Operation completed successfully.",
    "data": { ... },
    "meta": { "timestamp": "2026-10-17T07:00:00Z" }
  }
  ```
- **`PaginationParams`**: Validated query parameters: `page` ($\ge 1$), `size` ($1 \le \text{size} \le 100$). Provides computed property `.offset`.
- **`PaginationMeta`**: Contains `total_records`, `current_page`, `page_size`, `total_pages`, `has_next`, `has_prev`.
- **`PaginatedData[T]`**: Wraps `items: List[T]` and `pagination: PaginationMeta`.

#### `app/schemas/token.py`
- **`TokenResponse`**: Contains `access_token`, `refresh_token`, `token_type`, and `expires_in`.
- **`RefreshTokenRequest`**: Validates incoming `refresh_token` string.
- **`TokenPayload`**: Schema for decoded JWT claims (`sub`, `role`, `type`, `exp`, `jti`).

#### `app/schemas/user.py`
- **`UserBase`**: Base fields with email validation and username regex (`^[a-zA-Z0-9_-]+$`).
- **`UserRegisterRequest`**: Validates password complexity: minimum 8 characters, at least 1 uppercase letter, 1 lowercase letter, 1 number, and 1 special character.
- **`UserLoginRequest`**: Accepts `login_identifier` (email or username) and `password`.
- **`UserUpdateRequest`**: Optional profile fields (`first_name`, `last_name`, `phone_number`).
- **`UserRoleUpdateRequest`**: Role change schema for admins.
- **`UserStatusUpdateRequest`**: Account activation/deactivation schema.
- **`PasswordChangeRequest`**: Validates `old_password` and new strong `new_password`.
- **`UserResponse`**: Safe user representation excluding sensitive password hashes.
- **`UserDetailResponse`**: Extends `UserResponse` with eager-loaded `addresses: List[AddressResponse]`.

#### `app/schemas/address.py`
- **`AddressBase`**: Validates street address, city, state, postal code, and country.
- **`AddressCreate`**: Input schema for creating addresses.
- **`AddressUpdate`**: Partial update schema with optional fields.
- **`AddressResponse`**: Response schema containing `uuid`, timestamps, and address details.

---

### 5. Repository Pattern (`app/repositories/`)

#### `app/repositories/base.py`
- **`BaseRepository[ModelType]`**:
  - `get_by_id(id: int) -> Optional[ModelType]`: $O(1)$ primary key lookup.
  - `get_by_uuid(uuid_str: str) -> Optional[ModelType]`: $O(\log N)$ indexed lookup.
  - `list_paginated(offset, limit) -> Sequence[ModelType]`: Retrieves ordered records.
  - `count() -> int`: Scalar count query.
  - `create(instance) -> ModelType`: Adds instance and flushes.
  - `update(instance) -> ModelType`: Flushes updates.
  - `delete(instance) -> None`: Removes instance from session.

#### `app/repositories/user_repository.py`
- **`UserRepository(BaseRepository[User])`**:
  - `get_by_email(email: str) -> Optional[User]`: Case-insensitive $O(\log N)$ indexed lookup.
  - `get_by_username(username: str) -> Optional[User]`: $O(\log N)$ indexed lookup.
  - `get_by_login_identifier(identifier: str) -> Optional[User]`: Resolves user by matching either email or username in a single optimized query.
  - `get_with_addresses(uuid_str: str) -> Optional[User]`: Uses `selectinload(User.addresses)` to fetch user and addresses in 2 efficient batch queries without N+1 overhead.
  - `email_exists(email: str) -> bool`: Fast `SELECT COUNT(1)` check.
  - `username_exists(username: str) -> bool`: Fast `SELECT COUNT(1)` check.
  - `list_users(offset, limit, role, is_active) -> Tuple[Sequence[User], int]`: Paginated query with dynamic filtering and total record count.

#### `app/repositories/address_repository.py`
- **`AddressRepository(BaseRepository[Address])`**:
  - `get_by_uuid_and_user_id(uuid_str: str, user_id: int) -> Optional[Address]`: Scoped query ensuring tenant isolation (user can only access their own address).
  - `list_by_user_id(user_id: int) -> Sequence[Address]`: Ordered by `is_default DESC, id DESC`.
  - `reset_default_addresses(user_id: int) -> None`: Single `UPDATE addresses SET is_default=0 WHERE user_id=:id AND is_default=1` query.

---

### 6. Business Logic Services (`app/services/`)

#### `app/services/auth_service.py`
- **`AuthService`**:
  - `register(user_in: UserRegisterRequest) -> User`: Validates uniqueness, hashes password, saves user with `CUSTOMER` role.
  - `authenticate(login_in: UserLoginRequest) -> TokenResponse`: Resolves identifier, verifies password with constant-time comparison, validates active status, generates access and refresh tokens.
  - `refresh_access_token(refresh_token: str) -> TokenResponse`: Implements **Token Rotation**: validates refresh token, confirms user status, and issues a fresh access token AND a fresh refresh token.
  - `change_password(user: User, change_in: PasswordChangeRequest) -> None`: Verifies old password against current hash and stores newly hashed password.

#### `app/services/user_service.py`
- **`UserService`**:
  - `get_by_uuid(uuid_str: str) -> User`: Retrieves user or raises `EntityNotFoundException`.
  - `get_profile_with_addresses(uuid_str: str) -> UserDetailResponse`: Loads user with addresses.
  - `update_profile(user: User, update_in: UserUpdateRequest) -> UserResponse`: Updates permitted fields.
  - `list_users(pagination, role, is_active) -> PaginatedData[UserResponse]`: Computes total pages, sets `has_next`/`has_prev`, and returns paginated users.
  - `update_user_role(target_uuid: str, role_in: UserRoleUpdateRequest) -> UserResponse`: Admin role modifier.
  - `update_user_status(target_uuid: str, status_in: UserStatusUpdateRequest) -> UserResponse`: Admin activation/deactivation.

#### `app/services/address_service.py`
- **`AddressService`**:
  - `list_user_addresses(user: User) -> List[AddressResponse]`: Lists addresses.
  - `get_user_address(user: User, address_uuid: str) -> AddressResponse`: Retrieves single address.
  - `create_user_address(user: User, create_in: AddressCreate) -> AddressResponse`: If `is_default=True`, clears prior defaults before inserting.
  - `update_user_address(user: User, address_uuid: str, update_in: AddressUpdate) -> AddressResponse`: Updates fields; resets other defaults if set to default.
  - `delete_user_address(user: User, address_uuid: str) -> None`: Deletes user address.

---

### 7. Dependencies & Guards (`app/api/deps.py`)

- **`oauth2_scheme`**: `OAuth2PasswordBearer` configured with token endpoint `/api/v1/auth/token` for interactive Swagger UI login.
- **`get_current_user(token, authorization, db) -> User`**:
  1. Extracts token from Swagger Authorization header or `Authorization: Bearer <token>`.
  2. Decodes JWT using `decode_jwt_token`.
  3. Asserts token type is `"access"`.
  4. Looks up user via `UserRepository.get_by_uuid`.
  5. Verifies `user.is_active is True`.
  6. Returns resolved `User` instance.
- **`require_roles(*allowed_roles: UserRole)`**:
  - Higher-order dependency returning an async guard:
  ```python
  @router.get("/admin-only", dependencies=[Depends(require_roles(UserRole.ADMIN))])
  ```
  - Rejects unauthorized roles with HTTP 403 `ForbiddenException`.

---

### 8. API Endpoints (`app/api/v1/endpoints/`)

#### Authentication (`auth.py`)
- `POST /api/v1/auth/register`: Public. Registers new customer. Returns HTTP 201 with `APIResponse[UserResponse]`.
- `POST /api/v1/auth/login`: Public. JSON login returning `APIResponse[TokenResponse]`.
- `POST /api/v1/auth/token`: Public. Form-data login for Swagger UI authorization button.
- `POST /api/v1/auth/refresh`: Public. Exchanges refresh token for new access and refresh token.
- `POST /api/v1/auth/change-password`: Authenticated. Updates current user password.

#### Users (`users.py`)
- `GET /api/v1/users/me`: Authenticated. Returns current user profile with nested addresses.
- `PATCH /api/v1/users/me`: Authenticated. Updates name and phone number.
- `GET /api/v1/users/`: Admin only (`ADMIN`, `SUPER_ADMIN`). Paginated user directory with filters.
- `GET /api/v1/users/{uuid}`: Admin or account owner. Retrieves specific user details.
- `PATCH /api/v1/users/{uuid}/role`: Admin only. Promotes or demotes user role.
- `PATCH /api/v1/users/{uuid}/status`: Admin only. Activates or suspends user account.

#### Addresses (`addresses.py`)
- `GET /api/v1/addresses/`: Authenticated. Lists all shipping/billing addresses for current user.
- `POST /api/v1/addresses/`: Authenticated. Adds a new address. Returns HTTP 201.
- `GET /api/v1/addresses/{uuid}`: Authenticated. Retrieves single address by UUID.
- `PUT /api/v1/addresses/{uuid}`: Authenticated. Modifies address details.
- `DELETE /api/v1/addresses/{uuid}`: Authenticated. Deletes address.

---

### 9. Application Entry Point (`app/main.py`)

- **`lifespan(app: FastAPI)`**:
  - **On Startup**: Initializes logging, validates MySQL connectivity (`SELECT 1`), and logs pool readiness.
  - **On Shutdown**: Closes and disposes SQLAlchemy connection pool cleanly.
- **Middleware**:
  - `CORSMiddleware`: Permitted origins, credentials, headers, and methods.
  - `correlation_and_timing_middleware`: Injects unique `X-Request-ID` and latency `X-Process-Time-Ms` headers.
- **Centralized Exception Handlers**:
  - `AppException`: Standard envelope with domain error codes and HTTP status.
  - `RequestValidationError`: Formats Pydantic validation errors cleanly with field path and rules.
  - `IntegrityError`: Captures database duplicate keys or foreign key violations as HTTP 409 conflicts.
  - `Exception` (Unhandled): Catches unexpected crashes, logs full traceback with request ID, and returns a safe HTTP 500 without leaking stack traces.
- **System Routes**:
  - `GET /health`: Liveness probe verifying MySQL database connection.
  - `GET /`: Service metadata and Swagger link.

---

## ⚡ Performance & Complexity Optimizations

| Operation | Implementation | Time Complexity | Space Complexity |
| :--- | :--- | :--- | :--- |
| User lookup by UUID | Indexed B-Tree | $O(\log N)$ | $O(1)$ |
| User lookup by Email | Indexed B-Tree | $O(\log N)$ | $O(1)$ |
| User lookup by Username | Indexed B-Tree | $O(\log N)$ | $O(1)$ |
| Login identifier match | Single `OR` query on indexed columns | $O(\log N)$ | $O(1)$ |
| Password verification | Constant-time `bcrypt.checkpw` | $O(1)$ | $O(1)$ |
| Address query with User | `selectinload` batch join | $O(M)$ | $O(M)$ |
| Default address reset | Single SQL `UPDATE` statement | $O(\log K)$ | $O(1)$ |
| User listing pagination | Indexed `order_by(id.desc())` with `LIMIT` | $O(\text{limit})$ | $O(\text{limit})$ |

---

## 🗄 Database Migrations (Alembic)

Migrations are located in `alembic/versions/`.

### Run Migrations:
```bash
cd /Users/manojkumar/Desktop/FastAPI/services/user_service
../../.venv/bin/alembic upgrade head
```

### Rollback Migration:
```bash
../../.venv/bin/alembic downgrade -1
```

### Create New Migration:
```bash
../../.venv/bin/alembic revision --autogenerate -m "describe_changes"
```

---

## 🚀 Setup & Running Locally

### 1. Prerequisites
- Python 3.11+
- MySQL (XAMPP running on `localhost:3306`)
- Database created: `fastapi_user_db`

### 2. Activate Virtual Environment
```bash
cd /Users/manojkumar/Desktop/FastAPI
source .venv/bin/activate
```

### 3. Start the User Microservice
```bash
python services/user_service/run.py
```
The server will start on **`http://localhost:8001`**.

- **Swagger UI Interactive Docs**: [http://localhost:8001/api/v1/docs](http://localhost:8001/api/v1/docs)
- **ReDoc Documentation**: [http://localhost:8001/api/v1/redoc](http://localhost:8001/api/v1/redoc)
- **Health Check Probe**: [http://localhost:8001/health](http://localhost:8001/health)

---

## 🧪 Automated Verification Tests

A verification suite is included in `verify_service.py`. It runs 11 end-to-end integration tests covering health, registration, duplicate rejection, weak password rejection, authentication, token rotation, profile updates, RBAC enforcement, address management, and eager loading:

```bash
cd /Users/manojkumar/Desktop/FastAPI
.venv/bin/python services/user_service/verify_service.py
```

**Output:**
```
==================================================
Starting Enterprise User Service Verification Tests
==================================================

[TEST 1] Testing /health endpoint...
  ✓ Service status: healthy, DB: connected

[TEST 2] Testing User Registration...
  ✓ User registered successfully with UUID: ...

[TEST 3] Testing Duplicate Registration Error Handling (409 Conflict)...
  ✓ Duplicate registration correctly rejected with 409 ENTITY_ALREADY_EXISTS

[TEST 4] Testing Weak Password Validation (422 Unprocessable Entity)...
  ✓ Weak password correctly rejected with 422 VALIDATION_ERROR

[TEST 5] Testing User Authentication & JWT Issuance...
  ✓ Successfully received JWT Access and Refresh tokens

[TEST 6] Testing Token Refresh & Rotation...
  ✓ Refresh token successfully rotated and new access token issued

[TEST 7] Testing Get Profile (/api/v1/users/me)...
  ✓ Profile retrieved for user: Antigravity Engineer (Role: CUSTOMER)

[TEST 8] Testing RBAC Authorization Guard (Customer accessing Admin endpoint)...
  ✓ RBAC guard successfully blocked non-admin user with 403 FORBIDDEN

[TEST 9] Testing Address Creation (/api/v1/addresses/)...
  ✓ Address created with UUID: ...

[TEST 10] Testing Address Listing (/api/v1/addresses/)...
  ✓ User has saved address(es)

[TEST 11] Testing Profile with eager-loaded addresses (selectinload optimization)...
  ✓ Profile successfully returned with eager-loaded address(es)

==================================================
🎉 ALL 11 ENTERPRISE VERIFICATION TESTS PASSED! 🎉
==================================================
```
