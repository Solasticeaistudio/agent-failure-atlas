from .approval import ApprovalBypassDetector
from .failure import SilentFailureDetector
from .injection import PromptInjectionDetector
from .repetition import RepeatedActionDetector
from .scope import ScopeViolationDetector
from .secrets import SecretExposureDetector

DEFAULT_DETECTORS = [
    ScopeViolationDetector(),
    ApprovalBypassDetector(),
    PromptInjectionDetector(),
    RepeatedActionDetector(),
    SilentFailureDetector(),
    SecretExposureDetector(),
]

__all__ = ["DEFAULT_DETECTORS"]
