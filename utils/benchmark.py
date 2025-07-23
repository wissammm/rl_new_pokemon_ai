import sys
import os
import random
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import PokemonRLCore, TurnType
import rustboyadvance_py
import utils.parser
import utils.pokemon_data

STEPS = 50
ROM_PATH = "/home/wboussella/Documents/rl_new_pokemon_ai/rl_new_pokemon_ai/pokeemerald_ai_rl/pokeemerald_modern.elf"
BIOS_PATH = "/home/wboussella/Documents/rl_new_pokemon_ai/rl_new_pokemon_ai/rustboyadvance-ng-for-rl/gba_bios.bin"
MAP_PATH = "/home/wboussella/Documents/rl_new_pokemon_ai/rl_new_pokemon_ai/pokeemerald_ai_rl/pokeemerald_modern.map"
POKEMON_CSV_PATH = "/home/wboussella/Documents/rl_new_pokemon_ai/rl_new_pokemon_ai/data/csv_data/pokemon_data.csv"

class Benchmark:
    def __init__(self):
        self.rl_core = PokemonRLCore(ROM_PATH, BIOS_PATH, MAP_PATH)
        obs = self.rl_core.reset()

    def run(self):
        step_times = []
        last_time = time.time()
        for step in range(STEPS):
            current_turn = self.rl_core.get_current_turn_type()
            required_agents = self.rl_core.get_required_agents()
            
            actions = {}
            for agent in required_agents:
                legal_actions = self.rl_core.action_manager.get_legal_actions(agent)
                if legal_actions:
                    actions[agent] = random.choice(legal_actions)  # Choose a random legal action
                else:
                    print(f"No legal actions available for {agent}")
            
            observations, rewards, done, info = self.rl_core.step(actions)
            
            now = time.time()
            step_time = now - last_time
            step_times.append(step_time)
            last_time = now

            if done:
                print("Episode finished!")
                break

        if step_times:
            avg_time = sum(step_times) / len(step_times)
            print(f"Average step time: {avg_time:.4f} seconds")

if __name__ == "__main__":
    benchmark = Benchmark()
    benchmark.run()