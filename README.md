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
- **Agent moves per refresh** controls how many single-cell decisions run per update. At 1, each decision is shown separately. Higher values speed up training and display the board after the last decision in the batch.
- **Live status** shows completed turns, the next agent, and its position in the current sequence, such as step 2 of 3.
- **How is learning changing?** Shows the reward and old and new Q values for moves updated in the latest step, along with the learning coefficients. Use the link to view the full memory as JSON.
- **Training history:** Shows completed episodes from sequential runs. **Ending turn** next to the episode number tells you how many turns the episode took. The table also includes food count, starting seed, distance metric, α/γ/ε values, and each agent's score and speed. If there are enough episodes with the same food count, the average reward for the first and last 10 episodes is also shown.

Agents act in the order **1 → 2 → 3**. An agent with speed 1, 2, or 3 gets that many consecutive decisions before the next agent acts. Each decision uses the updated board and can move one cell in a new direction. Waiting and attempts to move past an edge each use one decision. Food is collected immediately, and the agent continues its remaining decisions unless it collected the last green item.

A full turn finishes when all three agents have used their decisions. An episode ends immediately when the last green is collected or after 4,000 full turns. The history includes a final partial turn in the turn count.

An agent targets the second-nearest green item if its visible opponent is closer to the nearest one. In a new Q state, moves that approach the selected target start at 0.05, and all other actions start at zero. The agent learns which moves lead to green and red food from their rewards.

To shut down the application completely, press `Ctrl+C` in the terminal. Closing only the browser does not stop the server.

## Optional startup settings

```powershell
\.venv\Scripts\python.exe app.py --food-pairs 40 --seed 42 --paused
```

`--paused` starts the application paused. Use `--seed` to reproduce the same initial conditions; actions in the interface can affect the sequence of later random choices. Add `--port 8000` if you need a fixed port.

## Learning data file

An agent updates the Q value for its previous move when it makes its next decision. Within the same turn it uses the board immediately after its own move. If it already used its decisions, it waits for its next turn and learns from the board after the other agents have acted. At episode end, pending moves use a future Q value of zero.

The application saves Q values, visit counts, and completed episode results to `learning_memory_v4.json`. It saves at the end of an episode, when paused, when a new episode starts, and when you exit with `Ctrl+C`. On the next launch, the application resumes learning from this file and creates a new board. Pending Q updates are discarded when the board is reset.

The current state key includes the number of decisions remaining for the agent. When `learning_memory_v4.json` is absent, training starts with an empty Q table and episode history. To start paused with 40 items of each color, run the following command.

```powershell
\.venv\Scripts\python.exe app.py --food-pairs 40 --paused
```

For an explanation of the project's concepts, mathematics, and code, see `report.md`.
