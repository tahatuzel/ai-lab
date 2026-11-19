import unittest
from unittest.mock import patch

from simulation import Agent, Simulation


class LearningTransitionTests(unittest.TestCase):
    def make_simulation(self, greens: set[tuple[int, int]]) -> Simulation:
        simulation = Simulation(seed=42)
        simulation.agents = [Agent(1, (4, 5), 1), Agent(2, (6, 4), 1), Agent(3, (9, 9), 1)]
        simulation.green_foods = greens
        simulation.red_foods = set()
        return simulation

    def test_bootstrap_uses_board_after_other_agents_move(self) -> None:
        simulation = self.make_simulation({(5, 4), (4, 1)})
        agent = simulation.agents[0]
        with patch.object(simulation, "choose_action", side_effect=[0, 2, 4, 4]):
            simulation.step()
            old_key, action, _ = simulation.pending[1]
            early_key, _ = simulation.state_values(agent, simulation.observation_for(agent))
            self.assertEqual(simulation.memory.visits[old_key][action], 0)
            simulation.step()
            simulation.step()
            self.assertEqual(simulation.memory.visits[old_key][action], 0)

            next_key, next_values = simulation.state_values(agent, simulation.observation_for(agent))
            self.assertNotEqual(early_key, next_key)
            next_values[0] = 0.8
            simulation.step()

        self.assertEqual(simulation.memory.visits[old_key][action], 1)
        self.assertEqual(simulation.last_updates[0]["agent"], 1)
        self.assertEqual(simulation.last_updates[0]["future_q"], 0.8)
        self.assertAlmostEqual(simulation.last_updates[0]["target"], 0.72)

    def test_episode_end_learns_all_executed_actions(self) -> None:
        simulation = self.make_simulation({(5, 4)})
        with patch.object(simulation, "choose_action", side_effect=[0, 2]):
            self.assertIsNone(simulation.step())
            summary = simulation.step()

        self.assertEqual([agent["reward"] for agent in summary["agents"]], [0, 1, 0])
        self.assertEqual([(row["agent"], row["future_q"]) for row in simulation.last_updates],
                         [(1, 0.0), (2, 0.0)])
        self.assertEqual(sum(map(sum, simulation.memory.visits.values())), 2)
        self.assertFalse(simulation.pending)
        self.assertEqual(simulation.next_agent_index, 0)

    def test_state_distinguishes_immediate_green_from_approach(self) -> None:
        simulation = self.make_simulation({(5, 5)})
        agent = simulation.agents[0]
        near_key, near_values = simulation.state_values(agent, simulation.observation_for(agent))
        simulation.green_foods = {(6, 5)}
        far_key, far_values = simulation.state_values(agent, simulation.observation_for(agent))

        self.assertIn("|g8|p8|", near_key)
        self.assertIn("|g0|p8|", far_key)
        self.assertGreater(near_values[3], far_values[3])


if __name__ == "__main__":
    unittest.main()
