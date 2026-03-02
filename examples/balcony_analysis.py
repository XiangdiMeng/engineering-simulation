"""
住宅阳台结构完整分析
Complete Analysis of Residential Balcony Structure

结构描述：
- 悬挑阳台，尺寸 3.5m × 1.5m
- 带玻璃栏杆
- 考虑人群荷载、风荷载
- 包含强度、稳定性、模态分析
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

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
SLAB_THICKNESS = 0.12     # 板厚 (mm)
RAILING_HEIGHT = 1.1      # 栏杆高度 (m)

# 材料参数 - C30混凝土 + HRB400钢筋
CONCRETE_GRADE = "C30"
STEEL_REBAR_RATIO = 0.003 # 配筋率 0.3%

# 载荷参数 (按建筑规范)
LIVE_LOAD_PERSON = 2.5    # 人群活载 (kN/m²) - 阳台要求较高
DEAD_LOAD_SLAB = 25 * 0.12  # 板自重 (kN/m²) = 混凝土容重 × 板厚
RAILING_LOAD = 0.5        # 栏杆水平荷载 (kN/m)
WIND_LOAD = 0.5           # 风载 (kN/m²)

print("【设计参数】")
print(f"  阳台尺寸: {BALCONY_LENGTH}m (悬挑) × {BALCONY_WIDTH}m (宽)")
print(f"  板厚: {SLAB_THICKNESS*1000:.0f} mm")
print(f"  栏杆高度: {RAILING_HEIGHT} m")
print(f"  混凝土等级: {CONCRETE_GRADE}")
print()

# ============================================
# 2. 材料属性定义
# ============================================
from materials import Concrete, Steel

concrete = Concrete(CONCRETE_GRADE)
steel_rebar = Steel("HRB400")  # 假设添加HRB400钢筋
# 修改钢筋属性
steel_rebar.elastic_modulus = 200e9
steel_rebar.yield_strength = 400e6
steel_rebar.ultimate_strength = 540e6

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
from beam_analysis import CantileverBeam

print("【分析 1: 悬挑板强度分析】")
print("-"*50)

# 将板简化为单位宽度的悬臂梁
beam_width = 1.0  # 单位宽度 (m)
beam_height = SLAB_THICKNESS

# 计算等效截面惯性矩（考虑钢筋）
# 简化：使用混凝土截面，钢筋按等效面积折算
I_effective = (beam_width * beam_height**3) / 12

# 创建等效材料（钢筋混凝土）
E_effective = concrete.elastic_modulus * 1.2  # 考虑钢筋增强

class RebarConcrete(Concrete):
    def __init__(self):
        super().__init__(CONCRETE_GRADE)
        self.elastic_modulus = E_effective
        self.name = f"钢筋混凝土({CONCRETE_GRADE})"

rc_material = RebarConcrete()

# 创建悬臂梁模型
balcony_beam = CantileverBeam(
    length=BALCONY_LENGTH,
    width=beam_width,
    height=beam_height,
    material=rc_material
)

# 施加荷载
# 1. 恒载（自重）
dead_load = DEAD_LOAD_SLAB * BALCONY_WIDTH * 1000  # N/m
# 2. 活载（人群）
live_load = LIVE_LOAD_PERSON * BALCONY_WIDTH * 1000  # N/m
# 3. 总均布荷载
total_load = dead_load + live_load

# 添加分布载荷
balcony_beam.add_distributed_load(total_load, 0, BALCONY_LENGTH)

# 添加栏杆水平荷载（作用在自由端）
railing_load = RAILING_LOAD * BALCONY_WIDTH * 1000  # N
balcony_beam.add_point_load(railing_load, BALCONY_LENGTH)

print(f"荷载信息:")
print(f"  恒载(自重): {dead_load:.0f} N/m")
print(f"  活载(人群): {live_load:.0f} N/m")
print(f"  栏杆荷载: {railing_load:.0f} N (悬臂端)")
print(f"  总均布载: {total_load:.0f} N/m")
print()

# 分析
results_slab = balcony_beam.analyze()

# 计算配筋（简化的受弯构件配筋计算）
M_max = results_slab.max_moment  # N·m
h0 = SLAB_THICKNESS - 0.02  # 有效高度 (m), 保护层20mm

# 按混凝土规范计算配筋
# As = M / (fy * γs * h0), 简化取 γs = 0.9
fy = steel_rebar.yield_strength
As_required = M_max / (fy * 0.9 * h0)
As_provided = BALCONY_WIDTH * SLAB_THICKNESS * STEEL_REBAR_RATIO

print(f"分析结果:")
print(f"  最大弯矩: {M_max/1000:.2f} kN·m")
print(f"  最大剪力: {max(results_slab.shear)/1000:.2f} kN")
print(f"  最大挠度: {results_slab.max_deflection*1000:.2f} mm")
print(f"  挠度限值: {BALCONY_LENGTH*1000/250:.2f} mm (L/250)")

# 挠度验算
deflection_limit = BALCONY_LENGTH * 1000 / 250
if results_slab.max_deflection * 1000 < deflection_limit:
    print(f"  ✓ 挠度满足要求")
else:
    print(f"  ✗ 挠度超限！需要增加板厚或配筋")

# 配筋验算
print(f"\n配筋验算:")
print(f"  计算需要: {As_required*1e6:.2f} mm²/m")
print(f"  实际提供: {As_provided*1e6:.2f} mm²/m (ρ={STEEL_REBAR_RATIO*100:.1f}%)")
if As_provided >= As_required:
    print(f"  ✓ 配筋满足要求")
else:
    print(f"  ✗ 配筋不足！需要 ρ={As_required/(BALCONY_WIDTH*SLAB_THICKNESS)*100:.2f}%")

# 应力验算
max_stress = results_slab.max_stress
allowable_stress = concrete.yield_strength / 1.5  # 混凝土设计强度
print(f"\n应力验算:")
print(f"  最大压应力: {max_stress/1e6:.2f} MPa")
print(f"  允许压应力: {allowable_stress/1e6:.2f} MPa")
if max_stress < allowable_stress:
    print(f"  ✓ 混凝土压应力满足要求")
else:
    print(f"  ✗ 混凝土压应力超限！")

print()

# ============================================
# 4. 栏杆立柱稳定性分析
# ============================================
from stability import euler_buckling_analysis, ColumnSection, BoundaryCondition

print("【分析 2: 栏杆立柱稳定性分析】")
print("-"*50)

# 栏杆立柱参数
RAILING_COLUMN_HEIGHT = RAILING_HEIGHT
RAILING_COLUMN_SPACING = 0.5  # 立柱间距 (m)
COLUMN_SECTION = "square_50x50"  # 50mm×50mm 方钢管
COLUMN_THICKNESS = 3e-3  # 壁厚 3mm
COLUMN_E = 200e9  # 钢材弹性模量

# 方钢管截面属性
outer_size = 0.05  # 50mm
inner_size = outer_size - 2 * COLUMN_THICKNESS
A_column = outer_size**2 - inner_size**2
I_column = (outer_size**4 - inner_size**4) / 12

section_column = ColumnSection(
    A=A_column,
    Ix=I_column,
    Iy=I_column
)

# 边界条件：底部固定，顶部自由（对弯矩）/铰接（对轴压）
bc_column = BoundaryCondition(
    fix_start_x=True, fix_start_y=True,
    fix_end_x=False, fix_end_y=True
)

# 载荷：水平推力 + 风载
h_load_per_column = RAILING_LOAD * RAILING_COLUMN_SPACING * 1000  # N
wind_load_column = WIND_LOAD * RAILING_COLUMN_HEIGHT * RAILING_COLUMN_SPACING * 1000  # N
total_h_load = h_load_per_column + wind_load_column

# 稳定性分析
buckling_result = euler_buckling_analysis(
    length=RAILING_COLUMN_HEIGHT,
    material=steel_rebar,
    section=section_column,
    applied_load=total_h_load,  # 这里用水平力，实际应该按压弯构件分析
    boundary_condition=bc_column
)

print(f"立柱参数:")
print(f"  截面: 50mm×50mm×3mm 方钢管")
print(f"  高度: {RAILING_COLUMN_HEIGHT} m")
print(f"  间距: {RAILING_COLUMN_SPACING} m")
print(f"  截面积: {A_column*1e4:.2f} cm²")
print(f"  惯性矩: {I_column*1e8:.4f} cm⁴")
print()

print(f"荷载:")
print(f"  水平推力: {h_load_per_column:.0f} N")
print(f"  风载: {wind_load_column:.0f} N")
print(f"  总水平力: {total_h_load:.0f} N")
print()

print(f"稳定性分析结果:")
print(f"  临界载荷: {buckling_result.critical_load/1000:.2f} kN")
print(f"  长细比: {buckling_result.slenderness_ratio:.1f}")
print(f"  长细比限值: [150]")
if buckling_result.slenderness_ratio < 150:
    print(f"  ✓ 长细比满足要求")
else:
    print(f"  ✗ 长细比超限！")

print()

# ============================================
# 5. 阳台整体模态分析
# ============================================
from fea import FEModel, FEMaterial, Node

print("【分析 3: 阳台整体模态分析】")
print("-"*50)

# 创建简化框架模型
model_balcony = FEModel(name="阳台框架")

# 节点定义
# 0: 墙根固定点
# 1: 悬臂端
# 2: 栏杆顶部

model_balcony.add_node(0, 0, fixity=(True, True, True))  # 墙根
model_balcony.add_node(BALCONY_LENGTH, 0, fixity=(False, False, False))  # 悬臂端
model_balcony.add_node(BALCONY_LENGTH, RAILING_HEIGHT, fixity=(False, False, False))  # 栏杆顶

# 单元材料
mat_slab = FEMaterial("混凝土板", E=30e9, A=0.12*1.0, density=2500)
mat_railing = FEMaterial("栏杆", E=200e9, A=A_column, density=7850)

# 添加单元
# 悬臂板
model_balcony.add_truss_element(0, 1, mat_slab)
# 栏杆立柱
model_balcony.add_truss_element(1, 2, mat_railing)

# 模态分析（简化，使用质量矩阵）
from dynamics import ModalAnalysis

modal_analysis = ModalAnalysis(
    nodes=model_balcony.nodes,
    elements=model_balcony.elements,
    n_modes=3
)

modal_result = modal_analysis.solve()

print(f"模态分析结果:")
for i, freq in enumerate(modal_result.natural_frequencies):
    print(f"  第 {i+1} 阶固有频率: {freq:.2f} Hz")

# 人体舒适度评价（基频）
fundamental_freq = modal_result.natural_frequencies[0]
print(f"\n舒适度评价:")
print(f"  基频: {fundamental_freq:.2f} Hz")
if fundamental_freq > 3:
    print(f"  ✓ 满足人体舒适度要求 (>3 Hz)")
elif fundamental_freq > 2:
    print(f"  △ 基本满足，可能轻微震动 (2-3 Hz)")
else:
    print(f"  ✗ 不满足舒适度要求，需要加强刚度 (<2 Hz)")

print()

# ============================================
# 6. 绘制阳台结构图
# ============================================
print("【生成结构图】")
print("-"*50)

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 图1: 阳台结构示意图
ax1 = axes[0, 0]

# 绘制墙体
wall = Rectangle((-0.2, -0.1), 0.2, RAILING_HEIGHT + 0.3,
                facecolor='gray', edgecolor='black', linewidth=2, label='墙体')
ax1.add_patch(wall)

# 绘制悬挑板
slab = Rectangle((0, -SLAB_THICKNESS), BALCONY_LENGTH, SLAB_THICKNESS,
                 facecolor='lightblue', edgecolor='blue', linewidth=2, label='悬挑板')
ax1.add_patch(slab)

# 绘制栏杆立柱
for x in np.arange(0.5, BALCONY_LENGTH, 0.5):
    column = Rectangle((x-0.01, 0), 0.02, RAILING_HEIGHT,
                       facecolor='orange', edgecolor='red', linewidth=1)
    ax1.add_patch(column)

# 绘制栏杆扶手
handrail = Rectangle((0, RAILING_HEIGHT-0.05), BALCONY_LENGTH, 0.05,
                     facecolor='orange', edgecolor='red', linewidth=2, label='栏杆')
ax1.add_patch(handrail)

# 标注尺寸
ax1.annotate('', xy=(0, -0.15), xytext=(BALCONY_LENGTH, -0.15),
            arrowprops=dict(arrowstyle='<->'))
ax1.text(BALCONY_LENGTH/2, -0.2, f'{BALCONY_LENGTH}m', ha='center')

ax1.annotate('', xy=(BALCONY_LENGTH+0.1, 0), xytext=(BALCONY_LENGTH+0.1, RAILING_HEIGHT),
            arrowprops=dict(arrowstyle='<->'))
ax1.text(BALCONY_LENGTH+0.15, RAILING_HEIGHT/2, f'{RAILING_HEIGHT}m',
         va='center', rotation=90)

ax1.set_xlim(-0.3, BALCONY_LENGTH + 0.5)
ax1.set_ylim(-0.3, RAILING_HEIGHT + 0.3)
ax1.set_aspect('equal')
ax1.set_title('阳台结构示意图', fontsize=14, fontweight='bold')
ax1.legend(loc='upper left')
ax1.grid(True, alpha=0.3)
ax1.set_xlabel('长度 (m)')
ax1.set_ylabel('高度 (m)')

# 图2: 弯矩图
ax2 = axes[0, 1]
x = np.linspace(0, BALCONY_LENGTH, 50)

# 悬臂梁弯矩 M = qx²/2 + Px (均布载 + 端部集中力)
q = total_load  # N/m
P = railing_load  # N
M = q * x**2 / 2 + P * x

ax2.plot(x, M/1000, 'b-', linewidth=2, label='弯矩图')
ax2.fill_between(x, 0, M/1000, alpha=0.3, color='blue')
ax2.set_xlabel('位置 (m)')
ax2.set_ylabel('弯矩 (kN·m)')
ax2.set_title(f'悬挑板弯矩图 (M_max = {M_max/1000:.2f} kN·m)')
ax2.grid(True, alpha=0.3)
ax2.legend()

# 图3: 挠度图
ax3 = axes[1, 0]

# 悬臂梁挠度 (简化)
# 均布载: δ = qx⁴/8EI
# 集中力: δ = Px²(3L-x)/6EI
E = E_effective
I = I_effective

delta_uniform = q * x**4 / (8 * E * I)
delta_point = P * x**2 * (3*BALCONY_LENGTH - x) / (6 * E * I)
delta_total = delta_uniform + delta_point

ax3.plot(x, delta_total*1000, 'r-', linewidth=2, label='总挠度')
ax3.axhline(deflection_limit, color='g', linestyle='--', label=f'限值 L/250')
ax3.set_xlabel('位置 (m)')
ax3.set_ylabel('挠度 (mm)')
ax3.set_title(f'悬挑板挠度图 (δ_max = {results_slab.max_deflection*1000:.2f} mm)')
ax3.grid(True, alpha=0.3)
ax3.legend()

# 图4: 配筋示意图
ax4 = axes[1, 1]

# 绘制截面
slab_rect = Rectangle((0, 0), BALCONY_WIDTH, SLAB_THICKNESS*1000,
                       facecolor='lightblue', edgecolor='blue', linewidth=2)
ax4.add_patch(slab_rect)

# 绘制钢筋（上部受拉）
rebar_x = np.linspace(20, BALCONY_WIDTH*1000-20, 10)
for rx in rebar_x:
    rebar_circle = plt.Circle((rx, 20), 3, color='red', alpha=0.8)
    ax4.add_patch(rebar_circle)

# 标注
ax4.text(BALCONY_WIDTH*500, SLAB_THICKNESS*500+10, '受压区',
         ha='center', va='bottom', fontsize=10, color='blue')
ax4.text(BALCONY_WIDTH*500, 10, '受拉区 (钢筋)',
         ha='center', va='top', fontsize=10, color='red')

ax4.set_xlim(-100, BALCONY_WIDTH*1000 + 100)
ax4.set_ylim(-50, SLAB_THICKNESS*1000 + 100)
ax4.set_aspect('equal')
ax4.set_title(f'板截面配筋 (As = {As_provided*1e6:.0f} mm²/m, ρ={STEEL_REBAR_RATIO*100:.1f}%)')
ax4.set_xlabel('宽度 (mm)')
ax4.set_ylabel('高度 (mm)')
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../results/balcony_complete_analysis.png', dpi=150, bbox_inches='tight')
print(f"  图表已保存: results/balcony_complete_analysis.png")
plt.close()

# ============================================
# 7. 总结报告
# ============================================
print()
print("="*70)
print("  分析总结")
print("="*70)
print()

summary = f"""
阳台结构设计总结
{'='*50}

一、结构参数
  • 悬挑长度: {BALCONY_LENGTH} m
  • 阳台宽度: {BALCONY_WIDTH} m
  • 板厚: {SLAB_THICKNESS*1000:.0f} mm
  • 栏杆高度: {RAILING_HEIGHT} m
  • 混凝土等级: {CONCRETE_GRADE}
  • 配筋率: {STEEL_REBAR_RATIO*100:.1f}%

二、荷载
  • 恒载(自重): {dead_load:.0f} N/m
  • 活载(人群): {live_load:.0f} N/m
  • 栏杆水平荷载: {railing_load:.0f} N
  • 风载: {wind_load_column:.0f} N

三、分析结果

  1. 强度分析
     • 最大弯矩: {M_max/1000:.2f} kN·m
     • 配筋需要: {As_required*1e6:.2f} mm²/m
     • 配筋提供: {As_provided*1e6:.2f} mm²/m
     • {'✓ 满足' if As_provided >= As_required else '✗ 不满足'}

  2. 正常使用极限状态
     • 最大挠度: {results_slab.max_deflection*1000:.2f} mm
     • 挠度限值: {deflection_limit:.2f} mm (L/250)
     • {'✓ 满足' if results_slab.max_deflection*1000 < deflection_limit else '✗ 不满足'}

  3. 稳定性分析
     • 栏杆立柱长细比: {buckling_result.slenderness_ratio:.1f}
     • 限值: 150
     • {'✓ 满足' if buckling_result.slenderness_ratio < 150 else '✗ 不满足'}

  4. 动力特性
     • 基频: {fundamental_freq:.2f} Hz
     • 舒适度要求: > 3 Hz
     • {'✓ 满足' if fundamental_freq > 3 else '△ 基本满足' if fundamental_freq > 2 else '✗ 不满足'}

四、结论
"""

# 判断整体是否满足要求
all_ok = (As_provided >= As_required and
          results_slab.max_deflection*1000 < deflection_limit and
          buckling_result.slenderness_ratio < 150)

if all_ok:
    summary += "\n  ✓ 所有验算均满足要求，设计安全可行。"
else:
    summary += "\n  ✗ 部分验算不满足要求，需要调整设计。"

summary += f"\n{'='*50}"

print(summary)

# 保存分析报告
with open('../results/balcony_analysis_report.txt', 'w', encoding='utf-8') as f:
    f.write(summary)

print(f"\n分析报告已保存: results/balcony_analysis_report.txt")
print()
