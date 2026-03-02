"""
材料属性模块
定义常用工程材料的属性
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class Material:
    """材料基类"""
    name: str
    density: float           # 密度 (kg/m³)
    elastic_modulus: float   # 弹性模量 E (Pa)
    poissons_ratio: float    # 泊松比 ν
    yield_strength: float    # 屈服强度 (Pa)
    ultimate_strength: float # 极限强度 (Pa)
    thermal_expansion: float = 12e-6  # 热膨胀系数 (1/K)

    @property
    def shear_modulus(self) -> float:
        """剪切模量 G (Pa)"""
        return self.elastic_modulus / (2 * (1 + self.poissons_ratio))

    @property
    def bulk_modulus(self) -> float:
        """体积模量 K (Pa)"""
        return self.elastic_modulus / (3 * (1 - 2 * self.poissons_ratio))


class Steel(Material):
    """结构钢"""
    def __init__(self, grade: str = "Q235"):
        grades = {
            "Q235": {
                "density": 7850,
                "E": 200e9,
                "nu": 0.3,
                "yield": 235e6,
                "ultimate": 375e6
            },
            "Q345": {
                "density": 7850,
                "E": 206e9,
                "nu": 0.3,
                "yield": 345e6,
                "ultimate": 510e6
            },
            "45#": {
                "density": 7850,
                "E": 210e9,
                "nu": 0.29,
                "yield": 355e6,
                "ultimate": 600e6
            }
        }

        props = grades.get(grade, grades["Q235"])
        super().__init__(
            name=f"结构钢({grade})",
            density=props["density"],
            elastic_modulus=props["E"],
            poissons_ratio=props["nu"],
            yield_strength=props["yield"],
            ultimate_strength=props["ultimate"]
        )


class Aluminum(Material):
    """铝合金"""
    def __init__(self, alloy: str = "6061-T6"):
        alloys = {
            "6061-T6": {
                "density": 2700,
                "E": 68.9e9,
                "nu": 0.33,
                "yield": 276e6,
                "ultimate": 310e6
            },
            "7075-T6": {
                "density": 2810,
                "E": 71.7e9,
                "nu": 0.33,
                "yield": 503e6,
                "ultimate": 572e6
            }
        }

        props = alloys.get(alloy, alloys["6061-T6"])
        super().__init__(
            name=f"铝合金({alloy})",
            density=props["density"],
            elastic_modulus=props["E"],
            poissons_ratio=props["nu"],
            yield_strength=props["yield"],
            ultimate_strength=props["ultimate"]
        )


class Concrete(Material):
    """混凝土"""
    def __init__(self, grade: str = "C30"):
        grades = {
            "C30": {
                "density": 2400,
                "E": 30e9,
                "nu": 0.2,
                "yield": 20e6,      # 抗压强度
                "ultimate": 30e6
            },
            "C40": {
                "density": 2400,
                "E": 32.5e9,
                "nu": 0.2,
                "yield": 27e6,
                "ultimate": 40e6
            },
            "C50": {
                "density": 2450,
                "E": 34.5e9,
                "nu": 0.2,
                "yield": 32e6,
                "ultimate": 50e6
            }
        }

        props = grades.get(grade, grades["C30"])
        super().__init__(
            name=f"混凝土({grade})",
            density=props["density"],
            elastic_modulus=props["E"],
            poissons_ratio=props["nu"],
            yield_strength=props["yield"],
            ultimate_strength=props["ultimate"]
        )


# 材料数据库
MATERIAL_DB: Dict[str, Material] = {
    "steel_q235": Steel("Q235"),
    "steel_q345": Steel("Q345"),
    "aluminum_6061": Aluminum("6061-T6"),
    "concrete_c30": Concrete("C30"),
}


def get_material(material_type: str) -> Material:
    """
    从数据库获取材料

    Args:
        material_type: 材料类型

    Returns:
        Material 对象
    """
    return MATERIAL_DB.get(material_type, Steel("Q235"))


def calculate_stress_strain(
    material: Material,
    strain: float | np.ndarray
) -> float | np.ndarray:
    """
    计算应力（弹性范围）

    Args:
        material: 材料对象
        strain: 应变值

    Returns:
        应力值 (Pa)
    """
    return material.elastic_modulus * strain


def safety_factor(
    material: Material,
    working_stress: float
) -> float:
    """
    计算安全系数

    Args:
        material: 材料对象
        working_stress: 工作应力 (Pa)

    Returns:
        安全系数，当工作应力为0时返回无穷大
    """
    if working_stress == 0:
        return float('inf')
    return material.yield_strength / working_stress


if __name__ == "__main__":
    # 测试材料属性
    steel = Steel("Q345")
    print(f"材料: {steel.name}")
    print(f"弹性模量: {steel.elastic_modulus/1e9:.1f} GPa")
    print(f"剪切模量: {steel.shear_modulus/1e9:.1f} GPa")
    print(f"屈服强度: {steel.yield_strength/1e6:.0f} MPa")

    # 计算安全系数
    stress = 100e6  # 100 MPa
    sf = safety_factor(steel, stress)
    print(f"\n工作应力: {stress/1e6:.0f} MPa")
    print(f"安全系数: {sf:.2f}")
