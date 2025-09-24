"""Domain exceptions for molecular analysis platform."""


class DomainException(Exception):
    """Base exception for domain layer errors."""

    pass


class DockingException(DomainException):
    """Base exception for docking-related errors."""

    pass


class DockingSubmissionError(DockingException):
    """Error during docking job submission."""

    pass


class DockingStatusError(DockingException):
    """Error checking docking job status."""

    pass


class DockingResultsError(DockingException):
    """Error retrieving docking results."""

    pass


class DockingCancellationError(DockingException):
    """Error canceling docking job."""

    pass


class JobNotCompleteError(DockingException):
    """Job is not yet complete when results are requested."""

    pass


class MolecularPreparationException(DomainException):
    """Base exception for molecular preparation errors."""

    pass


class DrugNameResolutionError(MolecularPreparationException):
    """Error resolving drug name to SMILES."""

    pass


class SMILESConversionError(MolecularPreparationException):
    """Error converting SMILES to 3D structure."""

    pass


class FormatConversionError(MolecularPreparationException):
    """Error converting between molecular formats."""

    pass


class GeometryOptimizationError(MolecularPreparationException):
    """Error during molecular geometry optimization."""

    pass


class StructureValidationError(MolecularPreparationException):
    """Error during molecular structure validation."""

    pass


class LigandPreparationError(MolecularPreparationException):
    """Error in ligand preparation pipeline."""

    pass


class ExternalServiceException(DomainException):
    """Base exception for external service errors."""

    pass


class AuthenticationError(ExternalServiceException):
    """Error authenticating with external service."""

    pass


class ServiceDiscoveryError(ExternalServiceException):
    """Error discovering available services."""

    pass


class JobSubmissionError(ExternalServiceException):
    """Error submitting job to external service."""

    pass


class StatusCheckError(ExternalServiceException):
    """Error checking job status on external service."""

    pass


class FileListingError(ExternalServiceException):
    """Error listing files from external service."""

    pass


class FileDownloadError(ExternalServiceException):
    """Error downloading file from external service."""

    pass


class JobListingError(ExternalServiceException):
    """Error listing jobs from external service."""

    pass


class JobUpdateError(ExternalServiceException):
    """Error updating job on external service."""

    pass


class JobSharingError(ExternalServiceException):
    """Error with job sharing functionality."""

    pass
