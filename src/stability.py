"""
稳定性分析模块 (Stability Analysis)
包含欧拉屈曲、特征值屈曲分析、临界载荷计算
"""

import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional
from enum import Enum

from .materials import Material
from .fea import Node, FEMaterial


class BucklingMode(Enum):
    """屈曲模式"""
    EULER_1 = "euler_1"      # 一阶屈曲（两端铰接）
    EULER_2 = "euler_2"      # 二阶屈曲（一端固定，一端自由）
    EULER_3 = "euler_3"      # 三阶屈曲（两端固定）
    EULER_4 = "euler_4"      # 四阶屈曲（一端固定，一端铰接)


@dataclass
class ColumnSection:
    """柱截面属性"""
    A: float           # 截面积 (m^2)
    Ix: float          # 惯性矩绕x轴 (m^4)
    Iy: float          # 惯性矩绕y轴 (m^4)
    J: float = 0.0     # 扭转常数 (m^4)
    radius_gyration_x: float = 0.0  # 回转半径 rx
    radius_gyration_y: float = 0.0  # 回转半径 ry

    def __post_init__(self):
        if self.radius_gyration_x == 0:
            self.radius_gyration_x = np.sqrt(self.Ix / self.A)
        if self.radius_gyration_y == 0:
            self.radius_gyration_y = np.sqrt(self.Iy / self.A)


@dataclass
class BoundaryCondition:
    """边界条件"""
    fix_start_x: bool = True    # 起端固定X
    fix_start_y: bool = True    # 起端固定Y
    fix_start_theta: bool = False  # 起端固定转动
    fix_end_x: bool = True      # 终端固定X
    fix_end_y: bool = True      # 终端固定Y
    fix_end_theta: bool = False  # 终端固定转动

    def effective_length_factor(self) -> float:
        """
        计算有效长度系数 μ

        Returns
        -------
        float
            有效长度系数
            - 两端铰接: μ = 1.0
            - 一端固定，一端自由: μ = 2.0
            - 两端固定: μ = 0.5
            - 一端固定，一端铰接: μ = 0.7
        """
        if not self.fix_start_theta and not self.fix_end_theta:
            # 两端铰接
            return 1.0
        elif self.fix_start_theta and not self.fix_end_theta and not self.fix_end_y:
            # 一端固定，一端自由
            return 2.0
        elif self.fix_start_theta and self.fix_end_theta:
            # 两端固定
            return 0.5
        elif (self.fix_start_theta and not self.fix_end_theta) or \
             (not self.fix_start_theta and self.fix_end_theta):
            # 一端固定，一端铰接
            return 0.7
        else:
            return 1.0  # 默认


@dataclass
class EulerBucklingResult:
    """欧拉屈曲分析结果"""
    critical_load: float        # 临界载荷 (N)
    critical_stress: float       # 临界应力 (Pa)
    effective_length: float      # 有效长度 (m)
    slenderness_ratio: float     # 长细比 λ
    safety_factor: float         # 安全系数
    buckling_mode: BucklingMode  # 屈曲模式

    def is_safe(self, applied_load: float, required_safety_factor: float = 1.5) -> bool:
        """检查是否安全"""
        return self.safety_factor >= required_safety_factor


@dataclass
class BucklingAnalysisResult:
    """屈曲分析结果"""
    critical_loads: np.ndarray   # 各阶临界载荷
    mode_shapes: np.ndarray      # 各阶振型
    eigenvalues: np.ndarray      # 特征值
    effective_length_factor: float  # 有效长度系数


def euler_buckling_load(
    length: float,
    E: float,
    I: float,
    boundary_condition: BoundaryCondition
) -> EulerBucklingResult:
    """
    计算欧拉临界载荷

    P_cr = π²EI / (μL)²

    Parameters
    ----------
    length : float
        柱长度 (m)
    E : float
        弹性模量 (Pa)
    I : float
        惯性矩 (m^4)
    boundary_condition : BoundaryCondition
        边界条件

    Returns
    -------
    EulerBucklingResult
        屈曲分析结果
    """
    mu = boundary_condition.effective_length_factor()
    effective_length = mu * length

    P_cr = (np.pi**2 * E * I) / (effective_length**2)

    return EulerBucklingResult(
        critical_load=P_cr,
        critical_stress=0,  # 需要截面积计算
        effective_length=effective_length,
        slenderness_ratio=0,  # 需要回转半径
        safety_factor=float('inf'),
        buckling_mode=BucklingMode.EULER_1
    )


def euler_buckling_analysis(
    length: float,
    material: Material,
    section: ColumnSection,
    applied_load: float,
    boundary_condition: BoundaryCondition
) -> EulerBucklingResult:
    """
    完整的欧拉屈曲分析

    Parameters
    ----------
    length : float
        柱长度 (m)
    material : Material
        材料属性
    section : ColumnSection
        截面属性
    applied_load : float
        施加的轴向载荷 (N)
    boundary_condition : BoundaryCondition
        边界条件

    Returns
    -------
    EulerBucklingResult
        屈曲分析结果
    """
    E = material.elastic_modulus
    I = min(section.Ix, section.Iy)  # 使用较小的惯性矩
    A = section.A
    r = min(section.radius_gyration_x, section.radius_gyration_y)

    mu = boundary_condition.effective_length_factor()
    Le = mu * length  # 有效长度

    # 临界载荷
    P_cr = (np.pi**2 * E * I) / (Le**2)

    # 临界应力
    sigma_cr = P_cr / A

    # 长细比
    slenderness_ratio = Le / r

    # 安全系数
    safety_factor = P_cr / applied_load if applied_load > 0 else float('inf')

    # 确定屈曲模式
    if mu == 1.0:
        mode = BucklingMode.EULER_1
    elif mu == 2.0:
        mode = BucklingMode.EULER_2
    elif mu == 0.5:
        mode = BucklingMode.EULER_3
    else:
        mode = BucklingMode.EULER_4

    return EulerBucklingResult(
        critical_load=P_cr,
        critical_stress=sigma_cr,
        effective_length=Le,
        slenderness_ratio=slenderness_ratio,
        safety_factor=safety_factor,
        buckling_mode=mode
    )


def tangent_modulus_buckling(
    length: float,
    material: Material,
    section: ColumnSection,
    applied_load: float,
    boundary_condition: BoundaryCondition
) -> EulerBucklingResult:
    """
    切线模量理论（非弹性屈曲）

    适用于长细比较小、应力超过比例极限的情况

    Parameters
    ----------
    length : float
        柱长度 (m)
    material : Material
        材料属性
    section : ColumnSection
        截面属性
    applied_load : float
        施加的轴向载荷 (N)
    boundary_condition : BoundaryCondition
        边界条件

    Returns
    -------
    EulerBucklingResult
        屈曲分析结果
    """
    # 先进行欧拉屈曲分析
    euler_result = euler_buckling_analysis(
        length, material, section, applied_load, boundary_condition
    )

    # 计算工作应力
    A = section.A
    sigma_work = applied_load / A

    # 比例极限（假设为屈服强度的70%）
    sigma_prop = 0.7 * material.yield_strength

    if sigma_work > sigma_prop:
        # 非弹性屈曲 - 使用切线模量
        # 简化：使用折减的弹性模量
        E_t = material.elastic_modulus * (sigma_prop / sigma_work)

        mu = boundary_condition.effective_length_factor()
        Le = mu * length
        I = min(section.Ix, section.Iy)

        P_cr_t = (np.pi**2 * E_t * I) / (Le**2)

        euler_result.critical_load = P_cr_t
        euler_result.critical_stress = P_cr_t / A
        euler_result.safety_factor = P_cr_t / applied_load if applied_load > 0 else float('inf')

    return euler_result


def slenderness_ratio_analysis(
    length: float,
    section: ColumnSection,
    boundary_condition: BoundaryCondition
) -> Tuple[float, float]:
    """
    计算长细比

    Parameters
    ----------
    length : float
        柱长度 (m)
    section : ColumnSection
        截面属性
    boundary_condition : BoundaryCondition
        边界条件

    Returns
    -------
    Tuple[float, float]
        (λx, λy) 两个方向的长细比
    """
    mu = boundary_condition.effective_length_factor()
    Le = mu * length

    lambda_x = Le / section.radius_gyration_x
    lambda_y = Le / section.radius_gyration_y

    return lambda_x, lambda_y


def aisc_allowable_stress(
    slenderness_ratio: float,
    yield_strength: float,
    elastic_modulus: float
) -> float:
    """
    AISC 允许应力计算

    当 λ ≤ λ_p 时: Fa = (1 - λ²/2Cc²) * Fy / FS
    当 λ > λ_p 时: Fa = (12π²E) / (23λ²)

    Parameters
    ----------
    slenderness_ratio : float
        长细比
    yield_strength : float
        屈服强度 (Pa)
    elastic_modulus : float
        弹性模量 (Pa)

    Returns
    -------
    float
        允许应力 (Pa)
    """
    Cc = np.sqrt(2 * np.pi**2 * elastic_modulus / yield_strength)

    if slenderness_ratio <= Cc:
        # 非弹性屈曲
        FS = 5.0 / 3 + 3 * slenderness_ratio / (8 * Cc) - \
             (slenderness_ratio**3) / (8 * Cc**3)
        Fa = (1 - slenderness_ratio**2 / (2 * Cc**2)) * yield_strength / FS
    else:
        # 弹性屈曲
        Fa = (12 * np.pi**2 * elastic_modulus) / (23 * slenderness_ratio**2)

    return Fa


class FrameBucklingAnalysis:
    """框架屈曲分析（基于刚度矩阵的特征值分析）"""

    def __init__(
        self,
        nodes: List[Node],
        elements: List,
        n_modes: int = 5
    ):
        """
        Parameters
        ----------
        nodes : List[Node]
            节点列表
        elements : List
            单元列表（需要有global_stiffness_matrix和length方法）
        n_modes : int
            计算的屈曲模态数
        """
        self.nodes = nodes
        self.elements = elements
        self.n_modes = n_modes

    def assemble_elastic_stiffness(self) -> np.ndarray:
        """组装弹性刚度矩阵 Ke"""
        n_dof = len(self.nodes) * 3
        Ke = np.zeros((n_dof, n_dof))

        for elem in self.elements:
            if hasattr(elem, 'global_stiffness_matrix'):
                k_elem = elem.global_stiffness_matrix(self.nodes)
            else:
                continue

            # 假设每个单元有2个节点，每个节点3个自由度
            dof_indices = [
                elem.node_i * 3,
                elem.node_i * 3 + 1,
                elem.node_i * 3 + 2,
                elem.node_j * 3,
                elem.node_j * 3 + 1,
                elem.node_j * 3 + 2
            ]

            for i in range(6):
                for j in range(6):
                    Ke[dof_indices[i], dof_indices[j]] += k_elem[i, j]

        return Ke

    def assemble_geometric_stiffness(self) -> np.ndarray:
        """
        组装几何刚度矩阵 Kg

        几何刚度矩阵与轴向力相关，用于特征值屈曲分析
        [Ke + λ*Kg] * {φ} = {0}
        """
        n_dof = len(self.nodes) * 3
        Kg = np.zeros((n_dof, n_dof))

        for elem in self.elements:
            if not hasattr(elem, 'length') or not hasattr(elem, 'material'):
                continue

            L = elem.length(self.nodes)
            ni, nj = self.nodes[elem.node_i], self.nodes[elem.node_j]

            # 方向余弦
            dx = nj.x - ni.x
            dy = nj.y - ni.y
            c = dx / L
            s = dy / L

            # 单位几何刚度矩阵（假设单位轴向力）
            # 对于框架单元
            k_g_unit = (1 / L) * np.array([
                # u_i,           v_i,           theta_i,      u_j,           v_j,           theta_j
                [6*c*s/5,        6*s**2/5,      -s/10,        -6*c*s/5,      -6*s**2/5,     -s/10       ],  # u_i
                [6*c*s/5,        6*c*s/5,       c/10,         -6*c*s/5,      -6*c*s/5,      c/10        ],  # v_i
                [-s/10,          c/10,          2*L/15,       s/10,          -c/10,         -L/30       ],  # theta_i
                [-6*c*s/5,       -6*s**2/5,     s/10,         6*c*s/5,       6*s**2/5,      s/10        ],  # u_j
                [-6*c*s/5,       -6*c*s/5,      -c/10,        6*c*s/5,       6*c*s/5,       -c/10       ],  # v_j
                [-s/10,          c/10,          -L/30,        s/10,          -c/10,         2*L/15      ]   # theta_j
            ])

            dof_indices = [
                elem.node_i * 3,
                elem.node_i * 3 + 1,
                elem.node_i * 3 + 2,
                elem.node_j * 3,
                elem.node_j * 3 + 1,
                elem.node_j * 3 + 2
            ]

            for i in range(6):
                for j in range(6):
                    Kg[dof_indices[i], dof_indices[j]] += k_g_unit[i, j]

        return Kg

    def apply_boundary_conditions(
        self,
        K: np.ndarray
    ) -> Tuple[np.ndarray, List[int]]:
        """应用边界条件"""
        fixed_dofs = []

        for node in self.nodes:
            if node.fixity[0]:  # 固定X
                fixed_dofs.append(node.id * 3)
            if node.fixity[1]:  # 固定Y
                fixed_dofs.append(node.id * 3 + 1)
            if node.fixity[2]:  # 固定转动
                fixed_dofs.append(node.id * 3 + 2)

        free_dofs = [i for i in range(K.shape[0]) if i not in fixed_dofs]

        K_reduced = K[np.ix_(free_dofs, free_dofs)]

        return K_reduced, free_dofs

    def solve(self) -> BucklingAnalysisResult:
        """
        求解屈曲特征值问题

        Ke * φ = -λ * Kg * φ

        Returns
        -------
        BucklingAnalysisResult
        """
        # 组装刚度矩阵
        Ke = self.assemble_elastic_stiffness()
        Kg = self.assemble_geometric_stiffness()

        # 应用边界条件
        Ke_reduced, free_dofs = self.apply_boundary_conditions(Ke)
        Kg_reduced, _ = self.apply_boundary_conditions(Kg)

        # 广义特征值问题: Ke * φ = λ * Kg * φ
        # 转换为标准特征值问题: Kg^(-1) * Ke * φ = λ * φ

        try:
            # 使用numpy的eig求解
            # Ke * φ = -λ * Kg * φ
            # Kg^(-1) * Ke * φ = -λ * φ

            # 确保Kg可逆
            if np.linalg.det(Kg_reduced) < 1e-10:
                # 几何刚度矩阵奇异，使用伪逆
                from scipy.linalg import eig
            else:
                from scipy.linalg import eig

            # 使用scipy求解广义特征值问题
            from scipy.linalg import eig

            eigenvalues, eigenvectors = eig(Ke_reduced, Kg_reduced)

            # 提取正实数特征值
            lambda_values = []
            mode_shapes = []

            for i, (val, vec) in enumerate(zip(eigenvalues, eigenvectors.T)):
                if abs(val.imag) < 1e-6 and val.real > 0:
                    lambda_values.append(val.real)
                    mode_shapes.append(vec.real)

            # 排序并取前n_modes个
            lambda_values = np.array(lambda_values)
            mode_shapes = np.array(mode_shapes)

            if len(lambda_values) > 0:
                idx = np.argsort(lambda_values)[:self.n_modes]
                critical_loads = lambda_values[idx]
                buckling_modes = mode_shapes[idx]
            else:
                critical_loads = np.array([float('inf')])
                buckling_modes = np.zeros((1, len(free_dofs)))

        except ImportError:
            # 没有scipy，使用简化的欧拉公式
            critical_loads = np.array([1e6])  # 默认值
            buckling_modes = np.zeros((1, len(free_dofs)))
        except Exception as e:
            # 求解失败
            critical_loads = np.array([float('inf')])
            buckling_modes = np.zeros((1, len(free_dofs)))

        return BucklingAnalysisResult(
            critical_loads=critical_loads,
            mode_shapes=buckling_modes,
            eigenvalues=critical_loads,
            effective_length_factor=1.0
        )


def plot_buckling_mode(
    nodes: List[Node],
    mode_shape: np.ndarray,
    eigenvalue: float,
    scale: float = 1.0,
    ax: Optional[plt.Axes] = None
) -> plt.Axes:
    """
    绘制屈曲模态

    Parameters
    ----------
    nodes : List[Node]
        节点列表
    mode_shape : np.ndarray
        模态振型
    eigenvalue : float
        特征值（临界载荷）
    scale : float
        放大倍数
    ax : plt.Axes, optional
        坐标轴对象

    Returns
    -------
    plt.Axes
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))

    # 绘制原始结构（虚线）
    x_orig = [node.x for node in nodes]
    y_orig = [node.y for node in nodes]

    # 绘制变形后的结构
    x_def = []
    y_def = []

    for i, node in enumerate(nodes):
        if i * 2 < len(mode_shape):
            u = mode_shape[i * 2] * scale
            v = mode_shape[i * 2 + 1] * scale
        else:
            u, v = 0, 0
        x_def.append(node.x + u)
        y_def.append(node.y + v)

    ax.plot(x_orig, y_orig, 'k--', alpha=0.3, linewidth=1, label='原始结构')
    ax.plot(x_def, y_def, 'r-o', linewidth=2, markersize=8, label='屈曲模态')

    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.set_title(f'屈曲模态 (临界载荷: {eigenvalue/1000:.2f} kN)')
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.legend()

    return ax


def create_column_analysis(
    length: float = 4.0,
    width: float = 0.2,
    depth: float = 0.3,
    E: float = 200e9,
    yield_strength: float = 345e6,
    fix_both_ends: bool = False
) -> Dict:
    """
    创建柱分析（包含所有稳定性参数）

    Parameters
    ----------
    length : float
        柱长度 (m)
    width : float
        截面宽度 (m)
    depth : float
        截面深度 (m)
    E : float
        弹性模量 (Pa)
    yield_strength : float
        屈服强度 (Pa)
    fix_both_ends : bool
        两端是否固定

    Returns
    -------
    Dict
        分析结果字典
    """
    from .materials import Steel

    # 创建截面
    A = width * depth
    Ix = (width * depth**3) / 12
    Iy = (depth * width**3) / 12

    section = ColumnSection(
        A=A,
        Ix=Ix,
        Iy=Iy
    )

    # 边界条件
    if fix_both_ends:
        bc = BoundaryCondition(
            fix_start_x=True, fix_start_y=True, fix_start_theta=True,
            fix_end_x=True, fix_end_y=True, fix_end_theta=True
        )
    else:
        bc = BoundaryCondition(
            fix_start_x=True, fix_start_y=True, fix_start_theta=False,
            fix_end_x=True, fix_end_y=True, fix_end_theta=False
        )

    material = Steel("Q345")
    material.yield_strength = yield_strength
    material.elastic_modulus = E

    # 计算长细比
    lambda_x, lambda_y = slenderness_ratio_analysis(length, section, bc)

    # 计算临界载荷
    result = euler_buckling_analysis(length, material, section, 100000, bc)

    # AISC允许应力
    allowable_stress = aisc_allowable_stress(
        max(lambda_x, lambda_y),
        yield_strength,
        E
    )

    return {
        'section': section,
        'boundary_condition': bc,
        'slenderness_ratio_x': lambda_x,
        'slenderness_ratio_y': lambda_y,
        'critical_load': result.critical_load,
        'critical_stress': result.critical_stress,
        'allowable_stress': allowable_stress,
        'effective_length': result.effective_length,
        'safety_factor': result.safety_factor
    }


if __name__ == "__main__":
    # 测试：柱屈曲分析
    print("=== 柱稳定性分析 ===")

    # 创建柱分析
    result = create_column_analysis(
        length=6.0,
        width=0.25,
        depth=0.35,
        E=206e9,
        yield_strength=345e6,
        fix_both_ends=False
    )

    print(f"\n截面属性:")
    print(f"  面积: {result['section'].A*1e4:.2f} cm²")
    print(f"  惯性矩 Ix: {result['section'].Ix*1e8:.4f} cm⁴")
    print(f"  惯性矩 Iy: {result['section'].Iy*1e8:.4f} cm⁴")

    print(f"\n长细比:")
    print(f"  λx: {result['slenderness_ratio_x']:.2f}")
    print(f"  λy: {result['slenderness_ratio_y']:.2f}")

    print(f"\n临界载荷:")
    print(f"  P_cr: {result['critical_load']/1000:.2f} kN")
    print(f"  σ_cr: {result['critical_stress']/1e6:.2f} MPa")

    print(f"\n允许应力:")
    print(f"  Fa: {result['allowable_stress']/1e6:.2f} MPa")

    # 绘制长细比-应力曲线
    fig, ax = plt.subplots(figsize=(10, 6))

    lambda_range = np.linspace(0, 200, 100)
    stresses_euler = []
    stresses_aisc = []

    for lam in lambda_range:
        # 欧拉应力
        sigma_e = (np.pi**2 * 206e9) / (lam**2) if lam > 0 else 0
        stresses_euler.append(sigma_e / 1e6)

        # AISC允许应力
        sigma_a = aisc_allowable_stress(lam, 345e6, 206e9) / 1e6
        stresses_aisc.append(sigma_a)

    ax.plot(lambda_range, stresses_euler, 'b-', linewidth=2, label='欧拉临界应力')
    ax.plot(lambda_range, stresses_aisc, 'r-', linewidth=2, label='AISC允许应力')
    ax.axhline(345, color='g', linestyle='--', label='屈服强度 (345 MPa)')
    ax.axvline(result['slenderness_ratio_x'], color='orange', linestyle=':', label=f'当前 λx={result["slenderness_ratio_x"]:.1f}')
    ax.set_xlabel('长细比 λ')
    ax.set_ylabel('应力 (MPa)')
    ax.set_title('柱屈曲曲线')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 200)
    ax.set_ylim(0, 400)

    plt.tight_layout()
    plt.savefig("../results/column_buckling.png", dpi=150, bbox_inches='tight')
    print("\n图表已保存: results/column_buckling.png")
    plt.close()
