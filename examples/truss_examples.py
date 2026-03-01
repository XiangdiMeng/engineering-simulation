"""
桁架结构分析示例
日常生活中的桁架结构：屋顶、桥梁、输电塔等
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib.pyplot as plt
from src.truss import (
    TrussStructure,
    create_roof_truss,
    create_bridge_truss,
    TrussAnalysisResults,
    analyze_truss_performance,
    LoadType
)


def example_1_roof_truss():
    """示例 1: 三角形屋顶桁架（最常见的建筑结构）"""
    print("\n" + "="*60)
    print("示例 1: 三角形屋顶桁架")
    print("="*60)
    print("\n应用场景: 工业厂房、体育馆、仓库等建筑的屋顶")
    print("特点: 受力合理、耗材经济、施工方便\n")

    # 创建12米跨度的屋顶桁架
    roof_truss = create_roof_truss(
        span=12.0,        # 跨度 12m
        height=3.0,       # 高度 3m
        n_bays=6,          # 6 节
        chord_A=0.0005,    # 弦杆 500mm²
        web_A=0.0003,     # 腹杆 300mm²
        E=206e9,          # Q345钢
        snow_load=1500    # 雪载 1.5 kN/m
    )

    print(f"桁架参数:")
    print(f"  跨度: 12.0 m")
    print(f"  高度: 3.0 m")
    print(f"  节数: 6")
    print(f"  材料: Q345钢 (E=206 GPa)")
    print(f"  载荷: 自重 + 雪载(1.5 kN/m)")

    # 分析
    analysis = analyze_truss_performance(roof_truss, "屋顶桁架")


def example_2_warren_bridge_truss():
    """示例 2: Warren桁架桥"""
    print("\n" + "="*60)
    print("示例 2: Warren桁架桥")
    print("="*60)
    print("\n应用场景: 公路桥梁、铁路桥梁、人行天桥")
    print("特点: 结构简单、承载能力强、经典桁架形式\n")

    # 创建20米跨度的桥梁
    bridge_truss = create_bridge_truss(
        span=20.0,         # 跨度 20m
        height=4.0,        # 高度 4m
        n_panels=8,         # 8个面板
        chord_A=0.002,     # 弦杆 2000mm²
        web_A=0.001,       # 腹杆 1000mm²
        E=200e9,           # 结构钢
        traffic_load=100000  # 车辆荷载 100kN
    )

    print(f"桥梁参数:")
    print(f"  跨度: 20.0 m")
    print(f"  高度: 4.0 m")
    print(f"  面板数: 8")
    print(f"  材料: 结构钢 (E=200 GPa)")
    print(f"  载荷: 自重 + 车辆荷载(100kN)")

    # 分析
    analysis = analyze_truss_performance(bridge_truss, "Warren桥梁")


def example_3_comparison():
    """示例 3: 不同跨度屋顶桁架对比"""
    print("\n" + "="*60)
    print("示例 3: 不同跨度屋顶桁架性能对比")
    print("="*60)

    spans = [6, 12, 18, 24]  # 不同跨度
    results_list = []

    for span in spans:
        truss = create_roof_truss(
            span=span,
            height=span/4,     # 高跨比 1:4
            n_bays=int(span/2),
            chord_A=0.0005,
            web_A=0.0003,
            snow_load=1500
        )

        fe_results = truss.analyze()
        analysis = TrussAnalysisResults(fe_results, truss)

        # 计算性能指标
        max_disp = np.max(np.abs(fe_results.displacements)) * 1000  # mm
        max_stress = analysis.max_stress / 1e6  # MPa
        min_stress = analysis.min_stress / 1e6  # MPa
        total_mass = sum([
            elem.material.density * elem.material.A * elem.length(truss.nodes) *
            (span / len(truss.elements)) for elem in truss.elements
        ])

        results_list.append({
            "span": span,
            "max_disp": max_disp,
            "max_stress": max_stress,
            "min_stress": min_stress,
            "mass": total_mass
        })

    # 打印对比表格
    print(f"\n{'跨度(m)':<10} {'最大位移(mm)':<15} {'最大应力(MPa)':<15} {'最小应力(MPa)':<15} {'总重(kg)':<10}")
    print("-" * 70)
    for r in results_list:
        print(f"{r['span']:<10.0f} {r['max_disp']:<15.2f} {r['max_stress']:<15.2f} "
              f"{r['min_stress']:<15.2f} {r['mass']:<10.1f}")

    # 绘图
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    spans_arr = np.array([r['span'] for r in results_list])
    disps = np.array([r['max_disp'] for r in results_list])
    max_stresses = np.array([r['max_stress'] for r in results_list])
    min_stresses = np.array([r['min_stress'] for r in results_list])
    masses = np.array([r['mass'] for r in results_list])

    # 位移 vs 跨度
    axes[0, 0].plot(spans_arr, disps, 'bo-', linewidth=2, markersize=8)
    axes[0, 0].set_xlabel('跨度 (m)')
    axes[0, 0].set_ylabel('最大位移 (mm)')
    axes[0, 0].set_title('位移 vs 跨度')
    axes[0, 0].grid(True, alpha=0.3)

    # 最大应力 vs 跨度
    axes[0, 1].plot(spans_arr, max_stresses, 'rs-', linewidth=2, markersize=8, label='拉应力')
    axes[0, 1].plot(spans_arr, -min_stresses, 'bs--', linewidth=2, markersize=8, label='压应力(绝对值)')
    axes[0, 1].set_xlabel('跨度 (end)')
    axes[0, 1].set_ylabel('应力 (MPa)')
    axes[0, 1].set_title('最大应力 vs 跨度')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)

    # 应力比
    stress_ratio = max_stresses / (min_stresses + 1e-6)
    axes[1, 0].bar(spans_arr, stress_ratio, color='purple', alpha=0.7)
    axes[1, 0].set_xlabel('跨度 (m)')
    axes[1, 0].set_ylabel('拉/压应力比')
    axes[1, 0].set_title('应力比 vs 跨度')
    axes[1, 0].grid(True, alpha=0.3, axis='y')

    # 质量对比
    axes[1, 1].plot(spans_arr, masses, 'go-', linewidth=2, markersize=8)
    axes[1, 1].set_xlabel('跨度 (m)')
    axes[1, 1].set_ylabel('结构总重 (kg)')
    axes[1, 1].set_title('结构重量 vs 跨度')
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("results/truss_span_comparison.png", dpi=150, bbox_inches='tight')
    print(f"\n对比图表已保存: results/truss_span_comparison.png")
    plt.close()


def example_4_load_combination():
    """示例 4: 载荷组合分析"""
    print("\n" + "="*60)
    print("示例 4: 载荷组合分析")
    print("="*60)
    print("\n分析不同载荷组合下的结构响应\n")

    base_truss = create_roof_truss(
        span=12.0,
        height=3.0,
        n_bays=6,
        chord_A=0.0005,
        web_A=0.0003,
        snow_load=0  # 不加雪载，手动添加
    )

    load_cases = [
        {
            "name": "工况1: 恒载",
            "snow": 0,
            "description": "仅考虑自重"
        },
        {
            "name": "工况2: 恒载 + 雪载",
            "snow": 1500,
            "description": "自重 + 1.5 kN/m 雪载"
        },
        {
            "name": "工况3: 恒载 + 重雪载",
            "snow": 3000,
            "description": "自重 + 3.0 kN/m 雪载"
        }
    ]

    print(f"{'工况':<25} {'最大位移(mm)':<15} {'最大应力(MPa)':<15} {'最大拉力(kN)':<15}")
    print("-" * 70)

    for case in load_cases:
        # 复制基础桁架
        import copy
        truss = copy.deepcopy(base_truss)

        # 添加雪载
        if case["snow"] > 0:
            for i in range(6):  # 上弦单元ID从n_bays开始
                elem_id = 6 + i
                truss.add_distributed_load(elem_id, case["snow"], angle=-np.pi/2)

        # 分析
        results = truss.analyze()
        max_disp = np.max(np.abs(results.displacements)) * 1000
        max_stress = max(results.stresses.values()) / 1e6

        # 最大拉力
        max_tension = 0
        for elem_id, stress in results.stresses.items():
            if stress > 0:
                force = results.element_forces.get(elem_id, [0, 0, 0])[0]
                if force > max_tension:
                    max_tension = force

        print(f"{case['name']:<25} {max_disp:<15.2f} {max_stress:<15.2f} {max_tension/1000:<15.2f}")


def example_5_custom_roof_truss():
    """示例 5: 自定义屋顶桁架"""
    print("\n" + "="*60)
    print("示例 5: 自定义屋顶桁架设计")
    print("="*60)

    # 手动创建一个复杂桁架
    truss = TrussStructure(name="自定义普氏桁架")

    # 节点坐标
    nodes_coords = [
        (0, 0),      # 0
        (2, 0),      # 1
        (4, 0),      # 2
        (6, 0),      # 3
        (8, 0),      # 4
        (10, 0),     # 5
        (12, 0),     # 6
        (1, 2),      # 7
        (3, 3.5),    # 8
        (5, 4),      # 9
        (7, 4),      # 10
        (9, 3.5),    # 11
        (11, 2),     # 12
    ]

    for x, y in nodes_coords:
        # 左端固定，右端滚动
        fix_x = (x == 0)
        fix_y = (x == 0 or x == 12)
        truss.add_node(x, y, 0, fix_x, fix_y)

    # 连接单元（普氏桁架）
    steel = FEMaterial("Q345", 206e9, 0.0005, 7850)
    steel_web = FEMaterial("Q345", 206e9, 0.0003, 7850)

    # 下弦
    for i in range(6):
        truss.add_element(i, i+1, material=steel)

    # 上弦
    for i in range(5):
        truss.add_element(7+i, 7+i+1, material=steel)

    # 腹杆
    connections = [
        (0, 7), (7, 1),      # 左边斜杆
        (1, 7), (1, 8),
        (2, 8), (8, 3),
        (3, 8), (3, 9),
        (4, 9), (9, 4),
        (5, 9), (4, 10),
        (6, 10), (5, 11),
        (5, 11), (11, 12),
        (11, 12), (6, 12)
    ]

    for i, j in connections:
        truss.add_element(i, j, material=steel_web)

    # 添加载荷
    truss.add_gravity_load()
    truss.add_distributed_load(7, 2000, angle=-np.pi/2)  # 上弦雪载
    truss.add_point_load(3, 0, -50000)  # 集中载荷

    print(f"\n自定义桁架参数:")
    print(f"  跨度: 12.0 m")
    print(f"  高度: 4.0 m (最高点)")
    print(f"  节点数: {len(nodes_coords)}")
    print(f"  单元数: {len(connections)}")
    print(f"  载荷: 自重 + 雪载(2kN/m) + 集中力(50kN)")

    # 分析
    analysis = analyze_truss_performance(truss, "自定义普氏桁架")


if __name__ == "__main__":
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    # 运行所有示例
    example_1_roof_truss()
    example_2_warren_bridge_truss()
    example_3_comparison()
    example_4_load_combination()
    example_5_custom_roof_truss()

    print("\n" + "="*60)
    print("所有桁架分析示例完成！")
    print("="*60)
