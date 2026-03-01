"""
工程仿真包
Engineering Simulation Package
"""

from .materials import Material, Steel, Aluminum, Concrete
from .beam_analysis import SimplySupportedBeam, CantileverBeam
from .fea import FEModel, TrussElement, FEAResults, FEMaterial
from .truss import TrussStructure, create_roof_truss, create_bridge_truss

__version__ = "0.1.0"
__author__ = "Xiangdi Meng"

__all__ = [
    # Materials
    "Material",
    "Steel",
    "Aluminum",
    "Concrete",
    # Beam analysis
    "SimplySupportedBeam",
    "CantileverBeam",
    # FEA
    "FEModel",
    "TrussElement",
    "FEAResults",
    "FEMaterial",
    # Truss structures
    "TrussStructure",
    "create_roof_truss",
    "create_bridge_truss",
]
