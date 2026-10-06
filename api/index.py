import os
import sys

# Ensure repository root is on sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from app import app, application, handler

__all__ = ['app', 'application', 'handler']
