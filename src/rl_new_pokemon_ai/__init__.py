import os
from pathlib import Path
from utils.logging import logger # logger to use to generate logging
from typing import Dict

BASE_DIR = Path(os.path.abspath(__file__))
PATHS: Dict[str, Path] = {
    "ROM_PATH": Path(BASE_DIR, "../pokeemerald_ai_rl/pokeemerald_modern.elf"),
    "BIOS_PATH": Path(BASE_DIR, "../rustboyadvance-ng-for-rl/gba_bios.bin"),
    "MAP_PATH": Path(BASE_DIR, "../pokeemerald_ai_rl/pokeemerald_modern.map"),
    "POKEMON_CSV_PATH": Path(BASE_DIR, "../data/csv_data/pokemon_data.csv"),
    "SAVE_PATH": Path(BASE_DIR, "../savestate"),
    "PKMN_MOVES_PATH": Path(BASE_DIR / Path("../data/csv_data/moves_data.csv")),
}
