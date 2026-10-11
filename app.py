"""Local server and repeatable training runner for the BIL353 simulation."""

from __future__ import annotations

import argparse
import json
import mimetypes
import random
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

from simulation import (
    ALGORITHMS,
    BOARD_SIZE,
    MAX_FOOD_PAIRS,
    EpisodeSummary,
    LearningMemory,
    Simulation,
)

PROJECT_DIR = Path(__file__).resolve().parent
MEMORY_PATH = PROJECT_DIR / "agent_memory.json"
HTML_PATH = PROJECT_DIR / "index.html"


def make_handler(
    simulation: Simulation, auto_start: bool = True
) -> type[BaseHTTPRequestHandler]:
    shared: dict[str, Any] = {"running": auto_start, "last_summary": None}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            if self.path not in ("/api/tick", "/api/state"):
                super().log_message(format, *args)

        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, status: int, data: dict[str, Any]) -> None:
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self._send(status, body, "application/json; charset=utf-8")

        def _state(self) -> dict[str, Any]:
            agents = []
            for agent in simulation.agents:
                nearest = simulation.observation_for(agent).nearest_agent
                agents.append(
                    {
                        "id": agent.agent_id,
                        "x": agent.position[0],
                        "y": agent.position[1],
                        "speed": agent.speed,
                        "green": agent.green_collected,
                        "red": agent.red_collected,
                        "reward": agent.reward,
                        "nearest": list(nearest) if nearest is not None else None,
                    }
                )
            rewards = simulation.memory.recent_rewards[simulation.algorithm]
            average_reward = sum(rewards) / len(rewards) if rewards else 0.0
            return {
                "board_size": BOARD_SIZE,
                "running": shared["running"],
                "episode": simulation.episode,
                "completed_episodes": simulation.memory.episodes,
                "algorithm_episode": simulation.algorithm_episode,
                "algorithm": simulation.algorithm,
                "algorithms": ALGORITHMS,
                "step": simulation.step_count,
                "metric": simulation.metric,
                "food_pairs": simulation.food_pairs,
                "green_foods": [list(point) for point in sorted(simulation.green_foods)],
                "red_foods": [list(point) for point in sorted(simulation.red_foods)],
                "agents": agents,
                "total_reward": sum(agent.reward for agent in simulation.agents),
                "epsilon": simulation.memory.epsilon[simulation.algorithm],
                "epsilon_by_algorithm": simulation.memory.epsilon,
                "learned_pairs": len(simulation.memory.visits),
                "average_reward": average_reward,
                "performance": simulation.memory.performance_summary(),
                "history": simulation.memory.history[-120:],
                "last_summary": shared["last_summary"],
            }

        def do_GET(self) -> None:
            if self.path in ("/", "/index.html"):
                body = HTML_PATH.read_bytes()
                content_type = mimetypes.guess_type(HTML_PATH.name)[0] or "text/html"
                self._send(200, body, content_type + "; charset=utf-8")
            elif self.path == "/api/state":
                self._send_json(200, self._state())
            else:
                self._send_json(404, {"error": "Adres bulunamadı."})

        def do_POST(self) -> None:
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length > 10000:
                    raise ValueError("İstek çok büyük.")
                body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
                if not isinstance(body, dict):
                    raise ValueError("İstek içeriği JSON nesnesi olmalı.")

                if self.path == "/api/control":
                    self._control(body)
                    self._send_json(200, self._state())
                elif self.path == "/api/tick":
                    self._tick(body)
                    self._send_json(200, self._state())
                else:
                    self._send_json(404, {"error": "Adres bulunamadı."})
            except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as error:
                self._send_json(400, {"error": str(error)})

        def _control(self, body: dict[str, Any]) -> None:
            action = body.get("action")
            if action == "start":
                shared["running"] = True
            elif action == "pause":
                shared["running"] = False
                simulation.memory.save(MEMORY_PATH)
            elif action == "new_episode":
                try:
                    food_pairs = int(body.get("food_pairs", simulation.food_pairs))
                except (TypeError, ValueError) as error:
                    raise ValueError("Yiyecek çifti tam sayı olmalı.") from error
                if not 1 <= food_pairs <= MAX_FOOD_PAIRS:
                    raise ValueError(
                        f"Yiyecek çifti 1 ile {MAX_FOOD_PAIRS} arasında olmalı."
                    )
                algorithm = body.get("algorithm", simulation.algorithm)
                if algorithm not in ALGORITHMS:
                    raise ValueError("Seçilen algoritma desteklenmiyor.")
                simulation.memory.save(MEMORY_PATH)
                simulation.food_pairs = food_pairs
                simulation.algorithm = algorithm
                simulation.episode = simulation.memory.episodes + 1
                simulation.algorithm_episode = (
                    simulation.memory.algorithm_episodes[algorithm] + 1
                )
                simulation.new_episode()
                shared["last_summary"] = None
            else:
                raise ValueError("Bilinmeyen kontrol eylemi.")

        def _tick(self, body: dict[str, Any]) -> None:
            try:
                steps = int(body.get("steps", 1))
            except (TypeError, ValueError) as error:
                raise ValueError("Adım sayısı tam sayı olmalı.") from error
            if not 1 <= steps <= 50:
                raise ValueError("Adım sayısı 1 ile 50 arasında olmalı.")
            if shared["running"]:
                for _ in range(steps):
                    summary = simulation.step()
                    if summary is not None:
                        shared["last_summary"] = _summary_json(summary)

    return Handler


def _summary_json(summary: EpisodeSummary) -> dict[str, Any]:
    return {
        "episode": summary.episode,
        "algorithm_episode": summary.algorithm_episode,
        "algorithm": summary.algorithm,
        "green": summary.green_collected,
        "red": summary.red_collected,
        "reward": summary.total_reward,
        "steps": summary.steps,
        "epsilon": summary.epsilon,
        "planning_ms": summary.planning_ms,
    }


def train(
    memory: LearningMemory,
    episodes: int,
    algorithms: list[str],
    food_pairs: int,
    seed: int | None,
) -> None:
    base_seed = seed if seed is not None else random.SystemRandom().randrange(1, 2**31)
    results: dict[str, list[EpisodeSummary]] = {algorithm: [] for algorithm in algorithms}
    print(
        f"Eşleştirilmiş tahta tohumu başlangıcı: {base_seed}; "
        f"{episodes} tur × {len(algorithms)} algoritma, her renkten {food_pairs} yiyecek."
    )
    for round_index in range(episodes):
        paired_seed = base_seed + round_index
        for algorithm in algorithms:
            simulation = Simulation(food_pairs, paired_seed, memory, algorithm)
            while True:
                summary = simulation.step()
                if summary is not None:
                    break
            results[algorithm].append(summary)
            print(
                f"{algorithm:20} tur {round_index + 1:>3}/{episodes}: "
                f"yeşil {summary.green_collected:>3}, kırmızı {summary.red_collected:>3}, "
                f"ödül {summary.total_reward:>4}, adım {summary.steps:>4}, "
                f"planlama {summary.planning_ms:>8.1f} ms, "
                f"ε {summary.epsilon:.3f}"
            )

    print("\nİlk ve son bölüm grupları (yeşil / kırmızı / ödül / adım / planlama ms):")
    for algorithm, rows in results.items():
        split = max(1, len(rows) // 2)
        first, last = rows[:split], rows[-split:]

        def average(
            items: list[EpisodeSummary],
        ) -> tuple[float, float, float, float, float]:
            count = len(items)
            return (
                sum(item.green_collected for item in items) / count,
                sum(item.red_collected for item in items) / count,
                sum(item.total_reward for item in items) / count,
                sum(item.steps for item in items) / count,
                sum(item.planning_ms for item in items) / count,
            )

        before, after = average(first), average(last)
        print(
            f"{algorithm:20} ilk {before[0]:5.1f}/{before[1]:5.1f}/{before[2]:6.1f}"
            f"/{before[3]:6.1f}/{before[4]:8.1f}"
            f" → son {after[0]:5.1f}/{after[1]:5.1f}/{after[2]:6.1f}"
            f"/{after[3]:6.1f}/{after[4]:8.1f}"
        )
    memory.save(MEMORY_PATH)
    print(f"\nQ-değerleri: {MEMORY_PATH.name}")
    print(f"Bölüm sonuçları: {(PROJECT_DIR / 'training_results.csv').name}")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="BIL353 çok ajanlı yiyecek toplama simülasyonu"
    )
    parser.add_argument(
        "--food-pairs",
        type=int,
        default=125,
        help=f"Her renkten yiyecek sayısı (1-{MAX_FOOD_PAIRS})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Tekrarlanabilir başlangıç tahtası / eşleştirilmiş eğitim tohumu",
    )
    parser.add_argument("--port", type=int, default=0, help="Yerel sunucu portu (varsayılan: otomatik)")
    parser.add_argument(
        "--train-episodes",
        type=int,
        default=0,
        help="Her seçili algoritma için çalıştırılacak eğitim bölümü sayısı; 0 sunucuyu açar",
    )
    parser.add_argument(
        "--algorithms",
        nargs="+",
        choices=ALGORITHMS,
        default=list(ALGORITHMS),
        help="Toplu eğitimde kıyaslanacak algoritmalar",
    )
    parser.add_argument(
        "--paused",
        action="store_true",
        help="Tarayıcı arayüzü açıldığında otomatik öğrenmeyi duraklat",
    )
    args = parser.parse_args()
    if not 1 <= args.food_pairs <= MAX_FOOD_PAIRS:
        parser.error(f"--food-pairs 1 ile {MAX_FOOD_PAIRS} arasında olmalı")
    if not 0 <= args.port <= 65535:
        parser.error("--port 0 ile 65535 arasında olmalı")
    if args.train_episodes < 0:
        parser.error("--train-episodes sıfır veya pozitif olmalı")

    memory = LearningMemory.load(MEMORY_PATH)
    if args.train_episodes:
        train(memory, args.train_episodes, args.algorithms, args.food_pairs, args.seed)
        return

    simulation = Simulation(args.food_pairs, args.seed, memory)
    server = HTTPServer(("127.0.0.1", args.port), make_handler(simulation, not args.paused))
    url = f"http://127.0.0.1:{server.server_address[1]}"
    print(f"Simülasyon hazır: {url}")
    print("Ajanlar otomatik öğreniyor; tarayıcıdan duraklatabilir veya algoritma seçebilirsiniz.")
    print("Durdurmak ve öğrenmeyi kaydetmek için bu işlemi Ctrl+C ile kapatın.")
    webbrowser.open(url, new=2)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nSimülasyon durduruluyor.")
    finally:
        simulation.memory.save(MEMORY_PATH)
        server.server_close()


if __name__ == "__main__":
    main()
