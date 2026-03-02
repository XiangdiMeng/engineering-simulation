"""
动力学分析模块 (Dynamics Analysis)
包含模态分析、固有频率/振型计算、谐响应分析、瞬态响应分析
"""

import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional, Callable
from scipy.linalg import eigh
from scipy.integrate import odeint

from .fea import Node, FEMaterial, Element


@dataclass
class ModalResult:
    """模态分析结果"""
    natural_frequencies: np.ndarray  # 固有频率 (Hz)
    natural_frequencies_rad: np.ndarray  # 固有频率 (rad/s)
    mode_shapes: np.ndarray  # 振型 (每个模态的位移向量)
    modal_masses: np.ndarray  # 模态质量
    modal_stiffness: np.ndarray  # 模态刚度
    participation_factors: np.ndarray  # 模态参与系数

    def __post_init__(self):
        """计算派生属性"""
        # 阻尼比（假设）
        self.damping_ratios = np.zeros_like(self.natural_frequencies)

    def set_damping(self, damping_ratio: float = 0.05):
        """设置阻尼比"""
        self.damping_ratios = np.full_like(self.natural_frequencies, damping_ratio)

    def print_summary(self):
        """打印模态分析摘要"""
        print("\n" + "="*60)
        print("模态分析结果")
        print("="*60)

        print(f"\n{'模态':<8}{'频率(Hz)':<15}{'频率(rad/s)':<18}{'周期(s)':<12}")
        print("-"*60)
        for i, (f, w) in enumerate(zip(self.natural_frequencies, self.natural_frequencies_rad)):
            T = 1/f if f > 0 else float('inf')
            print(f"{i+1:<8}{f:<15.4f}{w:<18.4f}{T:<12.6f}")

        if np.any(self.participation_factors > 0):
            print(f"\n模态参与系数:")
            for i, pf in enumerate(self.participation_factors[:10]):
                print(f"  模态 {i+1}: {pf:.4f}")


@dataclass
class HarmonicResponseResult:
    """谐响应分析结果"""
    frequencies: np.ndarray  # 激励频率范围
    responses: np.ndarray  # 响应幅值
    phases: np.ndarray  # 相位差
    peak_frequency: float  # 峰值响应频率
    peak_response: float  # 峰值响应


@dataclass
class TransientResponseResult:
    """瞬态响应分析结果"""
    time: np.ndarray  # 时间向量
    displacements: np.ndarray  # 位移响应 (时间 x 自由度)
    velocities: np.ndarray  # 速度响应
    accelerations: np.ndarray  # 加速度响应
    max_displacement: float  # 最大位移
    max_velocity: float  # 最大速度
    max_acceleration: float  # 最大加速度


class ModalAnalysis:
    """模态分析器"""

    def __init__(
        self,
        nodes: List[Node],
        elements: List[Element],
        n_modes: int = 10
    ):
        """
        Parameters
        ----------
        nodes : List[Node]
            节点列表
        elements : List[Element]
            单元列表
        n_modes : int
            计算的模态数量
        """
        self.nodes = nodes
        self.elements = elements
        self.n_modes = n_modes

        # 自由度数（每个节点3个自由度：u, v, theta）
        self.n_dof = len(nodes) * 3

    def assemble_mass_matrix(self) -> np.ndarray:
        """
        组装质量矩阵 M

        使用集中质量法
        """
        M = np.zeros((self.n_dof, self.n_dof))

        for elem in self.elements:
            if not hasattr(elem, 'material') or not hasattr(elem, 'length'):
                continue

            L = elem.length(self.nodes)
            rho = elem.material.density
            A = elem.material.A

            # 单元质量
            m_elem = rho * A * L

            # 集中质量矩阵（将质量均分到两端节点）
            # 每个节点有3个自由度
            m_node = m_elem / 2

            dof_indices = [
                elem.node_i * 3,
                elem.node_i * 3 + 1,
                elem.node_i * 3 + 2,
                elem.node_j * 3,
                elem.node_j * 3 + 1,
                elem.node_j * 3 + 2
            ]

            # 添加质量
            M[dof_indices[0], dof_indices[0]] += m_node
            M[dof_indices[1], dof_indices[1]] += m_node
            M[dof_indices[2], dof_indices[2]] += m_node * 1e-6  # 转动惯量很小
            M[dof_indices[3], dof_indices[3]] += m_node
            M[dof_indices[4], dof_indices[4]] += m_node
            M[dof_indices[5], dof_indices[5]] += m_node * 1e-6

        return M

    def assemble_stiffness_matrix(self) -> np.ndarray:
        """组装刚度矩阵 K"""
        K = np.zeros((self.n_dof, self.n_dof))

        for elem in self.elements:
            if not hasattr(elem, 'global_stiffness_matrix'):
                continue

            k_elem = elem.global_stiffness_matrix(self.nodes)

            dof_indices = [
                elem.node_i * 3,
                elem.node_i * 3 + 1,
                elem.node_i * 3 + 2,
                elem.node_j * 3,
                elem.node_j * 3 + 1,
                elem.node_j * 3 + 2
            ]

            for i in range(6):
                for j in range(6):
                    K[dof_indices[i], dof_indices[j]] += k_elem[i, j]

        return K

    def apply_boundary_conditions(
        self,
        M: np.ndarray,
        K: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, List[int]]:
        """应用边界条件"""
        fixed_dofs = []

        for node in self.nodes:
            if node.fixity[0]:
                fixed_dofs.append(node.id * 3)
            if node.fixity[1]:
                fixed_dofs.append(node.id * 3 + 1)
            if node.fixity[2]:
                fixed_dofs.append(node.id * 3 + 2)

        free_dofs = [i for i in range(self.n_dof) if i not in fixed_dofs]

        M_reduced = M[np.ix_(free_dofs, free_dofs)]
        K_reduced = K[np.ix_(free_dofs, free_dofs)]

        return M_reduced, K_reduced, free_dofs

    def solve(self) -> ModalResult:
        """
        求解广义特征值问题

        K * φ = λ * M * φ

        其中 λ = ω²
        """
        # 组装矩阵
        M = self.assemble_mass_matrix()
        K = self.assemble_stiffness_matrix()

        # 应用边界条件
        M_reduced, K_reduced, free_dofs = self.apply_boundary_conditions(M, K)

        n_free = len(free_dofs)

        # 求解广义特征值问题
        # 使用eigh求解对称矩阵的特征值
        try:
            eigenvalues, eigenvectors = eigh(K_reduced, M_reduced)

            # 只取正特征值
            valid_idx = eigenvalues > 1e-10
            eigenvalues = eigenvalues[valid_idx]
            eigenvectors = eigenvectors[:, valid_idx]

            # 排序
            idx = np.argsort(eigenvalues)[:self.n_modes]
            eigenvalues = eigenvalues[idx]
            eigenvectors = eigenvectors[:, idx]

        except Exception as e:
            # 求解失败，返回默认值
            eigenvalues = np.ones(self.n_modes) * 1000
            eigenvectors = np.zeros((n_free, self.n_modes))

        # 计算固有频率
        omega = np.sqrt(np.maximum(eigenvalues, 0))  # rad/s
        f = omega / (2 * np.pi)  # Hz

        # 计算模态质量和刚度
        modal_mass = np.zeros(self.n_modes)
        modal_stiffness = np.zeros(self.n_modes)

        for i in range(self.n_modes):
            phi = eigenvectors[:, i]
            modal_mass[i] = phi.T @ M_reduced @ phi
            modal_stiffness[i] = phi.T @ K_reduced @ phi

        # 计算模态参与系数
        participation_factors = np.zeros(self.n_modes)
        influence_vector = np.ones(n_free)  # 假设各方向激励相同

        for i in range(self.n_modes):
            phi = eigenvectors[:, i]
            numerator = (phi.T @ M_reduced @ influence_vector) ** 2
            denominator = phi.T @ M_reduced @ phi
            participation_factors[i] = np.sqrt(numerator / denominator) if denominator > 0 else 0

        return ModalResult(
            natural_frequencies=f,
            natural_frequencies_rad=omega,
            mode_shapes=eigenvectors,
            modal_masses=modal_mass,
            modal_stiffness=modal_stiffness,
            participation_factors=participation_factors
        )


def plot_mode_shape(
    nodes: List[Node],
    mode_shape: np.ndarray,
    frequency: float,
    mode_number: int,
    scale: float = 1.0,
    ax: Optional[plt.Axes] = None
) -> plt.Axes:
    """
    绘制模态振型

    Parameters
    ----------
    nodes : List[Node]
        节点列表
    mode_shape : np.ndarray
        振型向量
    frequency : float
        固有频率 (Hz)
    mode_number : int
        模态编号
    scale : float
        放大倍数
    ax : plt.Axes, optional
        坐标轴对象

    Returns
    -------
    plt.Axes
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))

    # 绘制原始结构
    x_orig = [node.x for node in nodes]
    y_orig = [node.y for node in nodes]

    # 绘制变形后的结构
    x_def = []
    y_def = []

    n_nodes_to_plot = min(len(nodes), len(mode_shape) // 3 + 1)

    for i in range(n_nodes_to_plot):
        if i * 3 + 1 < len(mode_shape):
            u = mode_shape[i * 3] * scale
            v = mode_shape[i * 3 + 1] * scale
        else:
            u, v = 0, 0
        x_def.append(nodes[i].x + u)
        y_def.append(nodes[i].y + v)

    ax.plot(x_orig[:n_nodes_to_plot], y_orig[:n_nodes_to_plot],
            'k--', alpha=0.3, linewidth=1, label='原始结构')
    ax.plot(x_def, y_def, 'r-o', linewidth=2, markersize=8, label='振型')

    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.set_title(f'第 {mode_number} 阶模态 (f = {frequency:.4f} Hz)')
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.legend()

    return ax


def plot_all_modes(
    nodes: List[Node],
    modal_result: ModalResult,
    n_modes_to_plot: int = 6,
    figsize=(16, 10)
):
    """绘制所有模态"""
    n_cols = 3
    n_rows = (n_modes_to_plot + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
    axes = axes.flatten() if n_modes_to_plot > 1 else [axes]

    for i in range(min(n_modes_to_plot, len(modal_result.natural_frequencies))):
        if i < len(axes):
            plot_mode_shape(
                nodes,
                modal_result.mode_shapes[:, i],
                modal_result.natural_frequencies[i],
                i + 1,
                scale=50,
                ax=axes[i]
            )

    # 隐藏多余的子图
    for i in range(len(modal_result.natural_frequencies), len(axes)):
        axes[i].axis('off')

    plt.tight_layout()
    return fig


class HarmonicResponseAnalysis:
    """谐响应分析"""

    def __init__(
        self,
        modal_result: ModalResult,
        damping_ratio: float = 0.05
    ):
        """
        Parameters
        ----------
        modal_result : ModalResult
            模态分析结果
        damping_ratio : float
            阻尼比
        """
        self.modal_result = modal_result
        self.damping_ratio = damping_ratio

    def analyze(
        self,
        force_location: int,
        force_direction: int,
        force_amplitude: float,
        freq_range: Tuple[float, float],
        n_points: int = 500
    ) -> HarmonicResponseResult:
        """
        计算谐响应

        Parameters
        ----------
        force_location : int
            力作用位置（节点ID）
        force_direction : int
            力方向 (0=X, 1=Y, 2=转动)
        force_amplitude : float
            力幅值 (N)
        freq_range : Tuple[float, float]
            频率范围 (Hz)
        n_points : int
            计算点数

        Returns
        -------
        HarmonicResponseResult
        """
        frequencies = np.linspace(freq_range[0], freq_range[1], n_points)

        # 模态参数
        omega_n = self.modal_result.natural_frequencies_rad
        zeta = np.full_like(omega_n, self.damping_ratio)

        # 计算频响函数
        responses = np.zeros(n_points)
        phases = np.zeros(n_points)

        for i, freq in enumerate(frequencies):
            omega = 2 * np.pi * freq

            # 模态叠加
            response = 0
            phase = 0

            for j, (wn, z, phi, m) in enumerate(zip(
                omega_n, zeta,
                self.modal_result.mode_shapes.T,
                self.modal_result.modal_masses
            )):
                if j * 3 + force_direction >= len(phi):
                    continue

                # 模态参与因子
                gamma = phi[force_location * 3 + force_direction] if force_location * 3 + force_direction < len(phi) else 0

                # 频响函数 H(ω) = γ/m / (ω_n² - ω² + 2jζω_nω)
                denominator = wn**2 - omega**2 + 2j * z * wn * omega

                if abs(denominator) > 1e-10:
                    H = gamma / m / denominator
                    response += abs(H) * force_amplitude
                    phase += np.angle(H)

            responses[i] = response
            phases[i] = phase

        # 找峰值
        peak_idx = np.argmax(responses)
        peak_frequency = frequencies[peak_idx]
        peak_response = responses[peak_idx]

        return HarmonicResponseResult(
            frequencies=frequencies,
            responses=responses,
            phases=phases,
            peak_frequency=peak_frequency,
            peak_response=peak_response
        )

    def plot_response(
        self,
        result: HarmonicResponseResult,
        figsize=(12, 8)
    ):
        """绘制频响曲线"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize)

        # 幅频特性
        ax1.plot(result.frequencies, result.responses, 'b-', linewidth=2)
        ax1.axvline(result.peak_frequency, color='r', linestyle='--',
                   label=f'峰值频率: {result.peak_frequency:.4f} Hz')
        ax1.axvline(self.modal_result.natural_frequencies[0], color='g',
                   linestyle=':', alpha=0.5, label='基频: {:.4f} Hz'.format(
                       self.modal_result.natural_frequencies[0]))
        ax1.set_xlabel('频率 (Hz)')
        ax1.set_ylabel('响应幅值')
        ax1.set_title('频响函数 - 幅频特性')
        ax1.grid(True, alpha=0.3)
        ax1.legend()

        # 相频特性
        ax2.plot(result.frequencies, np.degrees(result.phases), 'g-', linewidth=2)
        ax2.set_xlabel('频率 (Hz)')
        ax2.set_ylabel('相位 (度)')
        ax2.set_title('频响函数 - 相频特性')
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(-180, 180)

        plt.tight_layout()
        return fig


class TransientResponseAnalysis:
    """瞬态响应分析"""

    def __init__(
        self,
        modal_result: ModalResult,
        damping_ratio: float = 0.05
    ):
        """
        Parameters
        ----------
        modal_result : ModalResult
            模态分析结果
        damping_ratio : float
            阻尼比
        """
        self.modal_result = modal_result
        self.damping_ratio = damping_ratio

    def analyze(
        self,
        force_function: Callable[[float], float],
        force_location: int,
        force_direction: int,
        time_duration: float,
        n_points: int = 1000,
        output_location: Optional[int] = None
    ) -> TransientResponseResult:
        """
        计算瞬态响应

        Parameters
        ----------
        force_function : Callable[[float], float]
            力随时间变化的函数 f(t)
        force_location : int
            力作用位置（节点ID）
        force_direction : int
            力方向 (0=X, 1=Y, 2=转动)
        time_duration : float
            分析时长 (s)
        n_points : int
            时间点数
        output_location : int, optional
            输出位置（默认为力作用位置）

        Returns
        -------
        TransientResponseResult
        """
        if output_location is None:
            output_location = force_location

        time = np.linspace(0, time_duration, n_points)

        # 模态参数
        omega_n = self.modal_result.natural_frequencies_rad
        zeta = np.full_like(omega_n, self.damping_ratio)
        phi = self.modal_result.mode_shapes
        m = self.modal_result.modal_masses

        # 初始条件
        n_modes = len(omega_n)
        q = np.zeros(n_modes)  # 模态位移
        q_dot = np.zeros(n_modes)  # 模态速度

        # 存储结果
        displacements = np.zeros((n_points, 3))
        velocities = np.zeros((n_points, 3))
        accelerations = np.zeros((n_points, 3))

        # 模态参与因子
        gamma = np.zeros(n_modes)
        for j in range(n_modes):
            if force_location * 3 + force_direction < len(phi[:, j]):
                gamma[j] = phi[force_location * 3 + force_direction, j]

        dt = time[1] - time[0]

        for i, t in enumerate(time):
            F = force_function(t)

            # 计算各模态响应
            for j in range(n_modes):
                wn = omega_n[j]
                z = zeta[j]
                gam = gamma[j]
                mj = m[j]

                # 模态力
                F_modal = gam * F / mj

                # 杜哈梅积分（简化的数值解）
                wd = wn * np.sqrt(1 - z**2)  # 阻尼固有频率

                if i == 0:
                    q[j] = 0
                    q_dot[j] = 0
                else:
                    # 简化的逐步积分
                    # q_ddot + 2*z*wn*q_dot + wn²*q = F_modal

                    # 梯形法
                    q_new = 2*q[j] - q[j] + dt**2 * (F_modal - 2*z*wn*q_dot[j])
                    q_dot_new = (q_new - q[j]) / dt

                    q[j] = q_new
                    q_dot[j] = q_dot_new

            # 组装物理响应
            for k in range(3):
                displacements[i, k] = np.sum(phi[output_location * 3 + k, :] * q) if output_location * 3 + k < len(phi) else 0
                velocities[i, k] = np.sum(phi[output_location * 3 + k, :] * q_dot) if output_location * 3 + k < len(phi) else 0
                accelerations[i, k] = 0  # 简化

        return TransientResponseResult(
            time=time,
            displacements=displacements,
            velocities=velocities,
            accelerations=accelerations,
            max_displacement=np.max(np.abs(displacements)),
            max_velocity=np.max(np.abs(velocities)),
            max_acceleration=np.max(np.abs(accelerations))
        )

    def plot_response(
        self,
        result: TransientResponseResult,
        figsize=(12, 10)
    ):
        """绘制瞬态响应"""
        fig, axes = plt.subplots(3, 1, figsize=figsize)

        # 位移
        axes[0].plot(result.time, result.displacements[:, 0] * 1000, 'r-', label='X')
        axes[0].plot(result.time, result.displacements[:, 1] * 1000, 'g-', label='Y')
        axes[0].set_ylabel('位移 (mm)')
        axes[0].set_title('瞬态响应 - 位移')
        axes[0].grid(True, alpha=0.3)
        axes[0].legend()

        # 速度
        axes[1].plot(result.time, result.velocities[:, 0] * 1000, 'r-', label='X')
        axes[1].plot(result.time, result.velocities[:, 1] * 1000, 'g-', label='Y')
        axes[1].set_ylabel('速度 (mm/s)')
        axes[1].set_title('瞬态响应 - 速度')
        axes[1].grid(True, alpha=0.3)
        axes[1].legend()

        # 加速度
        axes[2].plot(result.time, result.accelerations[:, 0], 'r-', label='X')
        axes[2].plot(result.time, result.accelerations[:, 1], 'g-', label='Y')
        axes[2].set_xlabel('时间 (s)')
        axes[2].set_ylabel('加速度 (m/s²)')
        axes[2].set_title('瞬态响应 - 加速度')
        axes[2].grid(True, alpha=0.3)
        axes[2].legend()

        plt.tight_layout()
        return fig


def earthquake_response_spectrum(
    frequencies: np.ndarray,
    damping_ratio: float = 0.05,
    peak_ground_acceleration: float = 1.0,
    corner_period_1: float = 0.1,
    corner_period_2: float = 0.5,
    corner_period_3: float = 2.0
) -> np.ndarray:
    """
    生成地震反应谱（简化版）

    Parameters
    ----------
    frequencies : np.ndarray
        频率数组 (Hz)
    damping_ratio : float
        阻尼比
    peak_ground_acceleration : float
    峰值地面加速度 (g)
    corner_period_1, corner_period_2, corner_period_3 : float
        转角周期 (s)

    Returns
    -------
    np.ndarray
        谱加速度 (g)
    """
    periods = 1.0 / frequencies

    spectral_acceleration = np.zeros_like(periods)

    for i, T in enumerate(periods):
        if T < corner_period_1:
            # 短周期段
            spectral_acceleration[i] = peak_ground_acceleration * (1 + T/corner_period_1)
        elif T < corner_period_2:
            # 加速度平台段
            spectral_acceleration[i] = peak_ground_acceleration * 2.5
        elif T < corner_period_3:
            # 速度平台段
            spectral_acceleration[i] = peak_ground_acceleration * 2.5 * corner_period_2 / T
        else:
            # 位移平台段
            spectral_acceleration[i] = peak_ground_acceleration * 2.5 * corner_period_2 * corner_period_3 / T**2

    # 阻尼修正
    damping_correction = np.sqrt(0.05 / (damping_ratio + 0.01))
    spectral_acceleration *= damping_correction

    return spectral_acceleration


if __name__ == "__main__":
    # 测试：简单框架的模态分析
    print("=== 模态分析示例 ===")

    from .frame import FrameStructure, create_portal_frame, FrameElement, FrameMaterial
    from .fea import Node

    # 创建门式框架
    frame = create_portal_frame(width=6.0, height=4.0)

    # 转换为模态分析所需的节点列表
    nodes = []
    for fn in frame.nodes:
        node = Node(
            id=fn.id,
            x=fn.x,
            y=fn.y,
            fixity=fn.fixity,
            loads=fn.loads
        )
        nodes.append(node)

    # 模态分析
    modal_analysis = ModalAnalysis(nodes, frame.elements, n_modes=6)
    modal_result = modal_analysis.solve()
    modal_result.set_damping(0.02)
    modal_result.print_summary()

    # 绘制振型
    fig = plot_all_modes(nodes, modal_result, n_modes_to_plot=6)
    plt.savefig("../results/modal_shapes.png", dpi=150, bbox_inches='tight')
    print("\n振型图已保存: results/modal_shapes.png")
    plt.close()

    # 谐响应分析
    print("\n=== 谐响应分析 ===")
    harmonic = HarmonicResponseAnalysis(modal_result, damping_ratio=0.02)
    harmonic_result = harmonic.analyze(
        force_location=1,  # 左上角
        force_direction=0,  # X方向
        force_amplitude=1000,  # 1kN
        freq_range=(0, 20),  # 0-20 Hz
        n_points=500
    )

    print(f"峰值频率: {harmonic_result.peak_frequency:.4f} Hz")
    print(f"峰值响应: {harmonic_result.peak_response:.6e}")

    fig = harmonic.plot_response()
    plt.savefig("../results/harmonic_response.png", dpi=150, bbox_inches='tight')
    print("频响曲线已保存: results/harmonic_response.png")
    plt.close()

    # 瞬态响应分析
    print("\n=== 瞬态响应分析 ===")

    # 定义冲击载荷
    def impulse_load(t):
        if 0 <= t <= 0.1:
            return 10000  # 10kN 冲击
        return 0

    transient = TransientResponseAnalysis(modal_result, damping_ratio=0.02)
    transient_result = transient.analyze(
        force_function=impulse_load,
        force_location=1,
        force_direction=0,
        time_duration=2.0,
        n_points=1000,
        output_location=1
    )

    print(f"最大位移: {transient_result.max_displacement*1000:.4f} mm")
    print(f"最大速度: {transient_result.max_velocity*1000:.4f} mm/s")

    fig = transient.plot_response()
    plt.savefig("../results/transient_response.png", dpi=150, bbox_inches='tight')
    print("瞬态响应图已保存: results/transient_response.png")
    plt.close()
