#!/bin/bash

ROM_PATH="pokeemerald_ai_rl/pokeemerald_modern.elf"
CARGO_PROJECT_PATH="rustboyadvance-ng-for-rl"

if [ ! -f "$ROM_PATH" ]; then
    echo "Error: ROM not found at path: $ROM_PATH"
    exit 1
fi

cd "$CARGO_PROJECT_PATH" || { echo "Error: Failed to navigate to $CARGO_PROJECT_PATH"; exit 1; }

echo "Running: RUST_BACKTRACE=1 cargo run --release -- ../$ROM_PATH"
RUST_BACKTRACE=1 cargo run --release -- "../$ROM_PATH"