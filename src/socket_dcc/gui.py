"""Compatibility entry point for the canonical modular GUI."""

from socket_dcc.core.gui.window import MainWindow
from socket_dcc.interface import load_in_application, main

__all__ = ["MainWindow", "load_in_application", "main"]
