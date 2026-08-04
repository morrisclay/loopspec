"""Locate LoopSpec runtime data in a checkout or an installed wheel."""

import os


def resource_root():
    """Return the directory containing schema/, ontology/, and docs/."""
    module_dir = os.path.dirname(os.path.abspath(__file__))
    checkout = os.path.dirname(module_dir)
    if os.path.isfile(os.path.join(checkout, "schema", "loop.keys.yaml")):
        return checkout
    if os.path.isfile(os.path.join(module_dir, "schema", "loop.keys.yaml")):
        return module_dir
    raise RuntimeError("LoopSpec runtime data is missing; reinstall the loopspec package")


ROOT = resource_root()
