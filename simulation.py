"""The homework environment and a small, independent Q-table for each agent."""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass
from datetime import datetime, timezone
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
            memory.history = data["history"]
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
        """Predict an action using only the information visible to this agent."""
        position = observation.position
        dx, dy = DELTAS[action]
        for _ in range(observation.speed):
            destination = position[0] + dx, position[1] + dy
            if not (0 <= destination[0] < BOARD_SIZE and 0 <= destination[1] < BOARD_SIZE):
                break
            position = destination
            if position in observation.green_foods or position in observation.red_foods:
                break
        return position, position in observation.red_foods

    def state_values(self, agent: Agent, observation: Observation) -> tuple[str, list[float]]:
        target = min(observation.green_foods,
                     key=lambda point: (manhattan(observation.position, point), point),
                     default=observation.position)
        dx, dy = target[0] - observation.position[0], target[1] - observation.position[1]
        sx, sy = (dx > 0) - (dx < 0), (dy > 0) - (dy < 0)
        red_mask = sum(1 << action for action in range(4) if self.project(observation, action)[1])
        competition = int(manhattan(observation.nearest_agent, target)
                          <= manhattan(observation.position, target))
        key = f"{agent.agent_id}|{sx},{sy}|v{agent.speed}|r{red_mask}|c{competition}"
        # A small initial preference uses visible food; experience replaces these values.
        initial = [0.1 * (x * sx + y * sy) - 0.5 * bool(red_mask & (1 << action))
                   for action, (x, y) in enumerate(DELTAS)]
        initial[-1] = -0.05
        return key, self.memory.values(key, initial)

    def choose_action(self, values: list[float]) -> int:
        if self.rng.random() < self.memory.epsilon:
            return self.rng.randrange(len(ACTIONS))
        best = max(values)
        return self.rng.choice([index for index, value in enumerate(values) if value == best])

    def move(self, agent: Agent, action: int) -> int:
        """Finish one agent's move before the next agent can act."""
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
        """Run one agent's action; agents 1, 2, 3 together make one turn."""
        agent = self.agents[self.next_agent_index]
        key, values = self.state_values(agent, self.observation_for(agent))
        action = self.choose_action(values)
        reward = self.move(agent, action)
        self.next_agent_index = (self.next_agent_index + 1) % len(self.agents)
        if self.next_agent_index == 0:
            self.step_count += 1
        terminal = not self.green_foods or self.step_count >= self.MAX_EPISODE_STEPS
        next_values = [] if terminal else self.state_values(agent, self.observation_for(agent))[1]
        update = self.memory.learn(key, action, reward, next_values, terminal)
        self.last_updates = [{"agent": agent.agent_id, **update}]
        if not terminal:
            return None
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
            "steps": self.step_count + int(self.next_agent_index != 0),
            "turn_order": "sequential",
            "green": sum(agent.green for agent in self.agents),
            "red": sum(agent.red for agent in self.agents),
            "reward": sum(agent.reward for agent in self.agents),
            "agents": [{"id": agent.agent_id, "speed": agent.speed, "green": agent.green, "red": agent.red,
                        "reward": agent.reward} for agent in self.agents],
        }
        self.memory.history.append(result)
        self.new_episode()
        return result
