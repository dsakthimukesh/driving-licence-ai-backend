# End-to-End Request Flow Walkthrough

This document traces the complete lifecycle of HTTP requests across the layered architecture.

## Example 1: User Registration (`POST /api/v1/auth/register`)

```text
Client Request
      ↓
[Routes] auth_routes.register_user
      ↓ (Validates Pydantic schema & passes db session)
[Controllers] auth_controller.handle_register_user
      ↓ (Calls service function)
[Services] auth_service.register_user
      ↓ (Queries existing email & persists user)
[Repositories] user_repository.get_user_by_email & create_user
      ↓ (SQLAlchemy 2.x execution)
PostgreSQL Database (public.users)
```

1. **Route**: Receives `UserRegisterRequest` payload. Applies Pydantic validation.
2. **Controller**: Calls `auth_service.register_user`. Catches `UserAlreadyExistsError` and returns `HTTP 409 Conflict` if present.
3. **Service**: Normalizes email, calls `user_repository.get_user_by_email`. If clear, hashes password using Argon2id (`app/core/security.py`), constructs `User` model, and calls `user_repository.create_user`.
4. **Repository**: Executes `db.add(user)`, `db.commit()`, `db.refresh(user)`. Returns saved model.
5. **Response**: Controller maps output model into sanitized `UserRegisterResponse`.

---

## Example 2: Document Pre-signed Upload URL (`POST /api/v1/documents/upload-url`)

```text
Client Request
      ↓
[Routes] document_routes.generate_upload_url
      ↓ (Injects get_current_user & db session)
[Controllers] document_controller.handle_generate_upload_url
      ↓
[Services] document_service.initialize_upload
      ├──> [Repositories] document_repository.create_document (PENDING status)
      └──> [Storage Service] StorageService.create_signed_upload_url
            ↓
Pre-signed Upload URL returned to Client
```

1. Client receives temporary pre-signed URL from Supabase Storage.
2. Client uploads file bytes directly to Supabase Storage bucket without overloading FastAPI.
3. Client calls `POST /api/v1/documents/{document_id}/confirm-upload` to verify file existence.
