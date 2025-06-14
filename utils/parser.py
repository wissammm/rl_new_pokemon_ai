import re

class MapAnalyzer:
    def __init__(self, map_file):
        self.symbols = {}
        self._parse(map_file)
    
    def _parse(self, map_file):
        pattern = re.compile(r'^\s*(0x[0-9a-fA-F]+)\s+(\S+)')
        
        with open(map_file, 'r') as f:
            for line in f:
                match = pattern.match(line)
                if match:
                    addr, symbol = match.groups()
                    self.symbols[symbol] = addr
    
    def get_address(self, symbol):
        return self.symbols.get(symbol)
    
    
# analyzer = MapAnalyzer('/home/wboussella/Documents/rl_new_pokemon_ai/rl_new_pokemon_ai/pokeemerald_ai_rl/pokeemerald_modern.map')
# print(f"actionDone: {analyzer.get_address('actionDone')}")
# # print(f"Estimated size: {analyzer.get_size('gBattleMonForms')} bytes")
# print("ok")