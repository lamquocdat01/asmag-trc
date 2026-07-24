"""ASMAG-TRC pure-function safety layer.

Canonical, importable home for the safety arbitration function described in
Section 3.4 of the manuscript. Vendored from the submitted supplementary
package (ASMAG_TRC_Supplementary_Materials_v2.zip, code/) during the JSA
revision so the reference implementation lives in the repository rather than
only in the supplementary archive.
"""
from .final_safety_arbitration_v2 import final_safety_arbitration_v2

__all__ = ["final_safety_arbitration_v2"]
