"""BIL353 multi-agent simulation, planners and persistent online learning."""

from __future__ import annotations

import csv
import heapq
import json
import math
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

BOARD_SIZE = 50
MAX_FOOD_FRACTION = 0.30
MAX_FOOD_PAIRS = int(BOARD_SIZE * BOARD_SIZE * MAX_FOOD_FRACTION // 2)
RED_CELL_COST = 15.0
GAMMA = 0.90
TRACE_DECAY = 0.75
ALGORITHMS = ("A*", "Dijkstra", "Greedy Best-First", "Manhattan")

Position = tuple[int, int]
ACTION_DELTAS: dict[str, Position] = {
    "Up": (0, -1),
    "Down": (0, 1),
    "Left": (-1, 0),
    "Right": (1, 0),
    "No Action": (0, 0),
}
ACTION_ORDER = tuple(ACTION_DELTAS)
DIRECTIONS = ACTION_ORDER[:-1]


def manhattan(a: Position, b: Position) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _search_path(
    start: Position,
    goals: set[Position],
    red_foods: set[Position],
    algorithm: str,
    size: int,
    speed: int,
    green_foods: set[Position],
) -> tuple[list[Position], float, Position | None]:
    if algorithm not in ALGORITHMS[:-1]:
        raise ValueError(f"Yol bulma algoritması desteklenmiyor: {algorithm}")
    if speed < 1:
        raise ValueError("Hız en az 1 olmalı.")
    if not goals:
        return [], math.inf, None
    if start in goals:
        return [], 0.0, start

    def heuristic(point: Position) -> int:
        return min(manhattan(point, goal) for goal in goals)

    first_distance = heuristic(start)
    initial_priority = 0.0 if algorithm == "Dijkstra" else float(first_distance)
    frontier: list[tuple[float, float, float, Position]] = [
        (initial_priority, 0.0, 0.0, start)
    ]
    came_from: dict[Position, Position] = {}
    costs: dict[Position, float] = {start: 0.0}

    while frontier:
        _, _, cost_so_far, current = heapq.heappop(frontier)
        if cost_so_far != costs.get(current):
            continue
        if current in goals:
            path: list[Position] = []
            while current != start:
                path.append(current)
                current = came_from[current]
            path.reverse()
            reached = path[-1] if path else start
            return path, cost_so_far, reached

        for action in DIRECTIONS:
            dx, dy = ACTION_DELTAS[action]
            destination = current
            edge_cost = 0.0
            for _ in range(speed):
                next_cell = (destination[0] + dx, destination[1] + dy)
                if not (0 <= next_cell[0] < size and 0 <= next_cell[1] < size):
                    break
                destination = next_cell
                edge_cost += 1 + (RED_CELL_COST if destination in red_foods else 0)
                if destination in green_foods or destination in red_foods:
                    break
            if destination == current:
                continue

            next_cost = cost_so_far + edge_cost
            if next_cost >= costs.get(destination, math.inf):
                continue
            costs[destination] = next_cost
            came_from[destination] = current
            distance = heuristic(destination)
            if algorithm == "Dijkstra":
                priority, tie_breaker = next_cost, distance
            elif algorithm == "Greedy Best-First":
                priority, tie_breaker = distance, next_cost
            else:
                priority, tie_breaker = next_cost + distance, next_cost
            heapq.heappush(
                frontier, (priority, tie_breaker, next_cost, destination)
            )

    return [], math.inf, None


def find_path(
    start: Position,
    goal: Position,
    red_foods: set[Position],
    algorithm: str = "A*",
    size: int = BOARD_SIZE,
    speed: int = 1,
    green_foods: set[Position] | None = None,
) -> tuple[list[Position], float]:
    """Find a risk-weighted route while modelling each full-speed action."""
    path, cost, _ = _search_path(
        start, {goal}, red_foods, algorithm, size, speed, green_foods or set()
    )
    return path, cost


def find_path_to_any(
    start: Position,
    goals: set[Position],
    red_foods: set[Position],
    algorithm: str,
    speed: int,
    green_foods: set[Position],
    size: int = BOARD_SIZE,
) -> tuple[list[Position], float, Position | None]:
    """Find the nearest reachable food if the preferred target is unreachable."""
    return _search_path(start, goals, red_foods, algorithm, size, speed, green_foods)


def astar(
    start: Position,
    goal: Position,
    red_foods: set[Position],
    size: int = BOARD_SIZE,
) -> tuple[list[Position], float]:
    """Compatibility wrapper for the original A* helper."""
    return find_path(start, goal, red_foods, "A*", size)


def direction_between(start: Position, next_cell: Position) -> str:
    if start[0] == next_cell[0]:
        return "Down" if next_cell[1] > start[1] else "Up"
    if start[1] == next_cell[1]:
        return "Right" if next_cell[0] > start[0] else "Left"
    return "No Action"


@dataclass(slots=True)
class Agent:
    agent_id: int
    position: Position
    speed: int
    green_collected: int = 0
    red_collected: int = 0
    reward: int = 0
    eligibility: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Observation:
    position: Position
    velocity: int
    green_foods: frozenset[Position]
    red_foods: frozenset[Position]
    nearest_agent: Position | None


@dataclass(frozen=True, slots=True)
class EpisodeSummary:
    episode: int
    algorithm_episode: int
    algorithm: str
    steps: int
    green_collected: int
    red_collected: int
    total_reward: int
    epsilon: float
    planning_ms: float


class LearningMemory:
    """Algorithm-specific Q-tables, exploration rates and recent results."""

    VERSION = 2

    def __init__(self) -> None:
        self.q_values: dict[str, float] = {}
        self.visits: dict[str, int] = {}
        self.episodes = 0
        self.algorithm_episodes = {name: 0 for name in ALGORITHMS}
        self.epsilon = {name: 0.18 for name in ALGORITHMS}
        self.recent_rewards = {name: [] for name in ALGORITHMS}
        self.history: list[dict[str, object]] = []

    @classmethod
    def load(cls, path: Path) -> LearningMemory:
        memory = cls()
        if not path.exists():
            return memory
        data = json.loads(path.read_text(encoding="utf-8"))
        version = data.get("version")
        if version not in (1, cls.VERSION):
            raise ValueError(f"Desteklenmeyen öğrenme dosyası sürümü: {version!r}")

        if version == 1:
            memory.q_values = {
                f"A*|{key}": float(value)
                for key, value in data.get("q_values", {}).items()
            }
            memory.visits = {
                f"A*|{key}": int(value)
                for key, value in data.get("visits", {}).items()
            }
            memory.episodes = int(data.get("episodes", 0))
            memory.algorithm_episodes["A*"] = memory.episodes
            memory.epsilon["A*"] = float(data.get("epsilon", 0.18))
            memory.recent_rewards["A*"] = [
                float(value) for value in data.get("recent_rewards", [])
            ][-100:]
            return memory

        memory.q_values = {
            str(key): float(value) for key, value in data.get("q_values", {}).items()
        }
        memory.visits = {
            str(key): int(value) for key, value in data.get("visits", {}).items()
        }
        memory.episodes = int(data.get("episodes", 0))
        for name in ALGORITHMS:
            memory.algorithm_episodes[name] = int(
                data.get("algorithm_episodes", {}).get(name, 0)
            )
            memory.epsilon[name] = float(data.get("epsilon", {}).get(name, 0.18))
            memory.recent_rewards[name] = [
                float(value)
                for value in data.get("recent_rewards", {}).get(name, [])
            ][-100:]
        memory.history = [
            row for row in data.get("history", []) if isinstance(row, dict)
        ][-500:]
        return memory

    def save(self, path: Path) -> None:
        data = {
            "version": self.VERSION,
            "q_values": self.q_values,
            "visits": self.visits,
            "episodes": self.episodes,
            "algorithm_episodes": self.algorithm_episodes,
            "epsilon": self.epsilon,
            "recent_rewards": self.recent_rewards,
            "history": self.history[-500:],
        }
        temporary_path = path.with_suffix(path.suffix + ".tmp")
        temporary_path.write_text(
            json.dumps(data, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        temporary_path.replace(path)

    @staticmethod
    def _key(algorithm: str, agent_id: int, state: str, action: str) -> str:
        return f"{algorithm}|{agent_id}|{state}|{action}"

    def value(self, algorithm: str, agent_id: int, state: str, action: str) -> float:
        return self.q_values.get(self._key(algorithm, agent_id, state, action), 0.0)

    def learn(
        self,
        algorithm: str,
        agent: Agent,
        state: str,
        action: str,
        reward: int,
        next_state: str,
        terminal: bool,
    ) -> None:
        key = self._key(algorithm, agent.agent_id, state, action)
        for trace_key in list(agent.eligibility):
            strength = agent.eligibility[trace_key] * GAMMA * TRACE_DECAY
            if strength < 0.01:
                del agent.eligibility[trace_key]
            else:
                agent.eligibility[trace_key] = strength
        agent.eligibility[key] = 1.0

        next_value = 0.0
        if not terminal:
            next_value = max(
                self.value(algorithm, agent.agent_id, next_state, next_action)
                for next_action in ACTION_ORDER
            )
        old_value = self.q_values.get(key, 0.0)
        temporal_difference = reward + GAMMA * next_value - old_value
        visit_count = self.visits.get(key, 0)
        learning_rate = max(0.04, 0.30 / math.sqrt(visit_count + 1))
        for trace_key, strength in agent.eligibility.items():
            updated = self.q_values.get(trace_key, 0.0) + (
                learning_rate * temporal_difference * strength
            )
            self.q_values[trace_key] = max(-10.0, min(10.0, updated))
        self.visits[key] = visit_count + 1

    def finish_episode(self, algorithm: str, reward: int) -> float:
        self.episodes += 1
        self.algorithm_episodes[algorithm] += 1
        rewards = (self.recent_rewards[algorithm] + [float(reward)])[-100:]
        self.recent_rewards[algorithm] = rewards
        average_reward = sum(rewards) / len(rewards)
        if average_reward > 0:
            self.epsilon[algorithm] = max(0.02, self.epsilon[algorithm] * 0.97)
        elif average_reward < 0:
            self.epsilon[algorithm] = min(0.25, self.epsilon[algorithm] * 1.05)
        return self.epsilon[algorithm]

    def add_result(self, row: dict[str, object], csv_path: Path) -> None:
        self.history = (self.history + [row])[-500:]
        columns = (
            "timestamp",
            "algorithm",
            "episode",
            "algorithm_episode",
            "seed",
            "food_pairs",
            "steps",
            "green",
            "red",
            "reward",
            "epsilon",
            "planning_ms",
        )
        write_header = not csv_path.exists() or csv_path.stat().st_size == 0
        with csv_path.open("a", newline="", encoding="utf-8") as result_file:
            writer = csv.DictWriter(result_file, fieldnames=columns)
            if write_header:
                writer.writeheader()
            writer.writerow(row)

    def performance_summary(self, window: int = 10) -> dict[str, dict[str, float | int]]:
        result: dict[str, dict[str, float | int]] = {}
        for algorithm in ALGORITHMS:
            rows = [row for row in self.history if row.get("algorithm") == algorithm]
            recent = rows[-window:]
            count = len(recent)
            result[algorithm] = {
                "episodes": self.algorithm_episodes[algorithm],
                "window": count,
                "avg_green": sum(int(row["green"]) for row in recent) / count if count else 0.0,
                "avg_red": sum(int(row["red"]) for row in recent) / count if count else 0.0,
                "avg_reward": sum(int(row["reward"]) for row in recent) / count if count else 0.0,
                "avg_planning_ms": (
                    sum(float(row["planning_ms"]) for row in recent) / count if count else 0.0
                ),
            }
        return result


class Simulation:
    """One 50 x 50 episode with three agents and one selected planner."""

    MAX_EPISODE_STEPS = 4000

    def __init__(
        self,
        food_pairs: int = 125,
        seed: int | None = None,
        memory: LearningMemory | None = None,
        algorithm: str = "A*",
    ) -> None:
        if not 1 <= food_pairs <= MAX_FOOD_PAIRS:
            raise ValueError(f"Yiyecek çifti 1 ile {MAX_FOOD_PAIRS} arasında olmalı.")
        if algorithm not in ALGORITHMS:
            raise ValueError(f"Algoritma desteklenmiyor: {algorithm}")
        self.food_pairs = food_pairs
        self.seed = seed
        self.rng = random.Random(seed)
        self.memory = memory or LearningMemory()
        self.algorithm = algorithm
        self.episode = self.memory.episodes + 1
        self.algorithm_episode = self.memory.algorithm_episodes[algorithm] + 1
        self._planning_seconds = 0.0
        self.new_episode()

    def new_episode(self) -> None:
        self.step_count = 0
        self._planning_seconds = 0.0
        self.metric = self.rng.choice(("Manhattan", "Euclidean"))
        cells = [(x, y) for y in range(BOARD_SIZE) for x in range(BOARD_SIZE)]
        placements = self.rng.sample(cells, self.food_pairs * 2 + 3)
        self.green_foods = set(placements[: self.food_pairs])
        self.red_foods = set(placements[self.food_pairs : self.food_pairs * 2])
        agent_cells = placements[self.food_pairs * 2 :]
        self.agents = [
            Agent(agent_id=index + 1, position=agent_cells[index], speed=self.rng.randint(1, 3))
            for index in range(3)
        ]
        self._episode_green = 0
        self._episode_red = 0

    def observation_for(self, agent: Agent) -> Observation:
        others = [other for other in self.agents if other.agent_id != agent.agent_id]
        if self.metric == "Manhattan":
            distance = lambda other: manhattan(agent.position, other.position)
        else:
            distance = lambda other: math.dist(agent.position, other.position)
        nearest = min(others, key=lambda other: (distance(other), other.agent_id))
        return Observation(
            position=agent.position,
            velocity=agent.speed,
            green_foods=frozenset(self.green_foods),
            red_foods=frozenset(self.red_foods),
            nearest_agent=nearest.position,
        )

    def _target_candidates(self, observation: Observation) -> list[Position]:
        if not observation.green_foods:
            return []
        ranked: list[tuple[tuple[float, int, int, int], Position]] = []

        for target in observation.green_foods:
            own_distance = manhattan(observation.position, target)
            own_time = own_distance / observation.velocity
            score = own_time
            if observation.nearest_agent is not None:
                other_time = manhattan(observation.nearest_agent, target) / 2.0
                if other_time <= own_time + 0.5:
                    score += 3.0 + max(0.0, own_time - other_time) * 0.25

            cluster_size = sum(
                1
                for dx in range(-3, 4)
                for dy in range(-3 + abs(dx), 4 - abs(dx))
                if (target[0] + dx, target[1] + dy) in observation.green_foods
            )
            score -= min(cluster_size - 1, 4) * 0.16
            key = (score, own_distance, target[1], target[0])
            ranked.append((key, target))
        ranked.sort()
        return [target for _, target in ranked]

    def _target(self, observation: Observation) -> Position | None:
        candidates = self._target_candidates(observation)
        return candidates[0] if candidates else None

    def _state_key(self, observation: Observation, target: Position | None) -> str:
        if target is None:
            return f"idle|v{observation.velocity}"
        dx = target[0] - observation.position[0]
        dy = target[1] - observation.position[1]
        x_direction = (dx > 0) - (dx < 0)
        y_direction = (dy > 0) - (dy < 0)
        nearest_red = min(
            (manhattan(observation.position, red) for red in observation.red_foods),
            default=BOARD_SIZE,
        )
        red_band = min(3, nearest_red // 2)
        competition = 0
        if observation.nearest_agent is not None:
            own_time = manhattan(observation.position, target) / observation.velocity
            other_time = manhattan(observation.nearest_agent, target) / 2.0
            competition = -1 if other_time < own_time - 0.5 else (
                1 if own_time < other_time - 0.5 else 0
            )
        return (
            f"{x_direction},{y_direction}|r{red_band}|c{competition}"
            f"|v{observation.velocity}"
        )

    @staticmethod
    def _project(observation: Observation, action: str) -> tuple[Position, int]:
        position = observation.position
        dx, dy = ACTION_DELTAS[action]
        red_hits = 0
        for _ in range(observation.velocity):
            next_position = (position[0] + dx, position[1] + dy)
            if not (0 <= next_position[0] < BOARD_SIZE and 0 <= next_position[1] < BOARD_SIZE):
                break
            position = next_position
            if position in observation.red_foods:
                red_hits += 1
                break
            if position in observation.green_foods:
                break
        return position, red_hits

    def _choose_action(
        self,
        agent: Agent,
        observation: Observation,
        state: str,
        target: Position | None,
        path: list[Position] | None = None,
    ) -> str:
        if target is None:
            return "No Action"

        planned_action = (
            direction_between(observation.position, path[0])
            if path
            else "No Action"
        )
        candidates: list[tuple[float, int, str]] = []
        for order, action in enumerate(ACTION_ORDER):
            projected, red_hits = self._project(observation, action)
            distance = manhattan(projected, target)
            score = -distance / observation.velocity - red_hits * RED_CELL_COST
            if action == planned_action and self.algorithm != "Manhattan":
                score += 5.0
            if action == "No Action" and target != observation.position:
                score -= 1.5
            score += self.memory.value(
                self.algorithm, agent.agent_id, state, action
            ) * 0.25
            candidates.append((score, -order, action))

        if self.rng.random() < self.memory.epsilon[self.algorithm]:
            safe_actions = [
                action
                for _, _, action in candidates
                if self._project(observation, action)[1] == 0
                and (action != "No Action" or target == observation.position)
            ]
            return self.rng.choice(safe_actions or ACTION_ORDER)
        return max(candidates)[2]

    def _next_state(self, agent: Agent) -> str:
        observation = self.observation_for(agent)
        return self._state_key(observation, self._target(observation))

    def step(self) -> EpisodeSummary | None:
        observations = {agent.agent_id: self.observation_for(agent) for agent in self.agents}
        planning_started = time.perf_counter()
        targets: dict[int, Position | None] = {}
        paths: dict[int, list[Position] | None] = {}
        for agent in self.agents:
            observation = observations[agent.agent_id]
            ranked_targets = self._target_candidates(observation)
            target = ranked_targets[0] if ranked_targets else None
            path: list[Position] | None = None
            if target is not None and self.algorithm != "Manhattan":
                reds = set(observation.red_foods)
                greens = set(observation.green_foods)
                preferred_targets = set(ranked_targets[:8])
                path, route_cost, reachable_target = find_path_to_any(
                    observation.position,
                    preferred_targets,
                    reds,
                    self.algorithm,
                    observation.velocity,
                    greens,
                )
                if reachable_target is None:
                    path, route_cost, reachable_target = find_path_to_any(
                        observation.position,
                        greens,
                        reds,
                        self.algorithm,
                        observation.velocity,
                        greens,
                    )
                if reachable_target is not None:
                    target = reachable_target
                else:
                    path = None
            targets[agent.agent_id] = target
            paths[agent.agent_id] = path

        states = {
            agent.agent_id: self._state_key(
                observations[agent.agent_id], targets[agent.agent_id]
            )
            for agent in self.agents
        }
        actions = {
            agent.agent_id: self._choose_action(
                agent,
                observations[agent.agent_id],
                states[agent.agent_id],
                targets[agent.agent_id],
                paths[agent.agent_id],
            )
            for agent in self.agents
        }
        self._planning_seconds += time.perf_counter() - planning_started
        rewards = {agent.agent_id: 0 for agent in self.agents}
        stopped: set[int] = set()
        moved_steps = {agent.agent_id: 0 for agent in self.agents}

        for _ in range(max(agent.speed for agent in self.agents)):
            proposals: dict[int, Position] = {}
            for agent in self.agents:
                if agent.agent_id in stopped or actions[agent.agent_id] == "No Action":
                    continue
                if moved_steps[agent.agent_id] >= agent.speed:
                    continue
                dx, dy = ACTION_DELTAS[actions[agent.agent_id]]
                destination = (agent.position[0] + dx, agent.position[1] + dy)
                if 0 <= destination[0] < BOARD_SIZE and 0 <= destination[1] < BOARD_SIZE:
                    proposals[agent.agent_id] = destination
                    moved_steps[agent.agent_id] += 1
                else:
                    stopped.add(agent.agent_id)

            claims: dict[Position, list[int]] = {}
            for agent_id, destination in proposals.items():
                claims.setdefault(destination, []).append(agent_id)
            for agent_id, destination in proposals.items():
                next(agent for agent in self.agents if agent.agent_id == agent_id).position = destination

            for destination, claimants in claims.items():
                if destination in self.green_foods:
                    winner = min(claimants, key=lambda agent_id: (actions[agent_id] != "Left", agent_id))
                    self.green_foods.remove(destination)
                    rewards[winner] += 1
                    self._episode_green += 1
                    winner_agent = next(agent for agent in self.agents if agent.agent_id == winner)
                    winner_agent.green_collected += 1
                    stopped.add(winner)
                elif destination in self.red_foods:
                    winner = min(claimants)
                    self.red_foods.remove(destination)
                    rewards[winner] -= 1
                    self._episode_red += 1
                    winner_agent = next(agent for agent in self.agents if agent.agent_id == winner)
                    winner_agent.red_collected += 1
                    stopped.add(winner)

        for agent in self.agents:
            reward = rewards[agent.agent_id]
            agent.reward += reward
            self.memory.learn(
                self.algorithm,
                agent,
                states[agent.agent_id],
                actions[agent.agent_id],
                reward,
                self._next_state(agent),
                not self.green_foods,
            )

        self.step_count += 1
        if not self.green_foods or self.step_count >= self.MAX_EPISODE_STEPS:
            total_reward = sum(agent.reward for agent in self.agents)
            epsilon = self.memory.finish_episode(self.algorithm, total_reward)
            summary = EpisodeSummary(
                episode=self.episode,
                algorithm_episode=self.algorithm_episode,
                algorithm=self.algorithm,
                steps=self.step_count,
                green_collected=self._episode_green,
                red_collected=self._episode_red,
                total_reward=total_reward,
                epsilon=epsilon,
                planning_ms=self._planning_seconds * 1000,
            )
            row: dict[str, object] = {
                "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "algorithm": self.algorithm,
                "episode": summary.episode,
                "algorithm_episode": summary.algorithm_episode,
                "seed": self.seed if self.seed is not None else "",
                "food_pairs": self.food_pairs,
                "steps": summary.steps,
                "green": summary.green_collected,
                "red": summary.red_collected,
                "reward": summary.total_reward,
                "epsilon": round(summary.epsilon, 6),
                "planning_ms": round(summary.planning_ms, 3),
            }
            root = Path(__file__).resolve().parent
            self.memory.add_result(row, root / "training_results.csv")
            self.memory.save(root / "agent_memory.json")
            self.episode += 1
            self.algorithm_episode += 1
            self.new_episode()
            return summary
        return None


if __name__ == "__main__":
    assert find_path((0, 0), (2, 0), set(), "A*")[1] == 2
    assert find_path((0, 0), (2, 0), set(), "Dijkstra")[1] == 2
    assert find_path((0, 0), (2, 0), set(), "Greedy Best-First")[1] == 2
    speed_path, speed_cost = find_path(
        (4, 43), (5, 43), set(), "A*", speed=3, green_foods={(5, 43)}
    )
    assert speed_path == [(5, 43)] and speed_cost == 1
    assert manhattan((0, 0), (2, 3)) == 5
    print("Simulation self-check passed.")
