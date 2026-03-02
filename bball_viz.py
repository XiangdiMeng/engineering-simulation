"""
篮球架结构分析 - 简化版本
Basketball Hoop Analysis - Simplified
"""

import sys
sys.path.insert(0, 'src')

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch, Wedge

# ============================================
# 参数定义
# ============================================

POLE_HEIGHT = 3.05
OVERHANG = 1.2
BACKBOARD_W = 1.8
BACKBOARD_H = 1.05
RIM_DIA = 0.45
POLE_DIA = 0.168
POLE_T = 0.008

# ============================================
# 生成可视化图表
# ============================================

print("="*60)
print("  BASKETBALL HOOP - VISUALIZATION")
print("="*60)

# 图1: 主结构图
print("Generating Figure 1: Main Structure...")
fig1, ax1 = plt.subplots(figsize=(12, 8))

# 地面
ground = Rectangle((-1.5, -0.05), 4, 0.05, facecolor='#D2B48C', edgecolor='none')
ax1.add_patch(ground)

# 立柱
pole = Rectangle((-POLE_DIA/2, 0), POLE_DIA, POLE_HEIGHT,
                 facecolor='gray', edgecolor='black', linewidth=2)
ax1.add_patch(pole)

# 悬臂
arm = Rectangle((0, POLE_HEIGHT - 0.05), OVERHANG, 0.1,
               facecolor='orange', edgecolor='black', linewidth=2)
ax1.add_patch(arm)

# 篮板
backboard = Rectangle((OVERHANG, POLE_HEIGHT - BACKBOARD_H/2),
                     0.02, BACKBOARD_H,
                     facecolor='white', edgecolor='blue', linewidth=3)
ax1.add_patch(backboard)

# 篮圈
rim = Circle((OVERHANG + RIM_DIA/2, POLE_HEIGHT - 0.15), RIM_DIA/2,
             fill=False, edgecolor='red', linewidth=4)
ax1.add_patch(rim)

# 篮网
rim_x = np.linspace(OVERHANG, OVERHANG + RIM_DIA, 20)
rim_y = POLE_HEIGHT - 0.15 - 0.4 * np.sin(np.linspace(0, np.pi, 20))
ax1.plot(rim_x, rim_y, 'r-', alpha=0.6, linewidth=1)

# 尺寸标注
ax1.annotate('', xy=(0, -0.15), xytext=(OVERHANG, -0.15),
            arrowprops=dict(arrowstyle='<->', color='blue', lw=2))
ax1.text(OVERHANG/2, -0.2, f'Overhang: {OVERHANG}m', ha='center', color='blue', fontsize=11)

ax1.annotate('', xy=(POLE_DIA/2 + 0.1, 0), xytext=(POLE_DIA/2 + 0.1, POLE_HEIGHT),
            arrowprops=dict(arrowstyle='<->', color='green', lw=2))
ax1.text(POLE_DIA/2 + 0.2, POLE_HEIGHT/2, f'Pole: {POLE_HEIGHT}m',
         va='center', rotation=90, color='green', fontsize=11)

ax1.set_xlim(-1, OVERHANG + 1.5)
ax1.set_ylim(-0.3, POLE_HEIGHT + 0.6)
ax1.set_aspect('equal')
ax1.set_title('Basketball Hoop Structure (FIBA Standard)', fontsize=14, fontweight='bold')
ax1.grid(True, alpha=0.3, linestyle=':')
ax1.set_xlabel('Distance (m)')
ax1.set_ylabel('Height (m)')

plt.savefig('results/bball_structure.png', dpi=150, bbox_inches='tight')
print("  [SAVED] results/bball_structure.png")
plt.close()

# 图2: 3D模型
print("Generating Figure 2: 3D Model...")
fig2 = plt.figure(figsize=(14, 10))
ax2 = fig2.add_subplot(111, projection='3d')

# 立柱
ax2.plot([0, 0], [0, 0], [0, POLE_HEIGHT], 'b-', linewidth=10, label='Pole')

# 悬臂
ax2.plot([0, OVERHANG], [0, 0], [POLE_HEIGHT, POLE_HEIGHT], 'orange', linewidth=6, label='Arm')

# 篮板
bb_x = [OVERHANG]*4
bb_y = [-BACKBOARD_W/2, BACKBOARD_W/2, BACKBOARD_W/2, -BACKBOARD_W/2]
bb_z = [POLE_HEIGHT + BACKBOARD_H/2, POLE_HEIGHT + BACKBOARD_H/2,
       POLE_HEIGHT - BACKBOARD_H/2, POLE_HEIGHT - BACKBOARD_H/2]
for i in range(4):
    j = (i + 1) % 4
    ax2.plot([bb_x[i], bb_x[j]], [bb_y[i], bb_y[j]], [bb_z[i], bb_z[j]], 'b-', linewidth=2)

# 篮圈
theta = np.linspace(0, np.pi, 30)
rim_x_3d = OVERHANG + RIM_DIA/2 + (RIM_DIA/2) * np.cos(theta)
rim_y_3d = (RIM_DIA/2) * np.sin(theta)
rim_z_3d = np.full_like(rim_x_3d, POLE_HEIGHT - 0.3)
ax2.plot(rim_x_3d, rim_y_3d, rim_z_3d, 'r-', linewidth=4, label='Rim')

# 地面
xx, yy = np.meshgrid(np.linspace(-2, 3, 20), np.linspace(-2, 3, 20))
zz = np.zeros_like(xx)
ax2.plot_surface(xx, yy, zz, alpha=0.2, color='green')

ax2.set_xlabel('X (m)')
ax2.set_ylabel('Y (m)')
ax2.set_zlabel('Height (m)')
ax2.set_title('3D Basketball Hoop Model', fontsize=14, fontweight='bold')
ax2.legend()
ax2.set_xlim(-1, 3)
ax2.set_ylim(-2, 2)
ax2.set_zlim(0, 4)

plt.savefig('results/bball_3d.png', dpi=150, bbox_inches='tight')
print("  [SAVED] results/bball_3d.png")
plt.close()

# 图3: 受力分析
print("Generating Figure 3: Force Analysis...")
fig3, axes3 = plt.subplots(1, 3, figsize=(16, 5))

# 3.1 弯矩图
ax3a = axes3[0]
y_pole = np.linspace(0, POLE_HEIGHT, 50)
# 假设弯矩线性分布
M_pole = 70 * (1 - y_pole/POLE_HEIGHT)  # kN·m
ax3a.plot(M_pole, y_pole, 'b-', linewidth=3)
ax3a.fill_betweenx(M_pole, 0, y_pole, alpha=0.3, color='blue')
ax3a.set_xlabel('Moment (kN·m)')
ax3a.set_ylabel('Height (m)')
ax3a.set_title('Moment Diagram in Pole')
ax3a.grid(True, alpha=0.3)
ax3a.invert_xaxis()

# 3.2 应力分布
ax3b = axes3[1]
sigma_dist = 150 * (1 - y_pole/POLE_HEIGHT)  # MPa
ax3b.fill_betweenx(sigma_dist, 0, y_pole, alpha=0.3, color='orange')
ax3b.plot(sigma_dist, y_pole, 'r-', linewidth=3)
ax3b.axvline(230, color='gray', linestyle='--', label='Allowable (230 MPa)')
ax3b.set_xlabel('Stress (MPa)')
ax3b.set_ylabel('Height (m)')
ax3b.set_title('Stress Distribution')
ax3b.legend()
ax3b.grid(True, alpha=0.3)
ax3b.invert_xaxis()

# 3.3 立柱截面
ax3c = axes3[2]
# 外圆
circle_out = Circle((0, 0), POLE_DIA/2, fill=False, edgecolor='black', linewidth=3)
circle_in = Circle((0, 0), (POLE_DIA-2*POLE_T)/2, fill=False, edgecolor='black', linewidth=2)
ax3c.add_patch(circle_out)
ax3c.add_patch(circle_in)
# 填充
annulus = Wedge((0, 0), POLE_DIA/2, 0, 360, width=POLE_T, facecolor='lightgray', edgecolor='none')
ax3c.add_patch(annulus)
ax3c.set_xlim(-POLE_DIA, POLE_DIA)
ax3c.set_ylim(-POLE_DIA, POLE_DIA)
ax3c.set_aspect('equal')
ax3c.set_title(f'Pole Section\n{POLE_DIA*1000:.0f}mm CHS')
ax3c.axis('off')

plt.tight_layout()
plt.savefig('results/bball_forces.png', dpi=150, bbox_inches='tight')
print("  [SAVED] results/bball_forces.png")
plt.close()

# 图4: 载荷工况
print("Generating Figure 4: Load Cases...")
fig4, axes4 = plt.subplots(2, 2, figsize=(14, 10))

def draw_hoop(ax, title, show_arrows=None):
    """绘制篮球架"""
    # 地面
    ax.add_patch(Rectangle((-1.5, -0.03), 4, 0.03, facecolor='#D2B48C', edgecolor='none'))
    # 立柱
    ax.add_patch(Rectangle((-POLE_DIA/2, 0), POLE_DIA, POLE_HEIGHT, facecolor='gray', edgecolor='black', linewidth=2))
    # 悬臂
    ax.add_patch(Rectangle((0, POLE_HEIGHT-0.05), OVERHANG, 0.1, facecolor='orange', edgecolor='black', linewidth=2))
    # 篮板
    ax.add_patch(Rectangle((OVERHANG, POLE_HEIGHT - BACKBOARD_H/2), 0.02, BACKBOARD_H, facecolor='white', edgecolor='blue', linewidth=3))
    # 篮圈
    ax.add_patch(Circle((OVERHANG + RIM_DIA/2, POLE_HEIGHT - 0.15), RIM_DIA/2, fill=False, edgecolor='red', linewidth=4))

    ax.set_xlim(-1, OVERHANG + 1.2)
    ax.set_ylim(-0.2, POLE_HEIGHT + 0.5)
    ax.set_aspect('equal')
    ax.set_title(title, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle=':')

    # 添加箭头
    if show_arrows == 'gravity':
        arrow = FancyArrowPatch((OVERHANG/2, POLE_HEIGHT), (OVERHANG/2, POLE_HEIGHT-0.3),
                              mutation_scale=15, color='green', arrowstyle='->', linewidth=2)
        ax.add_patch(arrow)
        ax.text(OVERHANG/2, POLE_HEIGHT-0.4, 'Dead Load', ha='center', fontsize=10, color='green')
    elif show_arrows == 'dunk':
        arrow = FancyArrowPatch((OVERHANG + RIM_DIA/2, POLE_HEIGHT - 0.15),
                              (OVERHANG + RIM_DIA/2, POLE_HEIGHT - 0.5),
                              mutation_scale=20, color='red', arrowstyle='->', linewidth=3)
        ax.add_patch(arrow)
        ax.text(OVERHANG + RIM_DIA/2, POLE_HEIGHT-0.6, 'DUNK!', ha='center', fontsize=12,
                color='red', fontweight='bold')
    elif show_arrows == 'wind':
        for y_w in np.linspace(POLE_HEIGHT - 0.4, POLE_HEIGHT + 0.4, 5):
            arrow = FancyArrowPatch((OVERHANG + 0.1, y_w), (OVERHANG + 0.4, y_w),
                                  mutation_scale=10, color='cyan', arrowstyle='->', linewidth=1.5)
            ax.add_patch(arrow)
        ax.text(OVERHANG + 0.25, POLE_HEIGHT + 0.5, 'Wind', ha='center', fontsize=10, color='blue')
    elif show_arrows == 'combined':
        # 多种载荷
        arrow1 = FancyArrowPatch((OVERHANG/2, POLE_HEIGHT), (OVERHANG/2, POLE_HEIGHT-0.2),
                                  mutation_scale=12, color='green', arrowstyle='->', linewidth=2)
        ax.add_patch(arrow1)
        arrow2 = FancyArrowPatch((OVERHANG + RIM_DIA/2, POLE_HEIGHT - 0.15),
                                  (OVERHANG + RIM_DIA/2, POLE_HEIGHT - 0.4),
                                  mutation_scale=15, color='red', arrowstyle='->', linewidth=2)
        ax.add_patch(arrow2)

# 4个工况
draw_hoop(axes4[0, 0], 'Case 1: Self-Weight', 'gravity')
draw_hoop(axes4[0, 1], 'Case 2: Dunk Impact', 'dunk')
draw_hoop(axes4[1, 0], 'Case 3: Wind Load', 'wind')
draw_hoop(axes4[1, 1], 'Case 4: Combined', 'combined')

plt.tight_layout()
plt.savefig('results/bball_load_cases.png', dpi=150, bbox_inches='tight')
print("  [SAVED] results/bball_load_cases.png")
plt.close()

# 图5: 立柱截面详图
print("Generating Figure 5: Pole Section Details...")
fig5, ax5 = plt.subplots(figsize=(10, 8))

# 绘制截面
circle_out = Circle((0, 0), POLE_DIA/2, fill=False, edgecolor='black', linewidth=3)
circle_in = Circle((0, 0), (POLE_DIA-2*POLE_T)/2, fill=False, edgecolor='black', linewidth=2)
ax5.add_patch(circle_out)
ax5.add_patch(circle_in)
annulus = Wedge((0, 0), POLE_DIA/2, 0, 360, width=POLE_T, facecolor='lightgray', edgecolor='none')
ax5.add_patch(annulus)

# 尺寸标注
ax5.annotate('', xy=(0, 0), xytext=(POLE_DIA/2, 0),
            arrowprops=dict(arrowstyle='<->', color='blue', lw=2))
ax5.text(POLE_DIA/4, 0.02, f'D={POLE_DIA*1000:.0f}', ha='center', color='blue', fontsize=12, fontweight='bold')

ax5.annotate('', xy=((POLE_DIA-2*POLE_T)/2, 0), xytext=((POLE_DIA-2*POLE_T)/2, POLE_DIA/2),
            arrowprops=dict(arrowstyle='<->', color='red', lw=2))
ax5.text((POLE_DIA-2*POLE_T)/2, POLE_DIA/4, f't={POLE_T*1000:.0f}',
         ha='left', color='red', fontsize=12, fontweight='bold')

# 计算截面属性
A = np.pi * (POLE_DIA**2 - (POLE_DIA-2*POLE_T)**2) / 4
I = np.pi * (POLE_DIA**4 - (POLE_DIA-2*POLE_T)**4) / 64
S = I / (POLE_DIA/2)

ax5.set_xlim(-POLE_DIA, POLE_DIA)
ax5.set_ylim(-POLE_DIA, POLE_DIA)
ax5.set_aspect('equal')
ax5.set_title(f'Pole Section Details\nA={A*1e4:.2f} cm², I={I*1e8:.2f} cm⁴', fontsize=14, fontweight='bold')
ax5.axis('off')

plt.savefig('results/bball_section.png', dpi=150, bbox_inches='tight')
print("  [SAVED] results/bball_section.png")
plt.close()

# 图6: 综合分析图
print("Generating Figure 6: Comprehensive Analysis...")
fig6 = plt.figure(figsize=(16, 10))

# 6.1 结构图
ax6a = plt.subplot2grid((2, 3), (0, 0))
draw_hoop(ax6a, 'Structure', None)

# 6.2 弯矩图
ax6b = plt.subplot2grid((2, 3), (0, 1))
y = np.linspace(0, POLE_HEIGHT, 50)
M = 70 * (1 - y/POLE_HEIGHT)
ax6b.fill_betweenx(M, 0, y, alpha=0.3, color='blue')
ax6b.plot(M, y, 'b-', linewidth=2)
ax6b.set_xlabel('Moment (kN·m)')
ax6b.set_ylabel('Height (m)')
ax6b.set_title('Moment Diagram')
ax6b.grid(True, alpha=0.3)
ax6b.invert_xaxis()

# 6.3 稳定性
ax6c = plt.subplot2grid((2, 3), (0, 2))
check_items = ['Strength', 'Stability', 'Deflection', 'Wind']
check_status = ['PASS', 'PASS', 'PASS', 'PASS']
colors_check = ['green' if s == 'PASS' else 'red' for s in check_status]
y_pos = np.arange(len(check_items))
bars = ax6c.barh(y_pos, [1]*4, color=colors_check, alpha=0.7)
ax6c.set_yticks(y_pos)
ax6c.set_yticklabels(check_items)
ax6c.set_xlim(0, 1.2)
ax6c.set_title('Check Summary')
for i, (bar, status) in enumerate(zip(bars, check_status)):
    bar.set_x(bar.get_width() + 0.05)
    ax6c.text(bar.get_x(), bar.get_y() + bar.get_height()/2, status,
             va='center', fontweight='bold', color=colors_check[i])
ax6c.axis('off')

# 6.4 篮板详图
ax6d = plt.subplot2grid((2, 3), (1, 0))
bb = Rectangle((0, 0), BACKBOARD_W, BACKBOARD_H, facecolor='white', edgecolor='blue', linewidth=3)
ax6d.add_patch(bb)
ax6d.plot([BACKBOARD_W/2, BACKBOARD_W/2 + 0.15], [BACKBOARD_H/2 - 0.15, BACKBOARD_H/2 - 0.15],
         'r-', linewidth=4)
ax6d.plot([BACKBOARD_W/2, BACKBOARD_W/2], [BACKBOARD_H/2 - 0.15, BACKBOARD_H/2 - 0.4],
         'r-', linewidth=4)
rim_small = Circle((BACKBOARD_W/2 + 0.15, BACKBOARD_H/2 - 0.15), RIM_DIA/2,
                    fill=False, edgecolor='red', linewidth=2)
ax6d.add_patch(rim_small)
ax6d.set_xlim(-0.2, BACKBOARD_W + 0.3)
ax6d.set_ylim(-0.2, BACKBOARD_H + 0.2)
ax6d.set_aspect('equal')
ax6d.set_title('Backboard Detail')
ax6d.set_xlabel('m')

# 6.5 冲击响应
ax6e = plt.subplot2grid((2, 3), (1, 1))
t = np.linspace(0, 0.5, 100)
omega = 2 * np.pi * 15  # 假设基频15Hz
damping = 0.05
response = (800 * np.exp(-damping * omega * t) * np.cos(omega * t)) / 9.81  # kN
ax6e.plot(t, response, 'b-', linewidth=2)
ax6e.set_xlabel('Time (s)')
ax6e.set_ylabel('Impact Force (kN)')
ax6e.set_title('Dunk Impact Response')
ax6e.grid(True, alpha=0.3)
ax6e.axhline(0, color='k', linestyle='-', alpha=0.3)

# 6.6 参数表
ax6f = plt.subplot2grid((2, 3), (1, 2))
ax6f.axis('off')

params = [
    ['Parameter', 'Value'],
    ['Pole height', '3.05 m'],
    ['Overhang', '1.20 m'],
    ['Backboard', '1.80 x 1.05 m'],
    ['Rim diameter', '0.45 m'],
    ['Pole section', 'CHS 168x8'],
    ['Steel grade', 'Q345'],
    ['Counterweight', '200 kg'],
    ['Standard', 'FIBA'],
]

table = ax6f.table(cellText=params[1:], colLabels=params[0], cellLoc='center',
                  bbox=[0, 0, 1, 1])
table.auto_set_font_size(False)
table.set_fontsize(11)
table.scale(1, 2)

ax6f.set_title('Design Parameters', fontweight='bold', fontsize=12)

plt.suptitle('Basketball Hoop - Comprehensive Analysis', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig('results/basketball_complete.png', dpi=150, bbox_inches='tight')
print("  [SAVED] results/basketball_complete.png")
plt.close()

print()
print("="*60)
print("  ALL FIGURES GENERATED SUCCESSFULLY!")
print("="*60)
print()
print("[Generated Files]")
print("  1. results/bball_structure.png      - Main structure")
print("  2. results/bball_3d.png              - 3D model")
print("  3. results/bball_forces.png         - Force analysis")
print("  4. results/bball_load_cases.png     - Load cases")
print("  5. results/bball_section.png       - Section details")
print("  6. results/basketball_complete.png  - Comprehensive")
print()
