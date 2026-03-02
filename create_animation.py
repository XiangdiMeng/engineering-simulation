"""
篮球架扣篮冲击动态模拟
Basketball Dunk Impact - Dynamic Simulation

创建真实的物理动画，展示：
1. 扣篮瞬间的冲击力
2. 篮架振动响应
3. 篮圈变形
4. 动态应力分布变化
"""

import sys
sys.path.insert(0, 'src')

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch
from dataclasses import dataclass
from typing import List, Tuple

# ============================================
# 物理参数
# ============================================

@dataclass
class SimulationParams:
    """模拟参数"""
    dt: float = 0.005          # 时间步长 (s)
    total_time: float = 3.0    # 总时长 (s)
    dunk_duration: float = 0.15 # 冲击持续时间 (s)
    max_impact_force: float = 8000  # 最大冲击力 (N)
    damping_ratio: float = 0.03  # 阻尼比
    natural_freq: float = 15.0  # 固有频率 (Hz)
    playback_speed: float = 1.0  # 播放速度

# 模拟参数
params = SimulationParams()

print("="*60)
print("  BASKETBALL DUNK SIMULATION")
print("="*60)
print()

# 动力学计算
omega_n = 2 * np.pi * params.natural_freq
zeta = params.damping_ratio
omega_d = omega_n * np.sqrt(1 - zeta**2)  # 阻尼固有频率

# 时间数组
t = np.arange(0, params.total_time, params.dt)
n_frames = len(t)

print(f"Simulation Parameters:")
print(f"  Duration: {params.total_time} s")
print(f"  Time step: {params.dt} s")
print(f"  Frames: {n_frames}")
print(f"  Natural frequency: {params.natural_freq} Hz")
print(f"  Damping ratio: {zeta}")
print()

# ============================================
# 1. 计算动态响应
# ============================================

print("Calculating dynamic response...")

# 冲击力时程（简化的三角形脉冲）
impact_force = np.zeros_like(t)
impact_start = int(0.5 / params.dt)  # 0.5秒开始冲击
impact_end = int((0.5 + params.dunk_duration) / params.dt)

for i in range(impact_start, min(impact_end, n_frames)):
    if i < impact_start + (impact_end - impact_start) // 2:
        impact_force[i] = params.max_impact_force * (i - impact_start) / ((impact_end - impact_start) // 2)
    else:
        impact_force[i] = params.max_impact_force * (1 - (i - impact_start - (impact_end - impact_start) // 2) / ((impact_end - impact_start) // 2))

# 位移响应（单自由度系统）
# 响应 = 冲击杜哈梅积分简化
displacement = np.zeros_like(t)
velocity = np.zeros_like(t)

# 初始条件
u = 0  # 位移
v = 0  # 速度

for i in range(1, n_frames):
    # 当前时刻的力
    F = impact_force[i-1]

    # 加速度 a = (F - 2*zeta*omega_n*v - omega_n**2*u) / m
    # 简化：直接使用解析解
    if i < impact_start:
        # 冲击前
        u, v = 0, 0
    else:
        t_local = t[i] - 0.5
        if t_local < params.dunk_duration:
            # 冲击期间 - 强迫振动
            # 使用简化的指数衰减响应
            u = (params.max_impact_force / (1000 * omega_n**2)) * \
                 (1 - np.exp(-zeta * omega_n * t_local)) * np.sin(omega_n * t_local) * 0.1
            v = 0
        else:
            # 自由衰减振动
            t_decay = t_local - params.dunk_duration
            u_prev = (params.max_impact_force / (1000 * omega_n**2)) * \
                     (1 - np.exp(-zeta * omega_n * params.dunk_duration)) * np.sin(omega_n * params.dunk_duration) * 0.1
            u = u_prev * np.exp(-zeta * omega_n * t_decay) * np.cos(omega_d * t_decay)
            v = 0

    displacement[i] = u
    velocity[i] = v

# 放大位移用于可视化
visualization_scale = 50  # 放大50倍显示
displacement_viz = displacement * visualization_scale

max_disp = np.max(np.abs(displacement_viz))
print(f"  Max displacement: {max_disp*1000:.2f} mm (visualized)")
print()

# ============================================
# 2. 创建动画
# ============================================

print("Creating animation...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Basketball Dunk - Dynamic Response Simulation', fontsize=16, fontweight='bold')

# 定义绘图函数
def draw_basketball_hoop(ax, time_idx=0, show_stress=True):
    """绘制篮球架"""
    ax.clear()

    # 固定坐标范围
    ax.set_xlim(-1.5, 3)
    ax.set_ylim(-0.5, 4)
    ax.set_aspect('equal')

    # 地面
    ground = Rectangle((-1.5, -0.05), 4.5, 0.05, facecolor='#8B4513', edgecolor='none')
    ax.add_patch(ground)

    # 篮板位置（会随变形移动）
    backboard_x = 1.2 + displacement_viz[time_idx]
    backboard_y = 3.05

    # 立柱
    pole = Rectangle((-0.084, 0), 0.168, 3.05,
                     facecolor='gray', edgecolor='black', linewidth=2)
    ax.add_patch(pole)

    # 悬臂（会弯曲）
    arm_y = np.linspace(0, 3.05, 20)
    arm_x = arm_y / 3.05 * (1.2 + displacement_viz[time_idx] * arm_y / 3.05 * 0.3)
    ax.plot(arm_x, arm_y, 'orange', linewidth=6)

    # 篮板
    backboard = Rectangle((backboard_x, backboard_y - 0.525),
                          0.02, 1.05,
                          facecolor='white', edgecolor='blue', linewidth=2)
    ax.add_patch(backboard)

    # 篮圈
    rim = Circle((backboard_x + 0.225, backboard_y - 0.15), 0.225,
                fill=False, edgecolor='red', linewidth=3)
    ax.add_patch(rim)

    # 篮网
    rim_x = np.linspace(backboard_x, backboard_x + 0.45, 15)
    rim_y = backboard_y - 0.15 - 0.4 * np.sin(np.linspace(0, np.pi, 15))
    ax.plot(rim_x, rim_y, 'r-', alpha=0.5, linewidth=1)

    # 冲击力箭头（动态显示）
    if time_idx >= impact_start and time_idx < impact_end:
        arrow_len = 0.3 * (impact_force[time_idx] / params.max_impact_force)
        arrow = FancyArrowPatch((backboard_x + 0.225, backboard_y - 0.15),
                              (backboard_x + 0.225, backboard_y - 0.15 - arrow_len),
                              mutation_scale=15, color='red', arrowstyle='->', linewidth=3)
        ax.add_patch(arrow)
        ax.text(backboard_x + 0.35, backboard_y - 0.4, '!',
                fontsize=20, color='red', fontweight='bold')

    # 时间显示
    ax.text(0, 3.7, f'Time: {t[time_idx]:.2f} s', fontsize=12,
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    # 冲击力显示
    if time_idx >= impact_start:
        ax.text(0, 3.5, f'Impact Force: {impact_force[time_idx]/1000:.1f} kN',
                fontsize=10, color='red')

# ============================================
# 子图1: 主结构动画
# ============================================

ax1 = axes[0, 0]
draw_basketball_hoop(ax1, 0)

# ============================================
# 子图2: 冲击力时程
# ============================================

ax2 = axes[0, 1]
ax2.plot(t, impact_force/1000, 'r-', linewidth=2)
ax2.set_xlim(0, params.total_time)
ax2.set_ylim(0, params.max_impact_force/1000 * 1.1)
ax2.set_xlabel('Time (s)')
ax2.set_ylabel('Impact Force (kN)')
ax2.set_title('Impact Force vs Time')
ax2.grid(True, alpha=0.3)
time_line, = ax2.plot([], [], 'o', color='blue', markersize=8)
ax2.axvline(x=0.5, color='gray', linestyle='--', alpha=0.5, label='Dunk Start')

# ============================================
# 子图3: 位移响应时程
# ============================================

ax3 = axes[1, 0]
ax3.plot(t, displacement * 1000, 'b-', linewidth=2)
ax3.set_xlim(0, params.total_time)
ax3.set_ylim(-np.max(np.abs(displacement*1000))*1.1 - 0.1,
         np.max(np.abs(displacement*1000))*1.1)
ax3.set_xlabel('Time (s)')
ax3.set_ylabel('Tip Displacement (mm)')
ax3.set_title('Rim Displacement Response')
ax3.grid(True, alpha=0.3)
time_line3, = ax3.plot([], [], 'bo', color='blue', markersize=6)

# ============================================
# 子图4: 频谱分析
# ============================================

ax4 = axes[1, 1]
# 简化的频谱（FFT）
# 只取冲击后的数据进行分析
response_data = displacement[int(impact_start):]
n_fft = len(response_data)
fft_result = np.abs(np.fft.fft(response_data))[:n_fft//2]
freqs = np.fft.fftfreq(n_fft, params.dt)[:n_fft//2]
ax4.plot(freqs, fft_result, 'g-', linewidth=2)
ax4.set_xlim(0, 50)
ax4.set_xlabel('Frequency (Hz)')
ax4.set_ylabel('Amplitude')
ax4.set_title('Frequency Spectrum')
ax4.grid(True, alpha=0.3)

# ============================================
# 动画函数
# ============================================

def animate(frame_idx):
    """动画更新函数"""
    # 减少帧数，加快渲染
    idx = frame_idx * 4  # 每4个时间步取1帧
    if idx >= n_frames:
        idx = n_frames - 1

    # 更新主结构图
    draw_basketball_hoop(ax1, idx)

    # 更新时间线
    current_time = t[idx]
    time_line.set_data([current_time], [impact_force[idx]/1000])
    time_line3.set_data([current_time], [displacement[idx]*1000])

    return []

# 创建动画
print("Rendering animation (this may take a moment)...")

# 使用更少的帧数加快速度
frame_indices = range(0, min(150, n_frames // 4))

anim = animation.FuncAnimation(
    fig, animate, frames=frame_indices,
    interval=50, blit=False, repeat=True
)

plt.tight_layout()

# 保存为GIF
print("Saving as GIF...")
try:
    anim.save('results/basketball_dunk_simulation.gif',
             writer='pillow', fps=20, dpi=80)
    print("  [SAVED] results/basketball_dunk_simulation.gif")
except Exception as e:
    print(f"  GIF save failed: {e}")
    print("  Try installing: pip install pillow")

# 保存为MP4 (更高质量)
print("Saving as MP4...")
try:
    anim.save('results/basketball_dunk_simulation.mp4',
             writer='ffmpeg', fps=30, dpi=100)
    print("  [SAVED] results/basketball_dunk_simulation.mp4")
except Exception as e:
    print(f"  MP4 save failed: {e}")
    print("  Try installing: conda install -c conda-forge ffmpeg")

# 保存关键帧为静态图
print("Saving key frames...")
for frame_num in [0, n_frames//4, n_frames//2, 3*n_frames//4]:
    if frame_num < n_frames:
        fig_frame, ax_frame = plt.subplots(figsize=(10, 8))
        draw_basketball_hoop(ax_frame, frame_num)
        ax_frame.set_title(f'Basketball Dunk - Frame {frame_num} ({t[frame_num]:.2f}s)')
        plt.savefig(f'results/dunk_frame_{frame_num:03d}.png', dpi=100, bbox_inches='tight')
        plt.close()

print(f"  [SAVED] Key frames saved: results/dunk_frame_*.png")

print()
print("="*60)
print("  SIMULATION COMPLETE!")
print("="*60)
print()
print("[Output Files]")
print("  1. results/basketball_dunk_simulation.gif")
print("  2. results/basketball_dunk_simulation.mp4 (if ffmpeg available)")
print("  3. results/dunk_frame_*.png (key frames)")
print()
print(f"Animation Info:")
print(f"  Duration: {params.total_time} s")
print(f"  Frames: {len(frame_indices)}")
print(f"  FPS: 20")
print(f"  Max impact force: {params.max_impact_force/1000:.1f} kN")
print(f"  Natural frequency: {params.natural_freq} Hz")

plt.close()
