#!/bin/bash

ROM_PATH="pokeemerald_ai_rl/pokeemerald_modern.elf"

CARGO_PROJECT_PATH="rustboyadvance-ng-for-rl"

# Check if the ROM file exists
if [ ! -f "$ROM_PATH" ]; then
    echo "Error: ROM not found at path: $ROM_PATH"
    exit 1
fi

# Navigate to the Cargo project directory
cd "$CARGO_PROJECT_PATH" || { echo "Error: Failed to navigate to $CARGO_PROJECT_PATH"; exit 1; }

# Run the Cargo project with the ROM as argument
echo "Running: cargo run --release -- ../$ROM_PATH"
cargo run --release -- "../$ROM_PATH"
