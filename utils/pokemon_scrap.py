import pandas as pd
import re

def parse_pokemon_scrap(path):
    data = []
    with open(path) as f:
        lines = f.readlines()

    current = {}
    moves = []
    for line in lines:
        line = line.strip()
        if line.startswith("speciesName:"):
            if current:
                current['moves'] = moves
                data.append(current)
                current = {}
                moves = []
            current['speciesName'] = line.split(":", 1)[1].strip()
        elif line.startswith("id:"):
            current['id'] = int(line.split(":", 1)[1].strip())
        elif line.startswith("baseHP:"):
            current['baseHP'] = int(line.split(":", 1)[1].strip())
        elif line.startswith("baseAttack:"):
            current['baseAttack'] = int(line.split(":", 1)[1].strip())
        elif line.startswith("baseDefense:"):
            current['baseDefense'] = int(line.split(":", 1)[1].strip())
        elif line.startswith("baseSpeed:"):
            current['baseSpeed'] = int(line.split(":", 1)[1].strip())
        elif line.startswith("baseSpAttack:"):
            current['baseSpAttack'] = int(line.split(":", 1)[1].strip())
        elif line.startswith("baseSpDefense:"):
            current['baseSpDefense'] = int(line.split(":", 1)[1].strip())
        elif line.startswith("type0:"):
            current['type0'] = int(line.split(":", 1)[1].strip())
        elif line.startswith("type1:"):
            current['type1'] = int(line.split(":", 1)[1].strip())
        elif re.search(r"move\d+:\s*(\d+)", line):
            m = re.search(r"move\d+:\s*(\d+)", line)
            move_id = int(m.group(1))
            moves.append(move_id)
    if current:
        current['moves'] = moves
        data.append(current)

    df = pd.DataFrame(data)
    return df

df = parse_pokemon_scrap("data/data_scrap_from_mgba")
print(df.head(20))