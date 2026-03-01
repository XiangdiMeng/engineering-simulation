"""
工程仿真快速入门示例
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib.pyplot as plt
from src.materials import Steel, Aluminum, Concrete
from src.beam_analysis import SimplySupportedBeam, CantileverBeam


def example_1_simple_supported_beam():
    """示例 1: 简支梁受力分析"""
    print("\n" + "="*50)
    print("示例 1: 简支梁受力分析")
    print("="*50)

    # 创建简支梁
    beam = SimplySupportedBeam(
        length=6.0,           # 6米长
        width=0.15,           # 150mm宽
        height=0.3,          # 300mm高
        material=Steel("Q345")
    )

    print(f"\n梁参数:")
    print(f"  长度: {beam.length} m")
    print(f"  截面: {beam.width*1000:.0f} x {beam.height*1000:.0f} mm")
    print(f"  材料: {beam.material.name}")
    print(f"  惯性矩: {beam.I:.6f} m^4")

    # 施加集中载荷（跨中）
    P = 100000  # 100 kN
    beam.add_point_load(force=P, position=beam.length / 2)

    print(f"\n载荷:")
    print(f"  集中力: {P/1000:.1f} kN @ 跨中")

    # 分析
    results = beam.analyze()

    print(f"\n结果:")
    print(f"  最大挠度: {results.max_deflection * 1000:.2f} mm")
    print(f"  最大弯矩: {results.max_moment / 1000:.2f} kN·m")
    print(f"  最大应力: {results.max_stress / 1e6:.2f} MPa")
    print(f"  安全系数: {results.safety_factor:.2f}")

    # 绘图
    fig = results.plot(figsize=(12, 8))
    fig.savefig("results/example1_beam.png", dpi=150, bbox_inches='tight')
    print(f"\n图表已保存到: results/example1_beam.png")
    plt.close(fig)


def example_2_cantilever_beam():
    """示例 2: 悬臂梁分析"""
    print("\n" + "="*50)
    print("示例 2: 悬臂梁分析")
    print("="*50)

    # 创建悬臂梁
    beam = CantileverBeam(
        length=3.0,
        width=0.1,
        height=0.2,
        material=Aluminum("6061-T6")
    )

    print(f"\n梁参数:")
    print(f"  长度: {beam.length} m")
    print(f"  材料: {beam.material.name}")

    # 自由端施加集中载荷
    P = 5000  # 5 kN
    beam.add_point_load(force=P, position=beam.length)

    print(f"\n载荷:")
    print(f"  自由端集中力: {P/1000:.1f} kN")

    # 分析
    results = beam.analyze()

    print(f"\n结果:")
    print(f"  自由端挠度: {results.max_deflection * 1000:.2f} mm")
    print(f"  固定端弯矩: {results.max_moment / 1000:.2f} kN·m")
    print(f"  最大应力: {results.max_stress / 1e6:.2f} MPa")
    print(f"  安全系数: {results.safety_factor:.2f}")

    # 绘图
    fig = results.plot(figsize=(12, 8))
    fig.savefig("results/example2_cantilever.png", dpi=150, bbox_inches='tight')
    print(f"\n图表已保存到: results/example2_cantilever.png")
    plt.close(fig)


def example_3_material_comparison():
    """示例 3: 不同材料对比"""
    print("\n" + "="*50)
    print("示例 3: 不同材料对比")
    print("="*50)

    materials = {
        "Q345钢": Steel("Q345"),
        "6061铝": Aluminum("6061-T6"),
    }

    # 相同尺寸的梁
    length = 5.0
    width = 0.1
    height = 0.2
    load = 50000

    print(f"\n梁尺寸: {width*1000:.0f} x {height*1000:.0f} mm x {length} m")
    print(f"载荷: {load/1000:.1f} kN @ 跨中\n")

    results_list = []

    for name, mat in materials.items():
        beam = SimplySupportedBeam(length, width, height, mat)
        beam.add_point_load(force=load, position=length / 2)
        results = beam.analyze()

        results_list.append({
            "name": name,
            "deflection": results.max_deflection * 1000,
            "stress": results.max_stress / 1e6,
            "safety_factor": results.safety_factor,
            "mass": mat.density * length * width * height
        })

    # 打印对比表格
    print(f"{'材料':<12} {'挠度(mm)':<12} {'应力(MPa)':<12} {'安全系数':<12} {'质量(kg)':<10}")
    print("-" * 60)
    for r in results_list:
        print(f"{r['name']:<12} {r['deflection']:<12.2f} {r['stress']:<12.2f} "
              f"{r['safety_factor']:<12.2f} {r['mass']:<10.1f}")


def example_4_multiple_loads():
    """示例 4: 多载荷分析"""
    print("\n" + "="*50)
    print("示例 4: 多载荷简支梁")
    print("="*50)

    beam = SimplySupportedBeam(
        length=8.0,
        width=0.2,
        height=0.4,
        material=Steel("Q345")
    )

    print(f"\n梁参数:")
    print(f"  长度: {beam.length} m")
    print(f"  截面: {beam.width*1000:.0f} × {beam.height*1000:.0f} mm")

    # 添加多个载荷
    loads = [
        (30000, 2.0),
        (40000, 4.0),
        (30000, 6.0),
    ]

    for P, pos in loads:
        beam.add_point_load(force=P, position=pos)
        print(f"  载荷: {P/1000:.1f} kN @ {pos} m")

    # 添加分布载荷
    beam.add_distributed_load(magnitude=10000, start=1.0, end=7.0)
    print(f"  分布载荷: 10 kN/m @ 1.0-7.0 m")

    # 分析
    results = beam.analyze()

    print(f"\n结果:")
    print(f"  最大挠度: {results.max_deflection * 1000:.2f} mm")
    print(f"  最大弯矩: {results.max_moment / 1000:.2f} kN·m")
    print(f"  最大应力: {results.max_stress / 1e6:.2f} MPa")

    # 绘图
    fig = results.plot(figsize=(12, 8))
    fig.savefig("results/example4_multiple_loads.png", dpi=150, bbox_inches='tight')
    print(f"\n图表已保存到: results/example4_multiple_loads.png")
    plt.close(fig)


if __name__ == "__main__":
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    # 运行示例
    example_1_simple_supported_beam()
    example_2_cantilever_beam()
    example_3_material_comparison()
    example_4_multiple_loads()

    print("\n" + "="*50)
    print("所有示例运行完成！")
    print("="*50)
