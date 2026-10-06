from abc import ABC, abstractmethod

class Engine(ABC):
    @abstractmethod
    def update(self, state: dict, event: dict) -> dict:
        """Return updated structured state for an event."""
        raise NotImplementedError
