from env.core import BattleCore
import unittest

from rl_new_pokemon_ai import PATHS
from rl_new_pokemon_ai.env.core import BattleCore
from rl_new_pokemon_ai.pkmn_daycare.PettingZooEnv import PkmnDayCare

class TestPkmnDayCare:
    def setUp(self):
        core = BattleCore(PATHS["ROM"],PATHS["BIOS"],PATHS["MAPS"])
        self.daycare = PkmnDayCare(core)

    def tearDown(self):
        self.daycare.close()

    def test_step(self):
        self.daycare.reset(seed=42)
        for agent in self.daycare.turn_manager.get_required_agents():
            observation, reward, termination, truncation, info = self.daycare.last()

            if termination or truncation:
                action = None
            else:
                # insert neural network here to choose action from observation space
                #
                # until then here is a dummy fctn
                action = self.daycare.action_space(agent).sample()

            self.daycare.step(action)

    def test_reset(self):
        self.daycare.reset(seed=42)
        for agent in self.daycare.turn_manager.get_required_agents():
            observation, reward, termination, truncation, info = self.daycare.last()

            if termination or truncation:
                action = None
            else:
                # insert neural network here to choose action from observation space
                #
                # until then here is a dummy fctn
                action = self.daycare.action_space(agent).sample()

        self.daycare.step(action)
        self.daycare.reset()




            

if __name__ == "__main__":
    suite = unittest.TestSuite()
    
