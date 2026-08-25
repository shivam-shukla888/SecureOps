from abc import ABC, abstractmethod
from app.schemas.decision import ClassifierResult


class BaseAIProvider(ABC):
    @abstractmethod
    async def classify_request(self, user_request: str) -> ClassifierResult:
        """
        Classifies a user request into intent, resource, risk, and approval requirements.
        Must raise an Exception if classification fails.
        """
        pass
