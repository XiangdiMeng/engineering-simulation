"""
框架结构分析模块 (Frame Structure Analysis)
支持梁单元（考虑弯矩、剪力、轴力耦合）的2D框架分析
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional
from enum import Enum

from .fea import Node, FEMaterial, FEAResults
from .materials import Material


class SectionType(Enum):
    """截面类型"""
    RECTANGULAR = "rectangular"    # 矩形
    CIRCULAR = "circular"          # 圆形
    I_SECTION = "i_section"        # 工字形
    T_SECTION = "t_section"        # T形
    BOX = "box"                    # 箱形
    CUSTOM = "custom"              # 自定义


@dataclass
class Section:
    """截面属性"""
    section_type: SectionType
    A: float           # 截面积 (m^2)
    Iy: float          # 惯性矩绕y轴 (m^4)
    Iz: float          # 惯性矩绕z轴 (m^4)
    J: float = 0.0     # 扭转常数 (m^4)

    # 截面尺寸（用于绘图）
    width: float = 0.1     # 宽度 (m)
    height: float = 0.1    # 高度 (m)

    @staticmethod
    def rectangular(width: float, height: float) -> 'Section':
        """创建矩形截面"""
        A = width * height
        I = (width * height**3) / 12
        return Section(
            section_type=SectionType.RECTANGULAR,
            A=A,
            Iy=I,
            Iz=I,
            width=width,
            height=height
        )

    @staticmethod
    def circular(diameter: float) -> 'Section':
        """创建圆形截面"""
        A = np.pi * (diameter / 2)**2
        I = (np.pi * diameter**4) / 64
        return Section(
            section_type=SectionType.CIRCULAR,
            A=A,
            Iy=I,
            Iz=I,
            width=diameter,
            height=diameter
        )

    @staticmethod
    def i_section(
        height: float,   # 总高 (m)
        width: float,    # 翼缘宽 (m)
        tf: float,       # 翼缘厚 (m)
        tw: float        # 腹板厚 (m)
    ) -> 'Section':
        """创建工字形截面"""
        # 简化的工字钢计算
        A = 2 * width * tf + (height - 2 * tf) * tw

        # 惯性矩（中性轴在中心）
        I_top_bottom = 2 * (width * tf**3 / 12 + width * tf * ((height - tf) / 2)**2)
        I_web = (tw * (height - 2 * tf)**3) / 12
        I = I_top_bottom + I_web

        return Section(
            section_type=SectionType.I_SECTION,
            A=A,
            Iy=I,
            Iz=I,
            width=width,
            height=height
        )


@dataclass
class FrameMaterial:
    """框架材料属性（继承FEMaterial并扩展）"""
    E: float           # 弹性模量 (Pa)
    G: float           # 剪切模量 (Pa)
    A: float           # 截面积 (m^2)
    I: float           # 惯性矩 (m^4)
    density: float = 7850  # 密度 (kg/m^3)
    name: str = "Frame Material"

    @classmethod
    def from_material_and_section(
        cls,
        material: Material,
        section: Section
    ) -> 'FrameMaterial':
        """从材料和截面创建"""
        return cls(
            name=f"{material.name}",
            E=material.elastic_modulus,
            G=material.shear_modulus,
            A=section.A,
            I=section.Iz,  # 使用z轴惯性矩（平面内弯曲）
            density=material.density
        )


@dataclass
class FrameElement:
    """框架单元（考虑弯矩的梁单元）"""
    id: int
    node_i: int
    node_j: int
    material: FrameMaterial
    section: Optional[Section] = None
    release_i: Tuple[bool, bool, bool] = (False, False, False)  # 起端释放 (弯矩, 剪力, 轴力)
    release_j: Tuple[bool, bool, bool] = (False, False, False)  # 终端释放

    def length(self, nodes: List[Node]) -> float:
        """计算单元长度"""
        ni, nj = nodes[self.node_i], nodes[self.node_j]
        dx = nj.x - ni.x
        dy = nj.y - ni.y
        return np.sqrt(dx**2 + dy**2)

    def direction_cosine(self, nodes: List[Node]) -> Tuple[float, float]:
        """计算方向余弦 (cos, sin)"""
        ni, nj = nodes[self.node_i], nodes[self.node_j]
        L = self.length(nodes)
        c = (nj.x - ni.x) / L
        s = (nj.y - ni.y) / L
        return c, s

    def local_stiffness_matrix(self) -> np.ndarray:
        """
        计算局部坐标系下的单元刚度矩阵 (6x6)

        自由度顺序: [u1, v1, theta1, u2, v2, theta2]
        其中: u=轴向位移, v=横向位移, theta=转角
        """
        E = self.material.E
        A = self.material.A
        I = self.material.I
        L = 1.0  # 局部坐标系中，稍后变换时会考虑实际长度

        # 轴向刚度 (EA/L)
        k_axial = (E * A / L) * np.array([
            [1, 0, 0, -1, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [-1, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0]
        ])

        # 弯曲刚度 (欧拉-伯努利梁)
        k_bending = (E * I / L**3) * np.array([
            [0, 0, 0, 0, 0, 0],
            [0, 12, 6*L, 0, -12, 6*L],
            [0, 6*L, 4*L**2, 0, -6*L, 2*L**2],
            [0, 0, 0, 0, 0, 0],
            [0, -12, -6*L, 0, 12, -6*L],
            [0, 6*L, 2*L**2, 0, -6*L, 4*L**2]
        ])

        return k_axial + k_bending

    def global_stiffness_matrix(self, nodes: List[Node]) -> np.ndarray:
        """
        计算全局坐标系下的单元刚度矩阵 (6x6)
        """
        L = self.length(nodes)
        c, s = self.direction_cosine(nodes)

        E = self.material.E
        A = self.material.A
        I = self.material.I

        # 直接在全局坐标系下组装（考虑方向余弦）
        # 使用标准公式

        c2 = c**2
        s2 = s**2
        cs = c * s

        # 轴向项
        k1 = (E * A / L)
        # 弯曲项
        k2 = (12 * E * I / L**3)
        k3 = (6 * E * I / L**2)
        k4 = (4 * E * I / L)
        k5 = (2 * E * I / L)

        # 6x6 全局刚度矩阵
        # DOF: [u_i, v_i, theta_i, u_j, v_j, theta_j]
        K = np.array([
            # u_i             v_i             theta_i        u_j             v_j             theta_j
            [k1*c2 + k2*s2,   (k1-k2)*cs,     -k3*s,         -(k1*c2 + k2*s2), -(k1-k2)*cs,    -k3*s       ],  # u_i
            [(k1-k2)*cs,     k1*s2 + k2*c2,   k3*c,          -(k1-k2)*cs,    -(k1*s2 + k2*c2),  k3*c       ],  # v_i
            [-k3*s,           k3*c,           k4,             k3*s,           -k3*c,           k5          ],  # theta_i
            [-(k1*c2 + k2*s2), -(k1-k2)*cs,   k3*s,          k1*c2 + k2*s2,   (k1-k2)*cs,     k3*s       ],  # u_j
            [-(k1-k2)*cs,    -(k1*s2 + k2*c2), -k3*c,         (k1-k2)*cs,     k1*s2 + k2*c2,   -k3*c       ],  # v_j
            [-k3*s,           -k3*c,          k5,             k3*s,           -k3*c,           k4          ]   # theta_j
        ])

        return K

    def get_end_forces(
        self,
        nodes: List[Node],
        displacements: np.ndarray
    ) -> Tuple[float, float, float, float, float, float]:
        """
        计算单元端部内力

        Returns:
            (Fi_x, Fi_y, Mi, Fj_x, Fj_y, Mj)
            起端和终端的力（包括轴力、剪力、弯矩）
        """
        L = self.length(nodes)
        c, s = self.direction_cosine(nodes)

        # 提取节点位移
        u_i = displacements[self.node_i * 3]
        v_i = displacements[self.node_i * 3 + 1]
        theta_i = displacements[self.node_i * 3 + 2]
        u_j = displacements[self.node_j * 3]
        v_j = displacements[self.node_j * 3 + 1]
        theta_j = displacements[self.node_j * 3 + 2]

        E = self.material.E
        A = self.material.A
        I = self.material.I

        # 局部坐标系下的位移
        # 轴向位移
        u_local_i = c * u_i + s * v_i
        u_local_j = c * u_j + s * v_j
        # 横向位移
        v_local_i = -s * u_i + c * v_i
        v_local_j = -s * u_j + c * v_j

        # 局部坐标系下的端部力
        # 轴力
        N = (E * A / L) * (u_local_j - u_local_i)

        # 剪力和弯矩
        V = (12 * E * I / L**3) * (v_local_i - v_local_j) + (6 * E * I / L**2) * (theta_i + theta_j)
        M_i = (6 * E * I / L**2) * (v_local_j - v_local_i) + (4 * E * I / L) * theta_i + (2 * E * I / L) * theta_j
        M_j = (6 * E * I / L**2) * (v_local_j - v_local_i) + (2 * E * I / L) * theta_i + (4 * E * I / L) * theta_j

        # 转换回全局坐标系
        Fi_x = N * c - V * s
        Fi_y = N * s + V * c
        Fj_x = -N * c + V * s
        Fj_y = -N * s - V * c

        return Fi_x, Fi_y, M_i, Fj_x, Fj_y, M_j

    def get_max_stress(
        self,
        nodes: List[Node],
        displacements: np.ndarray
    ) -> Tuple[float, float]:
        """
        计算最大应力

        Returns:
            (max_axial_stress, max_bending_stress)
        """
        Fi_x, Fi_y, M_i, Fj_x, Fj_y, M_j = self.get_end_forces(nodes, displacements)

        # 轴力（取较大值）
        N = max(abs(Fi_x), abs(Fj_x))

        # 弯矩（取较大值）
        M = max(abs(M_i), abs(M_j))

        if self.section is None:
            # 近似计算
            A = self.material.A
            I = self.material.I
            # 假设矩形截面
            h = (12 * I / A)**0.5
            S = I / (h / 2)  # 截面模量
        else:
            A = self.section.A
            I = self.section.Iz
            h = self.section.height
            S = I / (h / 2)

        sigma_axial = N / A
        sigma_bending = M / S

        return sigma_axial, sigma_bending


@dataclass
class FrameNode:
    """框架节点"""
    id: int
    x: float
    y: float
    fixity: Tuple[bool, bool, bool] = (False, False, False)  # (固定X, 固定Y, 固定转动)
    loads: Tuple[float, float, float] = (0.0, 0.0, 0.0)   # (Fx, Fy, M)
    spring: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # (Kx, Ky, K_theta) 弹簧刚度

    def __repr__(self):
        return f"FrameNode({self.id}, {self.x:.2f}, {self.y:.2f})"


@dataclass
class FrameResults:
    """框架分析结果"""
    nodes: List[FrameNode]
    elements: List[FrameElement]
    displacements: np.ndarray
    reactions: Dict[int, Tuple[float, float, float]]
    element_forces: Dict[int, Tuple[float, float, float, float, float, float]]
    element_stresses: Dict[int, Tuple[float, float, float]]  # (轴力应力, 弯曲应力, 组合应力)

    def plot(
        self,
        show_deformation: bool = True,
        show_forces: bool = True,
        show_moment: bool = True,
        scale: float = 50,
        figsize=(16, 10)
    ):
        """绘制框架分析结果"""
        if show_forces and show_moment:
            fig, axes = plt.subplots(2, 2, figsize=figsize)
        else:
            fig, axes = plt.subplots(1, 1, figsize=(12, 8))
            axes = np.array([[axes]])

        # 1. 结构简图
        ax1 = axes[0, 0]
        self._plot_structure(ax1, deformed=False)

        # 2. 变形图
        if show_deformation:
            ax2 = axes[0, 1]
            self._plot_structure(ax2, deformed=True, scale=scale)

        # 3. 弯矩图
        if show_moment:
            ax3 = axes[1, 0]
            self._plot_moment_diagram(ax3)

        # 4. 剪力图
        if show_forces:
            ax4 = axes[1, 1]
            self._plot_shear_diagram(ax4)

        plt.tight_layout()
        return fig

    def _plot_structure(self, ax, deformed: bool = False, scale: float = 50):
        """绘制结构"""
        for elem in self.elements:
            ni, nj = self.nodes[elem.node_i], self.nodes[elem.node_j]

            if deformed:
                u_i = self.displacements[elem.node_i * 3] * scale
                v_i = self.displacements[elem.node_i * 3 + 1] * scale
                u_j = self.displacements[elem.node_j * 3] * scale
                v_j = self.displacements[elem.node_j * 3 + 1] * scale

                x = [ni.x + u_i, nj.x + u_j]
                y = [ni.y + v_i, nj.y + v_j]

                # 绘制原始结构（虚线）
                ax.plot([ni.x, nj.x], [ni.y, nj.y], 'k--', alpha=0.3, linewidth=1)
            else:
                x = [ni.x, nj.x]
                y = [ni.y, nj.y]

            ax.plot(x, y, 'b-o', linewidth=3, markersize=8)

        # 绘制节点和支座
        for node in self.nodes:
            marker = '^' if node.fixity[0] or node.fixity[1] else 'o'
            color = 'red' if node.fixity[0] or node.fixity[1] or node.fixity[2] else 'black'
            ax.plot(node.x, node.y, marker, markersize=12, color=color, zorder=5)
            ax.text(node.x, node.y - 0.2, f'{node.id}', fontsize=9, ha='center')

        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        title = '变形图' if deformed else '结构简图'
        if deformed:
            title += f' (放大{scale}倍)'
        ax.set_title(title)
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')

    def _plot_moment_diagram(self, ax):
        """绘制弯矩图"""
        max_moment = 0

        for elem in self.elements:
            forces = self.element_forces.get(elem.id)
            if forces is None:
                continue

            Mi, Mj = forces[2], forces[5]

            ni, nj = self.nodes[elem.node_i], self.nodes[elem.node_j]
            x = [ni.x, nj.x]
            y = [ni.y, nj.y]

            # 弯矩值（绘图用）
            # 计算垂直于杆件的方向
            dx = nj.x - ni.x
            dy = nj.y - ni.y
            L = np.sqrt(dx**2 + dy**2)
            nx, ny = -dy/L, dx/L  # 法向量

            # 缩放因子
            scale = 0.001

            # 绘制弯矩（叠加在结构上）
            # 在杆件中点显示弯矩值
            mid_x = (ni.x + nj.x) / 2
            mid_y = (ni.y + nj.y) / 2

            # 取较大弯矩
            M_plot = max(abs(Mi), abs(Mj))

            # 绘制弯矩图
            M_values = np.linspace(Mi, Mj, 20)
            x_local = np.linspace(0, L, 20)

            # 弯矩图偏移
            offset_x = mid_x + ny * M_values * scale
            offset_y = mid_y - nx * M_values * scale

            # 绘制杆件
            ax.plot(x, y, 'k-', linewidth=1, alpha=0.3)

            # 绘制弯矩图
            x_plot = []
            y_plot = []
            for i, (xi_local, M) in enumerate(zip(x_local, M_values)):
                # 沿杆件的位置
                px = ni.x + (dx/L) * xi_local
                py = ni.y + (dy/L) * xi_local
                # 弯矩偏移
                px += ny * M * scale
                py -= nx * M * scale
                x_plot.append(px)
                y_plot.append(py)

            color = 'red' if Mi > 0 or Mj > 0 else 'blue'
            ax.plot(x_plot, y_plot, color=color, linewidth=2)

            # 标注数值
            ax.text(mid_x, mid_y, f'{M_plot/1000:.1f}',
                   fontsize=8, ha='center', color=color,
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.7))

            max_moment = max(max_moment, abs(Mi), abs(Mj))

        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        ax.set_title(f'弯矩图 (kN·m)')
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')

    def _plot_shear_diagram(self, ax):
        """绘制剪力图"""
        for elem in self.elements:
            forces = self.element_forces.get(elem.id)
            if forces is None:
                continue

            Vi, Vj = forces[1], forces[4]  # 剪力

            ni, nj = self.nodes[elem.node_i], self.nodes[elem.node_j]

            mid_x = (ni.x + nj.x) / 2
            mid_y = (ni.y + nj.y) / 2

            V_avg = (Vi + Vj) / 2

            # 绘制杆件
            ax.plot([ni.x, nj.x], [ni.y, nj.y], 'k-', linewidth=1, alpha=0.3)

            # 绘制剪力箭头
            dx = nj.x - ni.x
            dy = nj.y - ni.y
            L = np.sqrt(dx**2 + dy**2)
            nx, ny = -dy/L, dx/L  # 法向量

            # 剪力方向
            scale = 0.0005
            ax.arrow(mid_x, mid_y, ny * V_avg * scale, -nx * V_avg * scale,
                    head_width=0.15, head_length=0.1, fc='green', ec='green')

            # 标注数值
            color = 'green'
            ax.text(mid_x, mid_y + 0.2, f'{V_avg/1000:.1f}kN',
                   fontsize=8, ha='center', color=color,
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.7))

        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        ax.set_title('剪力图 (kN)')
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')

    def print_summary(self):
        """打印结果摘要"""
        print("\n" + "="*60)
        print("框架结构分析结果")
        print("="*60)

        print(f"\n节点数: {len(self.nodes)}")
        print(f"单元数: {len(self.elements)}")

        print(f"\n最大位移:")
        max_disp_x = np.max(np.abs(self.displacements[0::3])) * 1000
        max_disp_y = np.max(np.abs(self.displacements[1::3])) * 1000
        max_disp_theta = np.max(np.abs(self.displacements[2::3])) * 180 / np.pi

        for i in range(0, len(self.displacements), 3):
            if abs(self.displacements[i]) > 0 or abs(self.displacements[i+1]) > 0:
                node_id = i // 3
                print(f"  节点 {node_id}: dx={self.displacements[i]*1000:.3f}mm, "
                      f"dy={self.displacements[i+1]*1000:.3f}mm, "
                      f"theta={self.displacements[i+2]*180/np.pi:.3f}°")

        print(f"\n支座反力:")
        for node_id, (rx, ry, rm) in self.reactions.items():
            print(f"  节点 {node_id}: Rx={rx/1000:.2f}kN, Ry={ry/1000:.2f}kN, M={rm/1000:.2f}kN·m")

        print(f"\n单元内力:")
        for elem_id, (Fxi, Fyi, Mi, Fxj, Fyj, Mj) in self.element_forces.items():
            N = (Fxi + Fxj) / 2 / 1000  # 平均轴力
            V = (Fyi + Fyj) / 2 / 1000  # 平均剪力
            M = max(abs(Mi), abs(Mj)) / 1000  # 最大弯矩
            print(f"  单元 {elem_id}: N={N:.2f}kN, V={V:.2f}kN, M={M:.2f}kN·m")


class FrameStructure:
    """框架结构"""

    def __init__(self, name: str = "Frame Structure"):
        self.name = name
        self.nodes: List[FrameNode] = []
        self.elements: List[FrameElement] = []
        self.materials: Dict[int, FrameMaterial] = {}

    def add_node(
        self,
        x: float,
        y: float,
        fix_x: bool = False,
        fix_y: bool = False,
        fix_theta: bool = False,
        fx: float = 0,
        fy: float = 0,
        moment: float = 0
    ) -> int:
        """添加节点"""
        node_id = len(self.nodes)
        node = FrameNode(
            id=node_id,
            x=x,
            y=y,
            fixity=(fix_x, fix_y, fix_theta),
            loads=(fx, fy, moment)
        )
        self.nodes.append(node)
        return node_id

    def add_element(
        self,
        node_i: int,
        node_j: int,
        material: FrameMaterial
    ) -> int:
        """添加框架单元"""
        elem_id = len(self.elements)
        elem = FrameElement(
            id=elem_id,
            node_i=node_i,
            node_j=node_j,
            material=material
        )
        self.elements.append(elem)
        return elem_id

    def assemble_stiffness_matrix(self) -> np.ndarray:
        """组装总体刚度矩阵"""
        n_nodes = len(self.nodes)
        n_dof = n_nodes * 3  # 每个节点3个自由度

        K = np.zeros((n_dof, n_dof))

        for elem in self.elements:
            k_elem = elem.global_stiffness_matrix(self.nodes)

            # 自由度索引
            dof_indices = [
                elem.node_i * 3,     # u_i
                elem.node_i * 3 + 1, # v_i
                elem.node_i * 3 + 2, # theta_i
                elem.node_j * 3,     # u_j
                elem.node_j * 3 + 1, # v_j
                elem.node_j * 3 + 2  # theta_j
            ]

            for i in range(6):
                for j in range(6):
                    K[dof_indices[i], dof_indices[j]] += k_elem[i, j]

        return K

    def apply_boundary_conditions(
        self,
        K: np.ndarray,
        F: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, List[int]]:
        """应用边界条件"""
        n_dof = len(self.nodes) * 3
        fixed_dofs = []

        for node in self.nodes:
            if node.fixity[0]:  # 固定X
                fixed_dofs.append(node.id * 3)
            if node.fixity[1]:  # 固定Y
                fixed_dofs.append(node.id * 3 + 1)
            if node.fixity[2]:  # 固定转动
                fixed_dofs.append(node.id * 3 + 2)

        free_dofs = [i for i in range(n_dof) if i not in fixed_dofs]

        K_reduced = K[np.ix_(free_dofs, free_dofs)]
        F_reduced = F[free_dofs]

        return K_reduced, F_reduced, free_dofs

    def solve(self) -> FrameResults:
        """求解框架结构"""
        # 1. 组装总体刚度矩阵
        K = self.assemble_stiffness_matrix()

        # 2. 组装载荷向量
        n_dof = len(self.nodes) * 3
        F = np.zeros(n_dof)

        for node in self.nodes:
            fx, fy, m = node.loads
            F[node.id * 3] = fx
            F[node.id * 3 + 1] = fy
            F[node.id * 3 + 2] = m

        # 3. 应用边界条件
        K_reduced, F_reduced, free_dofs = self.apply_boundary_conditions(K, F)

        # 4. 求解位移
        try:
            u_reduced = np.linalg.solve(K_reduced, F_reduced)
        except np.linalg.LinAlgError:
            raise ValueError("结构不稳定或缺少约束！")

        # 5. 组装完整位移向量
        u = np.zeros(n_dof)
        u[free_dofs] = u_reduced

        # 6. 计算单元内力
        element_forces = {}
        element_stresses = {}

        for elem in self.elements:
            forces = elem.get_end_forces(self.nodes, u)
            element_forces[elem.id] = forces

            # 计算应力
            sigma_a, sigma_b = elem.get_max_stress(self.nodes, u)
            element_stresses[elem.id] = (sigma_a, sigma_b, sigma_a + sigma_b)

        # 7. 计算支座反力
        reactions = {}
        R = K @ u - F

        for node in self.nodes:
            rx = R[node.id * 3] if node.fixity[0] else 0
            ry = R[node.id * 3 + 1] if node.fixity[1] else 0
            rm = R[node.id * 3 + 2] if node.fixity[2] else 0
            if abs(rx) > 1e-6 or abs(ry) > 1e-6 or abs(rm) > 1e-6:
                reactions[node.id] = (rx, ry, rm)

        return FrameResults(
            nodes=self.nodes,
            elements=self.elements,
            displacements=u,
            reactions=reactions,
            element_forces=element_forces,
            element_stresses=element_stresses
        )


# 便捷函数
def create_portal_frame(
    width: float = 6.0,
    height: float = 4.0,
    section_width: float = 0.2,
    section_height: float = 0.3,
    E: float = 200e9,
    fix_top: bool = False
) -> FrameStructure:
    """
    创建门式框架

    Parameters
    ----------
    width : float
        框架宽度 (m)
    height : float
        框架高度 (m)
    section_width : float
        截面宽度 (m)
    section_height : float
        截面高度 (m)
    E : float
        弹性模量 (Pa)
    fix_top : bool
        顶部是否固定（用于连续框架）

    Returns
    -------
    FrameStructure
    """
    frame = FrameStructure(name="门式框架")

    # 截面和材料
    section = Section.rectangular(section_width, section_height)
    material = FrameMaterial(
        name="Q345钢",
        E=E,
        G=E/(2*(1+0.3)),
        A=section.A,
        I=section.Iz,
        density=7850
    )

    # 创建节点
    # 左下角（固定）
    frame.add_node(0, 0, fix_x=True, fix_y=True, fix_theta=True)
    # 左上角
    frame.add_node(0, height, fix_theta=fix_top)
    # 右上角
    frame.add_node(width, height, fix_theta=fix_top)
    # 右下角（固定）
    frame.add_node(width, 0, fix_x=True, fix_y=True, fix_theta=True)

    # 创建单元
    # 左柱
    frame.add_element(0, 1, material)
    # 横梁
    frame.add_element(1, 2, material)
    # 右柱
    frame.add_element(2, 3, material)

    return frame


def create_cantilever_frame(
    length: float = 4.0,
    n_spans: int = 2,
    section_width: float = 0.15,
    section_height: float = 0.25,
    E: float = 200e9
) -> FrameStructure:
    """
    创建悬臂框架

    Parameters
    ----------
    length : float
        每跨长度 (m)
    n_spans : int
        跨数
    section_width : float
        截面宽度 (m)
    section_height : float
        截面高度 (m)
    E : float
        弹性模量 (Pa)

    Returns
    -------
    FrameStructure
    """
    frame = FrameStructure(name="悬臂框架")

    section = Section.rectangular(section_width, section_height)
    material = FrameMaterial(
        name="Q345钢",
        E=E,
        G=E/(2*(1+0.3)),
        A=section.A,
        I=section.Iz,
        density=7850
    )

    # 创建节点
    # 固定端
    frame.add_node(0, 0, fix_x=True, fix_y=True, fix_theta=True)

    # 其他节点
    for i in range(1, n_spans + 1):
        frame.add_node(i * length, 0)

    # 创建单元
    for i in range(n_spans):
        frame.add_element(i, i + 1, material)

    return frame


def analyze_frame_with_loads(
    frame: FrameStructure,
    horizontal_load: float = 10000,
    vertical_load: float = 20000
) -> FrameResults:
    """
    对框架施加载荷并分析

    Parameters
    ----------
    frame : FrameStructure
        框架结构
    horizontal_load : float
        水平载荷 (N)，施加在左上角
    vertical_load : float
        垂直载荷 (N)，施加在横梁中点

    Returns
    -------
    FrameResults
    """
    # 施加水平载荷（左上角）
    if horizontal_load != 0 and len(frame.nodes) > 1:
        node = frame.nodes[1]  # 左上角
        frame.nodes[1].loads = (horizontal_load, node.loads[1], node.loads[2])

    # 施加垂直载荷（横梁中点）
    if vertical_load != 0 and len(frame.nodes) > 2:
        node = frame.nodes[2]  # 右上角或横梁节点
        frame.nodes[2].loads = (node.loads[0], -vertical_load, node.loads[2])

    return frame.solve()


if __name__ == "__main__":
    # 测试：门式框架
    print("=== 门式框架分析 ===")

    frame = create_portal_frame(
        width=8.0,
        height=5.0,
        section_width=0.25,
        section_height=0.4,
        E=206e9
    )

    # 施加水平载荷
    frame.nodes[1].loads = (5000, 0, 0)  # 左上角水平力 5kN
    # 施加垂直载荷
    frame.nodes[2].loads = (0, -20000, 0)  # 右上角垂直力 20kN

    results = frame.solve()

    results.print_summary()

    # 绘图
    fig = results.plot(scale=100)
    plt.savefig("../results/frame_analysis.png", dpi=150, bbox_inches='tight')
    print("\n图表已保存: results/frame_analysis.png")
    plt.close()
