"""Integration test: PCO teaches an actor to compute a target function.

Actor starts with identity (f(x) = x).
Target: f(x) = 2*x if odd, x-1 if even.
Learner fixes one case per epoch (odd first, then even).
After 2 epochs, actor should produce correct outputs for all inputs.
"""

import asyncio

import pytest

from coglet import Coglet, CogletConfig, CogletRuntime, enact, listen
from coglet.pco.constraint import ConstraintCoglet
from coglet.pco.learner import LearnerCoglet
from coglet.pco.loss import LossCoglet
from coglet.pco.optimizer import ProximalCogletOptimizer


def target_fn(x: int) -> int:
    return 2 * x if x % 2 == 1 else x - 1


# ── Actor ───────────────────────────────────��──────────────

class MathActor(Coglet):
    """Actor with a replaceable function. Starts as identity."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fn = lambda x: x

    @enact("run")
    async def run_rollout(self, data):
        inputs = list(range(1, 11))
        results = [{"input": x, "output": self.fn(x), "expected": target_fn(x)} for x in inputs]
        await self.transmit("experience", {"results": results})

    @enact("update")
    async def apply_update(self, patch):
        self.fn = patch["fn"]


# ── Critic ─────────────────────────────────────────────────

class MathCritic(Coglet):
    @listen("experience")
    async def evaluate(self, experience):
        errors = [r for r in experience["results"] if r["output"] != r["expected"]]
        await self.transmit("evaluation", {
            "errors": errors,
            "correct": len(experience["results"]) - len(errors),
            "total": len(experience["results"]),
        })

    @enact("update")
    async def apply_update(self, patch):
        pass


# ── Loss ───────────────────────────────────────────────────

class ErrorCountLoss(LossCoglet):
    async def compute_loss(self, experience, evaluation):
        return {
            "name": "error_count",
            "magnitude": len(evaluation["errors"]),
            "errors": evaluation["errors"],
        }


# ── Learner ────────────────────────────────────────────────

class IncrementalLearner(LearnerCoglet):
    """Learns one pattern per epoch from experience.

    Looks at the evaluation errors directly. Fixes one case per epoch:
    Epoch 1: sees odd errors, learns the odd rule (multiply by 2).
    Epoch 2: sees even errors, learns the even rule (subtract 1).
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._odd_rule: float | None = None
        self._even_rule: float | None = None

    async def learn(self, experience, evaluation, signals):
        errors = evaluation.get("errors", [])

        odd_errors = [e for e in errors if e["input"] % 2 == 1]
        even_errors = [e for e in errors if e["input"] % 2 == 0]

        # Learn one new rule per call
        if odd_errors and self._odd_rule is None:
            e = odd_errors[0]
            self._odd_rule = e["expected"] / e["input"]
        elif even_errors and self._even_rule is None:
            e = even_errors[0]
            self._even_rule = e["expected"] - e["input"]

        odd_mult = self._odd_rule or 1
        even_offset = self._even_rule or 0

        def fn(x: int, _om=odd_mult, _eo=even_offset) -> int:
            if x % 2 == 1:
                return int(x * _om)
            return int(x + _eo)

        return {"fn": fn}


# ── Constraint ─────────────────────────────────────────────

class AlwaysAccept(ConstraintCoglet):
    async def check(self, patch):
        return {"accepted": True}


# ── Test ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pco_teaches_actor_target_function():
    runtime = CogletRuntime()
    pco_handle = await runtime.spawn(CogletConfig(
        cls=ProximalCogletOptimizer,
        kwargs=dict(
            actor_config=CogletConfig(cls=MathActor),
            critic_config=CogletConfig(cls=MathCritic),
            losses=[ErrorCountLoss()],
            constraints=[AlwaysAccept()],
            learner=IncrementalLearner(),
        ),
    ))
    pco = pco_handle.coglet
    actor = pco._actor_handle.coglet

    # Epoch 0: actor is identity, should have errors
    assert actor.fn(3) == 3  # identity
    assert actor.fn(4) == 4  # identity

    # Run 3 epochs (need 2 to learn both rules, 3rd confirms convergence)
    results = await pco.run(num_epochs=3)

    # Epoch 1 should have fixed odd inputs
    assert results[0]["accepted"] is True
    assert results[0]["signals"][0]["magnitude"] > 0  # had errors

    # After all epochs, actor should implement the target function
    for x in range(1, 11):
        assert actor.fn(x) == target_fn(x), f"actor.fn({x}) = {actor.fn(x)}, expected {target_fn(x)}"

    # Final epoch should have 0 errors
    assert results[2]["signals"][0]["magnitude"] == 0

    await runtime.shutdown()


@pytest.mark.asyncio
async def test_pco_epoch_results_show_convergence():
    """Verify error count decreases across epochs."""
    runtime = CogletRuntime()
    pco_handle = await runtime.spawn(CogletConfig(
        cls=ProximalCogletOptimizer,
        kwargs=dict(
            actor_config=CogletConfig(cls=MathActor),
            critic_config=CogletConfig(cls=MathCritic),
            losses=[ErrorCountLoss()],
            constraints=[AlwaysAccept()],
            learner=IncrementalLearner(),
        ),
    ))
    pco = pco_handle.coglet

    results = await pco.run(num_epochs=3)
    error_counts = [r["signals"][0]["magnitude"] for r in results]

    # Errors should strictly decrease: 10 (all wrong) → 5 (evens wrong) → 0
    assert error_counts[0] == 10  # identity gets nothing right
    assert error_counts[1] == 5   # odds fixed, evens still wrong
    assert error_counts[2] == 0   # all correct

    await runtime.shutdown()
