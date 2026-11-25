# BIL353 — Multi-Agent Food Collection: Project Report

This report explains the rules, learning method, and software components of a simulation in which three agents compete to collect food. Each component is covered by three questions: **What is it? What does it do? How is it used in this project?** Short code examples and numerical calculations support the explanations. Setup and run commands are in `README.md`.

## 1. Project purpose and scope

Imagine a game board with three players, green food to collect, and red food to avoid. We call each player an **agent**. An agent is a piece of software that receives information about its surroundings and chooses a move.

Our task is not to control the players by hand. We make each agent choose a move, receive a reward for its result, and use that experience to change later choices. This is called **reinforcement learning**: instead of giving the agent a list of correct moves in advance, we use rewards to communicate the outcomes of its behavior.

The project uses one learning method: tabular **Q-learning**. We do not train a neural network or a language model. The core environment runs in Python; an HTML page displays and controls it.

### Where are the assignment requirements met?

| Requirement | Implementation | Code location |
|---|---|---|
| 50 × 50 board | Coordinates range from 0 to 49; 2,500 cells in total | `simulation.py`: `BOARD_SIZE` |
| Equal numbers of green and red items, placed randomly, with a total of at most 30% of cells | At most 375 of each color; random cells are selected without replacement | `MAX_FOOD_PAIRS`, `Simulation.new_episode()` |
| Three agents | Three `Agent` instances on different starting cells | `Simulation.new_episode()` |
| Only the nearest opponent's position | The observation contains one opponent coordinate | `Simulation.observation_for()` |
| Random choice of Manhattan or Euclidean distance | One metric is selected at the start of each episode | `new_episode()`, `observation_for()` |
| Food is observable | Coordinates for all green and red items are included in the observation | `Observation` |
| Random speed of 1–3 cells | The speed gives each agent 1–3 consecutive single-cell decisions per turn | `new_episode()`, `step()` |
| Up, down, left, right, and no action | Five discrete choices | `ACTIONS`, `DELTAS`, `move()` |
| Green +1, red −1; independent rewards | Only the collecting agent receives the food reward; only the agent that made the move gets its Q update | `Agent.reward`, `move()`, `LearningMemory.learn()` |
| Fixed move order | Agents 1 → 2 → 3 each use their decisions in order. Green food is checked after every decision | `Simulation.step()` |

We chose tabular Q-learning as the learning method. Agents move in a fixed order. The first agent to reach a food item collects it, and the next agent chooses based on the updated board.

## 2. Software components and responsibilities

| File | Responsibility |
|---|---|
| `simulation.py` | Agents, board, observations, movement, rewards, learning, and JSON memory |
| `app.py` | Local web server and communication between the HTML page and simulation |
| `index.html` | Drawing the board, buttons, settings, learning display, and episode results |
| `README.md` | Setup and run guide |
| `report.md` | Presentation report explaining the project's concepts, method, and components |
| `learning_memory_v4.json` | Learning data created when the application runs |

Python holds the actual game state. Drawing a circle for an agent in HTML does not move it: Python first changes the position, then HTML displays the new coordinates. This keeps the game rules in one place.

## 3. A short glossary for reading the code

- **Variable:** A name given to a value. `BOARD_SIZE = 50` stores the board size under a name.
- **Function:** A group of code that performs a task. `manhattan(a, b)` takes two positions and returns a distance.
- **Loop:** Repeats the same task. We loop through the agents to choose their moves.
- **Class / object:** Groups the data and behavior for a concept. We create three separate agent objects from the `Agent` class.
- **List:** An ordered collection. A state's five Q values are stored in a list in action order.
- **Tuple:** Used here for a fixed coordinate pair such as `(x, y)`.
- **Set:** Holds unique items. Food coordinates are stored in sets so we can quickly check whether a cell contains food.
- **Dictionary:** Looks up a value by its key. We use a state key to access its Q-value list.
- **`dataclass`:** Defines fields such as an agent's position and speed with little code.
- **Type annotation:** An expression such as `Position = tuple[int, int]` describes the expected data format; by itself, it does not validate user input.

`json`, `math`, `random`, `dataclasses`, `datetime`, and `pathlib` in `simulation.py`, as well as the HTTP server in `app.py`, come from Python's standard library. No extra packages are installed.

## 4. What are the board, cells, and coordinates?

The board has 50 columns and 50 rows. We represent a cell as `(x, y)`:

- `x` increases from left to right.
- `y` increases from top to bottom.
- The top-left cell is `(0, 0)` and the bottom-right cell is `(49, 49)`.

For example, an agent at `(10, 8)` moves to `(11, 8)` when it goes right and `(10, 7)` when it goes up. On screen coordinates, moving up decreases `y`.

In code:

```python
BOARD_SIZE = 50
Position = tuple[int, int]
```

We do not create a large matrix of 2,500 cell objects. Agent positions and sets of food coordinates are enough. If a coordinate is not in either set, that cell has no food.

## 5. How did we create a random starting board?

### First, the 30% limit

```text
50 × 50 = 2,500 cells
2,500 × 0.30 = 750 food cells
750 / 2 = at most 375 of each color
```

That is why `MAX_FOOD_PAIRS` is:

```python
MAX_FOOD_PAIRS = BOARD_SIZE * BOARD_SIZE * 30 // 100 // 2
```

If the user enters 125, we place 125 green and 125 red items, for 250 food items in total. `food_pairs` specifies how many items there are of each color.

### Choosing unique cells

`Simulation.new_episode()` does the following:

```python
cells = self.rng.sample(range(BOARD_SIZE ** 2), self.food_pairs * 2 + 3)
positions = [(cell % BOARD_SIZE, cell // BOARD_SIZE) for cell in cells]
```

`range(2500)` numbers the cells from 0 to 2499. `sample` does not select the same number twice. We convert a number to coordinates using division and remainder. For example, cell number 102 becomes:

```text
x = 102 % 50 = 2
y = 102 // 50 = 2
position = (2, 2)
```

The first `food_pairs` cells hold green food, the next equal number hold red food, and the final three are agent starting positions. This prevents food and agents from overlapping at the start.

Each agent's speed is set with `randint(1, 3)`. It determines how many consecutive decisions that agent gets each turn. Speed stays fixed for the episode and is selected again in the next episode. The assignment does not specify how often speed should be selected, so we choose it at the start of each episode.

`random.Random(seed)` is a random number generator. The same seed and sequence of operations can reproduce the same selections, which is useful for testing and investigating problems.

## 6. What is Manhattan distance?

Manhattan distance is a distance metric. Imagine a city with a grid of streets and count the cells traveled horizontally and vertically:

```text
d = |x₁ − x₂| + |y₁ − y₂|
```

The vertical bars mean absolute value: remove the sign of the result. Between `(2, 3)` and `(5, 7)`:

```text
|2 − 5| + |3 − 7| = 3 + 4 = 7
```

The implementation in `simulation.py` is:

```python
def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])
```

We use it for two purposes in the project:

1. To identify the nearest other agent if the episode uses the Manhattan metric.
2. To choose an agent's target food and summarize competition for that target.

This distance counts the horizontal and vertical cells between two points. The number of full turns to reach a target also depends on the agent's speed and the moves chosen by all three agents.

## 7. What is Euclidean distance, and why use it when diagonal moves are not allowed?

Euclidean distance is the straight-line length between two points:

```text
d = √((x₁ − x₂)² + (y₁ − y₂)²)
```

For the same example, the result is `√(3² + 4²) = 5`. Instead of writing the formula ourselves, Python uses the standard `math.dist` function.

**Measuring distance and moving are different tasks.** When Euclidean distance is selected, agents still cannot move diagonally. Only the choice of which opponent counts as nearest changes. The final assignment text we followed asks for a random choice between the two metrics, so we kept both.

For example, let the main agent be at `(0, 0)` and the other agents at `(3, 3)` and `(0, 5)`:

| Opponent | Manhattan | Euclidean |
|---|---:|---:|
| `(3, 3)` | 6 | about 4.24 |
| `(0, 5)` | 5 | 5 |

Manhattan distance considers the second opponent closer; Euclidean distance considers the first closer.

The two code sections are:

```python
# new_episode()
self.metric = self.rng.choice(("Manhattan", "Euclidean"))

# observation_for()
distance = manhattan if self.metric == "Manhattan" else math.dist
```

The metric is selected once at the start of an episode. If two opponents are equally close, the lower agent number breaks the tie. The assignment does not specify how to break ties, so we chose a consistent rule.

## 8. What does an agent know and not know?

An **observation** is the information an agent is allowed to use when making a decision. `Observation` contains:

```python
position       # Its own position
speed          # Its own speed
green_foods    # Positions of all green food
red_foods      # Positions of all red food
nearest_agent  # The position of one opponent
```

The other opponents' positions and both opponents' speeds are not in this object. `frozenset` carries the food coordinates as an immutable view; an agent cannot change the board's food while preparing a decision.

The simulation engine must know all agents to manage movement and collisions. `observation_for()` narrows that broad information and sends only the permitted observation to the decision code. Showing all agents on screen does not mean that every agent receives all of their positions for decision-making.

## 9. How are the five actions represented in code?

```python
ACTIONS = ("Up", "Down", "Left", "Right", "No Action")
DELTAS = ((0, -1), (0, 1), (-1, 0), (1, 0), (0, 0))
```

Items at the same index correspond to each other:

| Index | Action | Position change |
|---:|---|---|
| 0 | Up | `(0, -1)` |
| 1 | Down | `(0, 1)` |
| 2 | Left | `(-1, 0)` |
| 3 | Right | `(1, 0)` |
| 4 | No Action | `(0, 0)` |

Neither x nor y changes at the same time, so diagonal movement is not possible. “No Action” is a choice; it is not an automatic waiting state.

The assignment uses the phrase “4 branches” in the same item where it lists five actions. The implementation uses the five actions explicitly listed. One action is selected for each move.

## 10. How does a fast agent use its decisions?

A speed-3 agent gets up to three decisions in succession. Each decision uses a fresh observation and moves at most one cell. The agent can change direction after any decision.

Suppose a speed-3 agent starts at `(4, 5)` with green food at `(5, 4)` and elsewhere on the board. It can move right to `(5, 5)`, move up to `(5, 4)`, collect the food immediately, and use its third decision to move toward another item. Collecting the final green item ends the episode immediately.

Choosing **No Action** or attempting to step past a board edge leaves the position unchanged and uses one decision. `project()` predicts a candidate's one-cell destination, including the board boundary. `move()` applies the selected action, removes food from the destination, and returns the reward for that decision.

## 11. Sequential moves and food competition

**What is it?** Sequential execution means each agent uses all of its decisions before the next agent starts. The order is **agent 1 → agent 2 → agent 3** on every full turn.

**What does it do?** The effect of each move is applied to the board immediately. It is clear who collected each food item, and the next agent does not decide based on food that is no longer there.

**How is it used in this project?** `Simulation.step()` executes one decision for the active agent. If it reaches food, the item is removed immediately and that agent receives +1 for green or −1 for red. The next decision uses the updated board. That decision belongs to the same agent if it has any left, or to the next agent once the allowance is spent.

For example, suppose agents 1 and 2 could both reach the same green item. If agent 1 collects it, agent 2 chooses based on the remaining food. If agent 1 collects the last green item, the episode ends before any remaining decisions.

Multiple agents may occupy the same cell; agents do not block one another. The fixed order can give an advantage to the agent that moves first when several agents can reach the same food. This is a limitation of the execution model.

## 12. The difference between reward, state, and Q value

To understand learning, distinguish these three concepts:

- **Reward `r`:** What just happened? Collecting green gives +1, collecting red gives −1, and collecting no food gives 0.
- **State `s`:** What conditions did the agent face when it made a decision? For example, the target is in the upper right, the agent has speed 2, and there is a red-food risk to the left.
- **Q value `Q(s,a)`:** How much future reward might result from choosing action `a` in state `s`? It is the agent's estimate.

A Q value is not the actual score. An agent may have 7 points while the Q value of moving right in a particular state is 0.35. One is the reward it has collected in the past; the other is an estimate about the future.

`Agent.reward` calculates the actual score:

```python
@property
def reward(self):
    return self.green - self.red
```

For example, an agent that collects 12 green and 3 red items has a score of `12 − 3 = 9`. The interface summarizes the team score, but we do not give that total to every agent as its learning reward. Each agent learns from the food it collected.

## 13. How did we summarize the state without encoding the whole board?

Creating a separate learning-table entry for every possible board arrangement would require a lot of memory. `Simulation.state_values()` creates a smaller state key.

We rank the two nearest green items by Manhattan distance. If the visible opponent is strictly closer to the first item, the agent selects the second. With one green item left, it remains the target. Coordinate order breaks ties between food items. The key then describes the selected target and includes:

| Part | Meaning | Why it is needed |
|---|---|---|
| Agent number | 1, 2, or 3 | Keeps the learning tables separate |
| `sx,sy` | Horizontal and vertical direction to the target: −1, 0, +1 | Summarizes the directions in which to approach the target |
| `v` | Agent speed | Gives the total number of decisions on each of the agent's turns |
| `m` | Decisions remaining in the agent's current turn, including the upcoming choice | Distinguishes acting again immediately from letting opponents act next |
| `r` | Bit mask of red-food risks in the four movement directions | Distinguishes nearby hazards |
| `g` | Bit mask of directions that collect green in this move | Distinguishes moves that give an immediate reward |
| `p` | Bit mask of directions that reduce Manhattan distance to the target | Accounts for the result of one step in each direction, including board edges |
| `c` | Is the visible opponent at least as close to the selected target as we are? | Records competition even when the agent has switched targets or has only one option |

Example key:

```text
1|1,-1|v2|m1|r4|g0|p9|c1
```

This is agent 1, with speed 2 and one decision left in its turn. The target is to the upper right, and the visible opponent is at least as close to it as agent 1. Moving left encounters red (`r4`). No green can be collected in one move (`g0`). Up and right move closer to the target (`p9 = 1 + 8`).

### How do we calculate direction signs?

```python
sx = (dx > 0) - (dx < 0)
```

In Python, `True` behaves like `1` and `False` like `0`. If `dx` is positive, the result is `1 − 0 = 1`; if it is negative, the result is `0 − 1 = −1`; if it is zero, the result is `0 − 0 = 0`. We do the same for y.

### What is a bit mask?

We store four separate yes/no values in one number:

| Direction | Number added if the property is true |
|---|---:|
| Up | 1 |
| Down | 2 |
| Left | 4 |
| Right | 8 |

If left and right are risky, `r = 4 + 8 = 12`. `1 << action` produces the number for the corresponding action. All three masks use the same encoding. For example, with a single green item one cell to the right, the result is `g8` and `p8`. If it is two cells to the right, the result is `g0` and `p8`. In either case, this decision can move one cell regardless of the agent's speed.

We use the episode's distance metric to identify the visible opponent. The target selection and `c` use Manhattan distance for both agents. The opponent's speed is unknown, so this comparison measures distance only.

Different boards can still produce the same key. For example, with speed 1, targets two and ten cells to the right produce the same state if all other features are equal. The moves of opponents that the agent cannot see can also change the next board.

## 14. How is the Q table stored?

`LearningMemory.q_values` is a dictionary whose keys are states and whose values are five Q numbers:

```json
{
  "1|1,-1|v2|m1|r4|g0|p9|c1": [0.05, 0.0, 0.0, 0.05, 0.0]
}
```

The list order is always `Up, Down, Left, Right, No Action`. Up and right start at 0.05 because both approach the target. The red-food risk appears in the state key and affects the Q value through the reward when an agent tries that action.

The `visits` list for the same key stores how many times each action actually received a learning update:

```json
{
  "1|1,-1|v2|m1|r4|g0|p9|c1": [3, 0, 1, 7, 0]
}
```

This means that up was updated 3 times, left once, and right 7 times. This version does not use visit counts to change the learning rate; it stores them so we can inspect the learning process.

Because the agent number is part of the key, agent 1's reward does not change agent 2's row. The data is held in one physical dictionary, but the tables are logically separate.

A row may also be created when looking up the next state's values. Therefore, some rows counted as “learned states” may not yet have had an action selected and updated. The actual number of learning updates is the sum of `visits`; the interface displays this as “Q updates.”

## 15. How does an agent move when it initially knows nothing?

For a new state, a move that reduces the distance to the selected target starts at 0.05. All other actions, including waiting, start at zero. This small preference gives the agent a direction before it has experience.

An action that approaches the target starts at 0.05 whether it collects green, collects red, or reaches an empty cell. The `g` and `r` masks let learning assign different values to those situations as the agent receives rewards.

`LearningMemory.values()` saves these values the first time a state is seen. Later visits use the updated Q values. The environment's reward is +1, −1, or 0 according to the food collected during the move. Initial preferences guide behavior only when no experience has been recorded for that state.

## 16. How does the agent choose an action? ε-greedy

Always taking the move that currently looks best could prevent the agent from discovering whether another choice is better. We address this with some **exploration**.

`Simulation.choose_action()`:

```python
if self.rng.random() < self.memory.epsilon:
    return self.rng.randrange(len(ACTIONS))
best = max(values)
return self.rng.choice([i for i, value in enumerate(values) if value == best])
```

- With probability `ε`, choose one of the five actions at random.
- Otherwise, choose an action with the highest Q value.
- If several actions share the highest value, choose randomly among them.

At the start, `ε = 0.20`, so exploration happens in about one decision out of five. This does not mean every fifth decision is random; a separate probability is applied at every decision.

The exploration rate decreases with the number of completed episodes:

```python
max(0.05, 0.20 * 0.97 ** episodes)
```

It is 0.20 in the first episode and about 0.147 after 10 episodes. It has a minimum of 0.05. This lets the agent use what it has learned more often without eliminating new behavior entirely.

The three agents have separate Q values, but in this simplified version α, γ, and ε are shared by the program. Random exploration can lead to red food. Making mistakes is part of learning from negative rewards.

## 17. Step-by-step Q-learning mathematics

`Q(s,a)` estimates the discounted total reward an agent expects to receive over its own moves if it takes action `a` in state `s`. If it can collect green two decisions later, that food contributes `γ² × 1` to today's estimate. With `γ = 0.90`, the value is 0.81. This lets the Q value account for a preparatory move that does not collect food immediately.

The update first calculates a target, then the temporal difference (`δ`):

```text
target = r + γ × max Q(s′,a′)
δ = target − Q_old(s,a)
Q_new(s,a) = Q_old(s,a) + α × δ
```

| Symbol | Meaning | In this project |
|---|---|---|
| `s` | State before the move | State key |
| `a` | The move taken | One of five actions |
| `r` | Reward from this move | +1, −1, or 0 |
| `s′` | The same agent's state at its next decision | The updated board and the number of decisions left at that point |
| `max Q(s′,a′)` | Best estimated future in the new state | Highest of the five Q values |
| `α` | How much weight should new information get? | 0.20 |
| `γ` | How much should future reward matter? | 0.90 |

### What does α do?

It is the learning rate. A value of 0.20 means the old estimate moves 20% of the way toward the new target. One experience does not erase the entire history.

### What does γ do?

It sets the weight of future rewards. The agent values not only rewards next to it, but also rewards expected on later moves. For example, if the best Q value in the new state is 0.4, its contribution to the target is `0.9 × 0.4 = 0.36`.

### When does the agent observe its next state?

If the agent has decisions remaining, its next state uses the board immediately after its own move. If it just finished its turn, its next decision comes after the other agents have acted. For example, agent 1 may move toward a green item on its last decision, and agent 2 may collect it before agent 1 acts again. Agent 1 updates its earlier choice from the board it now sees. Agent 2 receives +1 for the item it collected.

If the five Q values in the current state are `[0.1, 0.4, −0.2, 0.2, −0.05]`, the future estimate is 0.4. With reward 0 and old Q of 0.1, the target is 0.36, the temporal difference is 0.26, and the new Q is `0.1 + 0.2 × 0.26 = 0.152`. This update uses 0.4 even if the agent chooses a different action on its next move because of exploration. Q-learning is **off-policy** because its target uses the best estimated action, independently of the exploratory policy being followed.

### Numerical example: green food collected

Suppose old Q = 0.1, reward = +1, and the best Q in the new state = 0.4:

```text
Target = 1 + 0.9 × 0.4 = 1.36
Error  = 1.36 − 0.1 = 1.26
New Q  = 0.1 + 0.2 × 1.26 = 0.352
```

The next time the agent encounters a similar state, this move is evaluated at 0.352 instead of 0.1.

### Numerical example: red food collected

Keep the same old and future Q values, but set the reward to −1:

```text
Target = −1 + 0.9 × 0.4 = −0.64
New Q  = 0.1 + 0.2 × (−0.64 − 0.1) = −0.048
```

This move becomes less desirable. After several similar experiences, the value of a decision that leads to red food can change further.

### What changes when an episode ends?

No reward follows the end of a completed episode, so we use `future = 0`. If the old Q value of the agent that collected the final green is 0.1:

```text
Target = 1
New Q  = 0.1 + 0.2 × (1 − 0.1) = 0.28
```

The episode ends when the last green is collected or when 4,000 full turns have passed. Every pending move is updated using its own immediate reward and a future Q value of zero. For example, if another agent collected the last green and a pending move's reward was 0, that move's target is also zero.

### The code

`LearningMemory.learn()`:

```python
old = values[action]
future = 0.0 if terminal else max(next_values)
target = reward + GAMMA * future
values[action] += ALPHA * (target - old)
self.visits[key][action] += 1
```

The interface shows the old Q, reward, future Q, target, and new Q values calculated in the latest call to this function. The visit count increases by 1 only for the updated state-action pair.

### Why tabular Q-learning?

Each agent has five discrete actions and a small summary of its observation. We can store five numbers for each state. This makes it possible to inspect how one move changes Q values in the interface and JSON file. The algorithm learns from observed transitions without modeling opponents' decision rules or the probabilities of board transitions.

| Method | Assessment for this project |
|---|---|
| Fixed heuristic that moves toward the nearest green | Easy to implement and provides a comparison point for training. It does not accumulate experience or change later decisions. |
| SARSA | Uses a similar Q table. Its target contains the Q value of the action actually selected next. We chose Q-learning because we want to learn the value of the best estimated action while exploratory moves are being made. |
| Monte Carlo learning | Can update a move's value using the total reward observed after an episode ends. Episodes can last up to 4,000 turns, so we chose to update when the same agent next makes a decision. |
| Deep Q-Network (DQN) | Estimates values with a neural network instead of a table. It could be considered for raw boards or larger observations. The current state summary fits in a table, where each update can be inspected directly. |

Because the full board and other agents' decisions do not fit in the state key, the same observation can lead to different results. We therefore measure training by comparing performance on new boards with an untrained initial policy.

## 18. Move, turn, and episode flow

A **decision** is one agent choosing an action and receiving its result. A **turn** covers all three agents using their consecutive decisions in order. An **episode** starts with a fresh board and ends when the green food runs out or 4,000 full turns pass.

`Simulation.step()` executes one decision. The interface can show each step separately.

1. Prepare an observation and state values for the active agent, including its remaining decisions.
2. If that agent has a pending previous move, update it using the Q values from this observation.
3. The agent selects a new action using its Q values and ε. `move()` applies the action and returns the individual reward. The decision uses one slot and is held for learning.
4. End the episode if no green food remains, or if agent 3's final decision completes 4,000 full turns. Update every pending move with a future Q value of zero, save the result, and start a new board with agent 1.
5. If the episode continues, the same agent acts while it has decisions remaining. When its allowance is spent, the next agent takes over.

Each decision prepares a fresh observation. Agent 2 sees the board after agent 1 has used all its decisions. Agent 3 sees the board after both earlier agents have done so.

During an episode, `step_count` counts completed full turns. The result's `steps` field also counts the final partial turn in which the last green was collected. For example, an episode that ends on agent 2's move in its first turn is recorded as taking 1 turn.

### Follow two decisions by the same agent

Suppose agent 1 is at `(4, 5)`, has speed 2, and the final green is at `(5, 4)`. It can reach the food by choosing right and then up.

- On the first decision, agent 1 moves right to `(5, 5)` and receives 0.
- With one decision left, it observes the new board and updates the previous right move using the Q values for this state.
- It chooses up, reaches `(5, 4)`, receives +1, and ends the episode.
- The terminal update for up uses a future Q value of zero. If up started at 0.05, its new Q value is `0.05 + 0.2 × (1 − 0.05) = 0.24`.
- The episode result is added to history and the next board starts with agent 1.

Starting a new episode does not reset the Q table. **The board changes; learned experience remains.**

## 19. How is learning saved to JSON?

**JSON** is a common text format for storing dictionaries and lists. Python objects disappear when the application closes; writing them to a file lets us restore them on the next run.

`LearningMemory.save()` stores:

| Field | Contents |
|---|---|
| `version` | File format version |
| `episodes` | Number of completed episodes |
| `q_values` | State-action values for the agents |
| `visits` | State-action update counts |
| `history` | Parameters and results for all completed episodes |

A history row contains the date, episode number, food count per color, starting seed, selected distance metric, α/γ/ε values, number of turns, total green/red/reward, and each agent's individual speed and score. History stores only results marked with `turn_order: "sequential"`. Q values, visit counts, and the total learning counter that determines the exploration rate are retained independently of the number of history records.

The `ACTIONS` order determines which action each Q-list index represents. The `/api/memory` view also returns action names and the current coefficients.

### Why not save the entire board at every step?

Current Q values and visit counts are enough to continue learning. Saving all positions at every step would create much more data. Therefore:

- The Q table is updated in memory when a transition for an agent's previous move is completed.
- The interface shows updates from the latest step.
- Results for all completed episodes are stored in history.
- Previous Q values and board snapshots for every step are not archived separately.

### How do we prevent a partial file write?

The application writes `learning_memory_v4.json.tmp` before replacing the main file.

```python
temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
temporary.replace(path)
```

`indent=2` makes the file readable with lines and indentation. `ensure_ascii=False` keeps characters readable. Using a temporary file reduces the risk that the main file will be left partially written.

Data is saved at the end of an episode, when paused, when the new episode button is used, and when exiting with Ctrl+C. If the process is forcibly stopped, updates since the last save may be lost. This is a consequence of not writing to disk at every step.

`LearningMemory.load()` reads the file if it exists; otherwise, it starts with empty memory. During loading, history records that are not from sequential runs are filtered out, and the cleaned data is saved. If the file is corrupted or its version is unsupported, loading raises an error instead of silently resetting learning.

The expanded state key includes the remaining decisions and is stored in `learning_memory_v4.json`. When this file is absent, training begins with an empty Q table and episode history. Earlier fixed-direction runs used `learning_memory_v3.json`. When the application restarts or the user manually starts a new episode, the simulation creates a fresh board using the saved Q values and clears pending decisions.

### How to interpret the seed correctly

A seed is the **starting** value for a random number generator. If automatic episodes run one after another in a single `Simulation` instance, the generator continues from where it left off. Therefore, seeing the same starting seed in the history does not mean automatic episodes used the same board.

For a controlled comparison, create a new `Simulation` with the same seed for each episode to reproduce the same starting board, speeds, and metric. The learning memory can be kept separate and shared across episodes. In the application's default random startup, the seed field is `null`, which HTML displays as “Random.”

## 20. How do Python and HTML communicate?

A browser cannot call a Python function directly. `app.py` starts a small **HTTP server** at `127.0.0.1`, which points to this computer. HTTP is the communication method a browser uses to send a request to an address and receive a response.

An **API** is a set of addresses and data rules that HTML can use:

| Address | Method | Function |
|---|---|---|
| `/` | GET | Returns the HTML page |
| `/api/state` | GET | Returns the current board and statistics |
| `/api/tick` | POST | If running, executes 1–20 single-cell decisions in order |
| `/api/control` | POST | Starts, pauses, or applies settings and creates a new episode |
| `/api/memory` | GET | Returns current Q memory, visits, and history as JSON |

GET requests data; POST requests an operation here. For example, HTML sends:

```json
{"action": "new_episode", "food_pairs": 40}
```

`Handler.control()` in `app.py` validates this, saves the current learning data, changes the food count, and calls `new_episode()`. The response contains the new board.

`integer()` checks integer values and bounds in one place. `12.5`, `true`, `"12"`, 0, and 376 are not accepted as food counts. The HTML number field prevents invalid input, and the server checks the same limits again because an API request can also come from outside the browser interface.

`main()` is the application entry point: it reads command-line settings, loads the JSON memory, creates the simulation and server, and opens the browser. On Ctrl+C, it saves memory and closes the server.

## 21. What does each part of the HTML code do?

`index.html` has three parts:

- **HTML:** The structure of buttons, fields, tables, and the drawing area.
- **CSS:** Colors, sizes, columns, and support for narrow screens.
- **JavaScript:** Server communication, drawing, and updating values on screen.

### `request()`

Sends an HTTP request with `fetch()` and reads the response as JSON. If the server reports an error, it creates an error to show to the user.

### `update()`

Adds requests to a Promise chain. A **Promise** represents the result of an operation that will finish later. We use the chain to prevent starting the next request before the current response has been processed.

This order matters: the response to an old step request must not arrive after a new episode request and redraw the old board. Refresh and control requests share the same queue.

### `control()`

Temporarily disables buttons while a control request is running, then enables them again when it finishes. A new-episode request sends the draft food count from the input field.

### `render()`

Converts scores and board state from the server into text and a table. It displays completed turns, the next agent and its step number, and the old and new Q values for the latest update.

The training history is rebuilt when a result is added. Each row contains parameters and the individual reward and speed for all three agents. The **Ending turn** column immediately beside the episode number shows the result's `steps` field; this includes the final partial turn. Total score is the sum of all agents' rewards.

If there are at least 20 completed episodes with the same food count and sequential order, the average total reward of the first and last 10 episodes is shown. This uses records whose food count matches the current setting and whose `turn_order` field is `sequential`. This small summary is not a substitute for a controlled scientific experiment.

### `draw()` and Canvas

**Canvas** is an HTML area where we draw with JavaScript. Its internal resolution is 600 × 600. Since the board is 50 × 50, each cell is `600 / 50 = 12` pixels wide.

We find the center of a cell with:

```javascript
const x = (agent.x + 0.5) * cell;
const y = (agent.y + 0.5) * cell;
```

`0.5` moves the point from the cell's upper-left corner to its center. Green food is drawn as circles, red food as squares, and agents as numbered colored circles. Dashed lines show the single nearest-opponent coordinate received from Python.

### Training speed and agent speed are different

The browser attempts to refresh about every 100 milliseconds. The slider controls the number of single-cell decisions per request. At 1, the browser shows each decision. At higher values up to 20, it shows the board after the last decision in the batch. The simulation checks for remaining green food after every decision. The browser waits for the current request to finish before sending another.

Agent speed is the number of consecutive decisions it gets each turn. The slider only changes how often those decisions are drawn. Training speed depends on computation time and the browser timer. Closing the browser tab stops requests to advance the simulation.

## 22. How do we evaluate learning performance?

**What is it?** Evaluation examines agent behavior using measurable results. Growth in the Q table or the number of updates alone does not show that a better policy has been learned.

**What does it do?** It helps us understand which behaviors changed between episodes and how those changes affected rewards. Because agents compete over shared food, we should examine both total and individual scores.

**How is it used in this project?** The interface shows completed episode results in a history table. The comparison uses these measures:

| Measure | Interpretation |
|---|---|
| Green collected | Shows access to target food |
| Red collected | Shows interaction with food agents should avoid |
| Total reward | Combined result of collecting green and red food |
| Turns used | Shows how long it took to reach the result, in turns |
| Individual agent rewards | Shows how competition affected each agent |
| All green collected | Shows whether the episode reached its goal |

If there are at least 20 completed episodes with the same food count and sequential order, the average total reward of the first and last 10 episodes is compared. Episodes with different food counts are not included in the same comparison. The history contains only sequential-run results.

Random placement, speeds, and the decreasing exploration rate also affect results. The history shows progress over a run under those conditions.

### Historical results with fixed-direction moves

In one run with the former fixed-direction movement, 40 items of each color, and a starting seed of 42, average net reward rose from 29.8 in the first 10 episodes to 36.6 in episodes 51–60. Average red items collected fell from 10.2 to 3.4, and all 40 green items were collected in every episode of both groups.

A separate controlled trial also used fixed-direction movement, plus an earlier target rule and stronger starting Q values. We trained on boards with 40 food items of each color. Training episode seeds were 0–59 and test-board seeds were 100–111. Each policy was evaluated from the same starting boards with fixed Q values and 5% exploration. The untrained policy used the previous green bonus and red penalty in its initial Q values.

| Prior training episodes | Average green | Average red | Average net reward | Average turns | Boards where all green was collected |
|---:|---:|---:|---:|---:|---:|
| 0 | 36.25 | 1.92 | 34.33 | 1,171.58 | 9/12 |
| 20 | 39.67 | 2.75 | 36.92 | 650.00 | 11/12 |
| 60 | 40.00 | 1.67 | 38.33 | 678.00 | 12/12 |

In this test, 60 episodes of training increased average net reward by 4 points and collected all green food on all 12 boards. The 20-episode policy took less time on average and collected more red food. These results apply to the earlier movement and learning setup, this food density, and these 12 boards.

## 23. Limitations and design decisions

- Q-learning is the only learning method; there is no route-planning comparison or neural network.
- α and γ are fixed. ε decreases with the episode count. We do not add dozens of user settings.
- Food is distributed randomly; the agents do not assume a hidden placement pattern.
- The state table does not include the entire board; we accept some information loss to keep memory small.
- Euclidean distance is used only to measure the nearest opponent; diagonal movement is never allowed.
- The 4,000-turn limit is an implementation decision that prevents an episode from continuing forever; it is not specified by the assignment.
- A decision moves at most one cell. Attempting to cross a board edge uses a decision and leaves the agent in place. Red food is collected on contact and gives a −1 reward.
- Agents are allowed to occupy the same cell. The assignment only specifies the outcome of food competition.
- The fixed 1 → 2 → 3 order can give the agent that moves first an advantage when several agents can reach the same food.
- Memory persists, but the exact board state is not saved. The application creates a new board when restarted.

## 24. Component flow and presentation summary

`ACTIONS`, `DELTAS`, `Agent`, and `Observation` in `simulation.py` form the basis of the environment. `new_episode()` creates the board; `observation_for()` prepares an observation; `project()` calculates a candidate move; and `move()` applies the real move. `state_values()`, `choose_action()`, and `LearningMemory.learn()` form the learning sequence. `step()` combines these pieces into the sequential move flow.

`main()` and `make_handler()` in `app.py` prepare the server; `state()`, `do_POST()`, and `control()` connect the interface to the simulation. In `index.html`, `request()`, `update()`, `control()`, `render()`, and `draw()` handle communication, user controls, and drawing.

You can follow the sequence from an on-screen button to a Q update:

```text
HTML button / timer
    → HTTP request
    → app.py validation
    → Simulation.step()
    → active agent observes the board → update Q for its previous move
    → one action → individual reward → save decision for the next Q update
    → check whether green food is gone / turn-limit check
    → continue with this agent if it has decisions left, otherwise advance
    → if episode ended, update pending moves, save history and JSON
    → HTTP response
    → update HTML text and redraw the board
```

During the demo, watch a speed-2 or speed-3 agent make consecutive decisions. The Q panel shows the previous decision's reward and the future Q value calculated from the new observation. After the last decision of its turn, the agent uses its next observation after the other agents have acted. When the final green is collected, pending moves are updated with a future Q value of zero.
