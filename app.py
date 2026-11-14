"""Serve the homework UI locally; all simulation controls are available in HTML."""

from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from simulation import ALPHA, GAMMA, ACTIONS, BOARD_SIZE, MAX_FOOD_PAIRS, LearningMemory, Simulation

PROJECT_DIR = Path(__file__).resolve().parent
MEMORY_PATH = PROJECT_DIR / "learning_memory.json"
HTML_PATH = PROJECT_DIR / "index.html"


def integer(body: dict, name: str, default: int, maximum: int) -> int:
    value = body.get(name, default)
    if type(value) is not int or not 1 <= value <= maximum:
        raise ValueError(f"{name}: 1–{maximum} arasında tam sayı girin.")
    return value


def memory_data(memory: LearningMemory) -> dict:
    return {"actions": ACTIONS, "alpha": ALPHA, "gamma": GAMMA,
            "epsilon": memory.epsilon, "episodes": memory.episodes,
            "q_values": memory.q_values, "visits": memory.visits, "history": memory.history}


def make_handler(simulation: Simulation, auto_start: bool = True) -> type[BaseHTTPRequestHandler]:
    shared = {"running": auto_start, "last_summary": None}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            if self.path not in ("/api/tick", "/api/state"):
                super().log_message(format, *args)

        def send_data(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type + "; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def send_json(self, status: int, data: dict) -> None:
            self.send_data(status, json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"),
                           "application/json")

        def state(self) -> dict:
            memory = simulation.memory
            return {
                "running": shared["running"], "board_size": BOARD_SIZE,
                "episode": memory.episodes + 1, "completed_episodes": memory.episodes,
                "step": simulation.step_count, "metric": simulation.metric,
                "food_pairs": simulation.food_pairs,
                "green_foods": sorted(simulation.green_foods),
                "red_foods": sorted(simulation.red_foods),
                "agents": [{"id": agent.agent_id, "x": agent.position[0], "y": agent.position[1],
                            "speed": agent.speed, "green": agent.green, "red": agent.red,
                            "reward": agent.reward,
                            "nearest": simulation.observation_for(agent).nearest_agent}
                           for agent in simulation.agents],
                "epsilon": memory.epsilon, "alpha": ALPHA, "gamma": GAMMA,
                "learned_states": len(memory.q_values),
                "updates": sum(sum(visits) for visits in memory.visits.values()),
                "last_updates": simulation.last_updates,
                "last_summary": shared["last_summary"], "history": memory.history,
            }

        def do_GET(self) -> None:
            if self.path in ("/", "/index.html"):
                self.send_data(200, HTML_PATH.read_bytes(), "text/html")
            elif self.path == "/api/state":
                self.send_json(200, self.state())
            elif self.path == "/api/memory":
                self.send_json(200, memory_data(simulation.memory))
            else:
                self.send_json(404, {"error": "Adres bulunamadı."})

        def do_POST(self) -> None:
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 <= length <= 10000:
                    raise ValueError("İstek uzunluğu 0–10000 bayt arasında olmalı.")
                body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
                if not isinstance(body, dict):
                    raise ValueError("İstek bir JSON nesnesi olmalı.")
                if self.path == "/api/control":
                    self.control(body)
                elif self.path == "/api/tick":
                    steps = integer(body, "steps", 1, 20)
                    if shared["running"]:
                        for _ in range(steps):
                            result = simulation.step()
                            if result is not None:
                                shared["last_summary"] = result
                                simulation.memory.save(MEMORY_PATH)
                else:
                    self.send_json(404, {"error": "Adres bulunamadı."})
                    return
                self.send_json(200, self.state())
            except (UnicodeDecodeError, ValueError, TypeError) as error:
                self.send_json(400, {"error": str(error)})
            except OSError as error:
                shared["running"] = False
                self.log_error("Dosya işlemi başarısız: %s", error)
                self.send_json(500, {"error": f"Veriler kaydedilemedi: {error}"})

        def control(self, body: dict) -> None:
            action = body.get("action")
            if action == "start":
                shared["running"] = True
            elif action == "pause":
                shared["running"] = False
                simulation.memory.save(MEMORY_PATH)
            elif action == "new_episode":
                food_pairs = integer(body, "food_pairs", simulation.food_pairs, MAX_FOOD_PAIRS)
                simulation.memory.save(MEMORY_PATH)
                simulation.food_pairs = food_pairs
                simulation.new_episode()
                shared["last_summary"] = None
            else:
                raise ValueError("Bilinmeyen kontrol eylemi.")

    return Handler


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="BIL353 yiyecek toplama ödevi")
    parser.add_argument("--food-pairs", type=int, default=125)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--paused", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.food_pairs <= MAX_FOOD_PAIRS:
        parser.error(f"--food-pairs 1–{MAX_FOOD_PAIRS} arasında olmalı")
    if not 0 <= args.port <= 65535:
        parser.error("--port 0–65535 arasında olmalı")
    memory = LearningMemory.load(MEMORY_PATH)
    simulation = Simulation(args.food_pairs, args.seed, memory)
    server = HTTPServer(("127.0.0.1", args.port), make_handler(simulation, not args.paused))
    url = f"http://127.0.0.1:{server.server_address[1]}"
    print(f"Simülasyon: {url}")
    print("Durdurmak ve belleği kaydetmek için Ctrl+C kullanın.")
    webbrowser.open(url, new=2)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nSimülasyon durduruldu.")
    finally:
        memory.save(MEMORY_PATH)
        server.server_close()


if __name__ == "__main__":
    main()
