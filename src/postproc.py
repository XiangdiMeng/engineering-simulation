"""
后处理与可视化模块 (Post-Processing and Visualization)
提供应力云图、变形动画、结果报告生成等功能
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.tri as tri
from matplotlib.patches import Polygon, FancyArrowPatch
from matplotlib.collections import LineCollection, PolyCollection
from mpl_toolkits.mplot3d import Axes3D
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional, Union
from pathlib import Path
import json
from datetime import datetime

from .fea import Node, Element, FEAResults


@dataclass
class ContourData:
    """等值线数据"""
    x: np.ndarray
    y: np.ndarray
    values: np.ndarray
    triangles: Optional[np.ndarray] = None
    elements: Optional[List] = None


@dataclass
class AnimationConfig:
    """动画配置"""
    n_frames: int = 30
    duration: float = 3.0  # 秒
    fps: int = 10
    scale: float = 100


class StressContourPlot:
    """应力云图绘制"""

    def __init__(self, results: FEAResults):
        """
        Parameters
        ----------
        results : FEAResults
            有限元分析结果
        """
        self.results = results

    def create_contour_data(self) -> ContourData:
        """创建等值线数据"""
        x = np.array([node.x for node in self.results.nodes])
        y = np.array([node.y for node in self.results.nodes])

        # 计算节点应力（平均相邻单元应力）
        node_stresses = np.zeros(len(self.results.nodes))
        node_count = np.zeros(len(self.results.nodes))

        for elem_id, stress in self.results.stresses.items():
            if elem_id < len(self.results.elements):
                elem = self.results.elements[elem_id]
                node_stresses[elem.node_i] += abs(stress)
                node_stresses[elem.node_j] += abs(stress)
                node_count[elem.node_i] += 1
                node_count[elem.node_j] += 1

        # 避免除零
        node_count[node_count == 0] = 1
        node_stresses /= node_count

        # 创建三角网格
        if len(x) >= 3:
            triangulation = tri.Triangulation(x, y)
        else:
            triangulation = None

        return ContourData(
            x=x,
            y=y,
            values=node_stresses / 1e6,  # 转换为MPa
            triangles=triangulation.triangles if triangulation else None,
            elements=self.results.elements
        )

    def plot_stress_contour(
        self,
        figsize=(12, 8),
        cmap: str = 'jet',
        show_colorbar: bool = True,
        show_deformation: bool = False,
        deformation_scale: float = 50
    ) -> plt.Figure:
        """
        绘制应力云图

        Parameters
        ----------
        figsize : tuple
            图形大小
        cmap : str
            颜色映射
        show_colorbar : bool
            是否显示色标
        show_deformation : bool
            是否叠加变形
        deformation_scale : float
            变形放大倍数

        Returns
        -------
        plt.Figure
        """
        fig, ax = plt.subplots(figsize=figsize)

        contour_data = self.create_contour_data()

        # 计算坐标
        x = contour_data.x.copy()
        y = contour_data.y.copy()

        if show_deformation and len(self.results.displacements) > 0:
            # 叠加变形
            for i in range(len(x)):
                if i * 2 < len(self.results.displacements):
                    x[i] += self.results.displacements[i * 2] * deformation_scale / 1000
                if i * 2 + 1 < len(self.results.displacements):
                    y[i] += self.results.displacements[i * 2 + 1] * deformation_scale / 1000

        # 绘制等值线
        if contour_data.triangles is not None:
            x_plot = x if not show_deformation else contour_data.x
            y_plot = y if not show_deformation else contour_data.y

            if show_deformation:
                # 变形后的坐标
                for i in range(len(x_plot)):
                    if i * 2 < len(self.results.displacements):
                        x_plot = x_plot.copy()
                        x_plot[i] = contour_data.x[i] + self.results.displacements[i * 2] * deformation_scale / 1000
                    if i * 2 + 1 < len(self.results.displacements):
                        y_plot = y_plot.copy()
                        y_plot[i] = contour_data.y[i] + self.results.displacements[i * 2 + 1] * deformation_scale / 1000

            triangulation = tri.Triangulation(x_plot, y_plot, contour_data.triangles)

            tcf = ax.tripcolor(
                triangulation,
                contour_data.values,
                shading='gouraud',
                cmap=cmap,
                edgecolors='k',
                linewidth=0.5
            )
        else:
            # 使用散点图
            sc = ax.scatter(x, y, c=contour_data.values, cmap=cmap, s=100, edgecolors='k')
            tcf = sc

        # 添加色标
        if show_colorbar:
            cbar = plt.colorbar(tcf, ax=ax)
            cbar.set_label('应力 (MPa)', fontsize=12)

        # 添加节点编号
        for node in self.results.nodes:
            ax.text(node.x, node.y, str(node.id),
                   fontsize=8, ha='center', va='bottom',
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.7))

        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        title = '应力云图'
        if show_deformation:
            title += f' (变形放大{deformation_scale}倍)'
        ax.set_title(title)
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')

        return fig

    def plot_displacement_contour(
        self,
        figsize=(12, 8),
        cmap: str = 'viridis',
        component: str = 'magnitude'  # 'magnitude', 'x', 'y'
    ) -> plt.Figure:
        """
        绘制位移云图

        Parameters
        ----------
        figsize : tuple
            图形大小
        cmap : str
            颜色映射
        component : str
            位移分量 ('magnitude', 'x', 'y')

        Returns
        -------
        plt.Figure
        """
        fig, ax = plt.subplots(figsize=figsize)

        x = np.array([node.x for node in self.results.nodes])
        y = np.array([node.y for node in self.results.nodes])

        # 计算位移值
        displacements = self.results.displacements
        values = np.zeros(len(self.results.nodes))

        for i in range(len(self.results.nodes)):
            if i * 2 + 1 < len(displacements):
                if component == 'magnitude':
                    values[i] = np.sqrt(displacements[i * 2]**2 + displacements[i * 2 + 1]**2)
                elif component == 'x':
                    values[i] = abs(displacements[i * 2])
                elif component == 'y':
                    values[i] = abs(displacements[i * 2 + 1])

        values *= 1000  # 转换为mm

        # 创建三角网格
        if len(x) >= 3:
            triangulation = tri.Triangulation(x, y)
            tcf = ax.tripcolor(
                triangulation,
                values,
                shading='gouraud',
                cmap=cmap,
                edgecolors='k',
                linewidth=0.5
            )

            plt.colorbar(tcf, ax=ax, label='位移 (mm)')
        else:
            sc = ax.scatter(x, y, c=values, cmap=cmap, s=100, edgecolors='k')
            plt.colorbar(sc, ax=ax, label='位移 (mm)')

        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        ax.set_title(f'位移云图 ({component})')
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')

        return fig


class DeformationAnimation:
    """变形动画"""

    def __init__(self, results: FEAResults):
        """
        Parameters
        ----------
        results : FEAResults
            有限元分析结果
        """
        self.results = results

    def create_animation(
        self,
        config: AnimationConfig = AnimationConfig(),
        mode: str = 'vibration',  # 'vibration', 'static'
        output_path: Optional[str] = None
    ) -> List[plt.Figure]:
        """
        创建变形动画（返回一系列帧）

        Parameters
        ----------
        config : AnimationConfig
            动画配置
        mode : str
            动画模式 ('vibration'=振动, 'static'=静态变形)
        output_path : str, optional
            保存路径

        Returns
        -------
        List[plt.Figure]
            帧列表
        """
        frames = []

        # 获取变形数据
        if mode == 'vibration':
            # 振动模式 - 正弦变化
            t_values = np.linspace(0, 2 * np.pi, config.n_frames)
        else:
            # 静态变形 - 逐渐加载
            t_values = np.linspace(0, 1, config.n_frames)

        for frame_idx, t in enumerate(t_values):
            fig, ax = plt.subplots(figsize=(10, 8))

            # 计算当前帧的变形
            if mode == 'vibration':
                scale_factor = np.sin(t) * config.scale
            else:
                scale_factor = t * config.scale

            # 绘制原始结构（虚线）
            for elem in self.results.elements:
                if hasattr(elem, 'node_i') and hasattr(elem, 'node_j'):
                    ni, nj = self.results.nodes[elem.node_i], self.results.nodes[elem.node_j]
                    ax.plot([ni.x, nj.x], [ni.y, nj.y], 'k--', alpha=0.3, linewidth=1)

            # 绘制变形后的结构
            x_def = []
            y_def = []

            for i, node in enumerate(self.results.nodes):
                if i * 2 + 1 < len(self.results.displacements):
                    u = self.results.displacements[i * 2] * scale_factor / 100
                    v = self.results.displacements[i * 2 + 1] * scale_factor / 100
                else:
                    u, v = 0, 0
                x_def.append(node.x + u)
                y_def.append(node.y + v)

            for elem in self.results.elements:
                if hasattr(elem, 'node_i') and hasattr(elem, 'node_j'):
                    ni_idx, nj_idx = elem.node_i, elem.node_j
                    ax.plot([x_def[ni_idx], x_def[nj_idx]], [y_def[ni_idx], y_def[nj_idx]],
                           'b-o', linewidth=2, markersize=8)

            ax.set_aspect('equal')
            ax.grid(True, alpha=0.3)
            ax.set_title(f'变形动画 - 帧 {frame_idx + 1}/{config.n_frames}')
            ax.set_xlabel('X (m)')
            ax.set_ylabel('Y (m)')

            frames.append(fig)

        # 保存为GIF（如果有imageio）
        if output_path:
            try:
                import imageio
                images = []
                for fig in frames:
                    fig.canvas.draw()
                    import io
                    buf = io.BytesIO()
                    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
                    buf.seek(0)
                    from PIL import Image
                    images.append(Image.open(buf))
                    plt.close(fig)

                images[0].save(
                    output_path,
                    save_all=True,
                    append_images=images[1:],
                    duration=config.duration * 1000 / config.n_frames,
                    loop=0
                )
                print(f"动画已保存: {output_path}")
            except ImportError:
                print("警告: 需要安装 imageio 和 PIL 才能保存GIF动画")

        return frames


class ResultReporter:
    """结果报告生成器"""

    def __init__(self, results: FEAResults, metadata: Optional[Dict] = None):
        """
        Parameters
        ----------
        results : FEAResults
            有限元分析结果
        metadata : Dict, optional
            额外的元数据
        """
        self.results = results
        self.metadata = metadata or {}

    def generate_summary(self) -> str:
        """生成文字摘要"""
        lines = []
        lines.append("="*60)
        lines.append("有限元分析结果报告")
        lines.append("="*60)
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 元数据
        if self.metadata:
            lines.append("\n分析参数:")
            for key, value in self.metadata.items():
                lines.append(f"  {key}: {value}")

        # 模型信息
        lines.append(f"\n模型信息:")
        lines.append(f"  节点数: {len(self.results.nodes)}")
        lines.append(f"  单元数: {len(self.results.elements)}")

        # 位移统计
        if len(self.results.displacements) > 0:
            max_disp = np.max(np.abs(self.results.displacements))
            min_disp = np.min(np.abs(self.results.displacements))
            lines.append(f"\n位移统计:")
            lines.append(f"  最大位移: {max_disp*1000:.4f} mm")
            lines.append(f"  最小位移: {min_disp*1000:.4f} mm")

            # 节点位移详情
            lines.append(f"\n节点位移详情:")
            for i, node in enumerate(self.results.nodes):
                if i * 2 + 1 < len(self.results.displacements):
                    u = self.results.displacements[i * 2] * 1000
                    v = self.results.displacements[i * 2 + 1] * 1000
                    if abs(u) > 0.01 or abs(v) > 0.01:
                        lines.append(f"  节点 {i}: u={u:.3f}mm, v={v:.3f}mm")

        # 应力统计
        if self.results.stresses:
            stresses = np.array(list(self.results.stresses.values())) / 1e6
            lines.append(f"\n应力统计:")
            lines.append(f"  最大应力: {np.max(stresses):.2f} MPa")
            lines.append(f"  最小应力: {np.min(stresses):.2f} MPa")
            lines.append(f"  平均应力: {np.mean(stresses):.2f} MPa")

        # 单元内力
        if self.results.element_forces:
            lines.append(f"\n单元内力:")
            for elem_id, force in self.results.element_forces.items():
                lines.append(f"  单元 {elem_id}: {force/1000:.2f} kN")

        # 支座反力
        if self.results.reactions:
            lines.append(f"\n支座反力:")
            for node_id, reaction in self.results.reactions.items():
                rx, ry = reaction
                lines.append(f"  节点 {node_id}: Rx={rx/1000:.2f}kN, Ry={ry/1000:.2f}kN")

        lines.append("="*60)

        return "\n".join(lines)

    def save_json(self, filepath: str):
        """保存为JSON格式"""
        data = {
            'metadata': self.metadata,
            'timestamp': datetime.now().isoformat(),
            'nodes': [
                {
                    'id': node.id,
                    'x': node.x,
                    'y': node.y,
                    'fixity': node.fixity
                }
                for node in self.results.nodes
            ],
            'elements': [
                {
                    'id': elem.id,
                    'node_i': elem.node_i,
                    'node_j': elem.node_j
                }
                for elem in self.results.elements
            ],
            'displacements': self.results.displacements.tolist(),
            'stresses': {k: v for k, v in self.results.stresses.items()},
            'reactions': {k: v for k, v in self.results.reactions.items()},
            'element_forces': {k: v for k, v in self.results.element_forces.items()}
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"结果已保存到: {filepath}")

    def generate_html_report(
        self,
        filepath: str,
        include_plots: bool = True
    ):
        """生成HTML报告"""
        html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>有限元分析报告</title>
    <style>
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            margin: 40px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            margin-top: 30px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #3498db;
            color: white;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .metric {
            display: inline-block;
            margin: 10px 20px 10px 0;
            padding: 15px;
            background-color: #ecf0f1;
            border-radius: 5px;
            min-width: 150px;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }
        .metric-label {
            color: #7f8c8d;
            font-size: 14px;
        }
        .plot-placeholder {
            background-color: #ecf0f1;
            padding: 20px;
            text-align: center;
            border-radius: 5px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>有限元分析报告</h1>
        <p>生成时间: {timestamp}</p>

        <h2>分析参数</h2>
        <table>
            <tr><th>参数</th><th>值</th></tr>
            {metadata_rows}
        </table>

        <h2>模型信息</h2>
        <div class="metric">
            <div class="metric-value">{n_nodes}</div>
            <div class="metric-label">节点数</div>
        </div>
        <div class="metric">
            <div class="metric-value">{n_elements}</div>
            <div class="metric-label">单元数</div>
        </div>

        <h2>位移结果</h2>
        <div class="metric">
            <div class="metric-value">{max_disp:.4f} mm</div>
            <div class="metric-label">最大位移</div>
        </div>

        <h2>应力结果</h2>
        <div class="metric">
            <div class="metric-value">{max_stress:.2f} MPa</div>
            <div class="metric-label">最大应力</div>
        </div>

        <h2>支座反力</h2>
        <table>
            <tr><th>节点</th><th>Rx (kN)</th><th>Ry (kN)</th></tr>
            {reaction_rows}
        </table>

        {plots_section}
    </div>
</body>
</html>
"""
        # 填充数据
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 元数据行
        metadata_rows = ""
        for key, value in self.metadata.items():
            metadata_rows += f"<tr><td>{key}</td><td>{value}</td></tr>"

        # 模型信息
        n_nodes = len(self.results.nodes)
        n_elements = len(self.results.elements)

        # 位移
        max_disp = np.max(np.abs(self.results.displacements)) * 1000 if len(self.results.displacements) > 0 else 0

        # 应力
        if self.results.stresses:
            max_stress = np.max(np.abs(list(self.results.stresses.values()))) / 1e6
        else:
            max_stress = 0

        # 支座反力行
        reaction_rows = ""
        for node_id, (rx, ry) in self.results.reactions.items():
            reaction_rows += f"<tr><td>{node_id}</td><td>{rx/1000:.2f}</td><td>{ry/1000:.2f}</td></tr>"

        # 图表区域
        plots_section = ""
        if include_plots:
            plots_section = """
            <h2>结果图表</h2>
            <div class="plot-placeholder">
                <p>应力云图和变形图请查看PNG文件</p>
            </div>
            """

        html_content = html_content.format(
            timestamp=timestamp,
            metadata_rows=metadata_rows,
            n_nodes=n_nodes,
            n_elements=n_elements,
            max_disp=max_disp,
            max_stress=max_stress,
            reaction_rows=reaction_rows,
            plots_section=plots_section
        )

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"HTML报告已保存到: {filepath}")


def plot_combined_results(
    results: FEAResults,
    figsize=(16, 12),
    save_path: Optional[str] = None
) -> plt.Figure:
    """
    绘制综合结果图

    Parameters
    ----------
    results : FEAResults
        有限元分析结果
    figsize : tuple
        图形大小
    save_path : str, optional
        保存路径

    Returns
    -------
    plt.Figure
    """
    fig = plt.figure(figsize=figsize)
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

    # 1. 结构简图
    ax1 = fig.add_subplot(gs[0, 0])
    for elem in results.elements:
        if hasattr(elem, 'node_i') and hasattr(elem, 'node_j'):
            ni, nj = results.nodes[elem.node_i], results.nodes[elem.node_j]
            ax1.plot([ni.x, nj.x], [ni.y, nj.y], 'b-o', linewidth=2, markersize=8)

    # 绘制支座
    for node in results.nodes:
        if node.fixity[0] or node.fixity[1]:
            ax1.plot(node.x, node.y, '^', markersize=15, color='red', zorder=5)

    ax1.set_aspect('equal')
    ax1.grid(True, alpha=0.3)
    ax1.set_title('结构简图')
    ax1.set_xlabel('X (m)')
    ax1.set_ylabel('Y (m)')

    # 2. 变形图
    ax2 = fig.add_subplot(gs[0, 1])
    scale = 100
    for elem in results.elements:
        if hasattr(elem, 'node_i') and hasattr(elem, 'node_j'):
            ni, nj = results.nodes[elem.node_i], results.nodes[elem.node_j]

            # 原始结构（虚线）
            ax2.plot([ni.x, nj.x], [ni.y, nj.y], 'k--', alpha=0.3, linewidth=1)

            # 变形后的结构
            if elem.node_i * 2 + 1 < len(results.displacements):
                u_i = results.displacements[elem.node_i * 2] * scale / 1000
                v_i = results.displacements[elem.node_i * 2 + 1] * scale / 1000
            else:
                u_i, v_i = 0, 0

            if elem.node_j * 2 + 1 < len(results.displacements):
                u_j = results.displacements[elem.node_j * 2] * scale / 1000
                v_j = results.displacements[elem.node_j * 2 + 1] * scale / 1000
            else:
                u_j, v_j = 0, 0

            ax2.plot([ni.x + u_i, nj.x + u_j], [ni.y + v_i, nj.y + v_j],
                    'r-', linewidth=2)

    ax2.set_aspect('equal')
    ax2.grid(True, alpha=0.3)
    ax2.set_title(f'变形图 (放大{scale}倍)')
    ax2.set_xlabel('X (m)')
    ax2.set_ylabel('Y (m)')

    # 3. 应力分布
    ax3 = fig.add_subplot(gs[1, :])
    if results.stresses:
        elem_ids = list(results.stresses.keys())
        stresses = np.array(list(results.stresses.values())) / 1e6
        colors = ['red' if s > 0 else 'blue' for s in stresses]

        bars = ax3.bar(elem_ids, stresses, color=colors, alpha=0.7)
        ax3.axhline(0, color='k', linestyle='--', linewidth=1)
        ax3.set_xlabel('单元编号')
        ax3.set_ylabel('应力 (MPa)')
        ax3.set_title('单元应力分布')
        ax3.grid(True, alpha=0.3, axis='y')

        for bar in bars:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}',
                    ha='center', va='bottom' if height > 0 else 'top', fontsize=8)

    # 4. 位移向量图
    ax4 = fig.add_subplot(gs[2, 0])
    x = [node.x for node in results.nodes]
    y = [node.y for node in results.nodes]

    # 绘制结构
    for elem in results.elements:
        if hasattr(elem, 'node_i') and hasattr(elem, 'node_j'):
            ni, nj = results.nodes[elem.node_i], results.nodes[elem.node_j]
            ax4.plot([ni.x, nj.x], [ni.y, nj.y], 'k-', alpha=0.3, linewidth=1)

    # 绘制位移向量
    for i, node in enumerate(results.nodes):
        if i * 2 + 1 < len(results.displacements):
            u = results.displacements[i * 2]
            v = results.displacements[i * 2 + 1]
            if abs(u) > 1e-6 or abs(v) > 1e-6:
                ax4.arrow(node.x, node.y, u, v,
                         head_width=0.1, head_length=0.05,
                         fc='red', ec='red', linewidth=2)

    ax4.set_aspect('equal')
    ax4.grid(True, alpha=0.3)
    ax4.set_title('位移向量')
    ax4.set_xlabel('X (m)')
    ax4.set_ylabel('Y (m)')

    # 5. 统计信息
    ax5 = fig.add_subplot(gs[2, 1])
    ax5.axis('off')

    if len(results.displacements) > 0:
        max_disp = np.max(np.abs(results.displacements)) * 1000
    else:
        max_disp = 0

    if results.stresses:
        max_stress = np.max(np.abs(list(results.stresses.values()))) / 1e6
        min_stress = np.min(list(results.stresses.values())) / 1e6
    else:
        max_stress = 0
        min_stress = 0

    stats_text = f"""
    统计摘要

    节点数: {len(results.nodes)}
    单元数: {len(results.elements)}

    最大位移: {max_disp:.4f} mm
    最大应力: {max_stress:.2f} MPa
    最小应力: {min_stress:.2f} MPa

    支座反力:
    """

    for node_id, (rx, ry) in results.reactions.items():
        stats_text += f"\n    节点 {node_id}: ({rx/1000:.2f}, {ry/1000:.2f}) kN"

    ax5.text(0.1, 0.9, stats_text, transform=ax5.transAxes,
            fontsize=12, verticalalignment='top', fontfamily='monospace')

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"综合结果图已保存: {save_path}")

    return fig


if __name__ == "__main__":
    # 测试：创建示例结果并生成报告
    from .fea import FEModel, FEMaterial
    from .materials import Steel

    print("=== 后处理与可视化测试 ===")

    # 创建简单模型
    model = FEModel(name="Test")
    model.add_node(0, 0, fixity=(True, True, False))
    model.add_node(1, 0, fixity=(False, True, False))
    model.add_node(0.5, 1, fixity=(False, False, False), loads=(0, -10000, 0))

    material = FEMaterial("Test", E=200e9, A=0.001, density=7850)
    model.add_truss_element(0, 2, material)
    model.add_truss_element(1, 2, material)
    model.add_truss_element(0, 1, material)

    results = model.solve()

    # 生成报告
    reporter = ResultReporter(results, metadata={'载荷': '10kN', '材料': 'Q345'})
    print(reporter.generate_summary())

    # 绘制综合结果
    fig = plot_combined_results(results, save_path="../results/combined_results.png")
    plt.close()

    # 绘制应力云图
    contour_plot = StressContourPlot(results)
    fig = contour_plot.plot_stress_contour()
    plt.savefig("../results/stress_contour.png", dpi=150, bbox_inches='tight')
    print("应力云图已保存: results/stress_contour.png")
    plt.close()
