"""
篮球架扣篮动态模拟 - 简化版
Basketball Dunk Dynamic Simulation - Simplified
"""

import sys
sys.path.insert(0, 'src')

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch

print("="*60)
print("  BASKETBALL DUNK - DYNAMIC SIMULATION")
print("="*60)

# 参数
dt = 0.01
total_time = 3.0
t = np.arange(0, total_time, dt)
n_frames = len(t)

dunk_start = int(1.0 / dt)
dunk_duration = int(0.2 / dt)

# 冲击力时程
impact_force = np.zeros_like(t)
max_force = 8000  # N

for i in range(dunk_start, min(dunk_start + dunk_duration, n_frames)):
    if i < dunk_start + dunk_duration // 2:
        impact_force[i] = max_force * (i - dunk_start) / (dunk_duration // 2)
    else:
        impact_force[i] = max_force * (1 - (i - dunk_start - dunk_duration // 2) / (dunk_duration // 2))

# 位移响应（简化）
displacement = np.zeros_like(t)
natural_freq = 15.0  # Hz
omega = 2 * np.pi * natural_freq
damping = 0.03

for i in range(dunk_start, n_frames):
    t_local = t[i] - 1.0
    if t_local < 0.2:
        # 冲击期间
        displacement[i] = (max_force / 1000 / omega**2) * \
                        (1 - np.exp(-damping * omega * t_local)) * \
                        np.sin(omega * t_local) * 0.1
    else:
        # 自由衰减
        t_decay = t_local - 0.2
        amp_at_impact = (max_force / 1000 / omega**2) * 0.1
        displacement[i] = amp_at_impact * np.exp(-damping * omega * t_decay) * np.cos(omega * t_decay)

# 放大系数
viz_scale = 100  # 放大100倍显示
displacement_viz = displacement * viz_scale

print(f"Max displacement: {np.max(np.abs(displacement_viz))*1000:.2f} mm")
print()

# 创建动画
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Basketball Dunk - Dynamic Simulation', fontsize=16, fontweight='bold')

def draw_frame(ax, frame_idx):
    """绘制指定帧"""
    ax.clear()

    idx = frame_idx * 5  # 加速播放，每5帧取1帧
    if idx >= n_frames:
        idx = n_frames - 1

    current_time = t[idx]
    disp = displacement_viz[idx]
    force = impact_force[idx]

    # 固定范围
    ax.set_xlim(-1.5, 3)
    ax.set_ylim(-0.3, 4)
    ax.set_aspect('equal')

    # 地面
    ax.add_patch(Rectangle((-1.5, -0.03), 4.5, 0.03, facecolor='#8B4513', edgecolor='none'))

    # 立柱
    ax.add_patch(Rectangle((-0.084, 0), 0.168, 3.05, facecolor='gray', edgecolor='black', linewidth=2))

    # 悬臂（简化为直线，加上位移）
    arm_x = np.linspace(0, 1.2, 20) + disp * (np.arange(20) / 19) * 0.2
    arm_y = np.linspace(3.05, 3.05, 20)
    ax.plot(arm_x, arm_y, 'orange', linewidth=8)

    # 篮板位置（随位移变化）
    bb_x = 1.2 + disp
    bb_y = 3.05
    ax.add_patch(Rectangle((bb_x, bb_y - 0.525), 0.02, 1.05, facecolor='white', edgecolor='blue', linewidth=3))

    # 篮圈
    ax.add_patch(Circle((bb_x + 0.225, bb_y - 0.15), 0.225, fill=False, edgecolor='red', linewidth=4))

    # 篮网
    rim_x = np.linspace(bb_x, bb_x + 0.45, 15)
    rim_y = bb_y - 0.15 - 0.4 * np.sin(np.linspace(0, np.pi, 15))
    ax.plot(rim_x, rim_y, 'r-', alpha=0.6, linewidth=1)

    # 冲击箭头
    if force > 0:
        arrow_len = 0.3 * (force / max_force)
        ax.add_patch(FancyArrowPatch((bb_x + 0.225, bb_y - 0.15),
                                  (bb_x + 0.225, bb_y - 0.15 - arrow_len),
                                  mutation_scale=20, color='red', arrowstyle='->', linewidth=4))
        ax.text(bb_x + 0.35, bb_y - 0.5, '!' if force > max_force*0.5 else 'Impact',
                fontsize=14, color='red', fontweight='bold')

    # 时间和力显示
    ax.text(0, 3.8, f'Time: {current_time:.2f}s | Force: {force/1000:.1f}kN',
            fontsize=11, bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

# 初始化子图
for ax in axes.flat:
    ax.set_xticks([])
    ax.set_yticks([])

# 主动画 - 左上
axes[0, 0].set_title('Main Animation', fontweight='bold')

# 力时程图 - 右上
ax2 = axes[0, 1]
ax2.plot(t, impact_force/1000, 'r-', linewidth=2)
ax2.set_xlim(0, total_time)
ax2.set_ylim(0, max_force/1000 * 1.1)
ax2.set_xlabel('Time (s)')
ax2.set_ylabel('Impact Force (kN)')
ax2.set_title('Impact Force vs Time')
ax2.grid(True, alpha=0.3)
time_line2, = ax2.plot([], [], 'bo', color='blue', markersize=8)

# 位移时程图 - 左下
ax3 = axes[1, 0]
ax3.plot(t, displacement * 1000, 'b-', linewidth=2)
ax3.set_xlim(0, total_time)
ax3.set_ylim(np.min(displacement*1000)*1.1 - 1, np.max(displacement*1000)*1.1 + 1)
ax3.set_xlabel('Time (s)')
ax3.set_ylabel('Displacement (mm)')
ax3.set_title('Rim Displacement Response')
ax3.grid(True, alpha=0.3)
time_line3, = ax3.plot([], [], 'bo', color='blue', markersize=8)

# 相位图 - 右下
ax4 = axes[1, 1]
# 速度
velocity = np.gradient(displacement * 1000, dt)
ax4.plot(t, velocity, 'g-', linewidth=2, label='Velocity')
ax4.plot(t, displacement * 1000, 'b-', linewidth=2, label='Displacement', alpha=0.6)
ax4.set_xlim(0, total_time)
ax4.set_xlabel('Time (s)')
ax4.set_ylabel('Amplitude')
ax4.set_title('Velocity & Displacement')
ax4.legend()
ax4.grid(True, alpha=0.3)

plt.tight_layout()

print("Creating animation...")
frames_to_generate = min(80, n_frames // 5)

def update(frame):
    # 主动画
    draw_frame(axes[0, 0], frame)

    # 更新时间线
    idx = frame * 5
    if idx < n_frames:
        time_line2.set_data([t[idx]], [impact_force[idx]/1000])
        time_line3.set_data([t[idx]], [displacement[idx]*1000])

    return []

# 创建动画
anim = animation.FuncAnimation(
    fig, update, frames=frames_to_generate,
    interval=50, blit=False, repeat=True
)

# 保存
print("Saving as GIF...")
try:
    anim.save('results/basketball_dunk.gif', writer='pillow', fps=15, dpi=80)
    print("  [SAVED] results/basketball_dunk.gif")
except Exception as e:
    print(f"  GIF save failed: {e}")

# 保存关键帧
print("Saving key frames...")
key_frames = [0, 10, 20, 30, 40, 50, 60, 70]
for i, frame_num in enumerate(key_frames):
    if frame_num < n_frames:
        fig_frame = plt.figure(figsize=(10, 8))
        ax_frame = fig_frame.add_subplot(111)
        draw_frame(ax_frame, frame_num)
        ax_frame.set_title(f'Basketball Dunk - Frame {i+1} ({t[frame_num]:.2f}s)', fontweight='bold')
        plt.savefig(f'results/dunk_frame_{i+1:02d}.png', dpi=100, bbox_inches='tight')
        plt.close()

print(f"  [SAVED] {len(key_frames)} key frames")

# 保存静态分析图
fig_static = plt.figure(figsize=(12, 10))

# 力时程
ax1 = fig_static.add_subplot(221)
ax1.plot(t, impact_force/1000, 'r-', linewidth=2, label='Impact Force')
ax1.axvline(1.0, color='gray', linestyle='--', alpha=0.5)
ax1.set_xlabel('Time (s)')
ax1.set_ylabel('Force (kN)')
ax1.set_title('Impact Force Time History')
ax1.legend()
ax1.grid(True, alpha=0.3)

# 位移响应
ax2 = fig_static.add_subplot(222)
ax2.plot(t, displacement * 1000, 'b-', linewidth=2, label='Rim Displacement')
ax2.set_xlabel('Time (s)')
ax2.set_ylabel('Displacement (mm)')
ax2.set_title('Displacement Response')
ax2.legend()
ax2.grid(True, alpha=0.3)

# 速度
ax3 = fig_static.add_subplot(223)
vel = np.gradient(displacement * 1000, dt)
accel = np.gradient(vel, dt) / 1000
ax3.plot(t, vel, 'g-', linewidth=2, label='Velocity')
ax3.plot(t, accel, 'r-', linewidth=2, label='Acceleration (m/s²)', alpha=0.6)
ax3.set_xlabel('Time (s)')
ax3.set_ylabel('Velocity (mm/s) / Acceleration (m/s²)')
ax3.set_title('Velocity & Acceleration')
ax3.legend()
ax3.grid(True, alpha=0.3)

# 相位图
ax4 = fig_static.add_subplot(224)
ax4.plot(displacement * 1000, vel, 'b-', linewidth=2)
ax4.set_xlabel('Displacement (mm)')
ax4.set_ylabel('Velocity (mm/s)')
ax4.set_title('Phase Plot (Velocity vs Displacement)')
ax4.grid(True, alpha=0.3)

plt.suptitle('Basketball Dunk - Dynamic Analysis Results', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('results/basketball_dunk_analysis.png', dpi=150, bbox_inches='tight')
print("  [SAVED] results/basketball_dunk_analysis.png")

plt.close()

print()
print("="*60)
print("  SIMULATION COMPLETE!")
print("="*60)
print()
print(f"Max impact force: {max_force/1000:.1f} kN")
print(f"Max rim displacement: {np.max(np.abs(displacement))*1000:.2f} mm")
print(f"Damping ratio: {damping}")
print(f"Natural frequency: {natural_freq} Hz")
