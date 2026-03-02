"""
住宅阳台结构完整分析
Complete Analysis of Residential Balcony Structure

运行方式: 在项目根目录运行 python run_balcony_analysis.py
"""

import sys
sys.path.insert(0, 'src')

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.collections import LineCollection

# ============================================
# 1. 结构设计参数
# ============================================
print("="*70)
print(" 住宅阳台结构设计分析")
print("="*70)
print()

# 几何参数
BALCONY_LENGTH = 3.5      # 悬挑长度 (m)
BALCONY_WIDTH = 1.5       # 阳台宽度 (m)
SLAB_THICKNESS = 0.12     # 板厚 (m)
RAILING_HEIGHT = 1.1      # 栏杆高度 (m)

# 材料参数
CONCRETE_GRADE = "C30"
STEEL_REBAR_RATIO = 0.003 # 配筋率 0.3%

# 载荷参数
LIVE_LOAD_PERSON = 2.5    # 人群活载 (kN/m²)
DEAD_LOAD_SLAB = 25 * SLAB_THICKNESS  # 板自重 (kN/m²)
RAILING_LOAD = 0.5        # 栏杆水平荷载 (kN/m)
WIND_LOAD = 0.5           # 风载 (kN/m²)

print("【设计参数】")
print(f"  阳台尺寸: {BALCONY_LENGTH}m (悬挑) x {BALCONY_WIDTH}m (宽)")
print(f"  板厚: {SLAB_THICKNESS*1000:.0f} mm")
print(f"  栏杆高度: {RAILING_HEIGHT} m")
print(f"  混凝土等级: {CONCRETE_GRADE}")
print()

# ============================================
# 2. 材料属性
# ============================================
from src.materials import Concrete

concrete = Concrete(CONCRETE_GRADE)

# 定义HRB400钢筋
class SteelRebar:
    def __init__(self):
        self.name = "HRB400钢筋"
        self.elastic_modulus = 200e9
        self.yield_strength = 400e6
        self.ultimate_strength = 540e6
        self.density = 7850

steel_rebar = SteelRebar()

print("【材料属性】")
print(f"  混凝土 {CONCRETE_GRADE}:")
print(f"    弹性模量: {concrete.elastic_modulus/1e9:.1f} GPa")
print(f"    抗压强度: {concrete.yield_strength/1e6:.0f} MPa")
print(f"  钢筋 HRB400:")
print(f"    屈服强度: {steel_rebar.yield_strength/1e6:.0f} MPa")
print()

# ============================================
# 3. 悬挑板分析 (简化为悬臂梁)
# ============================================
from src.beam_analysis import CantileverBeam

print("【分析 1: 悬挑板强度分析】")
print("-"*50)

# 等效钢筋混凝土材料
E_concrete = concrete.elastic_modulus
E_rebar_effective = E_concrete * 1.2  # 考虑钢筋增强

class RebarConcrete(Concrete):
    def __init__(self):
        super().__init__(CONCRETE_GRADE)
        self.elastic_modulus = E_rebar_effective
        self.name = f"钢筋混凝土({CONCRETE_GRADE})"

rc_material = RebarConcrete()

# 创建悬臂梁模型 (单位宽度)
balcony_beam = CantileverBeam(
    length=BALCONY_LENGTH,
    width=1.0,  # 单位宽度
    height=SLAB_THICKNESS,
    material=rc_material
)

# 计算荷载
dead_load = DEAD_LOAD_SLAB * BALCONY_WIDTH * 1000  # N/m
live_load = LIVE_LOAD_PERSON * BALCONY_WIDTH * 1000  # N/m
total_load = dead_load + live_load
railing_load = RAILING_LOAD * BALCONY_WIDTH * 1000  # N

print(f"荷载信息:")
print(f"  恒载(自重): {dead_load:.0f} N/m")
print(f"  活载(人群): {live_load:.0f} N/m")
print(f"  栏杆荷载: {railing_load:.0f} N")
print(f"  总均布载: {total_load:.0f} N/m")
print()

# 添加荷载
balcony_beam.add_distributed_load(total_load, 0, BALCONY_LENGTH)
balcony_beam.add_point_load(railing_load, BALCONY_LENGTH)

# 分析
results_slab = balcony_beam.analyze()

M_max = results_slab.max_moment
V_max = max(results_slab.shear)
deflection_limit = BALCONY_LENGTH * 1000 / 250

print(f"分析结果:")
print(f"  最大弯矩: {M_max/1000:.2f} kN·m (墙根处)")
print(f"  最大剪力: {V_max/1000:.2f} kN")
print(f"  最大挠度: {results_slab.max_deflection*1000:.2f} mm")
print(f"  挠度限值: {deflection_limit:.2f} mm (L/250)")

if results_slab.max_deflection * 1000 < deflection_limit:
    print(f"  ✓ 挠度满足要求")
else:
    print(f"  ✗ 挠度超限！")

# 配筋计算
h0 = SLAB_THICKNESS - 0.02  # 有效高度，保护层20mm
fy = steel_rebar.yield_strength
As_required = M_max / (fy * 0.9 * h0)
As_provided = BALCONY_WIDTH * SLAB_THICKNESS * STEEL_REBAR_RATIO

print(f"\n配筋验算:")
print(f"  计算需要: {As_required*1e6:.2f} mm²/m")
print(f"  实际提供: {As_provided*1e6:.2f} mm²/m (ρ={STEEL_REBAR_RATIO*100:.1f}%)")
if As_provided >= As_required:
    print(f"  ✓ 配筋满足要求")
else:
    print(f"  ✗ 配筋不足！需要 ρ={As_required/(BALCONY_WIDTH*SLAB_THICKNESS)*100:.2f}%")

# 应力验算
max_stress = results_slab.max_stress
allowable_stress = concrete.yield_strength / 1.5
print(f"\n应力验算:")
print(f"  最大压应力: {max_stress/1e6:.2f} MPa")
print(f"  允许压应力: {allowable_stress/1e6:.2f} MPa")
print(f"  {'✓ 混凝土压应力满足要求' if max_stress < allowable_stress else '✗ 混凝土压应力超限！'}")
print()

# ============================================
# 4. 栏杆立柱稳定性分析
# ============================================
from src.stability import euler_buckling_analysis, ColumnSection, BoundaryCondition

print("【分析 2: 栏杆立柱稳定性分析】")
print("-"*50)

# 方钢管截面
outer_size = 0.05  # 50mm
thickness = 3e-3
inner_size = outer_size - 2 * thickness
A_column = outer_size**2 - inner_size**2
I_column = (outer_size**4 - inner_size**4) / 12

section_column = ColumnSection(A=A_column, Ix=I_column, Iy=I_column)

# 边界条件
bc_column = BoundaryCondition(
    fix_start_x=True, fix_start_y=True,
    fix_end_x=False, fix_end_y=True
)

# 荷载
column_spacing = 0.5
h_load = RAILING_LOAD * column_spacing * 1000
wind_load = WIND_LOAD * RAILING_HEIGHT * column_spacing * 1000
total_h_load = h_load + wind_load

buckling_result = euler_buckling_analysis(
    length=RAILING_HEIGHT,
    material=steel_rebar,
    section=section_column,
    applied_load=total_h_load,
    boundary_condition=bc_column
)

print(f"立柱参数:")
print(f"  截面: 50mm x 50mm x 3mm 方钢管")
print(f"  高度: {RAILING_HEIGHT} m")
print(f"  间距: {column_spacing} m")
print()

print(f"荷载:")
print(f"  水平推力: {h_load:.0f} N")
print(f"  风载: {wind_load:.0f} N")
print()

print(f"稳定性分析结果:")
print(f"  临界载荷: {buckling_result.critical_load/1000:.2f} kN")
print(f"  长细比: {buckling_result.slenderness_ratio:.1f}")
print(f"  长细比限值: 150")
print(f"  {'✓ 长细比满足要求' if buckling_result.slenderness_ratio < 150 else '✗ 长细比超限！'}")
print()

# ============================================
# 5. 绘制结构图和分析结果
# ============================================
print("【生成结构图】")
print("-"*50)

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 图1: 阳台结构示意图
ax1 = axes[0, 0]

# 墙体
wall = Rectangle((-0.2, -0.1), 0.2, RAILING_HEIGHT + 0.3,
                facecolor='gray', edgecolor='black', linewidth=2, label='墙体')
ax1.add_patch(wall)

# 悬挑板
slab = Rectangle((0, -SLAB_THICKNESS), BALCONY_LENGTH, SLAB_THICKNESS,
                 facecolor='lightblue', edgecolor='blue', linewidth=2, label='悬挑板')
ax1.add_patch(slab)

# 栏杆立柱
for x in np.arange(0.3, BALCONY_LENGTH, 0.4):
    col = Rectangle((x-0.01, 0), 0.02, RAILING_HEIGHT,
                    facecolor='orange', edgecolor='red', linewidth=1)
    ax1.add_patch(col)

# 扶手
handrail = Rectangle((0, RAILING_HEIGHT-0.05), BALCONY_LENGTH, 0.05,
                     facecolor='orange', edgecolor='red', linewidth=2)
ax1.add_patch(handrail)

# 尺寸标注
ax1.annotate('', xy=(0, -0.15), xytext=(BALCONY_LENGTH, -0.15),
            arrowprops=dict(arrowstyle='<->'))
ax1.text(BALCONY_LENGTH/2, -0.2, f'{BALCONY_LENGTH}m', ha='center')

ax1.set_xlim(-0.3, BALCONY_LENGTH + 0.3)
ax1.set_ylim(-0.3, RAILING_HEIGHT + 0.3)
ax1.set_aspect('equal')
ax1.set_title('阳台结构示意图', fontsize=14, fontweight='bold')
ax1.legend(loc='upper left')
ax1.grid(True, alpha=0.3)

# 图2: 弯矩图
ax2 = axes[0, 1]
x = np.linspace(0, BALCONY_LENGTH, 50)
M = total_load * x**2 / 2 + railing_load * x

ax2.plot(x, M/1000, 'b-', linewidth=2, label='弯矩')
ax2.fill_between(x, 0, M/1000, alpha=0.3, color='blue')
ax2.set_xlabel('位置 (m)')
ax2.set_ylabel('弯矩 (kN·m)')
ax2.set_title(f'弯矩图 (M_max = {M_max/1000:.2f} kN·m)')
ax2.grid(True, alpha=0.3)

# 图3: 挠度图
ax3 = axes[1, 0]
E = E_rebar_effective
I = (1.0 * SLAB_THICKNESS**3) / 12
delta = total_load * x**4 / (8 * E * I) + railing_load * x**2 * (3*BALCONY_LENGTH - x) / (6 * E * I)

ax3.plot(x, delta*1000, 'r-', linewidth=2, label='挠度')
ax3.axhline(deflection_limit, color='g', linestyle='--', label=f'限值 L/250')
ax3.set_xlabel('位置 (m)')
ax3.set_ylabel('挠度 (mm)')
ax3.set_title(f'挠度图 (δ_max = {results_slab.max_deflection*1000:.2f} mm)')
ax3.legend()
ax3.grid(True, alpha=0.3)

# 图4: 配筋截面
ax4 = axes[1, 1]

# 板截面
slab_rect = Rectangle((0, 0), BALCONY_WIDTH*1000, SLAB_THICKNESS*1000,
                       facecolor='lightblue', edgecolor='blue', linewidth=2)
ax4.add_patch(slab_rect)

# 钢筋
for rx in np.linspace(30, BALCONY_WIDTH*1000-30, 8):
    rebar = plt.Circle((rx, 20), 4, color='red', alpha=0.8)
    ax4.add_patch(rebar)

ax4.text(BALCONY_WIDTH*500, SLAB_THICKNESS*600, '受压区',
         ha='center', fontsize=10, color='blue')
ax4.text(BALCONY_WIDTH*500, 30, '受拉区 (钢筋)',
         ha='center', fontsize=10, color='red', va='top')

ax4.set_xlim(-100, BALCONY_WIDTH*1000 + 100)
ax4.set_ylim(-50, SLAB_THICKNESS*1000 + 150)
ax4.set_aspect('equal')
ax4.set_title(f'配筋截面 (As = {As_provided*1e6:.0f} mm²/m)')
ax4.set_xlabel('mm')
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('results/balcony_analysis.png', dpi=150, bbox_inches='tight')
print(f"  图表已保存: results/balcony_analysis.png")
plt.close()

# ============================================
# 6. 总结报告
# ============================================
print()
print("="*70)
print("  分析总结")
print("="*70)
print()

strength_ok = As_provided >= As_required
deflection_ok = results_slab.max_deflection*1000 < deflection_limit
stability_ok = buckling_result.slenderness_ratio < 150

print(f"验算结果汇总:")
print(f"  1. 强度 (配筋):     {'✓ 满足' if strength_ok else '✗ 不满足'}")
print(f"  2. 挠度:          {'✓ 满足' if deflection_ok else '✗ 不满足'}")
print(f"  3. 稳定性 (立柱):  {'✓ 满足' if stability_ok else '✗ 不满足'}")
print()

if strength_ok and deflection_ok and stability_ok:
    print("  结论: ✓ 所有验算均满足要求，设计安全可行。")
else:
    print("  结论: ✗ 部分验算不满足，需要调整设计参数。")

print()
print(f"图表已保存至: results/balcony_analysis.png")
print("="*70)
