"""
梁结构分析模块
包含简支梁、悬臂梁、外伸梁等分析方法
"""

import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from .materials import Material


@dataclass
class PointLoad:
    """集中载荷"""
    force: float      # 力 (N), 向下为正
    position: float   # 位置 (m)


@dataclass
class DistributedLoad:
    """分布载荷"""
    magnitude: float  # 载荷密度 (N/m)
    start: float      # 起始位置 (m)
    end: float        # 结束位置 (m)


@dataclass
class BeamResults:
    """梁分析结果"""
    x: np.ndarray           # 位置数组
    deflection: np.ndarray  # 挠度
    slope: np.ndarray       # 转角
    moment: np.ndarray      # 弯矩
    shear: np.ndarray       # 剪力
    stress: np.ndarray      # 应力
    max_deflection: float   # 最大挠度
    max_moment: float       # 最大弯矩
    max_stress: float       # 最大应力
    safety_factor: float    # 安全系数

    def plot(self, figsize=(12, 10)):
        """绘制结果图表"""
        fig, axes = plt.subplots(4, 1, figsize=figsize)

        # 挠度
        axes[0].plot(self.x, self.deflection * 1000, 'b-', linewidth=2)
        axes[0].axhline(0, color='k', linestyle='--', alpha=0.3)
        axes[0].set_ylabel('挠度 (mm)')
        axes[0].set_title(f'最大挠度: {self.max_deflection * 1000:.2f} mm')
        axes[0].grid(True, alpha=0.3)

        # 转角
        axes[1].plot(self.x, self.slope * 180 / np.pi, 'g-', linewidth=2)
        axes[1].axhline(0, color='k', linestyle='--', alpha=0.3)
        axes[1].set_ylabel('转角 (度)')
        axes[1].grid(True, alpha=0.3)

        # 弯矩
        axes[2].plot(self.x, self.moment / 1000, 'r-', linewidth=2)
        axes[2].fill_between(self.x, 0, self.moment / 1000, alpha=0.3, color='red')
        axes[2].set_ylabel('弯矩 (kN·m)')
        axes[2].set_title(f'最大弯矩: {self.max_moment / 1000:.2f} kN·m')
        axes[2].grid(True, alpha=0.3)

        # 剪力
        axes[3].plot(self.x, self.shear / 1000, 'm-', linewidth=2)
        axes[3].axhline(0, color='k', linestyle='--', alpha=0.3)
        axes[3].set_xlabel('位置 (m)')
        axes[3].set_ylabel('剪力 (kN)')
        axes[3].grid(True, alpha=0.3)

        plt.tight_layout()
        return fig


class SimplySupportedBeam:
    """简支梁"""

    def __init__(
        self,
        length: float,
        width: float,
        height: float,
        material: Material
    ):
        self.length = length          # 长度 (m)
        self.width = width            # 宽度 (m)
        self.height = height          # 高度 (m)
        self.material = material      # 材料

        self.point_loads: List[PointLoad] = []
        self.distributed_loads: List[DistributedLoad] = []

        # 截面惯性矩
        self.I = (width * height ** 3) / 12
        # 截面模量
        self.S = (width * height ** 2) / 6
        # 截面积
        self.A = width * height

    def add_point_load(self, force: float, position: float):
        """添加集中载荷"""
        self.point_loads.append(PointLoad(force, position))
        return self

    def add_distributed_load(
        self,
        magnitude: float,
        start: float = None,
        end: float = None
    ):
        """添加分布载荷"""
        if start is None:
            start = 0
        if end is None:
            end = self.length
        self.distributed_loads.append(
            DistributedLoad(magnitude, start, end)
        )
        return self

    def analyze(self, n_points: int = 100) -> BeamResults:
        """分析梁的受力和变形"""
        x = np.linspace(0, self.length, n_points)

        # 初始化数组
        deflection = np.zeros_like(x)
        slope = np.zeros_like(x)
        moment = np.zeros_like(x)
        shear = np.zeros_like(x)

        E = self.material.elastic_modulus
        I = self.I

        # 计算支座反力
        R_left = 0
        R_right = 0

        # 集中载荷
        for load in self.point_loads:
            R_left += load.force * (self.length - load.position) / self.length
            R_right += load.force * load.position / self.length

        # 分布载荷
        for load in self.distributed_loads:
            L = load.end - load.start
            center = (load.start + load.end) / 2
            R_left += load.magnitude * L * (self.length - center) / self.length
            R_right += load.magnitude * L * center / self.length

        # 计算内力和变形
        for i, xi in enumerate(x):
            # 剪力
            shear[i] = R_left

            # 集中载荷产生的剪力变化
            for load in self.point_loads:
                if xi > load.position:
                    shear[i] -= load.force

            # 分布载荷产生的剪力变化
            for load in self.distributed_loads:
                if xi > load.start:
                    end_x = min(xi, load.end)
                    shear[i] -= load.magnitude * (end_x - load.start)

            # 弯矩 (剪力积分)
            if i > 0:
                dx = x[i] - x[i-1]
                moment[i] = moment[i-1] + shear[i] * dx

            # 挠度 (简化计算，只考虑一个集中载荷的情况)
            if len(self.point_loads) == 1:
                load = self.point_loads[0]
                a = load.position
                P = load.force
                L = self.length

                if xi <= a:
                    deflection[i] = (P * xi * (L**2 * 3 - 4 * a**2) -
                                     4 * xi**3) / (24 * E * I * L)
                else:
                    b = L - a
                    deflection[i] = (P * a * (3 * L**2 - 4 * b**2) *
                                     (L - xi) - (L - xi)**3) / (24 * E * I * L)

        # 计算应力
        stress = moment / self.S

        # 计算安全系数
        max_stress = np.max(np.abs(stress))
        sf = self.material.yield_strength / max_stress if max_stress > 0 else float('inf')

        return BeamResults(
            x=x,
            deflection=deflection,
            slope=slope,
            moment=moment,
            shear=shear,
            stress=stress,
            max_deflection=np.max(np.abs(deflection)),
            max_moment=np.max(np.abs(moment)),
            max_stress=max_stress,
            safety_factor=sf
        )


class CantileverBeam:
    """悬臂梁"""

    def __init__(
        self,
        length: float,
        width: float,
        height: float,
        material: Material
    ):
        self.length = length
        self.width = width
        self.height = height
        self.material = material

        self.point_loads: List[PointLoad] = []
        self.distributed_loads: List[DistributedLoad] = []

        self.I = (width * height ** 3) / 12
        self.S = (width * height ** 2) / 6
        self.A = width * height

    def add_point_load(self, force: float, position: float):
        """添加集中载荷"""
        self.point_loads.append(PointLoad(force, position))
        return self

    def add_distributed_load(
        self,
        magnitude: float,
        start: float = None,
        end: float = None
    ):
        """添加分布载荷"""
        if start is None:
            start = 0
        if end is None:
            end = self.length
        self.distributed_loads.append(
            DistributedLoad(magnitude, start, end)
        )
        return self

    def analyze(self, n_points: int = 100) -> BeamResults:
        """分析悬臂梁"""
        x = np.linspace(0, self.length, n_points)

        E = self.material.elastic_modulus
        I = self.I

        deflection = np.zeros_like(x)
        slope = np.zeros_like(x)
        moment = np.zeros_like(x)
        shear = np.zeros_like(x)

        # 计算每个位置的内力
        for i, xi in enumerate(x):
            # 剪力
            for load in self.point_loads:
                if xi >= load.position:
                    shear[i] += load.force

            for load in self.distributed_loads:
                if xi >= load.start:
                    end_x = min(xi, load.end)
                    shear[i] += load.magnitude * (end_x - load.start)

            # 弯矩 (从自由端向固定端积分)
            if i > 0:
                dx = x[i] - x[i-1]
                moment[i] = moment[i-1] + shear[i] * dx

        # 计算变形（悬臂梁自由端最大挠度）
        if len(self.point_loads) == 1:
            load = self.point_loads[0]
            a = load.position
            P = load.force

            for i, xi in enumerate(x):
                if xi <= a:
                    deflection[i] = P * xi ** 2 * (3 * a - xi) / (6 * E * I)
                else:
                    deflection[i] = P * a ** 2 * (3 * xi - a) / (6 * E * I)

        stress = moment / self.S
        max_stress = np.max(np.abs(stress))
        sf = self.material.yield_strength / max_stress if max_stress > 0 else float('inf')

        return BeamResults(
            x=x,
            deflection=-deflection,  # 向下为正
            slope=slope,
            moment=moment,
            shear=shear,
            stress=stress,
            max_deflection=np.max(np.abs(deflection)),
            max_moment=np.max(np.abs(moment)),
            max_stress=max_stress,
            safety_factor=sf
        )


if __name__ == "__main__":
    from .materials import Steel

    # 简支梁示例
    print("=== 简支梁分析 ===")
    beam = SimplySupportedBeam(
        length=5.0,
        width=0.1,
        height=0.2,
        material=Steel("Q345")
    )

    beam.add_point_load(force=50000, position=2.5)

    results = beam.analyze()
    print(f"最大挠度: {results.max_deflection * 1000:.2f} mm")
    print(f"最大弯矩: {results.max_moment / 1000:.2f} kN·m")
    print(f"最大应力: {results.max_stress / 1e6:.2f} MPa")
    print(f"安全系数: {results.safety_factor:.2f}")

    # 绘图
    results.plot()
    plt.savefig("../results/beam_analysis.png", dpi=150)
    plt.show()
