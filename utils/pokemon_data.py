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