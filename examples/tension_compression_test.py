"""
梁拉伸压缩试验测试
Tensile and Compressive Test of Beams
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib.pyplot as plt
from src.fea import (
    FEModel,
    TrussElement,
    FEAResults,
    analyze_cantilever_bar,
    analyze_fixed_bar_compression,
    create_bar_model
)
from src.materials import Steel, Aluminum


def test_1_cantilever_tension():
    """试验 1: 悬臂杆拉伸试验"""
    print("\n" + "="*60)
    print("试验 1: 悬臂杆拉伸试验")
    print("="*60)

    # 试件参数
    length = 0.5           # 试件长度 (m)
    diameter = 0.02       # 直径 (m) = 20 mm
    E = 200e9             # 弹性模量 (Pa) - 钢
    force = 100000        # 拉力 (N) = 100 kN

    print(f"\n试件参数:")
    print(f"  材料: 钢 (E = {E/1e9:.0f} GPa)")
    print(f"  长度: {length*1000:.0f} mm")
    print(f"  直径: {diameter*1000:.0f} mm")
    print(f"  拉力: {force/1000:.1f} kN")

    # 理论解
    A = np.pi * (diameter / 2) ** 2
    stress_theory = force / A
    strain_theory = stress_theory / E
    delta_L_theory = strain_theory * length

    print(f"\n理论解:")
    print(f"  横截面积: {A*1e6:.2f} mm^2")
    print(f"  应力: {stress_theory/1e6:.2f} MPa")
    print(f"  应变: {strain_theory*1e6:.2f} ue")
    print(f"  伸长量: {delta_L_theory*1000:.4f} mm")

    # 有限元分析
    results = analyze_cantilever_bar(
        length=length,
        diameter=diameter,
        force=force,
        material_E=E,
        n_elements=10
    )

    print(f"\n有限元结果:")
    print(f"  节点数: {len(results.nodes)}")
    print(f"  单元数: {len(results.elements)}")

    # 比较结果
    max_disp = results.displacements[-1 * 2]  # 最后一个节点的X位移
    print(f"\n结果对比:")
    print(f"  伸长量 (理论): {delta_L_theory*1000:.4f} mm")
    print(f"  伸长量 (FEM):  {max_disp*1000:.4f} mm")
    print(f"  相对误差: {abs(max_disp - delta_L_theory)/delta_L_theory*100:.2f}%")

    # 绘制应力分布
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 应力分布
    elem_stresses = [results.stresses[i]/1e6 for i in range(len(results.elements))]
    elem_centers = [(results.nodes[i].x + results.nodes[i+1].x)/2
                     for i in range(len(results.elements))]

    axes[0].bar(range(len(elem_stresses)), elem_stresses, color='red', alpha=0.7)
    axes[0].axhline(stress_theory/1e6, color='k', linestyle='--', label='理论值')
    axes[0].set_xlabel('单元编号')
    axes[0].set_ylabel('应力 (MPa)')
    axes[0].set_title('应力分布 (均匀拉伸)')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # 位移分布
    node_x = [node.x for node in results.nodes]
    node_disp = [results.displacements[i*2]*1e6 for i in range(len(results.nodes))]

    axes[1].plot(node_x, node_disp, 'bo-', linewidth=2, markersize=8)
    axes[1].set_xlabel('原始位置 (m)')
    axes[1].set_ylabel('位移 (um)')
    axes[1].set_title('轴向位移分布')
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("results/test1_tension.png", dpi=150, bbox_inches='tight')
    print(f"\n图表已保存: results/test1_tension.png")
    plt.close()


def test_2_fixed_fixed_compression():
    """试验 2: 两端固定杆压缩"""
    print("\n" + "="*60)
    print("试验 2: 两端固定杆压缩")
    print("="*60)

    # 试件参数
    length = 1.0           # 试件长度 (m)
    diameter = 0.05       # 直径 (m) = 50 mm
    E = 200e9             # 弹性模量
    force = -500000       # 压力 (N) = 500 kN (负值表示压缩)

    print(f"\n试件参数:")
    print(f"  材料: 钢 (E = {E/1e9:.0f} GPa)")
    print(f"  长度: {length*1000:.0f} mm")
    print(f"  直径: {diameter*1000:.0f} mm")
    print(f"  压力: {abs(force)/1000:.1f} kN")

    # 有限元分析
    results = analyze_fixed_bar_compression(
        length=length,
        diameter=diameter,
        force=force,
        material_E=E,
        n_elements=10
    )

    print(f"\n有限元结果:")
    print(f"  节点数: {len(results.nodes)}")
    print(f"  单元数: {len(results.elements)}")

    # 应力结果
    print(f"\n单元应力:")
    for elem_id, stress in results.stresses.items():
        print(f"  单元 {elem_id}: {stress/1e6:.2f} MPa (压缩)")

    # 支座反力
    print(f"\n支座反力:")
    for node_id, (rx, ry) in results.reactions.items():
        print(f"  节点 {node_id}: Rx = {rx/1000:.2f} kN")

    # 绘图
    fig = results.plot_structure(scale=100, figsize=(12, 6))
    fig.savefig("results/test2_compression_structure.png", dpi=150, bbox_inches='tight')
    print(f"\n结构图已保存: results/test2_compression_structure.png")
    plt.close()


def test_3_gradual_tension():
    """试验 3: 逐级加载拉伸试验"""
    print("\n" + "="*60)
    print("试验 3: 逐级加载拉伸试验 (应力-应变曲线)")
    print("="*60)

    # 试件参数 (标准拉伸试件)
    length = 0.2           # 标距长度 (m)
    diameter = 0.01       # 直径 (m) = 10 mm
    E = 200e9             # 弹性模量

    A = np.pi * (diameter / 2) ** 2

    print(f"\n试件参数:")
    print(f"  材料: 钢 (E = {E/1e9:.0f} GPa)")
    print(f"  标距长度: {length*1000:.0f} mm")
    print(f"  直径: {diameter*1000:.0f} mm")
    print(f"  横截面积: {A*1e6:.2f} mm^2")

    # 逐级加载
    forces = np.linspace(0, 50000, 11)  # 0 到 50 kN
    stresses_fem = []
    strains_fem = []

    print(f"\n逐级加载分析:")
    print(f"{'载荷(N)':<12} {'应力(MPa)':<12} {'应变(ue)':<12} {'伸长(mm)':<12}")
    print("-" * 50)

    for force in forces:
        if force == 0:
            continue

        results = analyze_cantilever_bar(
            length=length,
            diameter=diameter,
            force=force,
            material_E=E,
            n_elements=5
        )

        # 获取平均应力和应变
        avg_stress = np.mean(list(results.stresses.values())) / 1e6
        delta_L = results.displacements[-1 * 2]  # 自由端位移
        strain = delta_L / length

        stresses_fem.append(avg_stress)
        strains_fem.append(strain * 1e6)

        print(f"{force:<12.0f} {avg_stress:<12.2f} {strain*1e6:<12.2f} {delta_L*1000:<12.4f}")

    # 绘制应力-应变曲线
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(strains_fem, stresses_fem, 'bo-', linewidth=2, markersize=8, label='FEM结果')

    # 理论线 (胡克定律)
    strain_theory = np.array(strains_fem)
    stress_theory = E * strain_theory / 1e6
    ax.plot(strain_theory, stress_theory, 'r--', linewidth=2, label='胡克定律 (理论)')

    # 计算弹性模量
    coeffs = np.polyfit(strains_fem, stresses_fem, 1)
    E_fem = coeffs[0] * 1e9  # 转换为 Pa

    ax.set_xlabel('应变 (ue)')
    ax.set_ylabel('应力 (MPa)')
    ax.set_title(f'应力-应变曲线 (E_FEM = {E_fem/1e9:.2f} GPa)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 添加弹性模量标注
    ax.text(0.05, 0.95, f'E = {E_fem/1e9:.1f} GPa',
            transform=ax.transAxes, fontsize=12,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    plt.savefig("results/test3_stress_strain_curve.png", dpi=150, bbox_inches='tight')
    print(f"\n应力-应变曲线已保存: results/test3_stress_strain_curve.png")
    plt.close()


def test_4_comparison_materials():
    """试验 4: 不同材料拉伸对比"""
    print("\n" + "="*60)
    print("试验 4: 不同材料拉伸对比")
    print("="*60)

    # 试件参数
    length = 0.5
    diameter = 0.02

    materials = {
        "Q345钢": {"E": 206e9, "yield": 345e6},
        "6061铝": {"E": 68.9e9, "yield": 276e6},
    }

    force = 50000  # 50 kN

    print(f"\n试件参数: 长度={length}m, 直径={diameter*1000:.0f}mm, 载荷={force/1000:.0f}kN\n")

    results_list = []

    for name, props in materials.items():
        results = analyze_cantilever_bar(
            length=length,
            diameter=diameter,
            force=force,
            material_E=props["E"],
            n_elements=10
        )

        delta_L = results.displacements[-1 * 2]
        stress = np.mean(list(results.stresses.values()))
        safety_factor = props["yield"] / stress

        results_list.append({
            "name": name,
            "E": props["E"],
            "delta_L": delta_L,
            "stress": stress,
            "safety_factor": safety_factor
        })

        print(f"{name}:")
        print(f"  弹性模量: {props['E']/1e9:.1f} GPa")
        print(f"  伸长量: {delta_L*1000:.4f} mm")
        print(f"  应力: {stress/1e6:.2f} MPa")
        print(f"  安全系数: {safety_factor:.2f}")

    # 对比图表
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    names = list(materials.keys())
    delta_Ls = [r["delta_L"]*1000 for r in results_list]
    stresses = [r["stress"]/1e6 for r in results_list]
    safety_factors = [r["safety_factor"] for r in results_list]

    # 伸长量对比
    axes[0].bar(names, delta_Ls, color=['steelblue', 'orange'], alpha=0.7)
    axes[0].set_ylabel('伸长量 (mm)')
    axes[0].set_title('伸长量对比')
    axes[0].grid(True, alpha=0.3, axis='y')
    for i, v in enumerate(delta_Ls):
        axes[0].text(i, v, f'{v:.2f}', ha='center', va='bottom')

    # 应力对比
    axes[1].bar(names, stresses, color=['steelblue', 'orange'], alpha=0.7)
    axes[1].set_ylabel('应力 (MPa)')
    axes[1].set_title('应力对比')
    axes[1].grid(True, alpha=0.3, axis='y')
    for i, v in enumerate(stresses):
        axes[1].text(i, v, f'{v:.1f}', ha='center', va='bottom')

    # 安全系数对比
    axes[2].bar(names, safety_factors, color=['steelblue', 'orange'], alpha=0.7)
    axes[2].set_ylabel('安全系数')
    axes[2].set_title('安全系数对比')
    axes[2].grid(True, alpha=0.3, axis='y')
    axes[2].axhline(1.0, color='r', linestyle='--', label='安全限')
    axes[2].legend()
    for i, v in enumerate(safety_factors):
        axes[2].text(i, v, f'{v:.2f}', ha='center', va='bottom')

    plt.tight_layout()
    plt.savefig("results/test4_material_comparison.png", dpi=150, bbox_inches='tight')
    print(f"\n对比图表已保存: results/test4_material_comparison.png")
    plt.close()


if __name__ == "__main__":
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    # 运行所有试验
    test_1_cantilever_tension()
    test_2_fixed_fixed_compression()
    test_3_gradual_tension()
    test_4_comparison_materials()

    print("\n" + "="*60)
    print("所有拉伸压缩试验完成！")
    print("="*60)
