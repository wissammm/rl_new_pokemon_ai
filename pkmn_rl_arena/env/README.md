# Pkmn RL Arena

This sub pkg is the PettingZoo environment to help our RL agents to learn.

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
| 10 | ABILITY                                  | 
| 11 | ABILITY(placeholder)                     | 
| 12 | SPECIE_1 (deduced from SPECIES attribute)| 
| 13 | SPECIE_2 (deduced from SPECIES attribute)| 
|    | STATUS                                   | 
| 14 |   HP                                     | 
| 15 |   LEVEL                                  | 
| 16 |   FRIENDSHIP                             | 
| 17 |   MAX_HP                                 | 
| 18 |   HELD_ITEM                              | 
| 19 |   PP_BONUSES                             |
| 20 |   PERSONALITY                            | 
| 21 |   STATUS_1                               | 
| 22 |   STATUS_2                               | 
| 23 |   STATUS_3                               | 
|    | MOVE_1                                   |
| 24 |   ID                                     | 
| 25 |   PP                                     | 
|    | MOVE_2                                   |
| 26 |   ID                                     | 
| 27 |   PP                                     | 
|    | MOVE_3                                   |
| 28 |   ID                                     | 
| 29 |   PP                                     | 
|    | MOVE_4                                   |
| 30 |   ID                                     | 
| 31 |   PP                                     | 

                          



                          
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
