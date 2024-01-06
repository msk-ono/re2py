#!/bin/bash -eu

PYTHONPATH=src/ python examples/plot_nfa.py "a(bb)+a" images/nfa.svg
PYTHONPATH=src/ python examples/plot_match_process.py "a(bb)+a" abbbba images/
