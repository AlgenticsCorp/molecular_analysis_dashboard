"""Molecule domain entity for molecular analysis."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID


@dataclass
class Molecule:
    """Domain entity representing a molecular structure."""

    molecule_id: UUID
    org_id: UUID
    name: str
    format: str
    uri: str
    uploaded_by: UUID
    visibility: str
    created_at: datetime
    checksum: Optional[str] = None
    size_bytes: Optional[int] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    def add_tag(self, tag: str) -> None:
        """Add a tag to the molecule."""
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the molecule."""
        if tag in self.tags:
            self.tags.remove(tag)

    def set_property(self, key: str, value: Any) -> None:
        """Set a molecule property."""
        self.properties[key] = value

    def get_property(self, key: str, default: Any = None) -> Any:
        """Get a molecule property."""
        return self.properties.get(key, default)

    def is_public(self) -> bool:
        """Check if molecule is publicly visible."""
        return self.visibility == "public"

    def is_org_visible(self) -> bool:
        """Check if molecule is visible within organization."""
        return self.visibility in ["org", "public"]

    def is_accessible_by_user(self, user_id: UUID, user_org_id: UUID) -> bool:
        """
        Check if molecule is accessible by a specific user.

        Args:
            user_id: ID of the user requesting access
            user_org_id: Organization ID of the user

        Returns:
            True if user can access the molecule
        """
        # Owner can always access
        if user_id == self.uploaded_by:
            return True

        # Public molecules are accessible to all
        if self.visibility == "public":
            return True

        # Organization molecules are accessible to org members
        if self.visibility == "org" and user_org_id == self.org_id:
            return True

        # Private molecules only accessible to owner
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert molecule entity to dictionary."""
        return {
            "molecule_id": str(self.molecule_id),
            "org_id": str(self.org_id),
            "name": self.name,
            "format": self.format,
            "uri": self.uri,
            "checksum": self.checksum,
            "size_bytes": self.size_bytes,
            "properties": self.properties,
            "tags": self.tags,
            "uploaded_by": str(self.uploaded_by),
            "visibility": self.visibility,
            "created_at": self.created_at.isoformat(),
        }
