"""
SMD Converter
=============

GUI application which converts smd file which contains
hyper spectral data from multiple detectors into ibw file

Usage
=====
Launch GUI application with:
  >>> python -m smdconverter

"""

from .singlesmdconverter import App

__all__ = ['App']
