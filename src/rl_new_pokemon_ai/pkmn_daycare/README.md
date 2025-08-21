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
| 1  | PKMN_MOVES                               | 
| 2  | IS_ACTIVE                                | 
| 3  | SPECIES                                  | 
| 4  | STATS                                    |
| 5  |   ATK                                    | 
| 6  |   DEF                                    | 
| 7  |   SPEED                                  | 
| 8  |   SPATK                                  | 
| 9  |   SPDEF                                  | 
|    | IV                                       |
| 10  |   HP                                     | 
| 11 |   ATK                                    | 
| 12 |   DEF                                    | 
| 13 |   SPEED                                  | 
| 14 |   SPATK                                  | 
| 15 |   SPDEF                                  | 
| 16 |   SPDEF                                  | 
| 17 | ABILITY                                  | 
| 18 | ABILITY(placeholder)                     | 
| 19 | SPECIE_1 (deduced from SPECIES attribute)| 
| 20 | SPECIE_2 (deduced from SPECIES attribute)| 
|    | STATUS                                   | 
| 21 |   HP                                     | 
| 22 |   LEVEL                                  | 
| 23 |   FRIENDSHIP                             | 
| 24 |   MAX_HP                                 | 
| 25 |   HELD_ITEM                              | 
| 26 |   PP_BONUSES                             |
| 27 |   PERSONALITY                            | 
| 28 |   STATUS_1                               | 
| 29 |   STATUS_2                               | 
| 30 |   STATUS_3                               | 
|    | MOVE_1                                   |
| 31 |   ID                                     | 
| 32 |   PP                                     | 
|    | MOVE_2                                   |
| 33 |   ID                                     | 
| 34 |   PP                                     | 
|    | MOVE_3                                   |
| 35 |   ID                                     | 
| 36 |   PP                                     | 
|    | MOVE_4                                   |
| 37 |   ID                                     | 
| 38 |   PP                                     | 

                          










                          
Of these we remove SPECIES & IV's and we add moves data : 
|IDX | value                                    |
|----|------------------------------------------|
| 1  | pkmn_ID                                  |
| 2  | IS_ACTIVE                                |
|    | STATS :                                  |
| 3  |   ATK                                    |
| 4  |   DEF                                    |
| 5  |   SPEED                                  |
| 6  |   SPATK                                  |
| 7  |   SPDEF                                  |
| 8  | ABILITY                                  |
| 9  | ABILITY(placeholder)                     |
| 10  | SPECIE_1                                 |
| 11 | SPECIE_2                                 |
|    | STATUS:                                  |
| 12 |   HP                                     |
| 13 |   LEVEL                                  |
| 14 |   FRIENDSHIP                             |
| 15 |   MAX_HP                                 |
| 16 |   HELD_ITEM                              |
| 17 |   PP_BONUSES                             |
| 18 |   PERSONALITY                            |
| 19 |   STATUS_1                               | 
| 20 |   STATUS_2                               | 
| 21 |   STATUS_3                               | 
|    | MOVE_1                                   |
| 22 |   id                                     |
| 23 |   MAX_PP                                 |
| 24 |   CURR_PP                                |
| 25 |   effect                                 |
| 26 |   power                                  |
| 27 |   type                                   |
| 28 |   accuracy                               |
| 29 |   curr_pp                                |
| 30 |   max_pp                                 |
| 31 |   priority                               |
| 32 |   secondaryeffectchance                  |
| 33 |   target                                 |
| 34 |   flags                                  |
|    | MOVE_2                                   |
| 35 |   id                                     |
| 36 |   MAX_PP                                 |
| 37 |   CURR_PP                                |
| 38 |   effect                                 |
| 39 |   power                                  |
| 40 |   type                                   |
| 41 |   accuracy                               |
| 42 |   curr_pp                                |
| 43 |   max_pp                                 |
| 44 |   priority                               |
| 45 |   secondaryeffectchance                  |
| 46 |   target                                 |
| 47 |   flags                                  |
|    | MOVE_3                                   |
| 48 |   id                                     |
| 49 |   MAX_PP                                 |
| 50 |   CURR_PP                                |
| 51 |   effect                                 |
| 52 |   power                                  |
| 53 |   type                                   |
| 54 |   accuracy                               |
| 55 |   curr_pp                                |
| 56 |   max_pp                                 |
| 57 |   priority                               |
| 58 |   secondaryeffectchance                  |
| 59 |   target                                 |
| 60 |   flags                                  |
|    | MOVE_4                                   |
| 61 |   id                                     |
| 62 |   MAX_PP                                 |
| 63 |   CURR_PP                                |
| 64 |   effect                                 |
| 65 |   power                                  |
| 66 |   type                                   |
| 67 |   accuracy                               |
| 68 |   curr_pp                                |
| 69 |   max_pp                                 |
| 70 |   priority                               |
| 71 |   secondaryeffectchance                  |
| 72 |   target                                 |
| 73 |   flags                                  |
