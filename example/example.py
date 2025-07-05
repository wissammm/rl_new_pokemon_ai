import random
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rustboyadvance_py
import utils.parser
import utils.pokemon_data
import time
import pandas as pd

ROM_PATH = "/home/wboussella/Documents/rl_new_pokemon_ai/rl_new_pokemon_ai/pokeemerald_ai_rl/pokeemerald_modern.elf"
BIOS_PATH = "/home/wboussella/Documents/rl_new_pokemon_ai/rl_new_pokemon_ai/rustboyadvance-ng-for-rl/gba_bios.bin"
STEPS = 32000



parser = utils.parser.MapAnalyzer('/home/wboussella/Documents/rl_new_pokemon_ai/rl_new_pokemon_ai/pokeemerald_ai_rl/pokeemerald_modern.map')

gba = rustboyadvance_py.RustGba()
gba.load(BIOS_PATH,ROM_PATH )

addrs = {
    'testBuffer': int(parser.get_address('testBuffer'), 16),
    'stopHandleTurn': int(parser.get_address('stopHandleTurn'), 16),
    'actionDone': int(parser.get_address('actionDone'), 16),
    'monDataPlayer': int(parser.get_address('monDataPlayer'), 16),
    'monDataEnemy': int(parser.get_address('monDataEnemy'), 16),
}



name_by_addr = {v: k for k, v in addrs.items()}

gba.add_stop_addr(addrs['stopHandleTurn'],1,True,'stopHandleTurn')
steps_does = 0
cpt = 0
last_time = time.time()

while(1):
    steps_does = gba.run_to_next_stop(STEPS)
    if cpt%10000 == 0:
        print(f"Steps done: {steps_does}")
    if steps_does == -1:
        now = time.time()                         
        print(f"Time since last event: {now - last_time:.4f} seconds")
        last_time = now
        print("Enemy data:")
        print(utils.pokemon_data.to_pandas_mon_dump_data(gba.read_u32_list(addrs['monDataEnemy'],36)))
        print("Player data:")
        print(utils.pokemon_data.to_pandas_mon_dump_data(gba.read_u32_list(addrs['monDataPlayer'],36)))
        gba.write_u16(addrs['actionDone'],random.randint(0, 3))
        gba.write_u16(addrs['stopHandleTurn'],0)
        
    cpt+= 1

print("ok")