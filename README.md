# rl_new_pokemon_ai

Reinforcement learning environment and tools for Pokémon Emerald : 
    - Modified Emulator to have python librairy 
    - PettingZoo environnement for MARL
    - Quantization 
    - Neural Network graph manipulation 
    - Export 

##  Installation 
### Linux 
1. **Clone the repository**
2. **Set up a Python virtual environment**
3. **Install Python dependencies**
   ```sh
   pip install -r requirements.txt
   ```

4. **Build and install the rust emulator extension**
    ```
    cd rustboyadvance-ng-for-rl/platform/rustboyadvance-py
    maturin develop
    ```

5. **Compile the rom**

To compile the custom pokeemerald rom, go to see directly the INSTALL.md inside pokeemerald_ai_rl. Replace make modern by 
```bash
make modern DINFO=1 DOBSERVED_DATA=1 DSKIP_TEXT=1 DSKIP_GRAPHICS=1 NO_DEBUG=1 -j
```

## Project structure
```
rl_new_pokemon_ai/
├── rustboyadvance-ng-for-rl/           # Rust GBA emulator with Python bindings
├── pokeemerald_ai_rl/                  # Custom Pokémon Emerald ROM and build scripts
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
├── requirements.txt
└── .gitignore
```
- **rustboyadvance-ng-for-rl/**: Rust-based GBA emulator with Python bindings (PyO3)
- **pokeemerald_ai_rl/**: Custom Pokémon Emerald ROM and build instructions
- **src/**: Main Python code (environment, data, quantization, export)
- **data/**: Data files (CSV, etc.)
- **tests/**: Unit and integration tests (if present)
- **README.md**: Project documentation

## License
This project is licensed under the MIT License.  
See the [LICENSE](LICENSE) file for details.