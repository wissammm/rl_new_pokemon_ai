# rl_new_pokemon_ai

Reinforcement learning environment and tools for Pokémon Emerald : 
 - Fork of [rustboyadvance](https://github.com/michelhe/rustboyadvance-ng) a gba emulator written in rust :crab:.
   We added python bindings & a few functions added to help bridge the debugger with `pokemon_ai_for_rl`.
 - PettingZoo environnement for Multi-Agent Reinforcement Learning
 - Quantization
 - Neural Network graph manipulation 
 - Export of the network onto a gba flash card, effectively replacing the AI of the OG game with your AI.

##  Installation 
### Linux 
1. **Clone the repository**
git clone --recursive
2. **Set up a Python virtual environment**
3. **Install Python dependencies**
   ```sh
   pip install -r requirements.txt
   ```

4. **Build and install the rust emulator extension**
    ```
    cd rustboyadvance-ng-for-rl/platform/rustboyadvance-py
    maturin develop --features elf_support --realease
    ```

5. **Compile the rom**

To compile the custom pokeemerald rom, go to see directly the INSTALL.md inside pokeemerald_ai_rl. Replace make modern by 
```bash
make modern DINFO=1 DOBSERVED_DATA=1 DSKIP_TEXT=1 DSKIP_GRAPHICS=1 NO_DEBUG=1 -j
```


## Project structure
```
rl_new_pokemon_ai/
├──  agbcc                              # Library allowing to compile gba game with cc compiler
├──  data                               # data for training # TO BE MOVED
├──  example                            # TO DEFINE / TO ORDER
├── rustboyadvance-ng-for-rl/           # Rust GBA emulator with Python bindings
├── pokeemerald_ai_rl/                  # Custom Pokémon Emerald ROM modified for RL training & build scripts
├── data/                               # Data files (CSV, etc.)
├── src/                                # Main Python source code
│   ├── data/
│   │   ├── parser.py
│   │   └── pokemon_data.py
│   ├── env/
│   │   ├── core.py
│   │   └── benchmark.py
│   ├── export/
│   │   └── onnx_graph.py
│   ├── quantize/
│   │   └── quantize.py
├── README.md
├── pyproject.toml
├── uv.lock
├── .gitignore
└── .python-version
```
- **rustboyadvance-ng-for-rl/**: Rust-based GBA emulator with Python bindings (PyO3)
- **pokeemerald_ai_rl/**: Custom Pokémon Emerald ROM and build instructions
- **src/**: Main Python code (environment, data, quantization, export)
- **data/**: Data files (CSV, etc.)
- **tests/**: Unit and integration tests (#TO DO)
- **README.md**: Project documentation

##  Installation 
Requirements :
 - [cargo](https://doc.rust-lang.org/cargo/getting-started/installation.html) required to build rust code, to do so, you must install [rust](https://www.rust-lang.org/)
 ```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
 ```
 - [uv](https://docs.astral.sh/uv/getting-started/installation/)  Facultative but highly recommended
 ```bash
 curl -LsSf https://astral.sh/uv/install.sh | sh
 ```

### Linux 
1. **Clone the repository & its submodules**
```bash
git clone https://github.com/wissammm/rl_new_pokemon_ai.git  --recurse-submodule 
```
2. **Set up a Python virtual environment**
```bash
uv venv # use python venv if uv is not installed
source .venv/bin/activate
```
3. **Install Python dependencies**
```sh
uv pip compile pyproject.toml 
```

#### Install dependencies

##### Install [SDL2](https://github.com/libsdl-org/SDL)
1. Install SDL build dependencies (taken from [here](https://github.com/libsdl-org/SDL/blob/main/docs/README-linux.md#build-dependencies) : 
```bash
sudo apt-get install build-essential git make \
pkg-config cmake ninja-build gnome-desktop-testing libasound2-dev libpulse-dev \
libaudio-dev libjack-dev libsndio-dev libx11-dev libxext-dev \
libxrandr-dev libxcursor-dev libxfixes-dev libxi-dev libxss-dev libxtst-dev \
libxkbcommon-dev libdrm-dev libgbm-dev libgl1-mesa-dev libgles2-mesa-dev \
libegl1-mesa-dev libdbus-1-dev libibus-1.0-dev libudev-dev \
libpipewire-0.3-dev libwayland-dev libdecor-0-dev liburing-dev
```
2. Clone SDL2 : 
> [!WARNING] 
> Current version is SDL3 make sure to add the `--branch` arg shown below
```bash
 git clone https://github.com/libsdl-org/SDL.git SDL --branch=release-2.32.8 --depth=1
```
3. Install SDL (taken from [here](https://wiki.libsdl.org/SDL2/Installation)) : 
```bash
cd SDL
mkdir build
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release --parallel

#CMake >= 3.15
sudo cmake --install . --config Release

#CMake <= 3.14
sudo make install
```

#### Compile pokemon_ai_for_rl
To compile the custom pokeemerald rom, go to see directly the [pokeemerald_ai_rl's INSTALL.md](./pokeemerald_ai_rl/INSTALL.md).
> [!WARNING]
> 1. In [the build section](./pokeemerald_ai_rl/INSTALL.md#Build-pokeemerald) in each path replace `pokeemerald` with `pokeemard_ai_for_rl`
> 2. Replace the final `make modern` command by 
> ```bash
> make modern DINFO=1 DOBSERVED_DATA=1 DSKIP_TEXT=1 DSKIP_GRAPHICS=1 NO_DEBUG=1 -j
> ```

#### Install the rust emulator python extension
**Build and install the rust emulator extension**
```
cd rustboyadvance-ng-for-rl/platform/rustboyadvance-py
maturin develop --features elf_support --release -j6
```

#### Build & run the gba debugger with pokemon emerald loaded on it
```bash
./run_rom.sh
```


## License
This project is licensed under the MIT License.  
See the [LICENSE](LICENSE) file for details.
