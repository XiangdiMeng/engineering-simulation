"""
篮球架结构完整分析
Basketball Hoop Structure - Complete Analysis

结构组成：
1. 立柱 - 支撑整个系统
2. 悬臂横杆 - 连接立柱和篮板
3. 篮板 - 矩形框架
4. 篮圈 - 冲击载荷
5. 配重 - 稳定系统

分析内容：
- 强度分析
- 稳定性分析
- 模态分析
- 冲击响应分析
- 风载分析
"""

import sys
sys.path.insert(0, 'src')

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch, Polygon, Wedge
from matplotlib.collections import LineCollection
import matplotlib.patches as mpatches

# ============================================
# 1. 设计参数定义
# ============================================

print("="*70)
print("  BASKETBALL HOOP STRUCTURE ANALYSIS")
print("="*70)
print()

# 标准篮球架尺寸 (FIBA标准)
POLE_HEIGHT = 3.05        # 立柱高度 (m) - 地面到篮圈高度
POLE_DEPTH = 1.2          # 立柱埋深 (m)
OVERHANG_LENGTH = 1.2     # 悬臂长度 (m) - 篮板到立柱中心距离
BACKBOARD_WIDTH = 1.8     # 篮板宽度 (m)
BACKBOARD_HEIGHT = 1.05   # 篮板高度 (m)
RIM_DIAMETER = 0.45      # 篮圈直径 (m)
RIM_HEIGHT = 3.05        # 篮圈高度 (m)

# 立柱参数
POLE_OUTER_DIAMETER = 0.168  # 168mm 钢管
POLE_WALL_THICKNESS = 0.008   # 8mm 壁厚
POLE_E = 200e9                 # 钢材弹性模量

# 悬臂参数
ARM_LENGTH = OVERHANG_LENGTH
ARM_HEIGHT = 0.1          # 悬臂梁高度
ARM_WIDTH = 0.08          # 悬臂梁宽度

# 配重系统
COUNTERWEIGHT = 200       # 配重 (kg)

print("[Design Parameters - FIBA Standard]")
print(f"  Pole height (above ground): {POLE_HEIGHT} m")
print(f"  Overhang length: {OVERHANG_LENGTH} m")
print(f"  Backboard: {BACKBOARD_WIDTH}m x {BACKBOARD_HEIGHT}m")
print(f"  Rim diameter: {RIM_DIAMETER*1000:.0f} mm")
print(f"  Rim height: {RIM_HEIGHT} m")
print()

# ============================================
# 2. 材料属性
# ============================================

from materials import Steel

steel_q345 = Steel("Q345")
print("[Material Properties]")
print(f"  Steel Q345:")
print(f"    E = {steel_q345.elastic_modulus/1e9:.1f} GPa")
print(f"    fy = {steel_q345.yield_strength/1e6:.0f} MPa")
print(f"    fu = {steel_q345.ultimate_strength/1e6:.0f} MPa")
print()

# ============================================
# 3. 立柱分析
# ============================================

print("[Analysis 1: Pole Column Analysis]")
print("-"*70)

# 立柱截面属性
D_out = POLE_OUTER_DIAMETER
t = POLE_WALL_THICKNESS
D_in = D_out - 2 * t

A_pole = np.pi * (D_out**2 - D_in**2) / 4
I_pole = np.pi * (D_out**4 - D_in**4) / 64

# 截面模量
S_pole = I_pole / (D_out / 2)

print(f"Pole Section ({D_out*1000:.0f}mm x {t*1000:.0f}mm CHS):")
print(f"  Cross-sectional area: {A_pole*1e4:.2f} cm²")
print(f"  Moment of inertia: {I_pole*1e8:.4f} cm⁴")
print(f"  Section modulus: {S_pole*1e6:.2f} cm³")
print()

# 载荷计算
# 篮板重量
backboard_weight = 50 * 9.81  # N (假设50kg)
# 篮圈 + 篮网
rim_weight = 20 * 9.81  # N
# 悬臂重量
arm_weight = 30 * 9.81  # N
# 篮圈冲击载荷（扣篮）
dunk_load = 800 * 9.81  # N (假设80kg运动员冲击)

# 总载荷
vertical_load = backboard_weight + rim_weight + arm_weight
overhang_moment = vertical_load * OVERHANG_LENGTH + dunk_load * (OVERHANG_LENGTH + 0.15)

print(f"Loads:")
print(f"  Backboard weight: {backboard_weight:.0f} N")
print(f"  Rim + Net: {rim_weight:.0f} N")
print(f"  Arm weight: {arm_weight:.0f} N")
print(f"  Vertical load: {vertical_load:.0f} N")
print(f"  Dunk impact: {dunk_load:.0f} N")
print(f"  Overturning moment: {overhang_moment/1000:.2f} kN·m")
print()

# 立柱分析
# 立柱底部弯矩
M_base = overhang_moment
# 立柱底部轴向力
N_base = vertical_load + dunk_load + COUNTERWEIGHT * 9.81

# 应力计算
sigma_bending = M_base / S_pole
sigma_axial = N_base / A_pole
sigma_max = sigma_bending + sigma_axial

print(f"Stress at pole base:")
print(f"  Bending stress: {sigma_bending/1e6:.2f} MPa")
print(f"  Axial stress: {sigma_axial/1e6:.2f} MPa")
print(f"  Maximum stress: {sigma_max/1e6:.2f} MPa")
print(f"  Allowable stress: {steel_q345.yield_strength/1e6/1.5:.2f} MPa")

if sigma_max < steel_q345.yield_strength / 1.5:
    print(f"  [PASS] Strength OK")
else:
    print(f"  [FAIL] Strength insufficient")
print()

# 稳定性分析
from stability import euler_buckling_analysis, ColumnSection, BoundaryCondition

section_pole = ColumnSection(A=A_pole, Ix=I_pole, Iy=I_pole)

# 立柱边界条件：底部固定，顶部铰接
bc_pole = BoundaryCondition(
    fix_start_x=True, fix_start_y=True, fix_start_theta=True,
    fix_end_x=False, fix_end_y=True, fix_end_theta=False
)

buckling_pole = euler_buckling_analysis(
    length=POLE_HEIGHT + POLE_DEPTH,
    material=steel_q345,
    section=section_pole,
    applied_load=N_base,
    boundary_condition=bc_pole
)

print(f"Stability analysis:")
print(f"  Effective length: {buckling_pole.effective_length:.2f} m")
print(f"  Slenderness ratio: {buckling_pole.slenderness_ratio:.1f}")
print(f"  Critical load: {buckling_pole.critical_load/1000:.2f} kN")
print(f"  Safety factor: {buckling_pole.safety_factor:.2f}")

if buckling_pole.safety_factor > 2.0:
    print(f"  [PASS] Stability OK")
else:
    print(f"  [FAIL] Stability insufficient")
print()

# ============================================
# 4. 悬臂梁分析
# ============================================

print("[Analysis 2: Cantilever Arm Analysis]")
print("-"*70)

from beam_analysis import CantileverBeam

arm_beam = CantileverBeam(
    length=ARM_LENGTH,
    width=ARM_WIDTH,
    height=ARM_HEIGHT,
    material=steel_q345
)

# 施加载荷
arm_beam.add_point_load(dunk_load/2, ARM_LENGTH)  # 端部冲击
arm_beam.add_distributed_load((backboard_weight + rim_weight) / ARM_LENGTH, 0, ARM_LENGTH)

arm_results = arm_beam.analyze()

print(f"Cantilever arm results:")
print(f"  Max deflection: {arm_results.max_deflection*1000:.2f} mm")
print(f"  Max moment: {arm_results.max_moment/1000:.2f} kN·m")
print(f"  Max stress: {arm_results.max_stress/1e6:.2f} MPa")
print(f"  Safety factor: {arm_results.safety_factor:.2f}")
print()

# ============================================
# 5. 整体模态分析
# ============================================

print("[Analysis 3: Modal Analysis]")
print("-"*70)

from dynamics import ModalAnalysis
from fea import FEModel, FEMaterial, Node

# 创建简化框架模型
model_hoop = FEModel(name="Basketball Hoop")

# 节点定义
nodes_info = [
    # (x, y, fix_x, fix_y, fix_theta)
    (0, 0, True, True, True),              # 0: 立柱底部（固定）
    (0, POLE_HEIGHT, False, False, False), # 1: 立柱顶部
    (OVERHANG_LENGTH, POLE_HEIGHT, False, False, False), # 2: 篮板中心
    (OVERHANG_LENGTH, POLE_HEIGHT - 0.3, False, False, False), # 3: 篮圈位置
]

for info in nodes_info:
    model_hoop.add_node(info[0], info[1], (info[2], info[3], info[4]))

# 材料定义
mat_pole = FEMaterial("立柱", E=200e9, A=A_pole, density=7850)
mat_arm = FEMaterial("悬臂", E=200e9, A=0.008, density=7850)

# 添加单元
model_hoop.add_truss_element(0, 1, mat_pole)  # 立柱
model_hoop.add_truss_element(1, 2, mat_arm)  # 悬臂
model_hoop.add_truss_element(2, 3, mat_arm)  # 篮圈连接

# 模态分析
modal_hoop = ModalAnalysis(
    nodes=model_hoop.nodes,
    elements=model_hoop.elements,
    n_modes=3
)

modal_result = modal_hoop.solve()

print(f"Natural frequencies:")
for i, freq in enumerate(modal_result.natural_frequencies):
    print(f"  Mode {i+1}: {freq:.2f} Hz")

# 人体舒适度评估
if modal_result.natural_frequencies[0] > 2:
    print(f"  [PASS] Dynamic performance OK")
else:
    print(f"  [WARNING] Low natural frequency - may vibrate")
print()

# ============================================
# 6. 风载分析
# ============================================

print("[Analysis 4: Wind Load Analysis]")
print("-"*70)

# 风载计算（按建筑结构荷载规范）
# 基本风压（考虑室外条件）
w0 = 0.5  # kN/m²

# 风振系数
beta_z = 2.0

# 风压高度变化系数（3m高度）
mu_z = 0.8

# 体型系数
mu_s = 1.3  # 圆形截面

# 设计风压
w = beta_z * mu_z * mu_s * w0 * 1000  # N/m²

print(f"Wind load parameters:")
print(f"  Basic wind pressure: {w0} kN/m²")
print(f"  Design wind pressure: {w/1000:.3f} kN/m²")

# 篮板受风面积
A_backboard = BACKBOARD_WIDTH * BACKBOARD_HEIGHT
F_wind = w * A_backboard

print(f"  Wind force on backboard: {F_wind:.0f} N")

# 风载产生的倾覆力矩
M_wind = F_wind * (POLE_HEIGHT + BACKBOARD_HEIGHT/2)
print(f"  Overturning moment from wind: {M_wind/1000:.2f} kN·m")

# 配重稳定性校核
M_stabilizing = COUNTERWEIGHT * 9.81 * 0.3  # 配重力矩（假设力臂0.3m）
M_overturning = M_wind + overhang_moment - M_stabilizing

print(f"\nStability check:")
print(f"  Stabilizing moment (counterweight): {M_stabilizing/1000:.2f} kN·m")
print(f"  Total overturning moment: {(M_wind + overhang_moment)/1000:.2f} kN·m")

if M_overturning < 0:
    print(f"  [PASS) Structure stable against wind")
else:
    print(f"  [WARNING] May need additional counterweight")
print()

# ============================================
# 7. 生成可视化图表
# ============================================

print("[Generating Visualization]")
print("-"*70)

# 创建大图包含多个子图
fig = plt.figure(figsize=(16, 12))
gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

# 图1: 篮球架结构图
ax1 = fig.add_subplot(gs[0, 0])

# 绘制地面
ground = Rectangle((-2, -0.1), 5, 0.1, facecolor='lightbrown', edgecolor='brown')
ax1.add_patch(ground)

# 绘制立柱
pole = Rectangle((-POLE_OUTER_DIAMETER/2, 0), POLE_OUTER_DIAMETER, POLE_HEIGHT,
                 facecolor='gray', edgecolor='black', linewidth=2, label='Pole')
ax1.add_patch(pole)

# 绘制悬臂
arm = Rectangle((0, POLE_HEIGHT - ARM_HEIGHT/2), ARM_LENGTH, ARM_HEIGHT,
               facecolor='orange', edgecolor='black', linewidth=2, label='Arm')
ax1.add_patch(arm)

# 绘制篮板
backboard = Rectangle((OVERHANG_LENGTH, POLE_HEIGHT - BACKBOARD_HEIGHT/2 - ARM_HEIGHT/2),
                     0.05, BACKBOARD_HEIGHT,
                     facecolor='white', edgecolor='blue', linewidth=3, label='Backboard')
ax1.add_patch(backboard)

# 绘制篮圈
rim = Circle((OVERHANG_LENGTH + 0.025, POLE_HEIGHT - 0.3), RIM_DIAMETER/2,
             fill=False, edgecolor='red', linewidth=4, label='Rim')
ax1.add_patch(rim)

# 绘制篮网
rim_net_x = np.linspace(OVERHANG_LENGTH, OVERHANG_LENGTH + RIM_DIAMETER, 20)
rim_net_y = POLE_HEIGHT - 0.3 - 0.4 * np.sin(np.linspace(0, np.pi, 20))
ax1.plot(rim_net_x, rim_net_y, 'r-', alpha=0.5, linewidth=1, label='Net')

# 尺寸标注
ax1.annotate('', xy=(0, -0.2), xytext=(OVERHANG_LENGTH, -0.2),
            arrowprops=dict(arrowstyle='<->', color='blue'))
ax1.text(OVERHANG_LENGTH/2, -0.25, f'{OVERHANG_LENGTH}m', ha='center', color='blue')

ax1.annotate('', xy=(OVERHANG_LENGTH + 0.3, 0), xytext=(OVERHANG_LENGTH + 0.3, POLE_HEIGHT),
            arrowprops=dict(arrowstyle='<->', color='green'))
ax1.text(OVERHANG_LENGTH + 0.35, POLE_HEIGHT/2, f'{POLE_HEIGHT}m',
         va='center', rotation=90, color='green')

ax1.set_xlim(-1, OVERHANG_LENGTH + 0.8)
ax1.set_ylim(-0.5, POLE_HEIGHT + 0.8)
ax1.set_aspect('equal')
ax1.set_title('Basketball Hoop Structure', fontsize=14, fontweight='bold')
ax1.legend(loc='upper left')
ax1.grid(True, alpha=0.3)
ax1.set_xlabel('Distance (m)')
ax1.set_ylabel('Height (m)')

# 图2: 弯矩图
ax2 = fig.add_subplot(gs[0, 1])

x_pole = np.linspace(0, POLE_HEIGHT, 50)
x_arm = np.linspace(0, ARM_LENGTH, 30)

# 立柱弯矩（从底部到顶部线性减小）
M_pole_dist = M_base * (1 - x_pole / POLE_HEIGHT)

# 悬臂弯矩
M_arm_dist = (vertical_load * x_arm**2 / 2 +
              dunk_load * x_arm +
              backboard_weight * x_arm / 2)

ax2.plot(x_pole, M_pole_dist/1000, 'b-', linewidth=2, label='Pole')
ax2.axvline(0, color='gray', linestyle='--', alpha=0.5)
ax2.plot(x_arm, M_arm_dist/1000, 'r-', linewidth=2, label='Arm')
ax2.axhline(0, color='k', linestyle='-', alpha=0.3)
ax2.set_xlabel('Position (m)')
ax2.set_ylabel('Moment (kN·m)')
ax2.set_title('Moment Diagram')
ax2.legend()
ax2.grid(True, alpha=0.3)

# 图3: 立柱应力分布
ax3 = fig.add_subplot(gs[0, 2])

# 应力沿高度分布
sigma_dist = sigma_bending * (1 - x_pole / POLE_HEIGHT) + sigma_axial

ax3.fill_between(x_pole, 0, sigma_dist/1e6, alpha=0.3, color='blue')
ax3.plot(x_pole, sigma_dist/1e6, 'b-', linewidth=2)
ax3.axhline(steel_q345.yield_strength/1e6/1.5, color='r', linestyle='--',
           label=f'Allowable ({steel_q345.yield_strength/1e6/1.5:.0f} MPa)')
ax3.set_xlabel('Height (m)')
ax3.set_ylabel('Stress (MPa)')
ax3.set_title('Pole Stress Distribution')
ax3.legend()
ax3.grid(True, alpha=0.3)

# 图4: 振型图
ax4 = fig.add_subplot(gs[1, 0])

# 绘制前三阶振型
for mode_idx in range(min(3, len(modal_result.natural_frequencies))):
    freq = modal_result.natural_frequencies[mode_idx]

    # 绘制变形后的结构（简化）
    scale = 0.5 / (mode_idx + 1)  # 依次减小振幅

    # 立柱变形
    y_pole_orig = np.linspace(0, POLE_HEIGHT, 20)
    x_pole_def = scale * np.sin(np.pi * y_pole / POLE_HEIGHT) * (mode_idx + 1)
    x_pole_orig = np.zeros_like(y_pole_orig)
    ax4.plot(x_pole_orig + x_pole_def, y_pole_orig, '-',
            alpha=0.7, label=f'Mode {mode_idx+1} ({freq:.2f} Hz)')

    # 标记原始位置
    ax4.plot([0, 0], [0, POLE_HEIGHT], 'k--', alpha=0.2)

ax4.set_xlim(-1, 2)
ax4.set_ylim(-0.5, POLE_HEIGHT + 0.5)
ax4.set_title('Mode Shapes (exaggerated)')
ax4.legend()
ax4.grid(True, alpha=0.3)
ax4.set_aspect('equal')
ax4.set_xlabel('Deformation (m)')

# 图5: 配重稳定性分析
ax5 = fig.add_subplot(gs[1, 1])

# 绘制倾覆力矩与稳定力矩
scenarios = ['No Wind', 'With Wind']
overturn_moments = [overhang_moment/1000, (overhang_moment + M_wind)/1000]
stabilizing_moments = [M_stabilizing/1000, M_stabilizing/1000]

x = np.arange(len(scenarios))
width = 0.35

bars1 = ax5.bar(x - width/2, overturn_moments, width, label='Overturning', color='red', alpha=0.7)
bars2 = ax5.bar(x + width/2, stabilizing_moments, width, label='Stabilizing', color='green', alpha=0.7)

ax5.set_ylabel('Moment (kN·m)')
ax5.set_title('Stability Analysis')
ax5.set_xticks(x)
ax5.set_xticklabels(scenarios)
ax5.legend()
ax5.grid(True, alpha=0.3, axis='y')

# 添加数值标签
for bar in bars1:
    height = bar.get_height()
    ax5.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.1f}',
            ha='center', va='bottom', fontsize=9)

for bar in bars2:
    height = bar.get_height()
    ax5.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.1f}',
            ha='center', va='bottom', fontsize=9)

# 图6: 冲击响应
ax6 = fig.add_subplot(gs[1, 2])

# 简化的冲击响应曲线
t = np.linspace(0, 1, 100)
omega = 2 * np.pi * modal_result.natural_frequencies[0]  # 基频
damping_ratio = 0.05

# 冲击响应（简化）
response = (dunk_load / 1000) * np.exp(-damping_ratio * omega * t) * np.cos(omega * t)

ax6.plot(t, response, 'b-', linewidth=2)
ax6.set_xlabel('Time (s)')
ax6.set_ylabel('Force Response (kN)')
ax6.set_title('Dunk Impact Response')
ax6.grid(True, alpha=0.3)
ax6.axhline(0, color='k', linestyle='-', alpha=0.3)

# 图7: 立柱截面
ax7 = fig.add_subplot(gs[2, 0])

# 绘制圆管截面
circle_out = Circle((0, 0), D_out/2, fill=False, edgecolor='black', linewidth=2)
circle_in = Circle((0, 0), D_in/2, fill=False, edgecolor='black', linewidth=1)
ax7.add_patch(circle_out)
ax7.add_patch(circle_in)

# 填充
annulus = Wedge((0, 0), D_out/2, 0, 360, width=(D_out-D_in)/2, facecolor='lightgray', edgecolor='none')
ax7.add_patch(annulus)

# 标注
ax7.text(0, 0, f'{D_out*1000:.0f}\n{D_in*1000:.0f}', ha='center', va='center', fontsize=10)
ax7.set_xlim(-D_out, D_out)
ax7.set_ylim(-D_out, D_out)
ax7.set_aspect('equal')
ax7.set_title(f'Pole Section\nCHS {D_out*1000:.0f}x{t*1000:.0f}')
ax7.axis('off')

# 图8: 篮板侧视图
ax8 = fig.add_subplot(gs[2, 1])

# 篮板
bb = Rectangle((0, 0), BACKBOARD_WIDTH, BACKBOARD_HEIGHT,
               facecolor='white', edgecolor='blue', linewidth=3)
ax8.add_patch(bb)

# 篮圈连接
ax8.plot([BACKBOARD_WIDTH/2, BACKBOARD_WIDTH/2],
         [BACKBOARD_HEIGHT/2 - 0.15, BACKBOARD_HEIGHT/2 - 0.15],
         'r-', linewidth=4)
ax8.plot([BACKBOARD_WIDTH/2, BACKBOARD_WIDTH/2 + RIM_DIAMETER],
         [BACKBOARD_HEIGHT/2 - 0.15, BACKBOARD_HEIGHT/2 - 0.15],
         'r-', linewidth=4)

# 篮圈
rim_circle = Circle((BACKBOARD_WIDTH/2 + RIM_DIAMETER, BACKBOARD_HEIGHT/2 - 0.15),
                    RIM_DIAMETER/2, fill=False, edgecolor='red', linewidth=3)
ax8.add_patch(rim_circle)

ax8.set_xlim(-0.2, BACKBOARD_WIDTH + 0.5)
ax8.set_ylim(-0.2, BACKBOARD_HEIGHT + 0.2)
ax8.set_aspect('equal')
ax8.set_title('Backboard Side View')
ax8.set_xlabel('m')

# 图9: 载荷示意图
ax9 = fig.add_subplot(gs[2, 2])

# 简化的受力图
pole_x = [0, 0]
pole_y = [0, POLE_HEIGHT]
ax9.plot(pole_x, pole_y, 'b-', linewidth=8, label='Pole')

# 力箭头
# 自重
arrow_gw = FancyArrowPatch((0, POLE_HEIGHT), (-0.3, POLE_HEIGHT),
                            mutation_scale=20, color='green', arrowstyle='->', linewidth=2)
ax9.add_patch(arrow_gw)
ax9.text(-0.5, POLE_HEIGHT, f'Backboard\n{backboard_weight:.0f}N',
         ha='right', va='center', fontsize=9)

# 冲击载荷
arrow_dunk = FancyArrowPatch((OVERHANG_LENGTH, POLE_HEIGHT - 0.3),
                              (OVERHANG_LENGTH, POLE_HEIGHT - 0.6),
                              mutation_scale=20, color='red', arrowstyle='->', linewidth=3)
ax9.add_patch(arrow_dunk)
ax9.text(OVERHANG_LENGTH, POLE_HEIGHT - 0.7, f'Dunk!\n{dunk_load:.0f}N',
         ha='center', va='top', fontsize=10, color='red', fontweight='bold')

# 风载
arrow_wind = FancyArrowPatch((OVERHANG_LENGTH/2, POLE_HEIGHT),
                              (OVERHANG_LENGTH/2 + 0.3, POLE_HEIGHT),
                              mutation_scale=20, color='cyan', arrowstyle='->', linewidth=2)
ax9.add_patch(arrow_wind)
ax9.text(OVERHANG_LENGTH/2, POLE_HEIGHT + 0.15, f'Wind\n{F_wind:.0f}N',
         ha='center', va='bottom', fontsize=9)

ax9.set_xlim(-1, OVERHANG_LENGTH + 0.5)
ax9.set_ylim(-0.5, POLE_HEIGHT + 0.5)
ax9.set_aspect('equal')
ax9.set_title('Load Diagram')
ax9.legend(['Pole'], loc='lower left')
ax9.axis('off')

plt.savefig('results/basketball_hoop_analysis.png', dpi=150, bbox_inches='tight')
print("  [SAVED] results/basketball_hoop_analysis.png")
plt.close()

# ============================================
# 8. 生成单独的3D效果图
# ============================================

fig_3d = plt.figure(figsize=(14, 10))
ax_3d = fig_3d.add_subplot(111, projection='3d')

# 定义3D点
# 立柱
pole_3d_x = [0, 0]
pole_3d_y = [0, 0]
pole_3d_z = [0, POLE_HEIGHT]

# 悬臂
arm_3d_x = [0, OVERHANG_LENGTH]
arm_3d_y = [0, 0]
arm_3d_z = [POLE_HEIGHT, POLE_HEIGHT]

# 篮板角点
bb_offset = 0.1
bb_3d_x = [OVERHANG_LENGTH, OVERHANG_LENGTH,
          OVERHANG_LENGTH, OVERHANG_LENGTH]
bb_3d_y = [-BACKBOARD_WIDTH/2, BACKBOARD_WIDTH/2,
          BACKBOARD_WIDTH/2, -BACKBOARD_WIDTH/2]
bb_3d_z = [POLE_HEIGHT + BACKBOARD_HEIGHT/2, POLE_HEIGHT + BACKBOARD_HEIGHT/2,
          POLE_HEIGHT - BACKBOARD_HEIGHT/2, POLE_HEIGHT - BACKBOARD_HEIGHT/2]

# 篮圈
theta_rim = np.linspace(0, np.pi, 30)
rim_3d_x = OVERHANG_LENGTH + RIM_DIAMETER * np.cos(theta_rim)
rim_3d_y = RIM_DIAMETER * np.sin(theta_rim)
rim_3d_z = np.full_like(rim_3d_x, POLE_HEIGHT - 0.3)

# 绘制
# 立柱
ax_3d.plot(pole_3d_x, pole_3d_y, pole_3d_z, 'b-', linewidth=8, label='Pole')

# 悬臂
ax_3d.plot(arm_3d_x, arm_3d_y, arm_3d_z, 'orange', linewidth=6, label='Arm')

# 篮板
for i in range(4):
    j = (i + 1) % 4
    ax_3d.plot([bb_3d_x[i], bb_3d_x[j]],
              [bb_3d_y[i], bb_3d_y[j]],
              [bb_3d_z[i], bb_3d_z[j]], 'b-', linewidth=2)
ax_3d.text(OVERHANG_LENGTH, 0, POLE_HEIGHT, 'Backboard', fontsize=8)

# 篮圈
ax_3d.plot(rim_3d_x, rim_3d_y, rim_3d_z, 'r-', linewidth=3, label='Rim')

# 地面
xx, yy = np.meshgrid(np.linspace(-2, 2, 10), np.linspace(-2, 2, 10))
zz = np.zeros_like(xx)
ax_3d.plot_surface(xx, yy, zz, alpha=0.3, color='green')

# 设置坐标
ax_3d.set_xlabel('X (m)')
ax_3d.set_ylabel('Y (m)')
ax_3d.set_zlabel('Height (m)')
ax_3d.set_title('3D Basketball Hoop Model', fontsize=14, fontweight='bold')
ax_3d.set_xlim(-1, 3)
ax_3d.set_ylim(-2, 2)
ax_3d.set_zlim(0, 4)
ax_3d.legend()

plt.savefig('results/basketball_hoop_3d.png', dpi=150, bbox_inches='tight')
print("  [SAVED] results/basketball_hoop_3d.png")
plt.close()

# ============================================
# 9. 生成载荷工况图
# ============================================

fig_loads = plt.figure(figsize=(14, 10))

# 工况1: 自重
ax1 = fig_loads.add_subplot(221)
draw_hoop_structure(ax1, loads='deadweight')
ax1.set_title('Case 1: Dead Weight Only', fontweight='bold')

# 工况2: 扣篮冲击
ax2 = fig_loads.add_subplot(222)
draw_hoop_structure(ax2, loads='dunk')
ax2.set_title('Case 2: Dunk Impact', fontweight='bold')

# 工况3: 风载
ax3 = fig_loads.add_subplot(223)
draw_hoop_structure(ax3, loads='wind')
ax3.set_title('Case 3: Wind Load', fontweight='bold')

# 工况4: 组合载荷
ax4 = fig_loads.add_subplot(224)
draw_hoop_structure(ax4, loads='combined')
ax4.set_title('Case 4: Combined Loads', fontweight='bold')

plt.tight_layout()
plt.savefig('results/basketball_hoop_load_cases.png', dpi=150, bbox_inches='tight')
print("  [SAVED] results/basketball_hoop_load_cases.png")
plt.close()

print("="*70)
print("  ANALYSIS COMPLETE")
print("="*70)
print()
print("[Generated Figures]")
print("  1. results/basketball_hoop_analysis.png - Complete analysis")
print("  2. results/basketball_hoop_3d.png - 3D model")
print("  3. results/basketball_hoop_load_cases.png - Load cases")
print()

# ============================================
# 10. 总结报告
# ============================================

print("="*70)
print("  SUMMARY & RECOMMENDATIONS")
print("="*70)
print()

summary = f"""
Basketball Hoop Structural Analysis Summary
{'='*50}

1. DESIGN PARAMETERS (FIBA Standard)
   • Pole height: {POLE_HEIGHT}m
   • Overhang length: {OVERHANG_LENGTH}m
   • Backboard: {BACKBOARD_WIDTH}m × {BACKBOARD_HEIGHT}m
   • Rim diameter: {RIM_DIAMETER}m

2. POLE ANALYSIS
   • Section: CHS {D_out*1000:.0f}mm × {t*1000:.0f}mm
   • Cross-sectional area: {A_pole*1e4:.2f} cm²
   • Max stress at base: {sigma_max/1e6:.2f} MPa
   • Allowable stress: {steel_q345.yield_strength/1e6/1.5:.2f} MPa
   • Slenderness ratio: {buckling_pole.slenderness_ratio:.1f}
   • Critical load: {buckling_pole.critical_load/1000:.2f} kN
   • Safety factor: {buckling_pole.safety_factor:.2f}

3. CANTILEVER ARM
   • Max deflection: {arm_results.max_deflection*1000:.2f} mm
   • Max stress: {arm_results.max_stress/1e6:.2f} MPa

4. DYNAMIC PERFORMANCE
   • Fundamental frequency: {modal_result.natural_frequencies[0]:.2f} Hz
   • Dynamic characteristic: {'Stiff' if modal_result.natural_frequencies[0] > 3 else 'Flexible'}

5. STABILITY
   • Counterweight: {COUNTERWEIGHT} kg
   • Overturning moment (wind): {M_wind/1000:.2f} kN·m
   • Stabilizing moment: {M_stabilizing/1000:.2f} kN·m

{'='*50)

RECOMMENDATIONS:
{'='*50}
"""

checks = {
    'Pole Strength': sigma_max < steel_q345.yield_strength / 1.5,
    'Pole Stability': buckling_pole.safety_factor > 2.0,
    'Arm Deflection': arm_results.max_deflection * 1000 < 50,
    'Wind Stability': M_wind + overhang_moment < M_stabilizing + M_base
}

for check_name, result in checks.items():
    status = '[PASS]' if result else '[FAIL]'
    summary += f"  {status} {check_name}\n"

summary += f"\n{'='*50}\n"

print(summary)

# 保存报告
with open('results/basketball_hoop_report.txt', 'w', encoding='utf-8') as f:
    f.write(summary)

print("Report saved: results/basketball_hoop_report.txt")


# 辅助函数：绘制篮球架结构
def draw_hoop_structure(ax, loads='none'):
    """Draw basketball hoop with specified loads"""
    from matplotlib.patches import Rectangle, Circle, FancyArrowPatch

    # 立柱
    pole = Rectangle((-POLE_OUTER_DIAMETER/2, 0), POLE_OUTER_DIAMETER, POLE_HEIGHT,
                     facecolor='gray', edgecolor='black', linewidth=2)
    ax.add_patch(pole)

    # 悬臂
    arm = Rectangle((0, POLE_HEIGHT - ARM_HEIGHT/2), ARM_LENGTH, ARM_HEIGHT,
                   facecolor='orange', edgecolor='black', linewidth=2)
    ax.add_patch(arm)

    # 篮板
    backboard = Rectangle((OVERHANG_LENGTH, POLE_HEIGHT - BACKBOARD_HEIGHT/2),
                         0.02, BACKBOARD_HEIGHT,
                         facecolor='white', edgecolor='blue', linewidth=2)
    ax.add_patch(backboard)

    # 篮圈
    rim = Circle((OVERHANG_LENGTH + RIM_DIAMETER/2, POLE_HEIGHT - 0.15), RIM_DIAMETER/2,
                fill=False, edgecolor='red', linewidth=3)
    ax.add_patch(rim)

    # 地面
    ground = Rectangle((-1, -0.05), 3, 0.05, facecolor='lightbrown', edgecolor='none')
    ax.add_patch(ground)

    ax.set_xlim(-1, OVERHANG_LENGTH + 1)
    ax.set_ylim(-0.5, POLE_HEIGHT + 0.5)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)

    # 绘制载荷
    if loads == 'deadweight':
        # 自重箭头
        arrow = FancyArrowPatch((OVERHANG_LENGTH/2, POLE_HEIGHT),
                              (OVERHANG_LENGTH/2, POLE_HEIGHT - 0.2),
                              mutation_scale=15, color='green', arrowstyle='->', linewidth=2)
        ax.add_patch(arrow)
        ax.text(OVERHANG_LENGTH/2, POLE_HEIGHT - 0.3, f'Dead Load',
                ha='center', fontsize=10, color='green')

    elif loads == 'dunk':
        # 冲击载荷
        arrow = FancyArrowPatch((OVERHANG_LENGTH + RIM_DIAMETER/2, POLE_HEIGHT - 0.15),
                              (OVERHANG_LENGTH + RIM_DIAMETER/2, POLE_HEIGHT - 0.5),
                              mutation_scale=20, color='red', arrowstyle='->', linewidth=3)
        ax.add_patch(arrow)
        ax.text(OVERHANG_LENGTH + RIM_DIAMETER/2, POLE_HEIGHT - 0.6,
                f'DUNK!\n{dunk_load/1000:.0f}kN',
                ha='center', fontsize=10, color='red', fontweight='bold')

    elif loads == 'wind':
        # 风载
        y_wind = np.linspace(POLE_HEIGHT - BACKBOARD_HEIGHT/2,
                           POLE_HEIGHT + BACKBOARD_HEIGHT/2, 5)
        for yw in y_wind:
            arrow = FancyArrowPatch((OVERHANG_LENGTH + 0.1, yw),
                                  (OVERHANG_LENGTH + 0.4, yw),
                                  mutation_scale=10, color='cyan', arrowstyle='->', linewidth=1.5)
            ax.add_patch(arrow)
        ax.text(OVERHANG_LENGTH, POLE_HEIGHT + 0.4, 'Wind Load',
                ha='center', fontsize=10, color='blue')

    elif loads == 'combined':
        # 组合载荷
        arrow1 = FancyArrowPatch((OVERHANG_LENGTH/2, POLE_HEIGHT),
                               (OVERHANG_LENGTH/2, POLE_HEIGHT - 0.15),
                               mutation_scale=12, color='green', arrowstyle='->', linewidth=1.5)
        ax.add_patch(arrow1)

        arrow2 = FancyArrowPatch((OVERHANG_LENGTH + RIM_DIAMETER/2, POLE_HEIGHT - 0.15),
                               (OVERHANG_LENGTH + RIM_DIAMETER/2, POLE_HEIGHT - 0.4),
                               mutation_scale=15, color='red', arrowstyle='->', linewidth=2)
        ax.add_patch(arrow2)

        y_wind = np.linspace(POLE_HEIGHT - 0.3, POLE_HEIGHT + 0.3, 3)
        for yw in y_wind:
            arrow3 = FancyArrowPatch((OVERHANG_LENGTH + 0.05, yw),
                                   (OVERHANG_LENGTH + 0.25, yw),
                                   mutation_scale=8, color='cyan', arrowstyle='->', linewidth=1)
            ax.add_patch(arrow3)

        ax.text(OVERHANG_LENGTH/2, POLE_HEIGHT - 0.25, 'DL',
                ha='center', fontsize=8, color='green')
        ax.text(OVERHANG_LENGTH + RIM_DIAMETER/2, POLE_HEIGHT - 0.45, 'LL',
                ha='center', fontsize=8, color='red', fontweight='bold')
        ax.text(OVERHANG_LENGTH + 0.15, POLE_HEIGHT + 0.4, 'Wind',
                ha='center', fontsize=8, color='blue')
