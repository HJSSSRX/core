"""Unified exception hierarchy for ForHacker.

All domain exceptions inherit from ForHackerError, enabling the CLI to
catch and format them consistently while letting unexpected errors propagate.
"""


class ForHackerError(Exception):
    """Base exception for all ForHacker domain errors."""


class PluginLoadError(ForHackerError):
    """Plugin discovery or loading failed."""


class TaskExecutionError(ForHackerError):
    """A task failed during execution."""


class ConfigError(ForHackerError):
    """Configuration is missing or invalid."""


class EvidenceIntegrityError(ForHackerError):
    """Evidence hash verification failed."""
