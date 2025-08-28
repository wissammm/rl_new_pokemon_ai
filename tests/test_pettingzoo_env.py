from pkmn_rl_arena import ROM_PATH,BIOS_PATH,MAP_PATH
from pkmn_rl_arena.env.battle_core import BattleCore
from pkmn_rl_arena.env.arena import Arena

import unittest

class TestArena:
    def setUp(self):
        core = BattleCore(ROM_PATH,BIOS_PATH,MAP_PATH)
        self.arena = Arena(core)

    def tearDown(self):
        self.arena.close()

    def test_step(self):
        self.arena.reset(seed=42)
        for agent in self.arena.battle_state.get_required_agents():
            observation, reward, termination, truncation, info = self.arena.last()

            if termination or truncation:
                action = None
            else:
                # insert neural network here to choose action from observation space
                #
                # until then here is a dummy fctn
                action = self.arena.action_space(agent).sample()

            self.arena.step(action)

    def test_reset(self):
        self.arena.reset(seed=42)
        for agent in self.arena.battle_state.get_required_agents():
            observation, reward, termination, truncation, info = self.arena.last()

            if termination or truncation:
                action = None
            else:
                # insert neural network here to choose action from observation space
                #
                # until then here is a dummy fctn
                action = self.arena.action_space(agent).sample()

        self.arena.step(action)
        self.arena.reset()




            

if __name__ == "__main__":
    suite = unittest.TestSuite()
    
