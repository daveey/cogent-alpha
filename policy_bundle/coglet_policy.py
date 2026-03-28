"""Coglet policy for cogames CvC.

All interactions via movement. Score = aligned junctions held per tick.
Pipeline: mine each resource type → hub (craft hearts) → get aligner gear → align junctions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mettagrid.policy.policy import MultiAgentPolicy, AgentPolicy  # type: ignore[import-untyped]
from mettagrid.policy.policy_env_interface import PolicyEnvInterface  # type: ignore[import-untyped]
from mettagrid.simulator import Action  # type: ignore[import-untyped]

ELEMENTS = ("carbon", "oxygen", "germanium", "silicon")
DIRECTIONS = ("east", "south", "west", "north")
EXTRACTOR_TAGS = [f"type:{e}_extractor" for e in ELEMENTS]


@dataclass
class AgentState:
    step: int = 0
    wander_dir: int = 0
    wander_count: int = 0
    prev_pos: tuple[int, int] | None = None
    stuck: int = 0


class CogletAgentPolicy(AgentPolicy):
    def __init__(self, env: PolicyEnvInterface, agent_id: int):
        super().__init__(env)
        self._env = env
        self._id = agent_id
        self._cx = env.obs_height // 2
        self._cy = env.obs_width // 2
        self._center = (self._cx, self._cy)
        self._tags = {n: i for i, n in enumerate(env.tags)}
        self._acts = set(env.action_names)
        self._s = AgentState(wander_dir=agent_id % 4)

    def _act(self, n: str) -> Action:
        return Action(name=n if n in self._acts else "noop")

    def _tag(self, name: str) -> int | None:
        return self._tags.get(name)

    def _inv(self, obs: Any) -> dict[str, int]:
        items: dict[str, int] = {}
        for tok in obs.tokens:
            if tok.location != self._center:
                continue
            n = tok.feature.name
            if not n.startswith("inv:"):
                continue
            suf = n[4:]
            if not suf:
                continue
            item, sep, ps = suf.rpartition(":p")
            if not sep or not item or not ps.isdigit():
                item, power = suf, 0
            else:
                power = int(ps)
            v = int(tok.value)
            if v <= 0:
                continue
            base = max(int(tok.feature.normalization), 1)
            items[item] = items.get(item, 0) + v * (base ** power)
        return items

    def _closest(self, obs: Any, names: list[str]) -> tuple[int, int] | None:
        ids = {self._tag(n) for n in names} - {None}
        if not ids:
            return None
        best = None
        best_d = 999
        for tok in obs.tokens:
            if tok.feature.name != "tag" or tok.value not in ids:
                continue
            loc = tok.location
            if loc is None:
                continue
            d = abs(loc[0] - self._cx) + abs(loc[1] - self._cy)
            if 0 < d < best_d:  # skip d==0, we're already there
                best_d = d
                best = (loc[0], loc[1])
        return best

    def _closest_including_zero(self, obs: Any, names: list[str]) -> tuple[tuple[int, int] | None, int]:
        ids = {self._tag(n) for n in names} - {None}
        if not ids:
            return None, 999
        best = None
        best_d = 999
        for tok in obs.tokens:
            if tok.feature.name != "tag" or tok.value not in ids:
                continue
            loc = tok.location
            if loc is None:
                continue
            d = abs(loc[0] - self._cx) + abs(loc[1] - self._cy)
            if d < best_d:
                best_d = d
                best = (loc[0], loc[1])
        return best, best_d

    def _move(self, target: tuple[int, int]) -> Action:
        dr = target[0] - self._cx
        dc = target[1] - self._cy
        if dr == 0 and dc == 0:
            return self._act("noop")
        # Alternate to avoid walls
        step = self._s.step
        if step % 2 == 0:
            if abs(dr) >= abs(dc) and dr != 0:
                return self._act("move_south" if dr > 0 else "move_north")
            if dc != 0:
                return self._act("move_east" if dc > 0 else "move_west")
            return self._act("move_south" if dr > 0 else "move_north")
        else:
            if abs(dc) >= abs(dr) and dc != 0:
                return self._act("move_east" if dc > 0 else "move_west")
            if dr != 0:
                return self._act("move_south" if dr > 0 else "move_north")
            return self._act("move_east" if dc > 0 else "move_west")

    def _wander(self) -> Action:
        s = self._s
        if s.wander_count <= 0:
            s.wander_dir = (s.wander_dir + 1) % 4
            s.wander_count = 6 + (self._id * 3) % 5  # vary by agent
        s.wander_count -= 1
        return self._act(f"move_{DIRECTIONS[s.wander_dir]}")

    def _pos(self, obs: Any) -> tuple[int, int] | None:
        e = w = n = s = 0
        for tok in obs.tokens:
            if tok.location != self._center:
                continue
            if tok.feature.name == "lp:east": e = int(tok.value)
            elif tok.feature.name == "lp:west": w = int(tok.value)
            elif tok.feature.name == "lp:north": n = int(tok.value)
            elif tok.feature.name == "lp:south": s = int(tok.value)
        if e == 0 and w == 0 and n == 0 and s == 0:
            return None
        return (s - n, e - w)

    def _check_stuck(self, obs: Any) -> bool:
        pos = self._pos(obs)
        s = self._s
        if pos and pos == s.prev_pos:
            s.stuck += 1
        else:
            s.stuck = 0
        s.prev_pos = pos
        return s.stuck > 2

    def _unstick(self) -> Action:
        s = self._s
        s.stuck = 0
        s.wander_dir = (s.wander_dir + 1) % 4
        return self._act(f"move_{DIRECTIONS[s.wander_dir]}")

    def _has_gear(self, inv: dict[str, int], g: str) -> bool:
        return inv.get(g, 0) > 0

    def _any_gear(self, inv: dict[str, int]) -> str | None:
        for g in ("aligner", "scrambler", "miner", "scout"):
            if inv.get(g, 0) > 0:
                return g
        return None

    def step(self, obs: Any) -> Action:
        s = self._s
        s.step += 1
        inv = self._inv(obs)
        gear = self._any_gear(inv)
        hearts = inv.get("heart", 0)

        if self._check_stuck(obs):
            return self._unstick()

        # --- STRATEGY ---
        # All agents follow same pipeline:
        # 1. If no resources and no gear: go mine (find extractors)
        # 2. If have some resources: visit hub to craft hearts
        # 3. If have hearts but no aligner gear: get aligner gear
        # 4. If have aligner gear + hearts: go to junctions
        # 5. If have aligner gear but no hearts: go to hub for more

        total_res = sum(inv.get(e, 0) for e in ELEMENTS)

        # If we have aligner gear and hearts, go align junctions
        if gear == "aligner" and hearts > 0:
            # Find junctions NOT already ours (net:cogs)
            our_locs: set[tuple[int, int]] = set()
            net_cogs = self._tag("net:cogs")
            if net_cogs is not None:
                for tok in obs.tokens:
                    if tok.feature.name == "tag" and tok.value == net_cogs:
                        loc = tok.location
                        if loc is not None:
                            our_locs.add((loc[0], loc[1]))

            # Find all junctions
            junc_tag = self._tag("type:junction")
            if junc_tag is not None:
                best = None
                best_d = 999
                for tok in obs.tokens:
                    if tok.feature.name != "tag" or tok.value != junc_tag:
                        continue
                    loc = tok.location
                    if loc is None:
                        continue
                    pos = (loc[0], loc[1])
                    if pos in our_locs:
                        continue  # skip already-aligned
                    d = abs(loc[0] - self._cx) + abs(loc[1] - self._cy)
                    if d < best_d:
                        best_d = d
                        best = pos
                if best is not None:
                    return self._move(best)

            # No unaligned junctions visible — wander to find some
            return self._wander()

        # If we have aligner gear but no hearts, go to hub
        if gear == "aligner" and hearts == 0:
            hub = self._closest(obs, ["type:hub"])
            if hub:
                return self._move(hub)
            return self._wander()

        # If we have enough resources to buy aligner gear, go get it
        # Aligner costs: carbon:3, oxygen:1, germanium:1, silicon:1
        can_buy_aligner = (
            inv.get("carbon", 0) >= 3 and
            inv.get("oxygen", 0) >= 1 and
            inv.get("germanium", 0) >= 1 and
            inv.get("silicon", 0) >= 1
        )
        if can_buy_aligner and gear != "aligner":
            station = self._closest(obs, ["type:c:aligner"])
            if station:
                return self._move(station)
            # Can't see station — go to hub area first (stations are near hub)
            hub = self._closest(obs, ["type:hub"])
            if hub:
                return self._move(hub)
            return self._wander()

        # If we have some resources but not enough for gear, visit hub periodically
        # to deposit/craft, then keep mining
        if total_res > 10 and s.step % 100 < 20:
            hub = self._closest(obs, ["type:hub"])
            if hub:
                return self._move(hub)

        # Mine resources: go to nearest extractor
        # Prioritize elements we're low on
        lowest_element = min(ELEMENTS, key=lambda e: inv.get(e, 0))
        specific_tag = f"type:{lowest_element}_extractor"
        target = self._closest(obs, [specific_tag])
        if target:
            return self._move(target)

        # Try any extractor
        target = self._closest(obs, EXTRACTOR_TAGS)
        if target:
            return self._move(target)

        # Nothing visible — wander to explore
        return self._wander()

    def reset(self, simulation: Any = None) -> None:
        self._s = AgentState(wander_dir=self._id % 4)


class CogletPolicy(MultiAgentPolicy):
    short_names = ["coglet", "coglet-policy"]

    def __init__(self, policy_env_info: PolicyEnvInterface, device: str = "cpu", **kwargs: Any):
        super().__init__(policy_env_info, device=device, **kwargs)
        self._agents: dict[int, CogletAgentPolicy] = {}

    def agent_policy(self, agent_id: int) -> CogletAgentPolicy:
        if agent_id not in self._agents:
            self._agents[agent_id] = CogletAgentPolicy(self._policy_env_info, agent_id)
        return self._agents[agent_id]

    def reset(self) -> None:
        self._agents.clear()
