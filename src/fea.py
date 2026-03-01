"""
有限元分析模块 (Finite Element Analysis)
包含桁架、梁、杆件结构的有限元分析
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional
from enum import Enum


class ElementType(Enum):
    """单元类型"""
    TRUSS = "truss"          # 桁架单元（铰接）
    BEAM = "beam"            # 梁单元（刚性连接）
    FRAME = "frame"          # 框架单元
    SPRING = "spring"        # 弹簧单元


@dataclass
class Node:
    """节点"""
    id: int
    x: float                # X坐标 (m)
    y: float                # Y坐标 (m)
    fixity: Tuple[bool, bool, bool] = (False, False, False)  # (固定X, 固定Y, 固定转动)
    loads: Tuple[float, float, float] = (0.0, 0.0, 0.0)   # (Fx, Fy, M)

    def __repr__(self):
        return f"Node({self.id}, {self.x}, {self.y})"


@dataclass
class FEMaterial:
    """有限元材料属性"""
    name: str
    E: float               # 弹性模量 (Pa)
    A: float               # 截面积 (m^2)
    density: float = 7850  # 密度 (kg/m^3)


@dataclass
class Element:
    """单元基类"""
    id: int
    node_i: int            # 起始节点ID
    node_j: int            # 结束节点ID
    material: FEMaterial
    element_type: ElementType = ElementType.TRUSS
    _length: float = 0.0     # 缓存长度


class TrussElement(Element):
    """桁架单元（只承受轴向力）"""

    def __init__(self, id: int, node_i: int, node_j: int, material: FEMaterial):
        super().__init__(id, node_i, node_j, material, ElementType.TRUSS)

    def length(self, nodes: List[Node]) -> float:
        """计算单元长度"""
        ni, nj = nodes[self.node_i], nodes[self.node_j]
        dx = nj.x - ni.x
        dy = nj.y - ni.y
        return np.sqrt(dx**2 + dy**2)

    def stiffness_matrix(self, nodes: List[Node]) -> np.ndarray:
        """
        计算局部坐标系下的单元刚度矩阵 (2x2)
        [k] = (EA/L) * [[1, -1], [-1, 1]]
        """
        L = self.length(nodes)
        E = self.material.E
        A = self.material.A

        k = (E * A / L) * np.array([[1, -1], [-1, 1]])
        return k

    def global_stiffness_matrix(self, nodes: List[Node]) -> np.ndarray:
        """
        计算全局坐标系下的单元刚度矩阵 (4x4)
        """
        ni, nj = nodes[self.node_i], nodes[self.node_j]

        # 方向余弦
        L = self.length(nodes)
        c = (nj.x - ni.x) / L  # cos(theta)
        s = (nj.y - ni.y) / L  # sin(theta)

        E = self.material.E
        A = self.material.A

        # 变换矩阵 T
        T = np.array([
            [c, s, 0, 0],
            [0, 0, c, s]
        ])

        # 局部刚度矩阵
        k_local = (E * A / L) * np.array([[1, -1], [-1, 1]])

        # 全局刚度矩阵 K = T^T * k_local * T
        K = T.T @ k_local @ T

        return K

    def get_stress(self, nodes: List[Node], displacements: np.ndarray) -> float:
        """
        计算单元应力

        Args:
            nodes: 节点列表
            displacements: 位移向量 [u1, v1, u2, v2, ...]

        Returns:
            应力 (Pa), 正值为拉应力
        """
        ni, nj = nodes[self.node_i], nodes[self.node_j]
        L = self.length(nodes)

        # 提取节点位移
        u_i = displacements[self.node_i * 2]
        v_i = displacements[self.node_i * 2 + 1]
        u_j = displacements[self.node_j * 2]
        v_j = displacements[self.node_j * 2 + 1]

        # 方向余弦
        c = (nj.x - ni.x) / L
        s = (nj.y - ni.y) / L

        # 轴向位移
        delta_L = c * (u_j - u_i) + s * (v_j - v_i)

        # 应变 = delta_L / L
        strain = delta_L / L

        # 应力 = E * 应变
        stress = self.material.E * strain

        return stress

    def get_strain(self, nodes: List[Node], displacements: np.ndarray) -> float:
        """计算单元应变"""
        stress = self.get_stress(nodes, displacements)
        return stress / self.material.E

    def get_axial_force(self, nodes: List[Node], displacements: np.ndarray) -> float:
        """计算轴力 (N), 正值为拉力"""
        stress = self.get_stress(nodes, displacements)
        return stress * self.material.A


@dataclass
class FEAResults:
    """有限元分析结果"""
    nodes: List[Node] = field(default_factory=list)
    elements: List[Element] = field(default_factory=list)
    displacements: np.ndarray = field(default_factory=lambda: np.array([]))
    stresses: Dict[int, float] = field(default_factory=dict)
    reactions: Dict[int, Tuple[float, float]] = field(default_factory=dict)
    element_forces: Dict[int, float] = field(default_factory=dict)

    def plot_structure(
        self,
        show_deformation: bool = True,
        scale: float = 100,
        figsize=(12, 8)
    ):
        """绘制结构和变形"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

        # 原始结构
        for elem in self.elements:
            if isinstance(elem, TrussElement):
                ni, nj = self.nodes[elem.node_i], self.nodes[elem.node_j]
                ax1.plot([ni.x, nj.x], [ni.y, nj.y], 'b-o', linewidth=2, markersize=8)

        # 绘制节点
        x = [n.x for n in self.nodes]
        y = [n.y for n in self.nodes]
        ax1.plot(x, y, 'bo', markersize=10, zorder=5)

        # 绘制支座
        for node in self.nodes:
            if node.fixity[0] or node.fixity[1]:
                marker = '^' if node.fixity[1] else '>' if node.fixity[0] else 'o'
                ax1.plot(node.x, node.y, marker, markersize=15, color='red', zorder=6)

        # 绘制载荷
        for node in self.nodes:
            fx, fy, _ = node.loads
            if abs(fx) > 0 or abs(fy) > 0:
                ax1.arrow(node.x, node.y, fx/1000, fy/1000,
                         head_width=0.1, head_length=0.1, fc='red', ec='red')

        ax1.set_aspect('equal')
        ax1.grid(True, alpha=0.3)
        ax1.set_title('原始结构')
        ax1.set_xlabel('X (m)')
        ax1.set_ylabel('Y (m)')

        # 变形后的结构
        if show_deformation and len(self.displacements) > 0:
            for elem in self.elements:
                if isinstance(elem, TrussElement):
                    ni, nj = self.nodes[elem.node_i], self.nodes[elem.node_j]
                    u_i = self.displacements[elem.node_i * 2] * scale
                    v_i = self.displacements[elem.node_i * 2 + 1] * scale
                    u_j = self.displacements[elem.node_j * 2] * scale
                    v_j = self.displacements[elem.node_j * 2 + 1] * scale

                    x_def = [ni.x + u_i, nj.x + u_j]
                    y_def = [ni.y + v_i, nj.y + v_j]

                    # 根据应力着色
                    stress = self.stresses.get(elem.id, 0)
                    color = 'red' if stress > 0 else 'blue' if stress < 0 else 'gray'

                    ax2.plot(x_def, y_def, '-', color=color, linewidth=2)

            # 变形后的节点
            x_def = [self.nodes[i].x + self.displacements[i*2]*scale for i in range(len(self.nodes))]
            y_def = [self.nodes[i].y + self.displacements[i*2+1]*scale for i in range(len(self.nodes))]
            ax2.plot(x_def, y_def, 'go', markersize=8, zorder=5)

            # 绘制原始结构（虚线）
            for elem in self.elements:
                if isinstance(elem, TrussElement):
                    ni, nj = self.nodes[elem.node_i], self.nodes[elem.node_j]
                    ax2.plot([ni.x, nj.x], [ni.y, nj.y], 'k--', alpha=0.3)

        ax2.set_aspect('equal')
        ax2.grid(True, alpha=0.3)
        ax2.set_title(f'变形图 (放大{scale}倍)')
        ax2.set_xlabel('X (m)')
        ax2.set_ylabel('Y (m)')

        plt.tight_layout()
        return fig

    def plot_stress(self, figsize=(10, 6)):
        """绘制单元应力分布"""
        fig, ax = plt.subplots(figsize=figsize)

        if not self.elements:
            return fig

        elem_ids = []
        stresses = []
        colors = []

        for elem in self.elements:
            if isinstance(elem, TrussElement):
                elem_ids.append(elem.id)
                stress = self.stresses.get(elem.id, 0) / 1e6  # MPa
                stresses.append(stress)
                colors.append('red' if stress > 0 else 'blue')

        bars = ax.bar(elem_ids, stresses, color=colors, alpha=0.7)
        ax.axhline(0, color='k', linestyle='--', linewidth=1)
        ax.set_xlabel('单元编号')
        ax.set_ylabel('应力 (MPa)')
        ax.set_title('单元应力分布 (红色=拉应力, 蓝色=压应力)')
        ax.grid(True, alpha=0.3, axis='y')

        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}',
                   ha='center', va='bottom' if height > 0 else 'top')

        plt.tight_layout()
        return fig


class FEModel:
    """有限元模型"""

    def __init__(self, name: str = "FE Model"):
        self.name = name
        self.nodes: List[Node] = []
        self.elements: List[Element] = []
        self.n_dof = 0  # 总自由度数

    def add_node(
        self,
        x: float,
        y: float,
        fixity: Tuple[bool, bool, bool] = (False, False, False),
        loads: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    ) -> int:
        """添加节点，返回节点ID"""
        node_id = len(self.nodes)
        node = Node(node_id, x, y, fixity, loads)
        self.nodes.append(node)
        return node_id

    def add_truss_element(
        self,
        node_i: int,
        node_j: int,
        material: FEMaterial
    ) -> int:
        """添加桁架单元"""
        elem_id = len(self.elements)
        elem = TrussElement(elem_id, node_i, node_j, material)
        self.elements.append(elem)
        return elem_id

    def assemble_stiffness_matrix(self) -> np.ndarray:
        """组装总体刚度矩阵"""
        n_nodes = len(self.nodes)
        n_dof = n_nodes * 2  # 每个节点2个自由度 (u, v)

        K = np.zeros((n_dof, n_dof))

        # 组装每个单元的刚度矩阵
        for elem in self.elements:
            if isinstance(elem, TrussElement):
                k_elem = elem.global_stiffness_matrix(self.nodes)

                # 组装到总体刚度矩阵
                dof_indices = [
                    elem.node_i * 2,     # u_i
                    elem.node_i * 2 + 1, # v_i
                    elem.node_j * 2,     # u_j
                    elem.node_j * 2 + 1  # v_j
                ]

                for i in range(4):
                    for j in range(4):
                        K[dof_indices[i], dof_indices[j]] += k_elem[i, j]

        return K

    def apply_boundary_conditions(self, K: np.ndarray, F: np.ndarray) -> Tuple[np.ndarray, np.ndarray, List[int]]:
        """
        应用边界条件

        Returns:
            K_reduced: 约束后的刚度矩阵
            F_reduced: 约束后的力向量
            free_dofs: 自由度列表
        """
        n_dof = len(self.nodes) * 2
        fixed_dofs = []

        # 找出所有被约束的自由度
        for node in self.nodes:
            if node.fixity[0]:  # 固定X
                fixed_dofs.append(node.id * 2)
            if node.fixity[1]:  # 固定Y
                fixed_dofs.append(node.id * 2 + 1)

        # 自由度（未被约束的）
        free_dofs = [i for i in range(n_dof) if i not in fixed_dofs]

        # 约束后的刚度矩阵和力向量
        K_reduced = K[np.ix_(free_dofs, free_dofs)]
        F_reduced = F[free_dofs]

        return K_reduced, F_reduced, free_dofs

    def solve(self) -> FEAResults:
        """求解有限元问题"""
        # 1. 组装总体刚度矩阵
        K = self.assemble_stiffness_matrix()

        # 2. 组装载荷向量
        n_dof = len(self.nodes) * 2
        F = np.zeros(n_dof)

        for node in self.nodes:
            fx, fy, _ = node.loads
            F[node.id * 2] = fx
            F[node.id * 2 + 1] = fy

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

        # 6. 计算单元应力
        stresses = {}
        element_forces = {}

        for elem in self.elements:
            if isinstance(elem, TrussElement):
                stress = elem.get_stress(self.nodes, u)
                forces = elem.get_axial_force(self.nodes, u)
                stresses[elem.id] = stress
                element_forces[elem.id] = forces

        # 7. 计算支座反力
        reactions = {}
        K_full = K  # 完整刚度矩阵
        R = K_full @ u - F  # 反力 = Ku - F

        for node in self.nodes:
            rx = R[node.id * 2] if node.fixity[0] else 0
            ry = R[node.id * 2 + 1] if node.fixity[1] else 0
            if abs(rx) > 1e-6 or abs(ry) > 1e-6:
                reactions[node.id] = (rx, ry)

        return FEAResults(
            nodes=self.nodes,
            elements=self.elements,
            displacements=u,
            stresses=stresses,
            reactions=reactions,
            element_forces=element_forces
        )


# 便捷函数
def create_bar_model(
    length: float,
    n_elements: int,
    E: float,
    A: float,
    axial_force: float
) -> FEModel:
    """
    创建一维杆件拉伸/压缩模型
    简化版本：只考虑 X 方向的位移

    Args:
        length: 杆件总长 (m)
        n_elements: 单元数量
        E: 弹性模量 (Pa)
        A: 截面积 (m^2)
        axial_force: 轴向力 (N), 正值为拉伸

    Returns:
        FEModel 对象
    """
    model = FEModel(name="Bar Model")

    # 材料属性
    material = FEMaterial(
        name="Bar",
        E=E,
        A=A,
        density=7850
    )

    # 创建节点（沿 X 轴，Y=0，只允许 X 方向位移）
    dx = length / n_elements
    for i in range(n_elements + 1):
        x = i * dx
        # 左端固定，右端施加力
        if i == 0:
            fixity = (True, True, False)  # 固定X和Y，防止刚体位移
            loads = (0, 0, 0)
        elif i == n_elements:
            fixity = (False, True, False)  # 允许X位移，固定Y
            loads = (axial_force, 0, 0)
        else:
            fixity = (False, True, False)  # 允许X位移，固定Y
            loads = (0, 0, 0)

        model.add_node(x, 0, fixity, loads)

    # 创建单元
    for i in range(n_elements):
        model.add_truss_element(i, i + 1, material)

    return model


def analyze_cantilever_bar(
    length: float = 1.0,
    diameter: float = 0.02,
    force: float = 10000,
    material_E: float = 200e9,
    n_elements: int = 10
) -> FEAResults:
    """
    悬臂杆拉伸分析

    Args:
        length: 杆长 (m)
        diameter: 直径 (m)
        force: 拉力 (N)
        material_E: 弹性模量 (Pa)
        n_elements: 单元数量

    Returns:
        分析结果
    """
    A = np.pi * (diameter / 2) ** 2

    model = create_bar_model(
        length=length,
        n_elements=n_elements,
        E=material_E,
        A=A,
        axial_force=force
    )

    return model.solve()


def analyze_fixed_bar_compression(
    length: float = 1.0,
    diameter: float = 0.05,
    force: float = -500000,
    material_E: float = 200e9,
    n_elements: int = 10
) -> FEAResults:
    """
    两端固定杆压缩分析

    Args:
        length: 杆长 (m)
        diameter: 直径 (m)
        force: 压力 (N), 负值表示压缩
        material_E: 弹性模量 (Pa)
        n_elements: 单元数量

    Returns:
        分析结果
    """
    A = np.pi * (diameter / 2) ** 2

    model = FEModel(name="Fixed-Fixed Bar")

    material = FEMaterial(name="Bar", E=material_E, A=A, density=7850)

    # 创建节点（两端固定）
    dx = length / n_elements
    for i in range(n_elements + 1):
        x = i * dx
        # 两端固定
        if i == 0 or i == n_elements:
            fixity = (True, True, False)  # 固定X和Y
            loads = (0, 0, 0)
        else:
            fixity = (False, True, False)  # 允许X位移，固定Y
            loads = (0, 0, 0)

        model.add_node(x, 0, fixity, loads)

    # 创建单元
    for i in range(n_elements):
        model.add_truss_element(i, i + 1, material)

    return model.solve()


if __name__ == "__main__":
    # 测试：悬臂杆拉伸
    print("=== 悬臂杆拉伸试验 ===")
    results = analyze_cantilever_bar(
        length=1.0,
        diameter=0.02,
        force=50000,  # 50 kN 拉力
        material_E=200e9,
        n_elements=5
    )

    print(f"单元应力 (MPa):")
    for elem_id, stress in results.stresses.items():
        print(f"  单元 {elem_id}: {stress/1e6:.2f} MPa")

    print(f"\n节点位移 (mm):")
    for i, node in enumerate(results.nodes):
        u = results.displacements[i * 2] * 1000
        print(f"  节点 {i} ({node.x:.2f}m): {u:.4f} mm")

    # 绘图
    fig1 = results.plot_structure(scale=1000)
    plt.savefig("../results/fea_bar_tension.png", dpi=150)
    plt.close()

    fig2 = results.plot_stress()
    plt.savefig("../results/fea_stress.png", dpi=150)
    plt.close()

    print("\n图表已保存到 results/")
