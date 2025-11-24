"""
Custom exceptions for the application.
"""


class ComplianceEngineException(Exception):
    """Base exception for compliance engine."""

    pass


class GitHubAuthError(ComplianceEngineException):
    """GitHub authentication error."""

    pass


class WebhookVerificationError(ComplianceEngineException):
    """Webhook signature verification error."""

    pass


class EmbeddingProviderError(ComplianceEngineException):
    """Embeddings provider error."""

    pass


class LLMProviderError(ComplianceEngineException):
    """LLM provider error."""

    pass


class CodeParsingError(ComplianceEngineException):
    """Code parsing error."""

    pass


class StorageError(ComplianceEngineException):
    """Storage operation error."""

    pass


class RepositoryCloneError(ComplianceEngineException):
    """Repository cloning error."""

    pass


class JobExecutionError(ComplianceEngineException):
    """Job execution error."""

    pass
