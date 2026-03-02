"""
工程仿真包
Engineering Simulation Package
"""

from .materials import Material, Steel, Aluminum, Concrete
from .beam_analysis import SimplySupportedBeam, CantileverBeam
from .fea import FEModel, TrussElement, FEAResults, FEMaterial
from .truss import TrussStructure, create_roof_truss, create_bridge_truss
from .frame import FrameStructure, FrameElement, FrameMaterial, Section, create_portal_frame
from .stability import (ColumnSection, BoundaryCondition, euler_buckling_analysis,
                        slenderness_ratio_analysis, aisc_allowable_stress)
try:
    from .dynamics import ModalAnalysis, HarmonicResponseAnalysis, TransientResponseAnalysis
except ImportError as e:
    import warnings
    warnings.warn(
        f"动力学模块加载失败（可能缺少 scipy）: {e}. "
        "请安装 scipy: pip install scipy"
    )
    ModalAnalysis = None
    HarmonicResponseAnalysis = None
    TransientResponseAnalysis = None
from .postproc import StressContourPlot, DeformationAnimation, ResultReporter
from .combined import (ParametricStructure, create_cable_stayed_bridge, create_arch_bridge,
                       create_multistory_frame, LoadCase, LoadCombination)

__version__ = "0.2.0"
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
    # Frame structures
    "FrameStructure",
    "FrameElement",
    "FrameMaterial",
    "Section",
    "create_portal_frame",
    # Stability
    "ColumnSection",
    "BoundaryCondition",
    "euler_buckling_analysis",
    "slenderness_ratio_analysis",
    "aisc_allowable_stress",
    # Dynamics
    "ModalAnalysis",
    "HarmonicResponseAnalysis",
    "TransientResponseAnalysis",
    # Post-processing
    "StressContourPlot",
    "DeformationAnimation",
    "ResultReporter",
    # Combined structures
    "ParametricStructure",
    "create_cable_stayed_bridge",
    "create_arch_bridge",
    "create_multistory_frame",
    "LoadCase",
    "LoadCombination",
]
