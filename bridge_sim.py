"""
桥梁车辆通过振动分析 - 简化版
Bridge Vehicle Vibration Analysis - Simplified
"""

import sys
sys.path.insert(0, 'src')

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch

print("="*70)
print("  BRIDGE VIBRATION ANALYSIS")
print("  Vehicle: Moving Load Response")
print("="*70)
print()

# 参数
SPAN = 30.0                    # 跨度 (m)
EI = 1.2e10                   # 抗弯刚度
beam_mass = 1200              # kg/m
vehicle_weight = 30000         # N (约3吨)

# 固有频率
f1 = (np.pi / 2) * np.sqrt(EI / (beam_mass * SPAN**4))
print(f"Bridge Properties:")
print(f"  Span: {SPAN} m")
print(f"  First natural frequency: {f1:.2f} Hz")
print(f"  Vehicle weight: {vehicle_weight/1000:.0f} kN")
print()

# 临界速度
v_critical = np.sqrt(EI / beam_mass) / SPAN
v_critical_kmh = v_critical * 3.6
print(f"  Critical velocity: {v_critical_kmh:.1f} km/h")
print()

# ============================================
# 1. 速度 vs 动力放大系数分析
# ============================================

print("Calculating Dynamic Amplification Factors...")
print()

speeds = [10, 20, 30, 40, 50, 60, 80, 100]
results = []

for speed_kmh in speeds:
    speed = speed_kmh / 3.6
    v_ratio = speed / v_critical_kmh

    # 动力放大系数
    if speed < v_critical:
        DAF = 1 + 0.5 * v_ratio**0.7
    else:
        DAF = 1.8  # 限制

    # 静态挠度 (跨中)
    static_defl = (vehicle_weight * SPAN**3) / (48 * EI) * 1000  # mm
    dynamic_defl = static_defl * DAF

    results.append({
        'speed': speed_kmh,
        'v_ratio': v_ratio,
        'DAF': DAF,
        'static': static_defl,
        'dynamic': dynamic_defl
    })

# 打印结果
print("Speed Analysis:")
print("  Speed(km/h)  v/v_cr   DAF    Static(mm)   Dynamic(mm)")
print("-"*60)
for r in results:
    print(f"  {r['speed']:>10}     {r['v_ratio']:.2f}    {r['DAF']:.2f}    {r['static']:>8.1f}   {r['dynamic']:>8.1f}")

# 最危险情况
worst = max(results, key=lambda x: x['dynamic'])
print()
print(f"Most critical: {worst['speed']} km/h")
print(f"  Max deflection: {worst['dynamic']:.2f} mm")

# 挠度限值
limit = SPAN * 1000 / 600  # L/600
print(f"  Deflection limit: {limit:.2f} mm")
print()

# ============================================
# 2. 创建可视化图表
# ============================================

print("Creating visualizations...")

# 图1: 综合分析图
fig1 = plt.figure(figsize=(16, 10))
gs1 = fig1.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

# 2.1 速度-放大系数曲线
ax1a = fig1.add_subplot(gs1[0, 0])
speeds_list = [r['speed'] for r in results]
dafs_list = [r['DAF'] for r in results]
static_list = [r['static'] for r in results]
dynamic_list = [r['dynamic'] for r in results]

ax1a.plot(speeds_list, dafs_list, 'o-', color='orange', markersize=8, label='DAF')
ax1a.axvline(v_critical_kmh, color='r', linestyle='--', linewidth=2, label='Critical Speed')
ax1a.set_xlabel('Vehicle Speed (km/h)')
ax1a.set_ylabel('Dynamic Amplification Factor')
ax1a.set_title('DAF vs Speed')
ax1a.legend()
ax1a.grid(True, alpha=0.3)

# 2.2 静态vs动态挠度
ax1b = fig1.add_subplot(gs1[0, 1])
ax1b.plot(speeds_list, static_list, 'b--', label='Static', linewidth=2)
ax1b.plot(speeds_list, dynamic_list, 'r-', label='Dynamic', linewidth=3)
ax1b.axhline(limit, color='gray', linestyle='--', label='Limit (L/600)')
ax1b.set_xlabel('Vehicle Speed (km/h)')
ax1b.set_ylabel('Max Displacement (mm)')
ax1b.set_title('Static vs Dynamic Deflection')
ax1b.legend()
ax1b.grid(True, alpha=0.3)

# 2.3 静态挠度参考线
ax1c = fig1.add_subplot(gs1[0, 2])
for r in results:
    color = 'green' if r['dynamic'] < limit else 'red'
    bar_color = color if r['dynamic'] < limit else 'orange'
    ax1c.bar([r['speed']], [r['dynamic']], width=10, color=bar_color, alpha=0.7)

ax1c.axhline(limit, color='gray', linestyle='--', linewidth=2, label='Limit L/600')
ax1c.set_xticks([r['speed'] for r in results])
ax1c.set_xlabel('Vehicle Speed (km/h)')
ax1c.set_ylabel('Max Displacement (mm)')
ax1c.set_title('Deflection by Speed')
ax1c.grid(True, alpha=0.3, axis='y')

# 2.4 冲击系数曲线
ax1d = fig1.add_subplot(gs1[1, 0])
v_ratios = [r['v_ratio'] for r in results]
impacts = [r['DAF'] for r in results]
ax1d.plot(v_ratios, impacts, 'g-o', markersize=8)
ax1d.set_xlabel('Speed / Critical Speed')
ax1d.set_ylabel('Dynamic Amplification Factor')
ax1d.set_title('Impact Coefficient Curve')
ax1d.grid(True, alpha=0.3)

# 2.5 3D速度对比图
ax1e = fig1.add_subplot(gs1[1, 1], projection='3d')

# 桥梁
x_b = np.linspace(-2, SPAN + 2, 50)
y_b = np.zeros_like(x_b)

for i, speed_kmh in enumerate([20, 40, 60, 80]):
    ax1e.plot(x_b, y_b, '-', alpha=0.3, linewidth=1, label=f'{speed_kmh} km/h')

# 变形（根据速度）
for i, speed_kmh in enumerate([20, 40, 60, 80]):
    r = [r for r in results if r['speed'] == speed_kmh][0]
    disp_at_mid = r['dynamic'] / 1000 * 0.1  # 放大显示
    y_def = disp_at_mid * np.sin(np.pi * x_b / SPAN)
    ax1e.plot(x_b, y_def + y_b, '-', linewidth=2)

ax1e.set_xlim(-2, SPAN + 2)
ax1e.set_ylim(-0.5, 2)
ax1e.set_title('Bridge Deformation at Different Speeds')
ax1e.set_xlabel('Bridge Position (m)')
ax1e.set_zlabel('Deformation (amplified)')
ax1e.legend(fontsize=9, loc='upper right')
ax1e.grid(True, alpha=0.3)

# 2.6 桥梁结构示意
ax1f = fig1.add_subplot(gs1[1, 2])

# 地面
ax1f.add_patch(Rectangle((-2, -0.2), SPAN + 4, 0.2, facecolor='tan', edgecolor='none'))

# 桥墩
ax1f.add_patch(Rectangle((-1, 0), 1, 4, facecolor='gray', edgecolor='black'))
ax1f.add_patch(Rectangle((SPAN, 0), 1, 4, facecolor='gray', edgecolor='black'))

# 桥梁
ax1f.add_patch(Rectangle((0, 0), SPAN, 0.3, facecolor='blue', edgecolor='black', linewidth=2))
ax1f.add_patch(Rectangle((0, 0.3), SPAN, 0.9, facecolor='lightblue', edgecolor='blue', linewidth=1))

# 水面
water = Rectangle((-2, -3), SPAN + 4, 2.8, facecolor='lightblue', alpha=0.3, edgecolor='none')
ax1f.add_patch(water)

# 车辆位置示意图
for i, speed in enumerate([20, 40, 60, 80]):
    x_pos = (i + 1) / 5 * SPAN
    vehicle = Rectangle((x_pos - 0.6, 0.3), 1.2, 0.6, facecolor='orange', edgecolor='black')
    ax1f.add_patch(vehicle)

ax1f.set_xlim(-2, SPAN + 2)
ax1f.set_ylim(-1, 5)
ax1f.set_aspect('equal')
ax1f.set_title('Bridge Structure & Vehicle Positions (Not to Scale)')
ax1f.axis('off')

# 2.7 参数表
ax1g = fig1.add_subplot(gs1[2, :])
ax1g.axis('off')

# 计算统计数据
max_daf = max([r['DAF'] for r in results])

summary_text = f"""
BRIDGE ANALYSIS SUMMARY
{'='*50}

Bridge Parameters:
  • Span: {SPAN} m
  • First natural frequency: {f1:.2f} Hz
  • Critical velocity: {v_critical_kmh:.1f} km/h

Analysis Results:
  • Max DAF: {max_daf:.2f}

Safety Assessment:
  • Deflection limit: {limit:.2f} mm (L/600)

Recommendations:
  • Design speed: < {v_critical_kmh*0.7:.0f} km/h
  • Warning range: {v_critical_kmh*0.7:.0f} - {v_critical_kmh*1.0:.0f} km/h
  • Danger: > {v_critical_kmh*1.0:.0f} km/h

{'='*50}
"""

ax1g.text(0, 1, summary_text, fontsize=11, family='monospace',
         verticalalignment='top')

plt.tight_layout()
plt.savefig('results/bridge_comprehensive.png', dpi=150, bbox_inches='tight')
print("  [SAVED] results/bridge_comprehensive.png")
plt.close()

# ============================================
# 3. 创建车辆通过动画
# ============================================

print("Creating vehicle crossing animation...")

animation_speed = 40  # km/h
dt_anim = 0.02
total_time = SPAN / (animation_speed / 3.6) * 1.2
t_anim = np.arange(0, total_time, dt_anim)

# 车辆位置
vehicle_pos = animation_speed / 3.6 * t_anim
vehicle_pos = np.clip(vehicle_pos, 0, SPAN)

# 梁响应（简化）
beam_resp_anim = np.zeros_like(t_anim)
for i, x_veh in enumerate(vehicle_pos):
    if 0 <= x_veh <= SPAN:
        # 影响线
        influence = (x_veh * (SPAN**2 - x_veh**2)) / (SPAN**2)
        beam_resp_anim[i] = (vehicle_weight * SPAN**3 / (48 * EI) *
                         influence * 1000 *
                         (1 + 0.5 * (animation_speed/3.6 / v_critical_kmh)**0.7))

# 放大用于显示
disp_scale = 20
beam_disp_anim = beam_resp_anim * disp_scale / 1000

# 创建动画
fig_anim, ax_anim = plt.subplots(figsize=(14, 6))
ax_anim.set_xlim(-5, SPAN + 5)
ax_anim.set_ylim(-1, 5)
ax_anim.set_aspect('equal')
ax_anim.set_title(f'Vehicle Crossing Animation ({animation_speed} km/h)', fontsize=14, fontweight='bold')

def draw_anim_frame(ax, idx):
    """绘制动画帧"""
    ax.clear()
    ax_anim.set_xlim(-5, SPAN + 5)
    ax_anim.set_ylim(-1, 5)

    # 水面
    ax.add_patch(Rectangle((-5, -0.2), SPAN + 10, 0.2, facecolor='lightblue', alpha=0.3, edgecolor='none'))

    # 桥墩
    ax.add_patch(Rectangle((-1, 0), 1, 4, facecolor='gray', edgecolor='black'))
    ax.add_patch(Rectangle((SPAN, 0), 1, 4, facecolor='gray', edgecolor='black'))

    # 桥梁
    beam = Rectangle((0, 0), SPAN, 0.3, facecolor='blue', edgecolor='black', linewidth=2)
    ax_anim.add_patch(beam)

    # 梁变形（夸大）
    if idx < len(beam_disp_anim):
        x_deform = np.linspace(0, SPAN, 50)
        y_deform = beam_disp_anim[idx] * np.sin(np.pi * x_deform / SPAN)
        ax_anim.plot(x_deform, y_deform, 'r--', alpha=0.5, linewidth=2)

    # 车辆
    vx = vehicle_pos[idx]
    vehicle = Rectangle((vx - 0.6, 0.3), 1.2, 0.6, facecolor='orange', edgecolor='black', linewidth=2)
    ax_anim.add_patch(vehicle)

    # 车轮
    ax_anim.add_patch(Circle((vx + 0.4, 0.3), 0.4, facecolor='black'))
    ax_anim.add_patch(Circle((vx + 0.8, 0.3), 0.4, facecolor='black'))

    # 速度箭头
    arrow = FancyArrowPatch((vx + 0.6, 1.0), (vx + 0.6 + animation_speed/15, 1.0),
                              mutation_scale=15, color='green', arrowstyle='->', linewidth=2)
    ax_anim.add_patch(arrow)

    # 时间/挠度显示
    current_disp = beam_resp_anim[idx] if idx < len(beam_resp_anim) else 0
    ax_anim.text(0, 4.5, f'Position: {vx:.1f}m  Disp: {current_disp:.2f}mm',
                fontsize=11, bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    ax_anim.grid(True, alpha=0.3, linestyle=':')
    return []

# 动画帧
n_anim_frames = min(80, len(t_anim))
frame_indices = np.linspace(0, n_anim_frames - 1, 20, dtype=int)

def update_anim(frame_idx):
    frame_idx = frame_indices[frame_idx] if frame_idx < len(frame_indices) else frame_indices[-1]
    draw_anim_frame(ax_anim, frame_idx)
    return []

print("Rendering animation...")
try:
    anim = animation.FuncAnimation(fig_anim, update_anim, frames=len(frame_indices),
                                   interval=50, blit=False, repeat=True)
    anim.save('results/bridge_vehicle_crossing.gif', writer='pillow', fps=20, dpi=80)
    print("  [SAVED] results/bridge_vehicle_crossing.gif")
except Exception as e:
    print(f"  GIF save failed: {e}")

plt.close()

# ============================================
# 4. 保存关键帧
# ============================================

print("Saving key frames...")

key_moments = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
for i, moment in enumerate(key_moments):
    fig_frame = plt.figure(figsize=(12, 6))
    ax_frame = fig_frame.add_subplot(111)

    # 车辆位置
    vx = moment * SPAN
    vx = np.clip(vx, 0, SPAN)

    # 绘制场景
    ax_frame.add_patch(Rectangle((-2, -0.1), SPAN + 4, 0.1, facecolor='lightblue', alpha=0.3, edgecolor='none'))
    ax_frame.add_patch(Rectangle((-1, 0), 1, 4, facecolor='gray', edgecolor='black'))
    ax_frame.add_patch(Rectangle((0, 0), SPAN, 0.3, facecolor='blue', edgecolor='black', linewidth=2))
    ax_frame.add_patch(Rectangle((vx - 0.6, 0.3), 1.2, 0.6, facecolor='orange', edgecolor='black', linewidth=2))

    # 轮
    ax_frame.add_patch(Circle((vx + 0.4, 0.3), 0.4, facecolor='black'))
    ax_frame.add_patch(Circle((vx + 0.8, 0.3), 0.4, facecolor='black'))

    # 速度箭头
    ax_frame.add_patch(FancyArrowPatch((vx + 0.6, 1.0), (vx + 0.6 + 0.3, 1.0),
                                  mutation_scale=15, color='green', arrowstyle='->', linewidth=2))

    # 挠度条形图
    if 0 <= vx <= SPAN:
        influence = (vx * (SPAN**2 - vx**2)) / (SPAN**2)
        current_disp = (vehicle_weight * SPAN**3 / (48 * EI) *
                          influence * 1000 *
                          (1 + 0.5 * (animation_speed/3.6 / v_critical_kmh)**0.7))

        # 绘制在桥头
        bar_height = min(abs(current_disp) * 0.1, 2)
        color = 'green' if current_disp < limit/2 else 'red'
        bar = Rectangle((vx - 0.5, 4), 1.0, bar_height,
                       facecolor=color, alpha=0.7, edgecolor='black')
        ax_frame.add_patch(bar)

    ax_frame.set_xlim(-2, SPAN + 2)
    ax_frame.set_ylim(-0.5, 5)
    ax_frame.set_aspect('equal')
    ax_frame.set_title(f'Vehicle Crossing - Frame {i+1} (t={moment:.2f}s)', fontweight='bold')
    ax_frame.grid(True, alpha=0.3, linestyle=':')

    plt.savefig(f'results/bridge_frame_{i+1:02d}.png', dpi=100, bbox_inches='tight')
    plt.close()

print(f"  [SAVED] {len(key_moments)} key frames")

plt.close()

print()
print("="*70)
print("  BRIDGE VIBRATION ANALYSIS COMPLETE!")
print("="*70)
print()
print("[Output Files]")
print("  results/bridge_comprehensive.png   - Analysis dashboard")
print("  results/bridge_vehicle_crossing.gif  - Vehicle crossing animation")
print("  results/bridge_speed_comparison.png - Speed comparison")
print("  results/bridge_frame_XX.png        - Key frames")
print()
