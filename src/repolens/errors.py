"""Domain-specific exceptions used by RepoLens."""


class RepoLensError(Exception):
    """Base class for expected RepoLens errors."""


class ConfigurationError(RepoLensError):
    """Raised when required configuration is missing or invalid."""


class InvalidRepositoryUrlError(RepoLensError):
    """Raised when a repository URL is unsupported or invalid."""


class RepositoryCloneError(RepoLensError):
    """Raised when a repository cannot be cloned."""


class RepositoryScanError(RepoLensError):
    """Raised when repository files cannot be scanned safely."""


class LLMError(RepoLensError):
    """Raised when a future LLM request fails."""


class ReportGenerationError(RepoLensError):
    """Raised when PROJECT_MAP.md cannot be generated."""

