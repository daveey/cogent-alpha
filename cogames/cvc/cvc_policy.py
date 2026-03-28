"""CvC PolicyCoglet: CodeLet with LLM brain + Python fast policy.

Submitted to cogames as a MultiAgentPolicy. Each episode:
1. Python heuristic (CogletAgentPolicy) handles every step — fast path
2. LLM brain analyzes game state ~20 times per episode — slow path
3. On episode end, writes learnings/experience to disk for Coach to read

Coach (Claude Code) reads learnings across games and commits improvements.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from cvc.policy.anthropic_pilot import CogletBasePolicy, CogletAgentPolicy
from cvc.policy.semantic_cog import SharedWorldModel
from mettagrid.policy.policy import AgentPolicy
from mettagrid.policy.policy_env_interface import PolicyEnvInterface

_ELEMENTS = ("carbon", "oxygen", "germanium", "silicon")
_LLM_INTERVAL = 500  # call LLM every N steps (10000/500 = 20 per episode)
_LEARNINGS_DIR = os.environ.get("COGLET_LEARNINGS_DIR", "/tmp/coglet_learnings")


def _build_game_summary(agents: dict[int, CogletAgentPolicy]) -> dict[str, Any]:
    """Collect end-of-game summary from all agents."""
    summary: dict[str, Any] = {"agents": {}}
    for aid, agent in agents.items():
        agent_info: dict[str, Any] = {
            "steps": agent._step_index,
        }
        if agent._infos:
            agent_info["last_infos"] = dict(agent._infos)
        summary["agents"][aid] = agent_info
    return summary


class CogletPolicy(CogletBasePolicy):
    """PolicyCoglet: Python heuristic + LLM brain.

    Fast path: CogletAgentPolicy handles every step.
    Slow path: LLM guides strategy ~20 times per episode.
    End: writes learnings for Coach.
    """
    short_names = ["coglet", "coglet-policy"]
    minimum_action_timeout_ms = 30_000

    def __init__(self, policy_env_info: PolicyEnvInterface, device: str = "cpu", **kwargs: Any):
        super().__init__(policy_env_info, device=device, **kwargs)
        self._llm_client = None
        self._llm_log: list[dict[str, Any]] = []
        self._shared_directive: dict[str, Any] = {}
        self._episode_start = time.time()
        self._game_id = kwargs.get("game_id", f"game_{int(time.time())}")
        self._init_llm()

    def _init_llm(self) -> None:
        """Initialize Anthropic client if API key is available."""
        api_key = os.environ.get("COGORA_ANTHROPIC_KEY") or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return
        try:
            import anthropic
            self._llm_client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            pass

    def agent_policy(self, agent_id: int) -> AgentPolicy:
        if agent_id not in self._agent_policies:
            self._agent_policies[agent_id] = CogletBrainAgentPolicy(
                self.policy_env_info,
                agent_id=agent_id,
                world_model=SharedWorldModel(),
                shared_claims=self._shared_claims,
                shared_junctions=self._shared_junctions,
                llm_client=self._llm_client,
                llm_log=self._llm_log,
                shared_directive=self._shared_directive,
            )
        return self._agent_policies[agent_id]

    def reset(self) -> None:
        # Write learnings before reset (end of episode)
        if self._agent_policies:
            self._write_learnings()
        self._llm_log.clear()
        self._shared_directive.clear()
        self._episode_start = time.time()
        super().reset()

    def _write_learnings(self) -> None:
        """Write episode learnings/experience to disk for Coach."""
        learnings_dir = Path(_LEARNINGS_DIR)
        learnings_dir.mkdir(parents=True, exist_ok=True)

        game_summary = _build_game_summary(self._agent_policies)
        learnings = {
            "game_id": self._game_id,
            "duration_s": round(time.time() - self._episode_start, 1),
            "summary": game_summary,
            "llm_log": self._llm_log,
        }

        path = learnings_dir / f"{self._game_id}.json"
        path.write_text(json.dumps(learnings, indent=2, default=str))


class CogletBrainAgentPolicy(CogletAgentPolicy):
    """Agent policy with LLM brain that guides strategy mid-game.

    Every _LLM_INTERVAL steps, calls Claude to analyze game state and
    produce a MacroDirective that steers all agents' strategy.
    """

    def __init__(
        self,
        policy_env_info: PolicyEnvInterface,
        *,
        agent_id: int,
        world_model: SharedWorldModel,
        shared_claims: dict,
        shared_junctions: dict,
        llm_client: Any = None,
        llm_log: list | None = None,
        shared_directive: dict | None = None,
    ) -> None:
        super().__init__(
            policy_env_info,
            agent_id=agent_id,
            world_model=world_model,
            shared_claims=shared_claims,
            shared_junctions=shared_junctions,
        )
        self._llm = llm_client
        self._llm_log = llm_log if llm_log is not None else []
        self._last_llm_step = 0
        self._llm_interval = _LLM_INTERVAL
        self._llm_latencies: list[float] = []
        self._shared_directive = shared_directive if shared_directive is not None else {}

    def _macro_directive(self, state: Any) -> Any:
        """Return LLM-guided directive if available, else default."""
        from mettagrid_sdk.sdk import MacroDirective
        d = self._shared_directive
        if d and d.get("resource_bias"):
            return MacroDirective(resource_bias=d["resource_bias"])
        return super()._macro_directive(state)

    def step(self, obs: Any) -> Any:
        action = super().step(obs)

        # LLM brain: analyze adaptively (agent 0 only to avoid redundancy)
        if (
            self._llm is not None
            and self._agent_id == 0
            and self._step_index - self._last_llm_step >= self._llm_interval
        ):
            self._last_llm_step = self._step_index
            self._llm_analyze()
            self._adapt_interval()

        return action

    def _llm_analyze(self) -> None:
        """Call Claude to analyze game state and produce a strategy directive."""
        try:
            state = self._previous_state
            if state is None:
                return

            inv = state.self_state.inventory
            team = state.team_summary
            resources = {}
            if team:
                resources = {r: int(team.shared_inventory.get(r, 0)) for r in _ELEMENTS}

            lines = [
                f"CvC game step {self._step_index}/10000. 88x88 map, 8 agents vs clips.",
                f"HP: {inv.get('hp', 0)}, Hearts: {inv.get('heart', 0)}",
                f"Gear: aligner={inv.get('aligner', 0)} scrambler={inv.get('scrambler', 0)} miner={inv.get('miner', 0)}",
                f"Hub resources: {resources}",
            ]
            if team:
                roles: dict[str, int] = {}
                for m in team.members:
                    roles[m.role] = roles.get(m.role, 0) + 1
                lines.append(f"Team roles: {roles}")

            # Get junction count
            friendly_j = len([e for e in state.visible_entities if e.entity_type == "junction" and e.attributes.get("owner") == (team.team_id if team else "")])
            enemy_j = len([e for e in state.visible_entities if e.entity_type == "junction" and e.attributes.get("owner") not in {None, "neutral", (team.team_id if team else "")}])
            neutral_j = len([e for e in state.visible_entities if e.entity_type == "junction" and e.attributes.get("owner") in {None, "neutral"}])
            lines.append(f"Visible junctions: friendly={friendly_j} enemy={enemy_j} neutral={neutral_j}")

            lines.append(
                "\nRespond with ONLY a JSON object (no other text):"
                '\n{"resource_bias": "carbon"|"oxygen"|"germanium"|"silicon",'
                ' "analysis": "1-2 sentence analysis"}'
                "\nChoose resource_bias = the element with lowest supply."
            )

            t0 = time.perf_counter()
            response = self._llm.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=150,
                temperature=0.2,
                messages=[{"role": "user", "content": "\n".join(lines)}],
            )
            latency_ms = (time.perf_counter() - t0) * 1000

            text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    text = block.text
                    break

            # Parse JSON directive
            import json as _json
            try:
                directive = _json.loads(text)
                if isinstance(directive, dict):
                    if directive.get("resource_bias") in _ELEMENTS:
                        self._shared_directive["resource_bias"] = directive["resource_bias"]
                    analysis = directive.get("analysis", text[:100])
                else:
                    analysis = text[:100]
            except (_json.JSONDecodeError, ValueError):
                analysis = text[:100]

            self._llm_latencies.append(latency_ms)
            entry = {
                "step": self._step_index,
                "latency_ms": round(latency_ms),
                "interval": self._llm_interval,
                "analysis": analysis,
                "resources": resources,
                "directive": dict(self._shared_directive),
            }
            self._llm_log.append(entry)
            print(
                f"[coglet] step={self._step_index} llm={latency_ms:.0f}ms "
                f"interval={self._llm_interval}: {analysis[:100]}",
                flush=True,
            )

        except Exception as e:
            self._llm_log.append({
                "step": self._step_index,
                "error": str(e),
            })

    def _adapt_interval(self) -> None:
        """Adjust LLM call frequency based on measured latency."""
        if not self._llm_latencies:
            return
        avg_ms = sum(self._llm_latencies[-5:]) / min(len(self._llm_latencies), 5)
        if avg_ms < 2000:
            self._llm_interval = max(200, self._llm_interval - 50)
        elif avg_ms > 5000:
            self._llm_interval = min(1000, self._llm_interval + 100)
