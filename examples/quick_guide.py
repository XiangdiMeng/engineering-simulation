"""
工程仿真工具包 - 快速入门指南
Engineering Simulation Toolkit - Quick Start Guide
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

print("="*60)
print("工程仿真工具包 - 快速入门")
print("="*60)
print()

# ============================================
# 示例 1: 材料属性查询
# ============================================
print("【示例 1】材料属性查询")
print("-"*40)

from materials import Steel, Aluminum, Concrete, safety_factor

# 创建材料对象
q345 = Steel("Q345")
al_6061 = Aluminum("6061-T6")
c40 = Concrete("C40")

print(f"Q345钢:")
print(f"  弹性模量: {q345.elastic_modulus/1e9:.1f} GPa")
print(f"  屈服强度: {q345.yield_strength/1e6:.0f} MPa")
print(f"  剪切模量: {q345.shear_modulus/1e9:.1f} GPa")

print(f"\n6061铝合金:")
print(f"  弹性模量: {al_6061.elastic_modulus/1e9:.1f} GPa")
print(f"  屈服强度: {al_6061.yield_strength/1e6:.0f} MPa")

print(f"\nC40混凝土:")
print(f"  弹性模量: {c40.elastic_modulus/1e9:.1f} GPa")
print(f"  抗压强度: {c40.yield_strength/1e6:.0f} MPa")

# 计算安全系数
working_stress = 100e6  # 100 MPa
sf = safety_factor(q345, working_stress)
print(f"\n工作应力 100 MPa 下的安全系数: {sf:.2f}")

# ============================================
# 示例 2: 梁结构分析
# ============================================
print("\n" + "="*60)
print("【示例 2】简支梁分析")
print("-"*40)

from beam_analysis import SimplySupportedBeam
import matplotlib.pyplot as plt

# 创建简支梁
beam = SimplySupportedBeam(
    length=6.0,           # 跨度 6m
    width=0.15,           # 宽度 150mm
    height=0.25,          # 高度 250mm
    material=q345
)

# 添加载荷
beam.add_point_load(force=50000, position=3.0)  # 跨中 50kN

# 分析
results = beam.analyze()

print(f"简支梁 (跨度6m, 跨中载荷50kN):")
print(f"  最大挠度: {results.max_deflection*1000:.2f} mm")
print(f"  最大弯矩: {results.max_moment/1000:.2f} kN·m")
print(f"  最大应力: {results.max_stress/1e6:.2f} MPa")
print(f"  安全系数: {results.safety_factor:.2f}")

# 绘制结果图
fig = results.plot(figsize=(12, 8))
plt.savefig('../results/quick_start_beam.png', dpi=150, bbox_inches='tight')
print(f"  图表已保存: results/quick_start_beam.png")
plt.close()

# ============================================
# 示例 3: 桁架结构分析
# ============================================
print("\n" + "="*60)
print("【示例 3】桁架结构分析")
print("-"*40)

from truss import create_roof_truss

# 创建屋顶桁架
truss = create_roof_truss(
    span=15.0,           # 跨度 15m
    height=4.0,          # 高度 4m
    n_bays=8,            # 8节
    snow_load=3000       # 雪载 3kN/m
)

# 分析
truss_result = truss.analyze()

# 计算最大应力
max_stress = max(abs(s) for s in truss_result.stresses.values()) / 1e6
min_stress = min(s for s in truss_result.stresses.values()) / 1e6

print(f"屋顶桁架 (跨度15m, 8节):")
print(f"  节点数: {len(truss.nodes)}")
print(f"  单元数: {len(truss.elements)}")
print(f"  最大拉应力: {max_stress:.2f} MPa")
print(f"  最大压应力: {min_stress:.2f} MPa")

# 绘制桁架
fig = truss_result.plot_structure(show_deformation=True, scale=200)
plt.savefig('../results/quick_start_truss.png', dpi=150, bbox_inches='tight')
print(f"  图表已保存: results/quick_start_truss.png")
plt.close()

# ============================================
# 示例 4: 框架结构分析
# ============================================
print("\n" + "="*60)
print("【示例 4】门式框架分析")
print("-"*40)

from frame import create_portal_frame

# 创建门式框架
frame = create_portal_frame(
    width=10.0,              # 跨度 10m
    height=6.0,              # 高度 6m
    section_width=0.3,       # 柱宽度 300mm
    section_height=0.4,      # 柱高度 400mm
    E=206e9                  # 弹性模量
)

# 施加载荷
frame.nodes[1].loads = (10000, 0, 0)    # 左柱顶: 水平力 10kN
frame.nodes[2].loads = (0, -30000, 0)   # 右柱顶: 垂直力 30kN

# 分析
frame_result = frame.solve()

print(f"门式框架 (10m x 6m):")
print(f"  节点数: {len(frame.nodes)}")
print(f"  单元数: {len(frame.elements)}")

# 打印节点位移
for i in range(len(frame.nodes)):
    if i * 3 + 2 < len(frame_result.displacements):
        u = frame_result.displacements[i * 3] * 1000
        v = frame_result.displacements[i * 3 + 1] * 1000
        if abs(u) > 0.01 or abs(v) > 0.01:
            print(f"  节点 {i} 位移: dx={u:.3f}mm, dy={v:.3f}mm")

# 绘制结果
fig = frame_result.plot(scale=100)
plt.savefig('../results/quick_start_frame.png', dpi=150, bbox_inches='tight')
print(f"  图表已保存: results/quick_start_frame.png")
plt.close()

# ============================================
# 示例 5: 柱稳定性分析
# ============================================
print("\n" + "="*60)
print("【示例 5】柱屈曲分析")
print("-"*40)

from stability import (
    euler_buckling_analysis, ColumnSection, BoundaryCondition,
    slenderness_ratio_analysis
)

# 创建柱截面 (H型钢简化)
section = ColumnSection(
    A=0.015,        # 面积 150 cm²
    Ix=5.0e-4,      # 惯性矩
    Iy=1.5e-4
)

# 边界条件 (两端铰接)
bc = BoundaryCondition(
    fix_start_x=True, fix_start_y=True,
    fix_end_x=True, fix_end_y=True
    # fix_start_theta=False, fix_end_theta=False  # 默认为False，铰接
)

# 柱参数
column_length = 5.0  # 长度 5m
applied_load = 500000  # 轴向压力 500 kN

# 屈曲分析
buckling_result = euler_buckling_analysis(
    length=column_length,
    material=q345,
    section=section,
    applied_load=applied_load,
    boundary_condition=bc
)

print(f"柱屈曲分析 (长度5m, 两端铰接):")
print(f"  临界载荷: {buckling_result.critical_load/1000:.2f} kN")
print(f"  临界应力: {buckling_result.critical_stress/1e6:.2f} MPa")
print(f"  有效长度: {buckling_result.effective_length:.2f} m")
print(f"  长细比: {buckling_result.slenderness_ratio:.1f}")
print(f"  安全系数: {buckling_result.safety_factor:.2f}")

# 判断是否安全
if buckling_result.safety_factor > 2.0:
    print(f"  状态: 安全 ✓")
else:
    print(f"  状态: 不安全 ✗ (安全系数不足)")

# ============================================
# 示例 6: 多层框架
# ============================================
print("\n" + "="*60)
print("【示例 6】多层建筑框架")
print("-"*40)

from combined import create_multistory_frame

# 创建3层2跨框架
building = create_multistory_frame(
    width=6.0,              # 开间宽度 6m
    height_per_floor=3.5,   # 层高 3.5m
    n_floors=3,             # 3层
    n_bays=2,               # 2跨
    column_size=0.4,        # 柱尺寸 400mm
    beam_size=0.3,          # 梁尺寸 300mm
    E=30e9                  # 混凝土弹性模量
)

# 施加风载荷
for node in building.nodes:
    if node.y > 0:  # 非底层节点
        building.nodes[node.id].loads = (
            node.loads[0] + 5000,   # 水平风载 5kN
            node.loads[1],
            node.loads[2]
        )

print(f"多层框架 (3层2跨):")
print(f"  总节点数: {len(building.nodes)}")
print(f"  总单元数: {len(building.elements)}")
print(f"  建筑高度: {3.5 * 3:.1f} m")
print(f"  建筑宽度: {6.0 * 2:.1f} m")

# ============================================
# 总结
# ============================================
print("\n" + "="*60)
print("✅ 所有示例运行完成！")
print("生成的图表保存在 ../results/ 目录下")
print("="*60)

# 使用建议
print("\n📖 使用建议:")
print("  1. 根据工程需求选择合适的结构类型")
print("  2. 调整材料和几何参数以优化设计")
print("  3. 检查安全系数和变形是否满足规范要求")
print("  4. 使用 param_frame 进行参数化设计")
print("\n更多示例请参考 examples/ 目录")
