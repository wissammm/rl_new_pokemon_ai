import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rustboyadvance_py
import utils.parser

ROM_PATH = "/home/wboussella/Documents/rl_new_pokemon_ai/rl_new_pokemon_ai/pokeemerald_ai_rl/pokeemerald_modern.elf"
BIOS_PATH = "/home/wboussella/Documents/rl_new_pokemon_ai/rl_new_pokemon_ai/rustboyadvance-ng-for-rl/gba_bios.bin"
STEPS = 32000

parser = utils.parser.MapAnalyzer('/home/wboussella/Documents/rl_new_pokemon_ai/rl_new_pokemon_ai/pokeemerald_ai_rl/pokeemerald_modern.map')

gba = rustboyadvance_py.RustGba()
gba.load(BIOS_PATH,ROM_PATH )
addrs = []
addrs.append(int(parser.get_address('testBuffer'),16))
print(f"testBuffer address: {addrs[0]}")
for addr in addrs:
    gba.add_stop_addr(addr, 1, True, "testBuffer")

steps_does = 0
cpt = 0
while steps_does != -1:
    steps_does = gba.run_to_next_stop(STEPS)
    if cpt%1000 == 0:
        print(f"Steps done: {steps_does}")
    cpt+= 1

print("ok")