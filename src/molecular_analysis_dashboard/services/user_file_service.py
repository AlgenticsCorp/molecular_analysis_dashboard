"""Service for managing standalone user file uploads used by the file manager."""

from __future__ import annotations

import hashlib
import logging
import math
import mimetypes
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional
from uuid import UUID, uuid4

import aiofiles
from fastapi import UploadFile
from sqlalchemy import String, bindparam, text
from sqlalchemy.dialects.postgresql import ARRAY

from ..infrastructure.database import db_manager
from .file_validators import FileValidationError, validate_file

logger = logging.getLogger(__name__)


class UserFileService:
    """Provides CRUD operations for standalone user uploads."""

    SUPPORTED_FORMATS: Dict[str, str] = {
        ".pdb": "pdb",
        ".pdbqt": "pdbqt",
        ".sdf": "sdf",
        ".mol2": "mol2",
        ".mol": "mol2",
        ".xyz": "xyz",
    }

    ALLOWED_CATEGORIES: Iterable[str] = (
        "molecular_structure",
        "docking_result",
        "analysis_output",
        "protein_structure",
        "ligand_structure",
        "trajectory",
        "simulation",
        "other",
    )

    MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB hard limit
    DEFAULT_CATEGORY = "molecular_structure"
    DEFAULT_PARAMETER_NAME = "user_upload"
    DEFAULT_FILE_TYPE = "input"  # constrained by execution_files table

    def __init__(
        self,
        *,
        storage_backend: Optional[str] = None,
        storage_root: Optional[str] = None,
        storage_base_url: Optional[str] = None,
    ) -> None:
        self.storage_backend = storage_backend or os.getenv("STORAGE_BACKEND", "local")
        self.storage_root = Path(storage_root or os.getenv("FILE_MANAGER_STORAGE_ROOT", "/storage"))
        self.storage_base_url = storage_base_url or os.getenv("STORAGE_BASE_URL", "http://storage:8080")
        self._session_factory = db_manager.metadata_session_factory

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def upload_file(
        self,
        *,
        file: UploadFile,
        user_id: Optional[UUID],
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[Iterable[str]] = None,
        category: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Validate, persist, and register a molecular structure file."""
        if user_id is None:
            raise ValueError("User ID is required for standalone file uploads")

        file_bytes = await file.read()
        if not file_bytes:
            raise ValueError("Uploaded file is empty")

        if len(file_bytes) > self.MAX_FILE_SIZE_BYTES:
            raise ValueError("File exceeds maximum allowed size of 100MB")

        extension = Path(file.filename or "").suffix.lower()
        file_format = self._resolve_format(extension)

        try:
            validation = validate_file(file_bytes, file_format)
        except FileValidationError as exc:
            raise ValueError(str(exc)) from exc

        if not validation.get("is_valid", False):
            errors = validation.get("errors", [])
            if errors:
                raise ValueError("; ".join(errors))
            raise ValueError("File validation failed")

        display_filename = self._determine_display_name(name, extension)
        content_type = self._determine_content_type(file.content_type, extension)

        file_id = uuid4()
        storage_path = self._build_storage_path(user_id, file_id, extension)

        await self._store_file(file_bytes, storage_path)

        md5_hash = hashlib.md5(file_bytes).hexdigest()
        sha256_hash = hashlib.sha256(file_bytes).hexdigest()

        normalized_tags = self._normalize_tags(tags)
        normalized_category = self._normalize_category(category)

        async with self._session_factory() as session:
            insert_sql = text(
                """
                INSERT INTO execution_files (
                    file_id,
                    execution_id,
                    parameter_name,
                    file_type,
                    filename,
                    size_bytes,
                    content_type,
                    storage_backend,
                    storage_path,
                    download_url,
                    md5_hash,
                    sha256_hash,
                    user_id,
                    file_category,
                    description,
                    tags,
                    is_public,
                    created_by
                )
                VALUES (
                    :file_id,
                    NULL,
                    :parameter_name,
                    :file_type,
                    :filename,
                    :size_bytes,
                    :content_type,
                    :storage_backend,
                    :storage_path,
                    NULL,
                    :md5_hash,
                    :sha256_hash,
                    :user_id,
                    :file_category,
                    :description,
                    :tags,
                    FALSE,
                    :created_by
                )
                RETURNING
                    file_id,
                    filename,
                    size_bytes,
                    content_type,
                    storage_backend,
                    storage_path,
                    md5_hash,
                    sha256_hash,
                    uploaded_at,
                    description,
                    tags,
                    file_category,
                    is_public,
                    created_by,
                    user_id
                """
            )

            params = {
                "file_id": str(file_id),
                "parameter_name": self.DEFAULT_PARAMETER_NAME,
                "file_type": self.DEFAULT_FILE_TYPE,
                "filename": display_filename,
                "size_bytes": len(file_bytes),
                "content_type": content_type,
                "storage_backend": self.storage_backend,
                "storage_path": storage_path,
                "md5_hash": md5_hash,
                "sha256_hash": sha256_hash,
                "user_id": str(user_id),
                "file_category": normalized_category,
                "description": description,
                "tags": normalized_tags,
                "created_by": created_by,
            }

            try:
                result = await session.execute(insert_sql, params)
                await session.commit()
            except Exception as exc:
                await session.rollback()
                logger.exception("Failed to persist file metadata", exc_info=exc)
                # Best effort cleanup of stored file if DB persistence fails
                self._safe_remove(storage_path)
                raise

        record = result.mappings().one()
        return self._serialize_record(record, validation_data=validation, original_filename=file.filename, file_format=file_format)

    async def list_files(
        self,
        *,
        user_id: Optional[UUID] = None,
        file_format: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        tags: Optional[Iterable[str]] = None,
        sort_by: str = "uploaded_at",
        order: str = "desc",
        page: int = 1,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Return a paginated list of standalone files respecting filters."""
        page = max(page, 1)
        limit = max(1, min(limit, 200))

        sort_column = self._resolve_sort_column(sort_by)
        sort_order = "DESC" if order.lower() == "desc" else "ASC"

        filters = ["execution_id IS NULL"]
        params: Dict[str, Any] = {}

        if user_id is not None:
            filters.append("user_id = :user_id")
            params["user_id"] = str(user_id)

        if file_format:
            canonical_format = self._resolve_format(f".{file_format.lower().lstrip('.')}")
            filters.append("LOWER(filename) LIKE :format_pattern")
            params["format_pattern"] = f"%.{canonical_format}"
            if canonical_format == "mol2":
                # Support both .mol and .mol2 extensions
                filters[-1] = "(LOWER(filename) LIKE :format_pattern OR LOWER(filename) LIKE :alt_format_pattern)"
                params["format_pattern"] = "%.mol2"
                params["alt_format_pattern"] = "%.mol"

        if category:
            normalized_category = self._normalize_category(category)
            filters.append("file_category = :file_category")
            params["file_category"] = normalized_category

        if search:
            filters.append("(LOWER(filename) LIKE :search OR LOWER(description) LIKE :search)")
            params["search"] = f"%{search.lower()}%"

        tag_list = self._normalize_tags(tags)
        tag_bind = None
        if tag_list:
            filters.append("tags @> :tags")
            tag_bind = bindparam("tags", type_=ARRAY(String()))
            params["tags"] = tag_list

        where_clause = " AND ".join(filters)
        offset = (page - 1) * limit

        base_select = f"""
            SELECT
                file_id,
                filename,
                size_bytes,
                content_type,
                storage_backend,
                storage_path,
                md5_hash,
                sha256_hash,
                uploaded_at,
                description,
                tags,
                file_category,
                is_public,
                created_by,
                user_id
            FROM execution_files
            WHERE {where_clause}
            ORDER BY {sort_column} {sort_order}
            LIMIT :limit OFFSET :offset
        """

        select_clause = text(base_select)
        if tag_bind is not None:
            select_clause = select_clause.bindparams(tag_bind)

        params["limit"] = limit
        params["offset"] = offset

        count_sql = text(f"SELECT COUNT(*) AS total FROM execution_files WHERE {where_clause}")
        if tag_bind is not None:
            count_sql = count_sql.bindparams(tag_bind)

        async with self._session_factory() as session:
            result = await session.execute(select_clause, params)
            rows = result.mappings().all()

            count_result = await session.execute(count_sql, params)
            total = count_result.scalar_one()

        files = [self._serialize_record(row) for row in rows]
        total_pages = math.ceil(total / limit) if total else 1

        return {
            "total_files": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "files": files,
        }

    async def get_storage_stats(self, user_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Aggregate storage usage statistics for standalone files."""
        filters = ["execution_id IS NULL"]
        params: Dict[str, Any] = {}

        if user_id is not None:
            filters.append("user_id = :user_id")
            params["user_id"] = str(user_id)

        where_clause = " AND ".join(filters)

        summary_sql = text(
            f"""
            SELECT
                COUNT(*) AS total_files,
                COALESCE(SUM(size_bytes), 0) AS total_size_bytes
            FROM execution_files
            WHERE {where_clause}
        """
        )

        format_sql = text(
            f"""
            SELECT
                format,
                COUNT(*) AS file_count,
                COALESCE(SUM(size_bytes), 0) AS total_size
            FROM (
                SELECT
                    CASE
                        WHEN LOWER(filename) LIKE '%.pdb' THEN 'pdb'
                        WHEN LOWER(filename) LIKE '%.pdbqt' THEN 'pdbqt'
                        WHEN LOWER(filename) LIKE '%.sdf' THEN 'sdf'
                        WHEN LOWER(filename) LIKE '%.mol2' THEN 'mol2'
                        WHEN LOWER(filename) LIKE '%.mol' THEN 'mol2'
                        WHEN LOWER(filename) LIKE '%.xyz' THEN 'xyz'
                        ELSE 'other'
                    END AS format,
                    size_bytes
                FROM execution_files
                WHERE {where_clause}
            ) AS format_data
            GROUP BY format
        """
        )

        category_sql = text(
            f"""
            SELECT
                file_category,
                COUNT(*) AS file_count,
                COALESCE(SUM(size_bytes), 0) AS total_size
            FROM execution_files
            WHERE {where_clause}
            GROUP BY file_category
        """
        )

        async with self._session_factory() as session:
            summary_result = await session.execute(summary_sql, params)
            total_files, total_size = summary_result.one()

            format_result = await session.execute(format_sql, params)
            format_rows = format_result.all()

            category_result = await session.execute(category_sql, params)
            category_rows = category_result.all()

        total_files = self._ensure_int(total_files)
        total_size = self._ensure_int(total_size)

        files_by_format = {row[0]: self._ensure_int(row[1]) for row in format_rows}
        storage_by_format = {row[0]: self._ensure_int(row[2]) for row in format_rows}
        by_category = {
            row[0]: {
                "file_count": self._ensure_int(row[1]),
                "total_size_bytes": self._ensure_int(row[2]),
            }
            for row in category_rows
        }

        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "files_by_format": files_by_format,
            "storage_by_format": storage_by_format,
            "files_by_category": by_category,
        }

    async def get_file_metadata(self, file_id: UUID, user_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Fetch metadata for a standalone file and ensure caller access."""
        async with self._session_factory() as session:
            record = await self._fetch_record(session, file_id)

        self._enforce_access(record, user_id)
        return self._serialize_record(record)

    async def update_file_metadata(
        self,
        *,
        file_id: UUID,
        user_id: Optional[UUID] = None,
        filename: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[Iterable[str]] = None,
        category: Optional[str] = None,
        is_public: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Update mutable metadata attributes for a standalone file."""
        updates: List[str] = []
        params: Dict[str, Any] = {"file_id": str(file_id)}

        if filename is not None:
            new_name = filename.strip()
            if not new_name:
                raise ValueError("Filename cannot be empty")
            updates.append("filename = :filename")
            params["filename"] = new_name

        if description is not None:
            updates.append("description = :description")
            params["description"] = description

        if tags is not None:
            normalized_tags = self._normalize_tags(tags) or []
            updates.append("tags = :tags")
            params["tags"] = normalized_tags

        if category:
            updates.append("file_category = :file_category")
            params["file_category"] = self._normalize_category(category)

        if is_public is not None:
            updates.append("is_public = :is_public")
            params["is_public"] = bool(is_public)

        if not updates:
            raise ValueError("No metadata fields provided for update")

        update_sql = text(
            f"""
            UPDATE execution_files
            SET {', '.join(updates)}, updated_at = NOW()
            WHERE file_id = :file_id AND execution_id IS NULL
            RETURNING file_id,
                      filename,
                      size_bytes,
                      content_type,
                      storage_backend,
                      storage_path,
                      md5_hash,
                      sha256_hash,
                      uploaded_at,
                      description,
                      tags,
                      file_category,
                      is_public,
                      created_by,
                      user_id
        """
        )

        async with self._session_factory() as session:
            existing = await self._fetch_record(session, file_id)
            self._enforce_access(existing, user_id)

            try:
                result = await session.execute(update_sql, params)
                updated = result.mappings().first()
                if not updated:
                    await session.rollback()
                    raise ValueError("File not found")
                await session.commit()
            except Exception:
                await session.rollback()
                raise

        return self._serialize_record(updated)

    async def delete_file(self, file_id: UUID, user_id: Optional[UUID] = None) -> None:
        """Remove a standalone file and delete associated metadata."""
        async with self._session_factory() as session:
            record = await self._fetch_record(session, file_id)
            self._enforce_access(record, user_id)

            delete_sql = text(
                "DELETE FROM execution_files WHERE file_id = :file_id AND execution_id IS NULL"
            )

            await session.execute(delete_sql, {"file_id": str(file_id)})
            await session.commit()

        self._safe_remove(record["storage_path"])

    async def bulk_delete(self, file_ids: Iterable[UUID], user_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Delete multiple files, collecting per-file errors."""
        deleted = 0
        failed = 0
        errors: List[Dict[str, Any]] = []

        for file_id in file_ids:
            try:
                await self.delete_file(file_id, user_id=user_id)
                deleted += 1
            except Exception as exc:  # pragma: no cover - aggregated per design
                failed += 1
                errors.append({"file_id": str(file_id), "error": str(exc)})

        return {"deleted": deleted, "failed": failed, "errors": errors}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_format(self, extension: str) -> str:
        key = extension.lower().strip()
        if not key.startswith("."):
            key = f".{key}"
        if key not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported file format '{extension}'. "
                f"Supported formats: {', '.join(sorted(self.SUPPORTED_FORMATS.values()))}"
            )
        return self.SUPPORTED_FORMATS[key]

    def _resolve_sort_column(self, sort_by: str) -> str:
        mapping = {
            "uploaded_at": "uploaded_at",
            "filename": "LOWER(filename)",
            "name": "LOWER(filename)",
            "size": "size_bytes",
            "size_bytes": "size_bytes",
        }
        return mapping.get(sort_by.lower(), "uploaded_at")

    def _infer_format(self, filename: str) -> Optional[str]:
        extension = Path(filename).suffix.lower()
        return self.SUPPORTED_FORMATS.get(extension)

    def _determine_display_name(self, name: Optional[str], extension: str) -> str:
        base_name = (name or "").strip()
        if not base_name:
            return Path("uploaded").with_suffix(extension or ".dat").name
        if Path(base_name).suffix:
            return base_name
        return f"{base_name}{extension or ''}" if extension else base_name

    def _determine_content_type(self, provided: Optional[str], extension: str) -> str:
        if provided:
            return provided
        guess = mimetypes.guess_type(f"file{extension}")[0]
        return guess or "application/octet-stream"

    def _build_storage_path(self, user_id: UUID, file_id: UUID, extension: str) -> str:
        raw_ext = (extension or "").strip()
        if not raw_ext:
            safe_ext = ""
        elif raw_ext.startswith("."):
            safe_ext = raw_ext
        else:
            safe_ext = f".{raw_ext}"
        return f"/uploads/user/{user_id}/{file_id}{safe_ext}"

    async def _store_file(self, content: bytes, storage_path: str) -> None:
        if self.storage_backend != "local":
            raise RuntimeError("Only local storage backend is supported at this time")

        absolute_path = self.storage_root / storage_path.lstrip("/")
        absolute_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(absolute_path, "wb") as handle:
            await handle.write(content)

    def _safe_remove(self, storage_path: str) -> None:
        if self.storage_backend != "local":
            return
        absolute_path = self.storage_root / storage_path.lstrip("/")
        try:
            if absolute_path.exists():
                absolute_path.unlink()
        except Exception as exc:  # pragma: no cover - best effort cleanup
            logger.warning("Failed to remove file '%s': %s", absolute_path, exc)

    def _normalize_tags(self, tags: Optional[Iterable[str]]) -> Optional[List[str]]:
        if tags is None:
            return None
        normalized = [tag.strip() for tag in tags if tag and tag.strip()]
        return normalized if normalized else None

    def _ensure_int(self, value: Any) -> int:
        """Coerce database numeric types (including Decimal) into plain ints."""
        if value is None:
            return 0
        if isinstance(value, int):
            return value
        try:
            return int(value)
        except (TypeError, ValueError):
            logger.debug("Unable to coerce value '%s' to int; defaulting to 0", value)
            return 0

    def _normalize_category(self, category: Optional[str]) -> str:
        if not category:
            return self.DEFAULT_CATEGORY
        lowered = category.strip().lower()
        if lowered not in self.ALLOWED_CATEGORIES:
            raise ValueError(
                f"Invalid category '{category}'. Allowed values: {', '.join(self.ALLOWED_CATEGORIES)}"
            )
        return lowered

    def _serialize_record(
        self,
        record: Mapping[str, Any],
        *,
        validation_data: Optional[Dict[str, Any]] = None,
        original_filename: Optional[str] = None,
        file_format: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {
            "file_id": str(record["file_id"]),
            "filename": record.get("filename"),
            "size_bytes": record.get("size_bytes"),
            "content_type": record.get("content_type"),
            "storage_backend": record.get("storage_backend"),
            "storage_path": record.get("storage_path"),
            "md5_hash": record.get("md5_hash"),
            "sha256_hash": record.get("sha256_hash"),
            "uploaded_at": record.get("uploaded_at").isoformat() if record.get("uploaded_at") else None,
            "description": record.get("description"),
            "tags": record.get("tags") or [],
            "file_category": record.get("file_category"),
            "is_public": record.get("is_public", False),
            "created_by": record.get("created_by"),
            "user_id": str(record.get("user_id")) if record.get("user_id") else None,
            "download_url": self._build_download_url(record["file_id"]),
        }

        if original_filename:
            payload["original_filename"] = original_filename
        if file_format:
            payload["file_format"] = file_format
        elif payload.get("filename"):
            inferred = self._infer_format(payload["filename"])
            if inferred:
                payload["file_format"] = inferred
        if validation_data:
            payload["validation"] = validation_data

        return payload

    def _build_download_url(self, file_id: Any) -> str:
        return f"/api/v1/tasks-unified/files/{file_id}/download"

    async def _fetch_record(self, session, file_id: UUID) -> Mapping[str, Any]:
        query = text(
            """
            SELECT
                file_id,
                filename,
                size_bytes,
                content_type,
                storage_backend,
                storage_path,
                md5_hash,
                sha256_hash,
                uploaded_at,
                description,
                tags,
                file_category,
                is_public,
                created_by,
                user_id
            FROM execution_files
            WHERE file_id = :file_id AND execution_id IS NULL
        """
        )
        result = await session.execute(query, {"file_id": str(file_id)})
        record = result.mappings().first()
        if not record:
            raise ValueError("File not found")
        return record

    def _enforce_access(self, record: Mapping[str, Any], user_id: Optional[UUID]) -> None:
        owner = record.get("user_id")
        if owner and user_id and str(owner) != str(user_id):
            raise ValueError("Access denied for file")