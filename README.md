# 工程仿真项目 (Engineering Simulation)

Python 机械/结构工程仿真工具包 v0.2.0

## 功能特性

### 核心模块
- ✅ **材料属性** - 钢、铝合金、混凝土等常用工程材料
- ✅ **梁结构分析** - 简支梁、悬臂梁、外伸梁
- ✅ **有限元分析** - 桁架单元、刚度矩阵、求解器
- ✅ **桁架结构** - 屋顶桁架、桥梁桁架

### 扩展模块 (新增)
- ✅ **框架结构分析** - 梁单元(考虑弯矩、剪力、轴力耦合)
- ✅ **稳定性分析** - 欧拉屈曲、特征值屈曲、长细比计算
- ✅ **动力学分析** - 模态分析、谐响应、瞬态响应
- ✅ **后处理可视化** - 应力云图、变形动画、结果报告
- ✅ **组合结构** - 参数化建模、斜拉桥、拱桥、多层框架

### 工程应用
- 🏗️ 门式框架
- 🏢 多层建筑框架
- 🌉 斜拉桥
- ⛪ 拱桥
- 🏗️ 空间网架
- 📐 参数化设计

## 安装

### 环境要求
- Python 3.9+
- NumPy
- SciPy
- Matplotlib

### 安装依赖

```bash
pip install -r requirements.txt
```

## 快速开始

### 示例 1: 简支梁分析

```python
from src.beam_analysis import SimplySupportedBeam
from src.materials import Steel

# 创建简支梁
beam = SimplySupportedBeam(
    length=5.0,           # 长度 (m)
    width=0.1,            # 宽度 (m)
    height=0.2,           # 高度 (m)
    material=Steel("Q345")
)

# 施加集中载荷
beam.add_point_load(force=50000, position=2.5)

# 计算结果
results = beam.analyze()
print(f"最大挠度: {results.max_deflection*1000:.2f} mm")
print(f"安全系数: {results.safety_factor:.2f}")
```

### 示例 2: 框架结构分析

```python
from src.frame import create_portal_frame

# 创建门式框架
frame = create_portal_frame(
    width=8.0,
    height=5.0,
    section_width=0.25,
    section_height=0.4
)

# 施加载荷
frame.nodes[1].loads = (5000, 0, 0)  # 水平力 5kN
frame.nodes[2].loads = (0, -20000, 0)  # 垂直力 20kN

# 求解
results = frame.solve()
results.print_summary()
results.plot()
```

### 示例 3: 桁架结构

```python
from src.truss import create_roof_truss, analyze_truss_performance

# 创建屋顶桁架
truss = create_roof_truss(
    span=12.0,
    height=3.0,
    n_bays=6,
    snow_load=2000
)

# 分析
analysis = analyze_truss_performance(truss)
```

### 示例 4: 稳定性分析

```python
from src.stability import euler_buckling_analysis, ColumnSection, BoundaryCondition
from src.materials import Steel

# 创建柱截面
section = ColumnSection(
    A=0.01,           # 面积 (m²)
    Ix=8.33e-5,       # 惯性矩 (m⁴)
    Iy=8.33e-5
)

# 边界条件
bc = BoundaryCondition(fix_start_x=True, fix_start_y=True,
                       fix_end_x=True, fix_end_y=True)

# 屈曲分析
steel = Steel("Q345")
result = euler_buckling_analysis(4.0, steel, section, 100000, bc)

print(f"临界载荷: {result.critical_load/1000:.2f} kN")
print(f"长细比: {result.slenderness_ratio:.1f}")
```

### 示例 5: 模态分析

```python
from src.dynamics import ModalAnalysis, plot_all_modes

# 模态分析
modal = ModalAnalysis(nodes, elements, n_modes=6)
modal_result = modal.solve()
modal_result.print_summary()

# 绘制振型
fig = plot_all_modes(nodes, modal_result, n_modes_to_plot=6)
```

### 示例 6: 参数化建模

```python
from src.combined import ParametricStructure

# 参数化创建门式框架
param_frame = ParametricStructure("portal_frame")
param_frame.set_parameters(
    width=6.0,
    height=4.0,
    section_width=0.2,
    section_height=0.3
)

structure = param_frame.generate()
results = structure.solve()
```

## 项目结构

```
engineering-simulation/
├── src/                        # 源代码
│   ├── __init__.py            # 包初始化
│   ├── materials.py           # 材料属性
│   ├── beam_analysis.py       # 梁分析
│   ├── fea.py                 # 有限元分析
│   ├── truss.py               # 桁架结构
│   ├── frame.py               # 框架结构 [新增]
│   ├── stability.py           # 稳定性分析 [新增]
│   ├── dynamics.py            # 动力学分析 [新增]
│   ├── postproc.py            # 后处理可视化 [新增]
│   └── combined.py            # 组合结构 [新增]
├── tests/                      # 单元测试
│   ├── test_materials.py
│   ├── test_beam_analysis.py
│   ├── test_fea.py
│   └── run_tests.py
├── examples/                   # 示例代码
├── data/                       # 输入数据
├── results/                    # 仿真结果
└── requirements.txt            # 依赖列表
```

## API 文档

### 材料模块 (`materials`)

| 类/函数 | 描述 |
|---------|------|
| `Material` | 材料基类 |
| `Steel(grade)` | 结构钢 (Q235, Q345, 45#) |
| `Aluminum(alloy)` | 铝合金 (6061-T6, 7075-T6) |
| `Concrete(grade)` | 混凝土 (C30, C40, C50) |
| `safety_factor(material, stress)` | 计算安全系数 |

### 梁分析 (`beam_analysis`)

| 类 | 描述 |
|-----|------|
| `SimplySupportedBeam` | 简支梁 |
| `CantileverBeam` | 悬臂梁 |
| `BeamResults` | 分析结果类 |

### 有限元 (`fea`)

| 类 | 描述 |
|-----|------|
| `FEModel` | 有限元模型 |
| `TrussElement` | 桁架单元 |
| `FEMaterial` | 有限元材料 |
| `FEAResults` | 分析结果 |

### 框架结构 (`frame`)

| 类/函数 | 描述 |
|---------|------|
| `FrameStructure` | 框架结构类 |
| `FrameElement` | 框架单元 |
| `Section` | 截面类 |
| `create_portal_frame()` | 创建门式框架 |
| `create_cantilever_frame()` | 创建悬臂框架 |

### 稳定性 (`stability`)

| 类/函数 | 描述 |
|---------|------|
| `euler_buckling_analysis()` | 欧拉屈曲分析 |
| `ColumnSection` | 柱截面 |
| `BoundaryCondition` | 边界条件 |
| `aisc_allowable_stress()` | AISC允许应力 |

### 动力学 (`dynamics`)

| 类 | 描述 |
|-----|------|
| `ModalAnalysis` | 模态分析 |
| `HarmonicResponseAnalysis` | 谐响应分析 |
| `TransientResponseAnalysis` | 瞬态响应分析 |

### 后处理 (`postproc`)

| 类 | 描述 |
|-----|------|
| `StressContourPlot` | 应力云图 |
| `DeformationAnimation` | 变形动画 |
| `ResultReporter` | 结果报告 |

### 组合结构 (`combined`)

| 类/函数 | 描述 |
|---------|------|
| `ParametricStructure` | 参数化结构 |
| `create_cable_stayed_bridge()` | 斜拉桥 |
| `create_arch_bridge()` | 拱桥 |
| `create_multistory_frame()` | 多层框架 |

## 测试

运行单元测试:

```bash
cd tests
python run_tests.py
```

## 许可证

MIT License

## 作者

Xiangdi Meng
