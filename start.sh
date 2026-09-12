#!/usr/bin/env bash
set -e
playwright install chromium --with-deps
python main.py
