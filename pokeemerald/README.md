# Pokémon Emerald

This is a decompilation of Pokémon Emerald.

It builds the following ROM:

* [**pokeemerald.gba**](https://datomatic.no-intro.org/index.php?page=show_record&s=23&n=1961) `sha1: f3ae088181bf583e55daf962a92bb46f4f1d07b7`

To set up the repository, see [INSTALL.md](INSTALL.md).

For contacts and other pret projects, see [pret.github.io](https://pret.github.io/).

# Tasks 
## Create Env 
### Use Porymap to optimize tests, and to have a fast env
Branch remove_title_screen already allow to have a fast env but can be optimized with a batlle a the beginning in the truck 

Difficulty : Easy 

### Function to store and load Actions and Env
Want to have an array wich load and stores Actions, and Env into a buffer readable in a certain address from a python program

Difficulty : Hard

### Replace battle scripts by the response the python algo
Choose a Pokemon or an attack, something legal, and answer into a buffer which communicate with pokeemerald 

Difficulty : Hard

### Create a Coherant pokemon with a function
Create a Pokemon which is legal (like Pikachu can't surf (bad example, in the lore, he can)) 

Difficulty : Medium 

## Training AI
When the env is complete
### Small model using RL pytorch
Small model which train to be better in Pokemon, maybe only with one agent against Pokemon AI 

Difficulty : Low (maybe medium)