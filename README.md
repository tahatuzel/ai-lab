# BIL353 — Run Guide

This project uses Q-learning to help three agents collect green food and avoid red food on a 50 × 50 board. You can watch and control training in a browser. No external packages are required.

## Requirements

Python 3.10 or later. Run the commands from this project folder in PowerShell.

## First run

If you do not already have a virtual environment, create one:

```powershell
python -m venv .venv
```

Start the application:

```powershell
\.venv\Scripts\python.exe app.py
```

The browser opens automatically. If it does not, visit the `http://127.0.0.1:...` address printed in the terminal. Use the Python server instead of opening `index.html` directly.

## Using the HTML interface

- **Start / Pause:** Runs or pauses the simulation and learning. The simulation starts running by default.
- **Food count per color:** Enter an integer from 1 to 375. For example, 125 means 125 green and 125 red items.
- **Apply / New Episode:** Applies the food count and creates a new board. Learned Q values are kept. An unfinished episode is not saved as a completed episode.
- **Agent moves per refresh:** At the default value of 1, each agent's move is shown separately. Increase it from 1 to 20 to speed up training; agent movement speeds of 1–3 cells do not change. At higher values, moves are still processed in order, but only the final state is displayed.
- **Live status:** Shows the number of completed turns and the turn in which the next agent will move.
- **How is learning changing?** Shows the reward and old and new Q values for moves updated in the latest step, along with the learning coefficients. Use the link to view the full memory as JSON.
- **Training history:** Shows completed episodes from sequential runs. **Ending turn** next to the episode number tells you how many turns the episode took. The table also includes food count, starting seed, distance metric, α/γ/ε values, and each agent's score and speed. If there are enough episodes with the same food count, the average reward for the first and last 10 episodes is also shown.

Agents take turns in the order **1 → 2 → 3**. Each agent decides based on the current board, including changes made by earlier moves. Green food is checked after every move. If the last green item is collected, the episode result is saved before the next agent moves, and a new episode starts with agent 1. The next turn begins after all three agents have moved. If green food remains, the episode ends after 4,000 full turns. The turn count in the history includes the final partial turn in which the green food ran out.

To shut down the application completely, press `Ctrl+C` in the terminal. Closing only the browser does not stop the server.

## Optional startup settings

```powershell
\.venv\Scripts\python.exe app.py --food-pairs 40 --seed 42 --paused
```

`--paused` starts the application paused. Use `--seed` to reproduce the same initial conditions; actions in the interface can affect the sequence of later random choices. Add `--port 8000` if you need a fixed port.

## Learning data file

Each agent updates the Q value for its previous move when its turn comes around again, using the observation at that time. When an episode ends, pending moves use a future Q value of zero.

The application saves Q values, visit counts, and completed episode results to `learning_memory_v2.json`. It saves at the end of an episode, when paused, when a new episode starts, and when you exit with `Ctrl+C`. On the next launch, the application resumes learning from this file and creates a new board. Pending Q updates are discarded when the board is reset.

New state keys use a separate training history. The previous `learning_memory.json` file is kept locally. The new file starts with an empty memory on its first run. To start paused with 40 items of each color:

```powershell
\.venv\Scripts\python.exe app.py --food-pairs 40 --paused
```

For an explanation of the project's concepts, mathematics, and code, see `report.md`.
