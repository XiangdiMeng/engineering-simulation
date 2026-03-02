"""
组合结构与工程应用模块 (Combined Structures and Applications)
提供常见的工程结构模板、参数化建模和验证案例
"""

import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional, Callable
from enum import Enum
import copy

from .frame import (FrameStructure, FrameElement, FrameMaterial, Section,
                    create_portal_frame as _create_portal_frame,
                    create_cantilever_frame)
from .truss import TrussStructure, LoadType, create_roof_truss
from .fea import FEModel, FEMaterial, Node
from .materials import Material, Steel, Aluminum, Concrete


class StructureType(Enum):
    """结构类型"""
    TRUSS = "truss"                  # 桁架
    FRAME = "frame"                  # 框架
    BEAM = "beam"                    # 梁
    COMBINED = "combined"            # 组合结构
    ARCH = "arch"                    # 拱
    CABLE = "cable"                  # 悬索
    PLATE = "plate"                  # 板


class LoadCombination(Enum):
    """荷载组合（根据建筑规范）"""
    # 中国规范 GB 50009
    COMB_1 = "1.3D + 1.5L"           # 1.3恒载 + 1.5活载
    COMB_2 = "1.3D + 1.5L + 0.6W"    # + 风载
    COMB_3 = "1.3D + 1.5L + 0.5S"    # + 雪载
    COMB_4 = "1.0D + 1.4W"           # 风载控制
    COMB_5 = "1.0D + 1.4E"           # 地震控制


@dataclass
class LoadCase:
    """荷载工况"""
    name: str
    dead_load: float = 0.0           # 恒载 (N/m² 或 N)
    live_load: float = 0.0           # 活载 (N/m² 或 N)
    wind_load: float = 0.0           # 风载 (N/m² 或 N)
    snow_load: float = 0.0           # 雪载 (N/m² 或 N)
    seismic_load: float = 0.0        # 地震作用 (N)
    temperature: float = 0.0         # 温度变化 (°C)
    description: str = ""


@dataclass
class DesignParameters:
    """设计参数"""
    safety_factor: float = 1.5       # 安全系数
    deflection_limit: str = "L/250"  # 挠度限值
    drift_limit: str = "H/500"       # 层间位移限值
    vibration_limit: float = 1.0     # 固有频率限值 (Hz)


# ==================== 常见结构模板 ====================

def create_cable_stayed_bridge(
    span: float = 100.0,
    tower_height: float = 30.0,
    n_cables: int = 8,
    deck_width: float = 10.0,
    E_cable: float = 180e9,
    E_deck: float = 200e9,
    A_cable: float = 0.005,
    A_deck: float = 0.02
) -> TrussStructure:
    """
    创建斜拉桥模型

    Parameters
    ----------
    span : float
        主跨长度 (m)
    tower_height : float
        塔高 (m)
    n_cables : int
        每侧拉索数量
    deck_width : float
        桥面宽度 (m)
    E_cable : float
        拉索弹性模量 (Pa)
    E_deck : float
        桥面弹性模量 (Pa)
    A_cable : float
        拉索截面积 (m²)
    A_deck : float
        桥面截面积 (m²)

    Returns
    -------
    TrussStructure
    """
    bridge = TrussStructure(name="斜拉桥")

    # 材料
    cable_mat = FEMaterial("拉索", E_cable, A_cable, 6000)
    deck_mat = FEMaterial("桥面", E_deck, A_deck, 7850)

    # 桥面节点
    n_deck_nodes = n_cables * 2 + 2
    dx = span / (n_deck_nodes - 1)

    for i in range(n_deck_nodes):
        x = i * dx
        y = 0
        # 两端铰接
        if i == 0 or i == n_deck_nodes - 1:
            bridge.add_node(x, y, fix_x=True, fix_y=True)
        else:
            bridge.add_node(x, y, fix_x=False, fix_y=False)

    # 塔节点
    tower_base_left = n_deck_nodes
    tower_base_right = n_deck_nodes + 1
    tower_top_left = n_deck_nodes + 2
    tower_top_right = n_deck_nodes + 3

    # 左塔
    bridge.add_node(0, 0, fix_x=True, fix_y=True)  # 塔底
    bridge.add_node(0, tower_height, fix_x=False, fix_y=False)  # 塔顶

    # 右塔
    bridge.add_node(span, 0, fix_x=True, fix_y=True)
    bridge.add_node(span, tower_height, fix_x=False, fix_y=False)

    # 桥面单元
    for i in range(n_deck_nodes - 1):
        bridge.add_element(i, i + 1, material=deck_mat)

    # 拉索
    cable_spacing = span / (2 * n_cables)

    # 左侧拉索
    for i in range(n_cables):
        deck_node = i * 2 + 1
        tower_node = n_deck_nodes + 2
        bridge.add_element(deck_node, tower_node, material=cable_mat)

    # 右侧拉索
    for i in range(n_cables):
        deck_node = n_deck_nodes - 2 - i * 2
        tower_node = n_deck_nodes + 3
        bridge.add_element(deck_node, tower_node, material=cable_mat)

    # 载荷
    bridge.add_gravity_load()

    # 交通载荷（作用在桥面）
    traffic_load = 50000  # 50kN
    mid_node = n_deck_nodes // 2
    bridge.add_point_load(mid_node, 0, -traffic_load, name="车辆荷载")

    return bridge


def create_arch_bridge(
    span: float = 50.0,
    rise: float = 10.0,
    n_segments: int = 20,
    tube_diameter: float = 0.5,
    tube_thickness: float = 0.02,
    E: float = 200e9
) -> TrussStructure:
    """
    创建拱桥模型

    Parameters
    ----------
    span : float
        跨度 (m)
    rise : float
        矢高 (m)
    n_segments : int
        拱分段数
    tube_diameter : float
        管径 (m)
    tube_thickness : float
        壁厚 (m)
    E : float
        弹性模量 (Pa)

    Returns
    -------
    TrussStructure
    """
    arch = TrussStructure(name="拱桥")

    # 截面属性（圆管）
    A = np.pi * ((tube_diameter/2)**2 - (tube_diameter/2 - tube_thickness)**2)
    I = np.pi * (tube_diameter**4 - (tube_diameter - 2*tube_thickness)**4) / 64

    material = FEMaterial("钢管", E, A, 7850)

    # 拱轴线（抛物线）
    # y = 4 * rise * x * (span - x) / span^2

    # 创建拱节点
    for i in range(n_segments + 1):
        x = i * span / n_segments
        y = 4 * rise * x * (span - x) / span**2

        # 两端铰接
        if i == 0 or i == n_segments:
            arch.add_node(x, y, fix_x=True, fix_y=True)
        else:
            arch.add_node(x, y, fix_x=False, fix_y=False)

    # 拱单元
    for i in range(n_segments):
        arch.add_element(i, i + 1, material=material)

    # 添加桥面（简化）
    deck_nodes_start = n_segments + 1
    for i in range(n_segments + 1):
        x = i * span / n_segments
        y = -2  # 桥面在拱下方
        arch.add_node(x, y, fix_x=False, fix_y=False)

    # 立柱连接拱和桥面
    for i in range(n_segments + 1):
        arch.add_element(i, deck_nodes_start + i, material=FEMaterial("立柱", E, A/4, 7850))

    # 桥面单元
    for i in range(n_segments):
        arch.add_element(deck_nodes_start + i, deck_nodes_start + i + 1, material=material)

    # 载荷
    arch.add_gravity_load()

    # 交通载荷
    mid_deck_node = deck_nodes_start + n_segments // 2
    arch.add_point_load(mid_deck_node, 0, -50000, name="车辆荷载")

    return arch


def create_multistory_frame(
    width: float = 6.0,
    height_per_floor: float = 3.5,
    n_floors: int = 4,
    n_bays: int = 2,
    column_size: float = 0.4,
    beam_size: float = 0.3,
    E: float = 200e9
) -> FrameStructure:
    """
    创建多层框架结构

    Parameters
    ----------
    width : float
        开间宽度 (m)
    height_per_floor : float
        层高 (m)
    n_floors : int
        楼层数
    n_bays : int
        开间数
    column_size : float
        柱截面尺寸 (m)
    beam_size : float
        梁截面尺寸 (m)
    E : float
        弹性模量 (Pa)

    Returns
    -------
    FrameStructure
    """
    frame = FrameStructure(name=f"{n_floors}层框架")

    # 截面和材料
    column_section = Section.rectangular(column_size, column_size)
    beam_section = Section.rectangular(beam_size, beam_size)

    column_mat = FrameMaterial(
        name="柱",
        E=E,
        G=E/(2*(1+0.3)),
        A=column_section.A,
        I=column_section.Iz,
        density=2500  # 混凝土密度
    )

    beam_mat = FrameMaterial(
        name="梁",
        E=E,
        G=E/(2*(1+0.3)),
        A=beam_section.A,
        I=beam_section.Iz,
        density=2500
    )

    # 创建节点
    node_map = {}  # (floor, bay) -> node_id

    for floor in range(n_floors + 1):
        for bay in range(n_bays + 1):
            x = bay * width
            y = floor * height_per_floor

            # 底层固定
            fix_x = fix_y = fix_theta = (floor == 0)

            node_id = frame.add_node(x, y, fix_x, fix_y, fix_theta)
            node_map[(floor, bay)] = node_id

    # 创建柱
    for floor in range(n_floors):
        for bay in range(n_bays + 1):
            node_i = node_map[(floor, bay)]
            node_j = node_map[(floor + 1, bay)]
            frame.add_element(node_i, node_j, column_mat)

    # 创建梁
    for floor in range(1, n_floors + 1):
        for bay in range(n_bays):
            node_i = node_map[(floor, bay)]
            node_j = node_map[(floor, bay + 1)]
            frame.add_element(node_i, node_j, beam_mat)

    return frame


def create_space_truss(
    span_x: float = 20.0,
    span_y: float = 15.0,
    height: float = 2.5,
    n_cells_x: int = 10,
    n_cells_y: int = 8,
    chord_A: float = 0.001,
    web_A: float = 0.0005,
    E: float = 200e9
) -> Dict:
    """
    创建空间网架结构（3D）

    Parameters
    ----------
    span_x : float
        X方向跨度 (m)
    span_y : float
        Y方向跨度 (m)
    height : float
        网架高度 (m)
    n_cells_x : int
        X方向网格数
    n_cells_y : int
        Y方向网格数
    chord_A : float
        弦杆截面积 (m²)
    web_A : float
        腹杆截面积 (m²)
    E : float
        弹性模量 (Pa)

    Returns
    -------
    Dict
        包含节点、单元等信息的字典
    """
    # 3D节点
    nodes_3d = []
    elements_3d = []

    dx = span_x / n_cells_x
    dy = span_y / n_cells_y

    # 上弦节点
    for j in range(n_cells_y + 1):
        for i in range(n_cells_x + 1):
            nodes_3d.append({
                'id': len(nodes_3d),
                'x': i * dx,
                'y': j * dy,
                'z': height / 2,
                'fix': (i == 0 or i == n_cells_x) and (j == 0 or j == n_cells_y),
                'type': 'top'
            })

    top_offset = len(nodes_3d)

    # 下弦节点（错位半个网格）
    for j in range(n_cells_y):
        for i in range(n_cells_x):
            nodes_3d.append({
                'id': len(nodes_3d),
                'x': (i + 0.5) * dx,
                'y': (j + 0.5) * dy,
                'z': -height / 2,
                'fix': False,
                'type': 'bottom'
            })

    elem_id = 0

    # 上弦杆
    chord_mat = FEMaterial("弦杆", E, chord_A, 7850)
    web_mat = FEMaterial("腹杆", E, web_A, 7850)

    for j in range(n_cells_y + 1):
        for i in range(n_cells_x):
            node_i = j * (n_cells_x + 1) + i
            node_j = j * (n_cells_x + 1) + i + 1
            elements_3d.append({
                'id': elem_id,
                'node_i': node_i,
                'node_j': node_j,
                'material': chord_mat
            })
            elem_id += 1

    for j in range(n_cells_y):
        for i in range(n_cells_x + 1):
            node_i = j * (n_cells_x + 1) + i
            node_j = (j + 1) * (n_cells_x + 1) + i
            elements_3d.append({
                'id': elem_id,
                'node_i': node_i,
                'node_j': node_j,
                'material': chord_mat
            })
            elem_id += 1

    # 下弦杆
    for j in range(n_cells_y):
        for i in range(n_cells_x):
            node_i = top_offset + j * n_cells_x + i
            node_j = top_offset + j * n_cells_x + i + 1
            if i < n_cells_x - 1:
                elements_3d.append({
                    'id': elem_id,
                    'node_i': node_i,
                    'node_j': node_j,
                    'material': chord_mat
                })
                elem_id += 1

            node_j2 = top_offset + (j + 1) * n_cells_x + i
            if j < n_cells_y - 1:
                elements_3d.append({
                    'id': elem_id,
                    'node_i': node_i,
                    'node_j': node_j2,
                    'material': chord_mat
                })
                elem_id += 1

    # 腹杆（连接上下弦）
    for node in nodes_3d:
        if node['type'] == 'top':
            # 找到最近的下弦节点
            for j in range(n_cells_y):
                for i in range(n_cells_x):
                    bottom_node = top_offset + j * n_cells_x + i
                    # 简化：连接到周围的下弦节点
                    dx_abs = abs(node['x'] - nodes_3d[bottom_node]['x'])
                    dy_abs = abs(node['y'] - nodes_3d[bottom_node]['y'])
                    if dx_abs <= dx/2 + 0.01 and dy_abs <= dy/2 + 0.01:
                        elements_3d.append({
                            'id': elem_id,
                            'node_i': node['id'],
                            'node_j': bottom_node,
                            'material': web_mat
                        })
                        elem_id += 1

    return {
        'nodes': nodes_3d,
        'elements': elements_3d,
        'type': 'space_truss'
    }


# ==================== 荷载组合与设计验算 ====================

def apply_load_combination(
    structure,
    load_case: LoadCase,
    combination: LoadCombination = LoadCombination.COMB_1
):
    """
    应用荷载组合

    Parameters
    ----------
    structure : FrameStructure or TrussStructure
        结构对象
    load_case : LoadCase
        荷载工况
    combination : LoadCombination
        荷载组合类型
    """
    # 解析组合
    if combination == LoadCombination.COMB_1:
        # 1.3D + 1.5L
        factors = {'dead': 1.3, 'live': 1.5, 'wind': 0, 'snow': 0, 'seismic': 0}
    elif combination == LoadCombination.COMB_2:
        factors = {'dead': 1.3, 'live': 1.5, 'wind': 0.6, 'snow': 0, 'seismic': 0}
    elif combination == LoadCombination.COMB_3:
        factors = {'dead': 1.3, 'live': 1.5, 'wind': 0, 'snow': 0.5, 'seismic': 0}
    elif combination == LoadCombination.COMB_4:
        factors = {'dead': 1.0, 'live': 0, 'wind': 1.4, 'snow': 0, 'seismic': 0}
    elif combination == LoadCombination.COMB_5:
        factors = {'dead': 1.0, 'live': 0, 'wind': 0, 'snow': 0, 'seismic': 1.4}
    else:
        factors = {'dead': 1.0, 'live': 1.0, 'wind': 0, 'snow': 0, 'seismic': 0}

    # 应用荷载（这里需要根据具体结构类型实现）
    return factors


def check_design_criteria(
    results,
    design_params: DesignParameters,
    structure_span: float,
    structure_height: float
) -> Dict[str, bool]:
    """
    检查设计准则

    Parameters
    ----------
    results : 分析结果
    design_params : DesignParameters
        设计参数
    structure_span : float
        结构跨度 (m)
    structure_height : float
        结构高度 (m)

    Returns
    -------
    Dict[str, bool]
        各项准则的检查结果
    """
    checks = {}

    # 1. 强度检查
    max_stress = 0
    if hasattr(results, 'element_stresses'):
        for stress_tuple in results.element_stresses.values():
            stress = stress_tuple[2] if len(stress_tuple) > 2 else max(stress_tuple)
            max_stress = max(max_stress, abs(stress))
    elif hasattr(results, 'stresses'):
        max_stress = max(abs(s) for s in results.stresses.values()) / 1e6  # MPa

    checks['strength'] = max_stress < 345 / design_params.safety_factor  # 假设Q345

    # 2. 挠度检查
    max_deflection = 0
    if hasattr(results, 'displacements'):
        max_deflection = np.max(np.abs(results.displacements)) * 1000  # mm

    # 解析挠度限值
    if design_params.deflection_limit.startswith("L/"):
        limit_ratio = int(design_params.deflection_limit[2:])
        deflection_limit = structure_span * 1000 / limit_ratio  # mm
    else:
        deflection_limit = structure_span * 1000 / 250

    checks['deflection'] = max_deflection < deflection_limit

    # 3. 稳定性检查（简化）
    checks['stability'] = checks['strength']  # 简化处理

    return {
        'strength': checks['strength'],
        'deflection': checks['deflection'],
        'stability': checks['stability'],
        'max_stress': max_stress,
        'max_deflection': max_deflection,
        'deflection_limit': deflection_limit
    }


# ==================== 参数化建模 ====================

class ParametricStructure:
    """参数化结构建模"""

    def __init__(self, template: str = "frame"):
        """
        Parameters
        ----------
        template : str
            结构模板类型
        """
        self.template = template
        self.parameters = {}
        self.structure = None

    def set_parameter(self, name: str, value: float):
        """设置参数"""
        self.parameters[name] = value
        return self

    def set_parameters(self, **kwargs):
        """批量设置参数"""
        self.parameters.update(kwargs)
        return self

    def generate(self):
        """根据参数生成结构"""
        if self.template == "portal_frame":
            self.structure = _create_portal_frame(
                width=self.parameters.get('width', 6.0),
                height=self.parameters.get('height', 4.0),
                section_width=self.parameters.get('section_width', 0.2),
                section_height=self.parameters.get('section_height', 0.3),
                E=self.parameters.get('E', 200e9)
            )
        elif self.template == "multistory_frame":
            self.structure = create_multistory_frame(
                width=self.parameters.get('width', 6.0),
                height_per_floor=self.parameters.get('height_per_floor', 3.5),
                n_floors=self.parameters.get('n_floors', 4),
                n_bays=self.parameters.get('n_bays', 2),
                E=self.parameters.get('E', 200e9)
            )
        elif self.template == "roof_truss":
            from .truss import create_roof_truss
            self.structure = create_roof_truss(
                span=self.parameters.get('span', 12.0),
                height=self.parameters.get('height', 3.0),
                n_bays=self.parameters.get('n_bays', 6),
                E=self.parameters.get('E', 206e9)
            )
        elif self.template == "cable_stayed_bridge":
            self.structure = create_cable_stayed_bridge(
                span=self.parameters.get('span', 100.0),
                tower_height=self.parameters.get('tower_height', 30.0),
                n_cables=self.parameters.get('n_cables', 8)
            )
        else:
            raise ValueError(f"未知模板: {self.template}")

        return self.structure

    def analyze(self):
        """分析结构"""
        if self.structure is None:
            self.generate()
        return self.structure.solve()

    def optimize(
        self,
        objective: str = "weight",
        constraints: Optional[Dict] = None,
        max_iterations: int = 50
    ) -> Dict:
        """
        简单的尺寸优化

        Parameters
        ----------
        objective : str
            优化目标 ('weight', 'cost')
        constraints : Dict
            约束条件
        max_iterations : int
            最大迭代次数

        Returns
        -------
        Dict
            优化结果
        """
        if constraints is None:
            constraints = {'max_stress': 345e6, 'max_deflection': 0.02}

        history = []

        for iteration in range(max_iterations):
            # 生成结构
            structure = self.generate()
            results = structure.analyze()

            # 计算目标函数
            weight = self._calculate_weight(structure)

            # 检查约束
            checks = check_design_criteria(
                results,
                DesignParameters(),
                self.parameters.get('span', 10),
                self.parameters.get('height', 5)
            )

            history.append({
                'iteration': iteration,
                'weight': weight,
                'checks': checks,
                'parameters': self.parameters.copy()
            })

            # 简单的梯度下降（实际应用中需要更复杂的算法）
            if not checks['deflection']:
                # 挠度过大，增加截面
                self.parameters['section_height'] *= 1.1
                self.parameters['section_width'] *= 1.05
            elif not checks['strength']:
                # 应力过大，增加截面
                self.parameters['section_height'] *= 1.15
                self.parameters['section_width'] *= 1.1
            else:
                # 满足约束，尝试减小截面
                if iteration > 5:
                    self.parameters['section_height'] *= 0.98
                    self.parameters['section_width'] *= 0.98

        return {
            'optimal_parameters': self.parameters,
            'history': history
        }

    def _calculate_weight(self, structure) -> float:
        """计算结构重量"""
        weight = 0
        if hasattr(structure, 'elements'):
            for elem in structure.elements:
                if hasattr(elem, 'material') and hasattr(elem, 'length'):
                    L = elem.length(structure.nodes) if hasattr(structure, 'nodes') else 1
                    rho = elem.material.density
                    A = elem.material.A
                    weight += rho * A * L
        return weight


# ==================== 验证案例 ====================

def verification_cantilever_beam():
    """悬臂梁验证案例（与解析解对比）"""
    # 参数
    L = 2.0  # m
    b = 0.1  # m
    h = 0.2  # m
    P = 10000  # N
    E = 200e9  # Pa

    I = b * h**3 / 12

    # 解析解
    delta_analytical = P * L**3 / (3 * E * I)
    M_max_analytical = P * L
    sigma_max_analytical = M_max_analytical * h / (2 * I)

    # 有限元解
    from .frame import create_cantilever_frame
    frame = create_cantilever_frame(length=L, n_spans=1, E=E)
    frame.nodes[1].loads = (0, -P, 0)
    results = frame.solve()

    # 比较
    delta_fem = abs(results.displacements[1])  # 自由端Y位移

    return {
        'analytical': {
            'deflection': delta_analytical,
            'moment': M_max_analytical,
            'stress': sigma_max_analytical
        },
        'fem': {
            'deflection': delta_fem,
            'error': abs(delta_fem - delta_analytical) / delta_analytical * 100
        }
    }


def verification_simply_supported_beam():
    """简支梁验证案例"""
    # 参数
    L = 4.0  # m
    b = 0.15  # m
    h = 0.25  # m
    P = 20000  # N (跨中)
    E = 200e9  # Pa

    I = b * h**3 / 12

    # 解析解
    delta_analytical = P * L**3 / (48 * E * I)
    M_max_analytical = P * L / 4

    # 有限元解（使用框架）
    from .frame import FrameStructure, FrameMaterial, Section
    frame = FrameStructure(name="简支梁")

    section = Section.rectangular(b, h)
    material = FrameMaterial("Q345", E, E/(2*1.3), section.A, section.Iz, 7850)

    # 节点
    frame.add_node(0, 0, fix_x=True, fix_y=True, fix_theta=False)
    frame.add_node(L/2, 0, fix_x=False, fix_y=False, fix_theta=False)
    frame.add_node(L, 0, fix_x=True, fix_y=True, fix_theta=False)

    # 单元
    frame.add_element(0, 1, material)
    frame.add_element(1, 2, material)

    # 载荷
    frame.nodes[1].loads = (0, -P, 0)

    results = frame.solve()
    delta_fem = abs(results.displacements[4])  # 跨中Y位移

    return {
        'analytical_deflection': delta_analytical,
        'fem_deflection': delta_fem,
        'error_percent': abs(delta_fem - delta_analytical) / delta_analytical * 100
    }


if __name__ == "__main__":
    print("=== 组合结构与工程应用测试 ===")

    # 1. 创建斜拉桥
    print("\n1. 斜拉桥模型")
    bridge = create_cable_stayed_bridge(span=80, n_cables=6)
    results_bridge = bridge.analyze()
    print(f"节点数: {len(bridge.nodes)}, 单元数: {len(bridge.elements)}")

    # 2. 创建多层框架
    print("\n2. 多层框架模型")
    frame = create_multistory_frame(n_floors=3, n_bays=2)
    print(f"节点数: {len(frame.nodes)}, 单元数: {len(frame.elements)}")

    # 施加风载荷
    for node in frame.nodes:
        if node.y > 0:  # 只对非底层节点施加
            frame.nodes[node.id].loads = (5000, node.loads[1], node.loads[2])

    results_frame = frame.solve()

    # 3. 参数化建模
    print("\n3. 参数化建模")
    param_frame = ParametricStructure("portal_frame")
    param_frame.set_parameters(
        width=8.0,
        height=5.0,
        section_width=0.25,
        section_height=0.35
    )
    structure = param_frame.generate()
    print(f"门式框架: {len(structure.nodes)} 节点")

    # 4. 验证案例
    print("\n4. 验证案例 - 悬臂梁")
    cantilever_result = verification_cantilever_beam()
    print(f"解析解挠度: {cantilever_result['analytical']['deflection']*1000:.4f} mm")
    print(f"FEM解挠度: {cantilever_result['fem']['deflection']*1000:.4f} mm")
    print(f"误差: {cantilever_result['fem']['error']:.2f}%")

    print("\n5. 验证案例 - 简支梁")
    beam_result = verification_simply_supported_beam()
    print(f"解析解挠度: {beam_result['analytical_deflection']*1000:.4f} mm")
    print(f"FEM解挠度: {beam_result['fem_deflection']*1000:.4f} mm")
    print(f"误差: {beam_result['error_percent']:.2f}%")
