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

print("stop handle turn adress = ", parser.get_address('stopHandleTurn'))
gba = rustboyadvance_py.RustGba()
gba.load(BIOS_PATH,ROM_PATH )

addrs = {
    'stopHandleTurn': int(parser.get_address('stopHandleTurn'), 16),
    'stopHandleTurnCreateTeam': int(parser.get_address('stopHandleTurnCreateTeam'), 16),
    'actionDone': int(parser.get_address('actionDone'), 16),
    'monDataPlayer': int(parser.get_address('monDataPlayer'), 16),
    'monDataEnemy': int(parser.get_address('monDataEnemy'), 16),
}



name_by_addr = {v: k for k, v in addrs.items()}

gba.add_stop_addr(addrs['stopHandleTurn'],1,True,'stopHandleTurn',3)
gba.add_stop_addr(addrs['stopHandleTurnCreateTeam'],1,True,'stopHandleTurnCreateTeam',13)
id = 0

# get the adress of listTestBuffer
listTestBuffer_addr = int(parser.get_address('listTestBuffer'), 16)
print(parser.get_address('stopTestReadWrite'))


# get the adress of testBuffer
testBuffer_addr = int(parser.get_address('testBuffer'), 16)
print("testBuffer address: ", hex(testBuffer_addr))

# get the adress of stopHandleTurnCreateTeam
stopHandleTurnCreateTeam_addr = int(parser.get_address('stopHandleTurnCreateTeam'), 16)
print("stopHandleTurnCreateTeam address: ", hex(stopHandleTurnCreateTeam_addr))

cpt = 0
last_time = time.time()
while(1):
    id = gba.run_to_next_stop(STEPS)
    if cpt %10000 == 0:
        print(f"Step {id}")
    if id == 13:
        print("cpt = ", cpt)
        print("stop for id ", id)
        now = time.time()                         
        print(f"Time since last event: {now - last_time:.4f} seconds")
        last_time = now
        print("Enemy data:")
        # print(utils.pokemon_data.to_pandas_mon_dump_data(gba.read_u32_list(addrs['monDataPlayer'],36))[["current_hp"]])
        # print("Player data:")
        # print(utils.pokemon_data.to_pandas_mon_dump_data(gba.read_u32_list(addrs['monDataEnemy'],36))[["hp"]])
        gba.write_u16(addrs['actionDone'],random.randint(0, 3))
        gba.write_u16(addrs['stopHandleTurn'],0)
        
    cpt+= 1

print("ok")