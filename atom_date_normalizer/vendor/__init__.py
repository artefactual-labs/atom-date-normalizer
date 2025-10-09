"""Vendorized dependencies for atom_date_normalizer.

Expose submodules for reliable imports in various environments.
"""

# Ensure `from atom_date_normalizer.vendor import daterangeparser` works
from . import daterangeparser  # noqa: F401

