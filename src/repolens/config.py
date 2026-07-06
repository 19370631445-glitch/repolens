"""Configuration models for RepoLens."""

from pathlib import Path

from pydantic import BaseModel, Field, SecretStr


class RepoLensConfig(BaseModel):
    """Validated settings shared by the future analysis pipeline."""

    output_path: Path = Path("PROJECT_MAP.md")
    model_name: str = "not-configured"
    max_files: int = Field(default=200, ge=1)
    openai_api_key: SecretStr | None = Field(default=None, repr=False)


def load_config() -> RepoLensConfig:
    """Return default placeholder configuration.

    Environment and CLI option loading will be added in a later milestone.
    """
    return RepoLensConfig()

