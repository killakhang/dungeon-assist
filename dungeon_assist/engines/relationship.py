from .base import Engine

class RelationshipEngine(Engine):
    METRICS = ("affinity", "trust", "fear", "resentment")

    def update(self, state: dict, event: dict) -> dict:
        rel = state.setdefault("relationship", {})
        for metric in self.METRICS:
            delta = int(event.get(metric, 0))
            rel[metric] = max(-100, min(100, int(rel.get(metric, 0)) + delta))
        return state
