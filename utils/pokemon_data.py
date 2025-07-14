import pandas as pd

def to_pandas_mon_dump_data(array):
    """Convert Pokemon data array to pandas DataFrame with named columns"""
    data = {
        'isActive': array[0],
        'id': array[1],
        'baseAttack': array[2],
        'baseDefense': array[3],
        'baseSpeed': array[4],
        'baseSpAttack': array[5],
        'baseSpDefense': array[6],
        
        'moves': [array[7], array[8], array[9], array[10]],
        
        'hp_iv': array[11],
        'atk_iv': array[12],
        'def_iv': array[13],
        'speed_iv': array[14],
        'spatk_iv': array[15],
        'spdef_iv': array[16],
        
        'ability_num': array[17],
        'ability': array[18],
        'type0': array[19],  
        'type1': array[20], 
        
        'current_hp': array[21],
        'level': array[22],
        'friendship': array[23],
        'max_hp': array[24],
        'held_item': array[25],
        'pp_bonuses': array[26],
        'personality': array[27],
        'status1': array[28],
        'status2': array[29],
        'status3': array[30],
        
        'move1_pp': array[31],
        'move2_pp': array[32],
        'move3_pp': array[33],
        'move4_pp': array[34]
    }
    
    return pd.DataFrame([data])

def to_pandas_team_dump_data(array):
    """Convert a Pokémon team data array to a pandas DataFrame"""
    team_data = []
    for i in range(6): 
        start = i * 35
        end = start + 35
        mon_data = {
            'isActive': array[start],
            'id': array[start + 1],
            'baseAttack': array[start + 2],
            'baseDefense': array[start + 3],
            'baseSpeed': array[start + 4],
            'baseSpAttack': array[start + 5],
            'baseSpDefense': array[start + 6],
            
            'moves': [array[start + 7], array[start + 8], array[start + 9], array[start + 10]],
            
            'hp_iv': array[start + 11],
            'atk_iv': array[start + 12],
            'def_iv': array[start + 13],
            'speed_iv': array[start + 14],
            'spatk_iv': array[start + 15],
            'spdef_iv': array[start + 16],
            
            'ability_num': array[start + 17],
            'ability': array[start + 18],
            'type0': array[start + 19],  
            'type1': array[start + 20], 
            
            'current_hp': array[start + 21],
            'level': array[start + 22],
            'friendship': array[start + 23],
            'max_hp': array[start + 24],
            'held_item': array[start + 25],
            'pp_bonuses': array[start + 26],
            'personality': array[start + 27],
            'status1': array[start + 28],
            'status2': array[start + 29],
            'status3': array[start + 30],
            
            'move1_pp': array[start + 31],
            'move2_pp': array[start + 32],
            'move3_pp': array[start + 33],
            'move4_pp': array[start + 34]
        }
        team_data.append(mon_data)
    
    return pd.DataFrame(team_data)
