import rustboyadvance_py

ROM_PATH = "/home/wboussella/Documents/rl_new_pokemon_ai/rl_new_pokemon_ai/pokeemerald_ai_rl/pokeemerald_modern.gba"
BIOS_PATH = "/home/wboussella/Documents/rl_new_pokemon_ai/rl_new_pokemon_ai/rustboyadvance-ng-for-rl/gba_bios.bin"

gba = rustboyadvance_py.RustGba()
gba.load(BIOS_PATH,ROM_PATH )
print("ok")