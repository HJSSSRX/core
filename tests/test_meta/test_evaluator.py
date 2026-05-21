from forhacker.meta.evaluator import Evaluator, Proposal


def test_evaluator_scores_relevance():
    evaluator = Evaluator(relevance_threshold=0.5, quality_threshold=0.5)
    proposal = Proposal(
        title="New volatility plugin",
        what="Add volatility3 integration",
        why="Memory forensics is core",
        impact="plugin-forensics",
        risk="LOW",
        requires_coordination=False,
        relevance_score=0.9,
        quality_score=0.8,
    )
    assert evaluator.passes(proposal) is True


def test_evaluator_rejects_below_threshold():
    evaluator = Evaluator(relevance_threshold=0.9, quality_threshold=0.9)
    proposal = Proposal(
        title="Irrelevant idea",
        what="Something unrelated",
        why="No reason",
        impact="none",
        risk="LOW",
        requires_coordination=False,
        relevance_score=0.1,
        quality_score=0.1,
    )
    assert evaluator.passes(proposal) is False


def test_evaluator_watchdog_counts_zero_days():
    evaluator = Evaluator(relevance_threshold=0.5, quality_threshold=0.5)
    # Simulate 7 days with zero passing proposals but M>0 candidates
    for _ in range(7):
        evaluator.record_day(candidates=5, passed=0)
    assert evaluator.should_alert() is True
