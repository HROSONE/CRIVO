#!/usr/bin/env python3
"""Entrada de linha de comando para o experimento pointer-copy causal."""
from __future__ import annotations

import argparse
from pathlib import Path

from experimento_pointer_copy import main as run_main


def parse_args():
    p = argparse.ArgumentParser(description="Pointer-copy causal com Transformer congelado")
    p.add_argument("--drive-root", type=Path, required=True)
    p.add_argument("--batch-size", type=int, default=20)
    p.add_argument("--steps", type=int, default=1000)
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_main(drive_root=args.drive_root, batch_size=args.batch_size, steps=args.steps)
