from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

class LLMProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g. 'mock' or 'anthropic')."""
        pass

    @abstractmethod
    def analyze_bug(
        self,
        code_context: List[Dict[str, Any]],
        bug_description: str,
        repo_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze the bug description against code context.
        Must return structured dict containing:
        - severity: str ('low', 'medium', 'high', 'critical')
        - confidence: float (0.0 - 1.0)
        - suspected_root_cause: str
        - explanation: str
        - evidence: List[dict] (file, line range, snippet, observation)
        - affected_files: List[str]
        """
        pass

    @abstractmethod
    def generate_patch(
        self,
        finding: Dict[str, Any],
        code_context: List[Dict[str, Any]],
        custom_guidance: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a unified diff patch to fix the bug.
        Must return structured dict containing:
        - diff_content: str (valid unified diff)
        - affected_files: List[str]
        - rationale: str
        """
        pass

    @abstractmethod
    def generate_regression_test(
        self,
        finding: Dict[str, Any],
        patch: Dict[str, Any],
        code_context: List[Dict[str, Any]],
        target_framework: str = "pytest"
    ) -> Dict[str, Any]:
        """
        Generate an executable regression test for the reported bug.
        Must return structured dict containing:
        - file_path: str (path where test should reside)
        - test_code: str (runnable test code)
        - test_framework: str
        - test_rationale: str
        - assertion_description: str
        """
        pass
