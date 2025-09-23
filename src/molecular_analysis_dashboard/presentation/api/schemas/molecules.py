"""Pydantic schemas for molecule upload and storage API."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


class MoleculeUploadRequest(BaseModel):
    """Request schema for molecule upload."""

    name: str = Field(..., min_length=1, max_length=255, description="Molecule name")
    format: str = Field(..., description="File format (pdb, sdf, mol2, etc.)")
    properties: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional molecule properties"
    )
    tags: Optional[list[str]] = Field(default_factory=list, description="Molecule tags")
    visibility: str = Field(
        default="private", description="Visibility level (private, org, public)"
    )

    @validator("format")
    def validate_format(cls, v):
        """Validate molecule file format."""
        allowed_formats = {
            "pdb",
            "pdbqt",
            "sdf",
            "mol",
            "mol2",
            "xyz",
            "cif",
            "mmcif",
            "cml",
            "smiles",
        }
        if v.lower() not in allowed_formats:
            raise ValueError(f"Unsupported format: {v}. Allowed: {', '.join(allowed_formats)}")
        return v.lower()

    @validator("visibility")
    def validate_visibility(cls, v):
        """Validate visibility level."""
        allowed_visibility = {"private", "org", "public"}
        if v not in allowed_visibility:
            raise ValueError(f"Invalid visibility: {v}. Allowed: {', '.join(allowed_visibility)}")
        return v


class MoleculeUploadResponse(BaseModel):
    """Response schema for molecule upload."""

    molecule_id: UUID = Field(..., description="Unique molecule identifier")
    name: str = Field(..., description="Molecule name")
    format: str = Field(..., description="File format")
    uri: str = Field(..., description="Storage URI for the molecule file")
    size_bytes: Optional[int] = Field(None, description="File size in bytes")
    checksum: Optional[str] = Field(None, description="SHA256 checksum of file content")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Molecule properties")
    tags: list[str] = Field(default_factory=list, description="Molecule tags")
    visibility: str = Field(..., description="Visibility level")
    uploaded_by: UUID = Field(..., description="User who uploaded the molecule")
    created_at: datetime = Field(..., description="Upload timestamp")

    class Config:
        from_attributes = True


class StorageHealthResponse(BaseModel):
    """Response schema for storage service health check."""

    status: str = Field(..., description="Health status")
    service: str = Field(..., description="Service name")
    storage_root: str = Field(..., description="Storage root directory")
    available_space: Optional[int] = Field(None, description="Available storage space in bytes")


class FileInfoResponse(BaseModel):
    """Response schema for file information."""

    uri: str = Field(..., description="Storage URI")
    name: str = Field(..., description="File name")
    size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type")
    created_at: float = Field(..., description="Creation timestamp")
    modified_at: float = Field(..., description="Last modification timestamp")
    extension: str = Field(..., description="File extension")


class PresignedUrlResponse(BaseModel):
    """Response schema for presigned URL generation."""

    url: str = Field(..., description="Presigned URL for file access")
    expires_in: int = Field(..., description="URL expiration time in seconds")


class ErrorResponse(BaseModel):
    """Error response schema."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
