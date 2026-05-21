from forhacker.meta.evaluator import Evaluator, Proposal
from forhacker.meta.sources import DEFAULT_SOURCES


class MetaAgent:
    def __init__(self):
        self.evaluator = Evaluator()
        self.sources = list(DEFAULT_SOURCES)
        self.proposals: list[Proposal] = []

    def add_source(self, name: str, url: str, category: str):
        from forhacker.meta.sources import Source
        self.sources.append(Source(name=name, url=url, category=category))

    def submit_proposal(self, proposal: Proposal) -> bool:
        self.proposals.append(proposal)
        return self.evaluator.passes(proposal)

    def list_pending(self) -> list[Proposal]:
        return [p for p in self.proposals if self.evaluator.passes(p)]
