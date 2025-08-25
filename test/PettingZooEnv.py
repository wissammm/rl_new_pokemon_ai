from env.core import BattleCore
import unittest

from rl_new_pokemon_ai import PATHS
from rl_new_pokemon_ai.env.core import BattleCore
from rl_new_pokemon_ai.pkmn_daycare import PkmnDayCare

class TestPkmnDayCare(unittest.TestCase):
    def setUp(self):
        core = BattleCore(PATHS["ROM"],PATHS["BIOS"],PATHS["MAPS"])
        self.daycare = PkmnDayCare(core)

    def tearDown(self):
        self.daycare.close()

    def test_step(self):
        for agent in self.daycare.turn_manager.get_required_agents():
            observation, reward, termination, truncation, info = self.daycare.last()

            if termination or truncation:
                action = None
            else:
                action = self.daycare.compute_action(agent)

        self.daycare.step(action)

    def test_reset(self):
        for agent in self.daycare.turn_manager.get_required_agents():
            observation, reward, termination, truncation, info = self.daycare.last()

            if termination or truncation:
                action = None
            else:
                action = self.daycare.compute_action(agent)

        self.daycare.step(action)
        self.daycare.reset()
        self.assertEqual()


if __name__ == "__main__":
    suite = unittest.TestSuite()
    
