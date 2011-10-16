#!/bin/sh
export PYTHONDONTWRITEBYTECODE=1
exec python "$@" -- test_speedpad.py
