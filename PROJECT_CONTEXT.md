# Engineering Simulation Toolkit - Project Context

> 本文档用于让AI快速理解此工程仿真工具包项目的结构、功能和代码风格

---

## 项目概述

**项目名称**: Engineering Simulation Toolkit (工程仿真工具包)
**语言**: Python 3.x
**用途**: 机械/结构工程的有限元分析和动态仿真

**核心功能**:
- 梁结构分析 (弯矩、剪力、挠度)
- 桁架结构分析 (静定/超静定)
- 框架结构分析 (考虑弯矩+剪力+轴力耦合)
- 柱稳定性分析 (欧拉屈曲)
- 动力学分析 (模态、谐响应、瞬态响应)
- 后处理可视化 (应力云图、变形动画)
- 实际工程应用 (阳台、篮球架、桥梁等)

---

## 项目结构

```
engineering-simulation/
├── src/                          # 核心模块
│   ├── __init__.py
│   ├── materials.py              # 材料库 (钢材、混凝土、铝材等)
│   ├── fea.py                    # 有限元框架基类
│   ├── beam_analysis.py          # 梁分析 (简支梁、悬臂梁)
│   ├── truss.py                  # 桁架分析
│   ├── frame.py                  # 框架结构分析
│   ├── stability.py              # 稳定性分析 (欧拉屈曲)
│   ├── dynamics.py               # 动力学分析 (模态、谐响应、瞬态)
│   ├── postproc.py               # 后处理和可视化
│   └── combined.py               # 组合结构和模板
│
├── tests/                        # 单元测试
│   ├── run_all_tests.py          # 运行所有测试
│   └── test_*.py                 # 各模块测试
│
├── examples/                     # 示例程序
│   ├── quick_start.py            # 快速入门
│   └── *.py                      # 各类示例
│
├── *.py                          # 主要仿真脚本
│   ├── bridge_sim.py             # 桥梁车辆振动分析
│   ├── basketball_sim.py         # 篮球扣篮动态模拟
│   ├── bball_viz.py              # 篮球架可视化
│   ├── create_animation.py       # 动画生成
│   └── balcony_design_report.py  # 阳台设计分析
│
├── results/                      # 输出结果 (图片、GIF等)
│
├── USAGE.md                      # 使用文档
├── PROJECT_CONTEXT.md            # 本文档 - AI上下文
└── README.md                     # 项目说明
```

---

## 核心模块说明

### 1. materials.py - 材料库
```python
# 使用方式
from src.materials import Material, get_material

steel = Material(name="Q235钢", E=200e9, yield_strength=235e6, density=7850)
concrete = Material.concrete_grade("C30")
```

### 2. beam_analysis.py - 梁分析
```python
from src.beam_analysis import Beam, SimpleSupport, Cantilever, FixedFixed

beam = Beam(length=6.0, E=200e9, I=8.33e-5)
beam.add_point_load(force=10000, position=3.0)
results = beam.analyze()
```

### 3. truss.py - 桁架分析
```python
from src.truss import TrussStructure, TrussNode, TrussElement

truss = TrussStructure()
truss.add_node(0, 0, fixity="fixed")
truss.add_node(3, 0, fixity="pinned")
truss.add_element(0, 1, area=0.001, E=200e9)
truss.solve()
```

### 4. frame.py - 框架结构
```python
from src.frame import FrameStructure, FrameNode, FrameElement

frame = FrameStructure()
frame.add_node(0, 0, fixity="fixed")
frame.add_node(3, 0, fixity="free")
frame.add_beam_element(0, 1, section, material)
frame.solve()
```

### 5. dynamics.py - 动力学分析
```python
from src.dynamics import ModalAnalysis

modal = ModalAnalysis(nodes, elements, n_modes=5)
results = modal.solve()
results.print_summary()
```

---

## 代码风格约定

### 命名规范
- **类名**: PascalCase (例: `BeamElement`, `ModalAnalysis`)
- **函数/方法**: snake_case (例: `add_node`, `solve`)
- **常量**: UPPER_CASE (例: `E_MODULUS`, `SPAN`)
- **私有方法**: 前缀下划线 (例: `_assemble_k_matrix`)

### 单位约定 (SI)
- 长度: 米 (m)
- 力: 牛顿 (N)
- 应力: 帕斯卡 (Pa) 或 MPa (1e6 Pa)
- 质量: 千克 (kg)
- 时间: 秒 (s)

### 文档字符串
```python
def calculate_deflection(self, x: float) -> float:
    """计算梁在位置x处的挠度

    Args:
        x: 计算位置 (m)

    Returns:
        挠度值 (m), 向下为正
    """
```

---

## 常见模式

### 1. 导入路径
```python
# 脚本文件 (根目录运行)
import sys
sys.path.insert(0, 'src')
from src.materials import Material

# 模块间导入 (src/目录内)
from .materials import Material
from .fea import Node, Element
```

### 2. 绘图通用设置
```python
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch

fig, axes = plt.subplots(figsize=(12, 8))
ax.set_xlabel('X Label')
ax.set_ylabel('Y Label')
ax.set_title('Title', fontweight='bold')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('results/output.png', dpi=150, bbox_inches='tight')
```

### 3. 数据类 (dataclass)
```python
from dataclasses import dataclass

@dataclass
class AnalysisResult:
    max_displacement: float
    max_stress: float
    safety_factor: float
    passed: bool
```

---

## 重要注意事项

### 已知问题和解决方案
1. **相对导入**: 脚本直接运行时用 `sys.path.insert(0, 'src')`，模块内用 `from .xxx`
2. **Matplotlib颜色**: 不要同时使用格式字符串和 `color=` 参数
3. **FFT维度**: 确保频率数组长度与FFT结果长度一致
4. **f-string**: 嵌套引号使用不同类型，避免冲突

### 避免的常见错误
```python
# 错误 ❌
ax.plot(..., 'ro-', color='blue')  # 颜色冲突
f"Value {[r['x'] for r in results]:.2f}"  # 不能格式化列表

# 正确 ✅
ax.plot(..., 'o-', color='blue')
max_val = max([r['x'] for r in results])
f"Value: {max_val:.2f}"
```

---

## 输出文件约定

- 静态图片: `results/xxx.png` (dpi=150)
- 动画GIF: `results/xxx.gif` (fps=15-20, dpi=80)
- 关键帧: `results/xxx_frame_NN.png` (按顺序编号)

---

## 给AI的提示词模板

当在此项目上工作时，AI应该：

1. **首先了解需求**: 询问用户想分析什么结构
2. **检查现有模块**: 查看 `src/` 是否已有相关功能
3. **遵循代码风格**: 使用snake_case、dataclass、类型提示
4. **运行测试**: 修改后运行 `python tests/run_all_tests.py`
5. **生成可视化**: 结果应保存到 `results/` 目录
6. **处理单位**: 默认使用SI单位 (米、牛顿、帕斯卡)

---

## 项目历史 (重要决策)

### 2026-03-02 里程碑
- 完成了框架、稳定性、动力学、后处理模块
- 实现了阳台设计、篮球架、桥梁等实际应用
- 修复了多个f-string、颜色、FFT维度等bug
- 删除了有缺陷的 `bridge_vehicle.py`，保留 `bridge_sim.py`

### 架构决策
- 使用 `dataclass` 定义数据结构
- 继承 `fea.Element` 实现不同单元类型
- 可视化与计算分离，便于复用

---

## 快速开始示例

```python
# 运行桥梁仿真
python bridge_sim.py

# 运行篮球扣篮仿真
python basketball_sim.py

# 运行所有测试
python tests/run_all_tests.py
```

---

*最后更新: 2026-03-02*
*维护者: Claude (Anthropic)*
