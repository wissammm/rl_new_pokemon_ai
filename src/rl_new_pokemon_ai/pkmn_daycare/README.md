# Pkmn Daycare

This sub pkg is the PettingZoo environment for our prgrm to learn.

# Env
defined by 2 players :
1. Player
2. Ennemy

Each player has a team containing up to 6 pokemons.
Each pokemon is defined described by 35 values 

Fonction reset core.py
regarde savestate_manager
data_mon_dump.c pour descripteur de pkmn
Save state invalide nsi elle est faite prieure à une recompilation.
important files : battle.h
modifier list tests à lancer dans env/test.py

# PKMN DESCRITPION
Pokemons are described in 35 values by the game : 
|IDX | value                                    |
|----|------------------------------------------|
| 0  | PKMN_MOVES                               | 
| 1  | IS_ACTIVE                                | 
| 2  | SPECIES                                  | 
| 3  | STATS :                                  |
| 4  |   ATK                                    | 
| 5  |   DEF                                    | 
| 6  |   SPEED                                  | 
| 7  |   SPATK                                  | 
| 8  |   SPDEF                                  | 
|    | IV                                       |
| 9  |   HP                                     | 
| 10 |   ATK                                    | 
| 11 |   DEF                                    | 
| 12 |   SPEED                                  | 
| 13 |   SPATK                                  | 
| 14 |   SPDEF                                  | 
| 15 |   SPDEF                                  | 
| 16 | ABILITY                                  | 
| 17 | ABILITY(placeholder)                     | 
| 18 | SPECIE_1 (deduced from SPECIES attribute)| 
| 19 | SPECIE_2 (deduced from SPECIES attribute)| 
|    | STATUS:                                  | 
| 20 |   HP                                     | 
| 21 |   LEVEL                                  | 
| 22 |   FRIENDSHIP                             | 
| 23 |   MAX_HP                                 | 
| 24 |   HELD_ITEM                              | 
| 25 |   PP_BONUSES                             |
| 26 |   PERSONALITY                            | 
| 27 |   STATUS_1                               | 
| 27 |   STATUS_2                               | 
| 27 |   STATUS_3                               | 
| 28 | MOVES_1_ID                               | 
| 29 | MOVES_1_PP                               | 
| 30 | MOVES_2_ID                               | 
| 31 | MOVES_2_PP                               | 
| 32 | MOVES_3_ID                               | 
| 33 | MOVES_3_PP                               | 
| 34 | MOVES_4_ID                               | 
| 35 | MOVES_4_PP                               | 

                          










                          
Of these we remove SPECIES & IV's and we add moves data : 
|IDX | value                                    |
|----|------------------------------------------|
| 0  | pkmn_ID                                  |
| 1  | IS_ACTIVE                                |
|    | STATS :                                  |
| 2  |   ATK                                    |
| 3  |   DEF                                    |
| 4  |   SPEED                                  |
| 5  |   SPATK                                  |
| 6  |   SPDEF                                  |
| 7  | ABILITY                                  |
| 8  | ABILITY(placeholder)                     |
| 9  | SPECIE_1                                 |
| 10 | SPECIE_2                                 |
|    | STATUS:                                  |
| 11 |   HP                                     |
| 12 |   LEVEL                                  |
| 13 |   FRIENDSHIP                             |
| 14 |   MAX_HP                                 |
| 15 |   HELD_ITEM                              |
| 16 |   PP_BONUSES                             |
| 17 |   PERSONALITY                            |
| 18 |   STATUS                                 |
|    | MOVE_1                                   |
|    | MOVE_1_PP                                   |
|    | MOVE_2                                   |
|    | MOVE_2_PP                                   |
|    | MOVE_3                                   |
|    | MOVE_3_PP                                   |
|    | MOVE_4                                   |
|    | MOVE_4_PP                                   |
| 19 |   id                                     |
| 20 |   MAX_PP                                 |
| 21 |   CURR_PP                                |
| 22 |   effect                                 |
| 23 |   power                                  |
| 24 |   type                                   |
| 25 |   accuracy                               |
| 26 |   curr_pp                                |
| 27 |   max_pp                                 |
| 28 |   priority                               |
| 29 |   secondaryeffectchance                  |
| 30 |   target                                 |
| 31 |   flags                                  |
|    | MOVE_2                                   |
| 32 |   id                                     |
| 33 |   MAX_PP                                 |
| 34 |   CURR_PP                                |
| 35 |   effect                                 |
| 36 |   power                                  |
| 37 |   type                                   |
| 38 |   accuracy                               |
| 39 |   curr_pp                                |
| 40 |   max_pp                                 |
| 41 |   priority                               |
| 42 |   secondaryeffectchance                  |
| 43 |   target                                 |
| 44 |   flags                                  |
|    | MOVE_3                                   |
| 45 |   id                                     |
| 46 |   MAX_PP                                 |
| 47 |   CURR_PP                                |
| 48 |   effect                                 |
| 49 |   power                                  |
| 50 |   type                                   |
| 51 |   accuracy                               |
| 52 |   curr_pp                                |
| 53 |   max_pp                                 |
| 54 |   priority                               |
| 55 |   secondaryeffectchance                  |
| 56 |   target                                 |
| 57 |   flags                                  |
|    | MOVE_4                                   |
| 58 |   id                                     |
| 59 |   MAX_PP                                 |
| 60 |   CURR_PP                                |
| 61 |   effect                                 |
| 62 |   power                                  |
| 63 |   type                                   |
| 64 |   accuracy                               |
| 65 |   curr_pp                                |
| 66 |   max_pp                                 |
| 67 |   priority                               |
| 68 |   secondaryeffectchance                  |
| 69 |   target                                 |
| 70 |   flags                                  |
