"""The homework environment and a small, independent Q-table for each agent."""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from heapq import nsmallest
from pathlib import Path

BOARD_SIZE = 50
MAX_FOOD_PAIRS = BOARD_SIZE * BOARD_SIZE * 30 // 100 // 2
ALPHA = 0.20
GAMMA = 0.90
ACTIONS = ("Up", "Down", "Left", "Right", "No Action")
DELTAS = ((0, -1), (0, 1), (-1, 0), (1, 0), (0, 0))
Position = tuple[int, int]


def manhattan(a: Position, b: Position) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


@dataclass
class Agent:
    agent_id: int
    position: Position
    speed: int
    green: int = 0
    red: int = 0

    @property
    def reward(self) -> int:
        return self.green - self.red


@dataclass(frozen=True)
class Observation:
    position: Position
    speed: int
    green_foods: frozenset[Position]
    red_foods: frozenset[Position]
    nearest_agent: Position


class LearningMemory:
    """State keys include the agent id, so rewards never update another agent."""

    def __init__(self) -> None:
        self.q_values: dict[str, list[float]] = {}
        self.visits: dict[str, list[int]] = {}
        self.episodes = 0
        self.history: list[dict] = []

    @property
    def epsilon(self) -> float:
        return max(0.05, 0.20 * 0.97 ** self.episodes)

    @classmethod
    def load(cls, path: Path) -> LearningMemory:
        memory = cls()
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("version") != 1:
                raise ValueError("Desteklenmeyen öğrenme dosyası sürümü.")
            memory.q_values = data["q_values"]
            memory.visits = data["visits"]
            memory.episodes = data["episodes"]
            memory.history = [row for row in data["history"] if row.get("turn_order") == "sequential"]
            if len(memory.history) != len(data["history"]):
                memory.save(path)
        return memory

    def save(self, path: Path) -> None:
        data = {
            "version": 1,
            "episodes": self.episodes,
            "q_values": self.q_values,
            "visits": self.visits,
            "history": self.history,
        }
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(path)

    def values(self, key: str, initial: list[float]) -> list[float]:
        if key not in self.q_values:
            self.q_values[key] = initial
            self.visits[key] = [0] * len(ACTIONS)
        return self.q_values[key]

    def learn(self, key: str, action: int, reward: int, next_values: list[float], terminal: bool) -> dict:
        values = self.q_values[key]
        old = values[action]
        future = 0.0 if terminal else max(next_values)
        target = reward + GAMMA * future
        values[action] += ALPHA * (target - old)
        self.visits[key][action] += 1
        return {"action": ACTIONS[action], "reward": reward, "old_q": old,
                "future_q": future, "target": target, "new_q": values[action]}


class Simulation:
    MAX_EPISODE_STEPS = 4000

    def __init__(self, food_pairs: int = 125, seed: int | None = None,
                 memory: LearningMemory | None = None) -> None:
        if type(food_pairs) is not int or not 1 <= food_pairs <= MAX_FOOD_PAIRS:
            raise ValueError(f"Her renkten yiyecek sayısı 1–{MAX_FOOD_PAIRS} arasında tam sayı olmalı.")
        self.food_pairs = food_pairs
        self.seed = seed
        self.rng = random.Random(seed)
        self.memory = memory if memory is not None else LearningMemory()
        self.new_episode()

    def new_episode(self) -> None:
        self.step_count = 0
        self.next_agent_index = 0
        self.agent_steps_taken = 0
        self.pending: dict[int, tuple[str, int, int]] = {}
        self.last_updates: list[dict] = []
        self.metric = self.rng.choice(("Manhattan", "Euclidean"))
        cells = self.rng.sample(range(BOARD_SIZE ** 2), self.food_pairs * 2 + 3)
        positions = [(cell % BOARD_SIZE, cell // BOARD_SIZE) for cell in cells]
        self.green_foods = set(positions[:self.food_pairs])
        self.red_foods = set(positions[self.food_pairs:self.food_pairs * 2])
        self.agents = [Agent(index + 1, point, self.rng.randint(1, 3))
                       for index, point in enumerate(positions[-3:])]

    def observation_for(self, agent: Agent) -> Observation:
        distance = manhattan if self.metric == "Manhattan" else math.dist
        nearest = min((other for other in self.agents if other.agent_id != agent.agent_id),
                      key=lambda other: (distance(agent.position, other.position), other.agent_id))
        return Observation(agent.position, agent.speed, frozenset(self.green_foods),
                           frozenset(self.red_foods), nearest.position)

    @staticmethod
    def project(observation: Observation, action: int) -> tuple[Position, bool]:
        """Predict one cell of movement using the agent's observation."""
        x, y = observation.position
        dx, dy = DELTAS[action]
        destination = x + dx, y + dy
        if not (0 <= destination[0] < BOARD_SIZE and 0 <= destination[1] < BOARD_SIZE):
            destination = observation.position
        return destination, destination in observation.red_foods

    def state_values(self, agent: Agent, observation: Observation) -> tuple[str, list[float]]:
        targets = nsmallest(2, observation.green_foods,
                            key=lambda point: (manhattan(observation.position, point), point))
        target = targets[0] if targets else observation.position
        if (len(targets) == 2
                and manhattan(observation.nearest_agent, target) < manhattan(observation.position, target)):
            target = targets[1]
        dx, dy = target[0] - observation.position[0], target[1] - observation.position[1]
        sx, sy = (dx > 0) - (dx < 0), (dy > 0) - (dy < 0)
        distance = abs(dx) + abs(dy)
        red_mask = green_mask = progress_mask = 0
        for action in range(4):
            destination, hits_red = self.project(observation, action)
            bit = 1 << action
            if hits_red:
                red_mask |= bit
            if destination in observation.green_foods:
                green_mask |= bit
            if manhattan(destination, target) < distance:
                progress_mask |= bit
        competition = int(manhattan(observation.nearest_agent, target) <= distance)
        steps_left = agent.speed
        if agent is self.agents[self.next_agent_index]:
            steps_left -= self.agent_steps_taken
        key = (f"{agent.agent_id}|{sx},{sy}|v{agent.speed}|m{steps_left}|r{red_mask}"
               f"|g{green_mask}|p{progress_mask}|c{competition}")
        # Favor progress slightly. Food outcomes are learned from rewards.
        initial = [0.05 if progress_mask & (1 << action) else 0.0 for action in range(len(ACTIONS))]
        return key, self.memory.values(key, initial)

    def choose_action(self, values: list[float]) -> int:
        if self.rng.random() < self.memory.epsilon:
            return self.rng.randrange(len(ACTIONS))
        best = max(values)
        return self.rng.choice([index for index, value in enumerate(values) if value == best])

    def move(self, agent: Agent, action: int) -> int:
        """Apply one action and return the reward for that step."""
        if action == 4:
            return 0
        agent.position, _ = self.project(self.observation_for(agent), action)
        if agent.position in self.green_foods:
            self.green_foods.remove(agent.position)
            agent.green += 1
            return 1
        if agent.position in self.red_foods:
            self.red_foods.remove(agent.position)
            agent.red += 1
            return -1
        return 0

    def step(self) -> dict | None:
        """Run one decision. An agent gets one decision per unit of speed."""
        self.last_updates = []
        agent = self.agents[self.next_agent_index]
        key, values = self.state_values(agent, self.observation_for(agent))
        self._learn_pending(agent.agent_id, values)
        action = self.choose_action(values)
        reward = self.move(agent, action)
        self.pending[agent.agent_id] = (key, action, reward)
        self.agent_steps_taken += 1
        if self.agent_steps_taken == agent.speed:
            self.agent_steps_taken = 0
            self.next_agent_index = (self.next_agent_index + 1) % len(self.agents)
            if self.next_agent_index == 0:
                self.step_count += 1
        terminal = not self.green_foods or self.step_count >= self.MAX_EPISODE_STEPS
        if not terminal:
            return None
        for agent_id in tuple(self.pending):
            self._learn_pending(agent_id)
        epsilon = self.memory.epsilon
        self.memory.episodes += 1
        result = {
            "episode": self.memory.episodes,
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "food_pairs": self.food_pairs,
            "seed": self.seed,
            "metric": self.metric,
            "alpha": ALPHA,
            "gamma": GAMMA,
            "epsilon": epsilon,
            "steps": self.step_count + int(self.next_agent_index != 0 or self.agent_steps_taken != 0),
            "turn_order": "sequential",
            "green": sum(agent.green for agent in self.agents),
            "red": sum(agent.red for agent in self.agents),
            "reward": sum(agent.reward for agent in self.agents),
            "agents": [{"id": agent.agent_id, "speed": agent.speed, "green": agent.green, "red": agent.red,
                        "reward": agent.reward} for agent in self.agents],
        }
        self.memory.history.append(result)
        updates = self.last_updates
        self.new_episode()
        self.last_updates = updates
        return result

    def _learn_pending(self, agent_id: int, next_values: list[float] | None = None) -> None:
        transition = self.pending.pop(agent_id, None)
        if transition is not None:
            update = self.memory.learn(*transition, next_values or [], terminal=next_values is None)
            self.last_updates.append({"agent": agent_id, **update})
