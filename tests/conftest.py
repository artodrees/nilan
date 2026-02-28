"""Pytest configuration for Nilan tests."""
import sys
import os

# Add the repo root to sys.path so 'custom_components.nilan' is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
