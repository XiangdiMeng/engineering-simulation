"""
桁架结构分析模块 (Truss Structure Analysis)
支持2D/3D桁架结构的建模、分析和可视化
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from mpl_toolkits.mplot3d import Axes3D
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional, Literal
from enum import Enum
import copy

from .fea import FEModel, TrussElement, FEAResults, FEMaterial, Node


class LoadType(Enum):
    """载荷类型"""
    DEAD = "dead"           # 恒载（自重）
    LIVE = "live"           # 活载（如雪载）
    WIND = "wind"           # 风载
    POINT = "point"         # 集中载荷
    DISTRIBUTED = "distributed"  # 分布载荷


@dataclass
class Load:
    """载荷定义"""
    load_type: LoadType
    magnitude: float       # 载荷大小 (N 或 N/m)
    node_id: int = -1       # 作用节点ID
    element_id: int = -1    # 作用单元ID
    direction: Tuple[float, float, float] = (0, -1, 0)  # 方向向量
    name: str = ""
    color: str = "red"


@dataclass
class TrussStructure:
    """桁架结构"""
    name: str
    nodes: List[Node] = field(default_factory=list)
    elements: List[TrussElement] = field(default_factory=list)
    materials: Dict[int, FEMaterial] = field(default_factory=dict)
    loads: List[Load] = field(default_factory=list)
    supports: Dict[int, Tuple[bool, bool]] = field(default_factory=dict)  # 支座 {node_id: (fix_x, fix_y)}

    def __post_init__(self):
        """初始化时设置默认材料"""
        if not self.materials:
            # 默认使用Q345钢
            self.materials[-1] = FEMaterial(
                name="Q345钢",
                E=206e9,
                A=0.001,  # 默认截面积
                density=7850
            )

    def add_node(
        self,
        x: float,
        y: float,
        z: float = 0.0,
        fix_x: bool = False,
        fix_y: bool = False,
        fix_z: bool = False
    ) -> int:
        """添加节点"""
        node_id = len(self.nodes)
        node = Node(
            id=node_id,
            x=x,
            y=y,
            fixity=(fix_x, fix_y, fix_z),
            loads=(0, 0, 0)
        )
        self.nodes.append(node)
        if fix_x or fix_y:
            self.supports[node_id] = (fix_x, fix_y)
        return node_id

    def add_element(
        self,
        node_i: int,
        node_j: int,
        E: float = 206e9,
        A: float = 0.001,
        material: Optional[FEMaterial] = None
    ) -> int:
        """添加桁架单元"""
        elem_id = len(self.elements)

        if material is None:
            # 使用默认材料或创建新材料
            mat_id = max(self.materials.keys()) if self.materials else -1
            mat = self.materials.get(mat_id, FEMaterial("Q345钢", E, A, 7850))
        else:
            mat = material

        elem = TrussElement(elem_id, node_i, node_j, mat)
        self.elements.append(elem)

        return elem_id

    def add_point_load(
        self,
        node_id: int,
        fx: float,
        fy: float,
        fz: float = 0,
        load_type: LoadType = LoadType.POINT,
        name: str = ""
    ):
        """添加集中载荷"""
        self.loads.append(Load(
            load_type=load_type,
            magnitude=np.sqrt(fx**2 + fy**2 + fz**2),
            node_id=node_id,
            direction=(fx, fy, fz),
            name=name
        ))

    def add_gravity_load(self, g: float = 9.81):
        """添加自重载荷（恒载）"""
        for elem in self.elements:
            # 计算单元重量
            length = elem.length(self.nodes)
            weight = elem.material.density * elem.material.A * length * g
            weight_per_node = weight / 2

            # 均分到两端节点
            self.loads.append(Load(
                load_type=LoadType.DEAD,
                magnitude=weight_per_node,
                node_id=elem.node_i,
                direction=(0, -1, 0),  # 向下
                name=f"自重_单元{elem.id}"
            ))
            self.loads.append(Load(
                load_type=LoadType.DEAD,
                magnitude=weight_per_node,
                node_id=elem.node_j,
                direction=(0, -1, 0),
                name=f"自重_单元{elem.id}"
            ))

    def add_distributed_load(
        self,
        element_id: int,
        magnitude: float,  # N/m
        angle: float = 0,  # 角度（弧度），从X轴正向逆时针
        load_type: LoadType = LoadType.DISTRIBUTED
    ):
        """添加分布载荷"""
        self.loads.append(Load(
            load_type=load_type,
            magnitude=magnitude,
            element_id=element_id,
            direction=(np.cos(angle), np.sin(angle), 0)
        ))

    def analyze(self) -> FEAResults:
        """分析桁架结构"""
        # 创建FE模型
        model = FEModel(name=self.name)

        # 添加节点
        for node in self.nodes:
            model.add_node(node.x, node.y, node.fixity, node.loads)

        # 应用载荷
        for load in self.loads:
            if load.node_id >= 0:
                fx, fy, fz = load.direction
                Fx = load.magnitude * fx / (np.sqrt(fx**2 + fy**2 + fz**2) + 1e-10)
                Fy = load.magnitude * fy / (np.sqrt(fx**2 + fy**2 + fz**2) + 1e-10)
                old_loads = model.nodes[load.node_id].loads
                model.nodes[load.node_id].loads = (
                    old_loads[0] + Fx,
                    old_loads[1] + Fy,
                    old_loads[2]
                )

        # 添加单元
        for elem in self.elements:
            model.add_truss_element(elem.node_i, elem.node_j, elem.material)

        # 求解
        return model.solve()

    def get_element_forces(self, results: FEAResults) -> Dict[int, Tuple[float, float, float]]:
        """获取单元内力（轴力、剪力、弯矩）"""
        forces = {}
        for elem in self.elements:
            if isinstance(elem, TrussElement):
                axial_force = results.element_forces.get(elem.id, 0)
                stress = results.stresses.get(elem.id, 0)
                forces[elem.id] = (axial_force, 0, stress)  # (轴力N, 剪力N, 应力Pa)
        return forces


def create_roof_truss(
    span: float = 12.0,      # 跨度 (m)
    height: float = 3.0,     # 高度 (m)
    n_bays: int = 6,         # 节数
    chord_A: float = 0.0005, # 弦杆截面积 (m^2)
    web_A: float = 0.0003,   # 腹杆截面积 (m^2)
    E: float = 206e9,        # 弹性模量 (Pa)
    snow_load: float = 1000  # 雪载 (N/m)
) -> TrussStructure:
    """
    创建三角形屋顶桁架（最稳定的Warren桁架形式）

    Parameters
    ----------
    span : float
        跨度 (m)
    height : float
        桁架高度 (m)
    n_bays : int
        节数（必须是偶数）
    chord_A : float
        上下弦杆截面积 (m^2)
    web_A : float
        腹杆截面积 (m^2)
    E : float
        弹性模量 (Pa)
    snow_load : float
        雪载 (N/m)，施加在上弦

    Returns
    -------
    TrussStructure
        桁架结构对象
    """
    truss = TrussStructure(name="三角形屋顶桁架")

    # 几何参数
    bay_width = span / n_bays

    # 创建节点（经典三角形桁架布局）
    # 下弦节点（编号 0 到 n_bays）
    for i in range(n_bays + 1):
        x = i * bay_width
        y = 0
        z = 0
        # 左端固定X和Y，右端也固定X和Y（两端铰接）
        if i == 0:
            truss.add_node(x, y, z, fix_x=True, fix_y=True)
        elif i == n_bays:
            truss.add_node(x, y, z, fix_x=True, fix_y=True)
        else:
            truss.add_node(x, y, z, fix_x=False, fix_y=False)

    # 上弦节点（编号 n_bays+1 到 2*n_bays-1）
    for i in range(n_bays):
        x = (i + 0.5) * bay_width
        y = height
        z = 0
        truss.add_node(x, y, z, fix_x=False, fix_y=False)

    # 材料定义
    chord_material = FEMaterial("上下弦", E, chord_A, 7850)
    web_material = FEMaterial("腹杆", E, web_A, 7850)

    # 下弦杆
    for i in range(n_bays):
        truss.add_element(i, i + 1, material=chord_material)

    # 上弦杆
    for i in range(n_bays - 1):
        node_i = n_bays + 1 + i
        node_j = n_bays + 2 + i
        truss.add_element(node_i, node_j, material=chord_material)

    # 腹杆（Warren桁架 - W形：对角线+竖杆交替）
    for i in range(n_bays):
        if i < n_bays - 1:
            # 对角线：下弦节点i到上弦节点i+1
            truss.add_element(i, n_bays + 1 + i + 1, material=web_material)
            # 对角线：下弦节点i+1到上弦节点i
            truss.add_element(i + 1, n_bays + 1 + i, material=web_material)
        else:
            # 最后一节只加竖杆
            truss.add_element(i, n_bays + 1 + i, material=web_material)

    # 添加载荷
    # 1. 自重
    truss.add_gravity_load()

    # 2. 雪载（作用在上弦节点）
    if snow_load > 0:
        # 将分布载荷简化为节点载荷
        load_per_node = snow_load * bay_width
        for i in range(n_bays):
            node_id = n_bays + 1 + i
            truss.add_point_load(node_id, 0, -load_per_node, load_type=LoadType.LIVE, name="雪载")

    return truss


def create_bridge_truss(
    span: float = 20.0,
    height: float = 4.0,
    n_panels: int = 8,
    chord_A: float = 0.002,
    web_A: float = 0.001,
    E: float = 200e9,
    traffic_load: float = 50000  # 车辆荷载 (N)
) -> TrussStructure:
    """
    创建桥梁桁架（Warren桁架）- 最稳定的形式

    Parameters
    ----------
    span : float
        跨度 (m)
    height : float
        桁架高度 (m)
    n_panels : int
        面板数量
    chord_A : float
        弦杆截面积 (m^2)
    web_A : float
        腹杆截面积 (m^2)
    E : float
        弹性模量 (Pa)
    traffic_load : float
        交通荷载 (N)，作用在下弦跨中

    Returns
    -------
    TrussStructure
        桥梁桁架对象
    """
    truss = TrussStructure(name="Warren桥梁桁架")

    panel_width = span / n_panels

    # 创建节点（上弦和下弦）
    # 下弦节点 0 到 n_panels
    for i in range(n_panels + 1):
        x = i * panel_width
        y = 0
        # 两端都铰接（固定X和Y）
        if i == 0 or i == n_panels:
            truss.add_node(x, y, 0, fix_x=True, fix_y=True)
        else:
            truss.add_node(x, y, 0, fix_x=False, fix_y=False)

    # 上弦节点
    for i in range(n_panels):
        x = (i + 0.5) * panel_width
        y = height
        truss.add_node(x, y, 0, False, False)

    # Warren桁架单元
    chord_mat = FEMaterial("弦杆", E, chord_A, 7850)
    web_mat = FEMaterial("腹杆", E, web_A, 7850)

    # 下弦杆
    for i in range(n_panels):
        truss.add_element(i, i + 1, material=chord_mat)

    # 上弦杆（连接相邻的上弦节点）
    for i in range(n_panels - 1):
        node_i = n_panels + 1 + i
        node_j = n_panels + 2 + i
        truss.add_element(node_i, node_j, material=chord_mat)

    # 腹杆（W形模式：对角线+竖杆交替）
    for i in range(n_panels):
        if i < n_panels - 1:
            # 对角线：下弦节点i到上弦节点i+1
            truss.add_element(i, n_panels + 1 + i + 1, material=web_mat)
            # 对角线：下弦节点i+1到上弦节点i
            truss.add_element(i + 1, n_panels + 1 + i, material=web_mat)
        else:
            # 最后一节只加竖杆
            truss.add_element(i, n_panels + 1 + i, material=web_mat)

    # 添加载荷
    truss.add_gravity_load()

    # 交通荷载（作用在跨中）
    if traffic_load != 0:
        mid_node = n_panels // 2
        truss.add_point_load(mid_node, 0, -traffic_load, name="车辆荷载")

    return truss


class TrussAnalysisResults:
    """桁架分析结果扩展"""
    def __init__(self, fe_results: FEAResults, structure: TrussStructure):
        self.fe_results = fe_results
        self.structure = structure
        self.element_forces = structure.get_element_forces(fe_results)
        self.max_stress = 0
        self.min_stress = 0
        self.max_tension_element = None
        self.max_compression_element = None

        # 计算最大应力
        for elem_id, (axial, _, stress) in self.element_forces.items():
            if stress > self.max_stress:
                self.max_stress = stress
                self.max_tension_element = elem_id
            if stress < self.min_stress:
                self.min_stress = stress
                self.max_compression_element = elem_id

    def print_summary(self):
        """打印分析结果摘要"""
        print("\n" + "="*60)
        print(f"桁架结构分析结果: {self.structure.name}")
        print("="*60)

        print(f"\n结构信息:")
        print(f"  节点数: {len(self.structure.nodes)}")
        print(f"  单元数: {len(self.structure.elements)}")
        print(f"  载荷数: {len(self.structure.loads)}")

        print(f"\n应力分析:")
        print(f"  最大拉应力: {self.max_stress/1e6:.2f} MPa (单元 {self.max_tension_element})")
        print(f"  最大压应力: {self.min_stress/1e6:.2f} MPa (单元 {self.max_compression_element})")

        # 支座反力
        if self.fe_results.reactions:
            print(f"\n支座反力:")
            for node_id, (rx, ry) in self.fe_results.reactions.items():
                print(f"  节点 {node_id}: Rx = {rx/1000:.2f} kN, Ry = {ry/1000:.2f} kN")

        # 最大位移
        max_disp = np.max(np.abs(self.fe_results.displacements))
        print(f"\n变形:")
        print(f"  最大位移: {max_disp*1000:.4f} mm")

    def plot_detailed(
        self,
        show_forces: bool = True,
        show_displacement: bool = True,
        show_stress: bool = True,
        figsize=(16, 10)
    ):
        """绘制详细的分析图表"""
        if show_forces and show_displacement and show_stress:
            fig, axes = plt.subplots(2, 2, figsize=figsize)
        else:
            fig, axes = plt.subplots(1, 1, figsize=(12, 8))

        # 1. 结构简图 + 内力
        ax1 = axes[0, 0] if show_forces else axes
        if show_forces:
            # 绘制结构
            for elem in self.structure.elements:
                if isinstance(elem, TrussElement):
                    ni, nj = self.structure.nodes[elem.node_i], self.structure.nodes[elem.node_j]

                    # 根据内力着色
                    force = self.element_forces[elem.id][0]  # 轴力
                    color = 'red' if force > 0 else 'blue' if force < 0 else 'gray'
                    linewidth = 3 if abs(force) > 1000 else 1.5

                    ax1.plot([ni.x, nj.x], [ni.y, nj.y], color=color, linewidth=linewidth)
                    # 标注力的大小
                    mid_x = (ni.x + nj.x) / 2
                    mid_y = (ni.y + nj.y) / 2
                    ax1.text(mid_x, mid_y, f'{force/1000:.1f}kN',
                           fontsize=8, ha='center', color=color,
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))

            # 绘制节点
            for node in self.structure.nodes:
                marker = '^' if self.structure.supports.get(node.id, (False, False))[0] else 'o'
                color = 'red' if node.id in self.structure.supports else 'black'
                ax1.plot(node.x, node.y, marker, markersize=10, color=color, zorder=5)
                ax1.text(node.x, node.y - 0.3, f'{node.id}', fontsize=9, ha='center')

            ax1.set_aspect('equal')
            ax1.grid(True, alpha=0.3)
            ax1.set_title('结构简图与轴力 (红色=拉力, 蓝色=压力)')
            ax1.set_xlabel('X (m)')
            ax1.set_ylabel('Y (m)')

        # 2. 变形图
        ax2 = axes[0, 1] if show_displacement else axes
        if show_displacement:
            scale = 500  # 放大倍数

            # 绘制变形后的结构
            for elem in self.structure.elements:
                if isinstance(elem, TrussElement):
                    ni, nj = self.structure.nodes[elem.node_i], self.structure.nodes[elem.node_j]

                    # 原始位置（虚线）
                    ax2.plot([ni.x, nj.x], [ni.y, nj.y], 'k--', alpha=0.3, linewidth=1)

                    # 变形后的位置
                    u_i = self.fe_results.displacements[elem.node_i * 2] * scale
                    v_i = self.fe_results.displacements[elem.node_i * 2 + 1] * scale
                    u_j = self.fe_results.displacements[elem.node_j * 2] * scale
                    v_j = self.fe_results.displacements[elem.node_j * 2 + 1] * scale

                    x_def = [ni.x + u_i, nj.x + u_j]
                    y_def = [ni.y + v_i, nj.y + v_j]

                    stress = self.fe_results.stresses.get(elem.id, 0)
                    color = 'red' if stress > 0 else 'blue' if stress < 0 else 'gray'

                    ax2.plot(x_def, y_def, '-', color=color, linewidth=2)

            ax2.set_aspect('equal')
            ax2.grid(True, alpha=0.3)
            ax2.set_title(f'变形图 (放大{scale}倍)')
            ax2.set_xlabel('X (m)')
            ax2.set_ylabel('Y (m)')

        # 3. 应力分布图
        ax3 = axes[1, 0] if show_stress else None
        if show_stress:
            elem_ids = []
            stresses = []

            for elem in self.structure.elements:
                if isinstance(elem, TrussElement):
                    elem_ids.append(elem.id)
                    stress = self.fe_results.stresses.get(elem.id, 0) / 1e6
                    stresses.append(stress)

            colors = ['red' if s > 0 else 'blue' for s in stresses]

            bars = ax3.bar(elem_ids, stresses, color=colors, alpha=0.7)
            ax3.axhline(0, color='k', linestyle='--', linewidth=1)
            ax3.set_xlabel('单元编号')
            ax3.set_ylabel('应力 (MPa)')
            ax3.set_title('单元应力分布')
            ax3.grid(True, alpha=0.3, axis='y')

            # 添加数值标签
            for bar in bars:
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}',
                       ha='center', va='bottom' if height > 0 else 'top', fontsize=8)

        # 4. 载荷图
        ax4 = axes[1, 1] if show_stress else None
        if show_stress:
            # 绘制结构
            for elem in self.structure.elements:
                if isinstance(elem, TrussElement):
                    ni, nj = self.structure.nodes[elem.node_i], self.structure.nodes[elem.node_j]
                    ax4.plot([ni.x, nj.x], [ni.y, nj.y], 'b-o', linewidth=2, markersize=8)

            # 绘制载荷
            arrow_props = dict(arrowstyle='->', lw=2)
            for load in self.structure.loads:
                if load.node_id >= 0 and load.load_type != LoadType.DEAD:
                    node = self.structure.nodes[load.node_id]
                    fx, fy, fz = load.direction
                    scale = np.sqrt(fx**2 + fy**2)

                    if scale > 0:
                        fx, fy = fx/scale, fy/scale
                        ax4.arrow(node.x, node.y, fx, fy, fc='red', ec='red',
                                  length_includes_head=True, head_width=0.1, head_length=0.15)

            ax4.set_aspect('equal')
            ax4.grid(True, alpha=0.3)
            ax4.set_title('载荷图')
            ax4.set_xlabel('X (m)')
            ax4.set_ylabel('Y (m)')

        plt.tight_layout()
        return fig


def analyze_truss_performance(truss: TrussStructure, title: str = "桁架性能分析"):
    """
    全面分析桁架性能
    """
    results = truss.analyze()
    analysis = TrussAnalysisResults(results, truss)
    analysis.print_summary()

    # 绘制详细图表
    fig = analysis.plot_detailed()
    plt.savefig(f"results/truss_{title.replace(' ', '_')}.png", dpi=150, bbox_inches='tight')
    print(f"\n图表已保存: results/truss_{title.replace(' ', '_')}.png")
    plt.close()

    return analysis


if __name__ == "__main__":
    # 测试：创建屋顶桁架
    print("=== 三角形屋顶桁架分析 ===")
    roof_truss = create_roof_truss(
        span=12.0,
        height=3.0,
        n_bays=6,
        chord_A=0.0005,
        web_A=0.0003,
        snow_load=2000
    )

    results = analyze_truss_performance(roof_truss, "屋顶桁架")
