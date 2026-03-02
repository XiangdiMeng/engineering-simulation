# 工程仿真工具包 - 使用指南

## 📦 安装

```bash
# 1. 进入项目目录
cd "C:/Users/Mengxd/my test project/engineering-simulation"

# 2. 安装依赖
pip install numpy scipy matplotlib
```

## 🚀 三种使用方式

### 方式一：交互式使用（推荐）

在 Python 中直接导入使用：

```python
# 进入项目目录
cd "C:/Users/Mengxd/my test project/engineering-simulation"

# 启动 Python
python

# 或使用 Jupyter
jupyter notebook
```

```python
# 在 Python 中
import sys
sys.path.insert(0, 'src')

# 导入模块
from materials import Steel
from beam_analysis import SimplySupportedBeam

# 使用
steel = Steel("Q345")
beam = SimplySupportedBeam(5.0, 0.1, 0.2, steel)
beam.add_point_load(50000, 2.5)
results = beam.analyze()
print(f"最大挠度: {results.max_deflection*1000:.2f} mm")
```

### 方式二：运行示例

```bash
# 运行已有示例
cd examples

# 桁架示例
python truss_simple.py

# 框架分析（需要先修改导入）
python warren_truss_test.py
```

### 方式三：作为包安装

```bash
# 在项目根目录
pip install -e .
```

## 📖 常用功能示例

### 1. 查询材料属性

```python
from src.materials import Steel, Aluminum, Concrete

# 钢材
q345 = Steel("Q345")
print(f"E = {q345.elastic_modulus/1e9} GPa")
print(f"fy = {q345.yield_strength/1e6} MPa")

# 铝合金
al6061 = Aluminum("6061-T6")

# 混凝土
c40 = Concrete("C40")
```

### 2. 简支梁分析

```python
from src.beam_analysis import SimplySupportedBeam
from src.materials import Steel

# 创建梁
beam = SimplySupportedBeam(
    length=6.0,      # 跨度 (m)
    width=0.15,      # 宽度 (m)
    height=0.25,     # 高度 (m)
    material=Steel("Q345")
)

# 添加载荷
beam.add_point_load(force=50000, position=3.0)

# 分析
results = beam.analyze()

# 查看结果
print(f"最大挠度: {results.max_deflection*1000:.2f} mm")
print(f"最大应力: {results.max_stress/1e6:.2f} MPa")
print(f"安全系数: {results.safety_factor:.2f}")

# 绘图
results.plot().show()
```

### 3. 桁架结构

```python
from src.truss import create_roof_truss

# 自动生成屋顶桁架
truss = create_roof_truss(
    span=12.0,       # 跨度 (m)
    height=3.0,      # 高度 (m)
    n_bays=6,        # 节数
    snow_load=2000   # 雪载 (N/m)
)

# 分析
results = truss.analyze()

# 查看应力
for elem_id, stress in results.stresses.items():
    print(f"单元 {elem_id}: {stress/1e6:.2f} MPa")
```

### 4. 框架结构

```python
from src.frame import create_portal_frame

# 创建门式框架
frame = create_portal_frame(
    width=8.0,
    height=5.0,
    section_width=0.25,
    section_height=0.35
)

# 施加水平载荷
frame.nodes[1].loads = (5000, 0, 0)

# 求解
results = frame.solve()
results.print_summary()
results.plot()
```

### 5. 柱屈曲分析

```python
from src.stability import euler_buckling_analysis, ColumnSection, BoundaryCondition
from src.materials import Steel

# 定义截面
section = ColumnSection(
    A=0.01,         # 面积 (m²)
    Ix=8.33e-5,     # 惯性矩 (m⁴)
    Iy=8.33e-5
)

# 边界条件（两端铰接）
bc = BoundaryCondition()

# 计算
result = euler_buckling_analysis(
    length=4.0,
    material=Steel("Q345"),
    section=section,
    applied_load=100000,
    boundary_condition=bc
)

print(f"临界载荷: {result.critical_load/1000:.2f} kN")
print(f"长细比: {result.slenderness_ratio:.1f}")
print(f"安全系数: {result.safety_factor:.2f}")
```

## 📁 项目结构

```
engineering-simulation/
├── src/                    # 源代码（主要模块）
│   ├── materials.py        # 材料属性
│   ├── beam_analysis.py    # 梁分析
│   ├── fea.py             # 有限元分析
│   ├── truss.py           # 桁架结构
│   ├── frame.py           # 框架结构 [新]
│   ├── stability.py       # 稳定性分析 [新]
│   ├── dynamics.py        # 动力学分析 [新]
│   └── postproc.py        # 后处理 [新]
├── examples/              # 示例代码
├── tests/                 # 单元测试
└── results/               # 输出图表
```

## 🎯 使用流程

```
1. 定义材料
   ↓
2. 创建结构模型
   ↓
3. 施加边界条件和载荷
   ↓
4. 执行分析
   ↓
5. 查看结果/生成图表
```

## 💡 实用技巧

### 技巧1：快速查看材料库

```python
from src.materials import MATERIAL_DB

for name, mat in MATERIAL_DB.items():
    print(f"{name}: {mat.name}")
```

### 技巧2：批量分析

```python
# 比较不同载荷下的响应
for load in [10000, 20000, 30000, 40000]:
    beam = SimplySupportedBeam(5.0, 0.1, 0.2, steel)
    beam.add_point_load(load, 2.5)
    results = beam.analyze()
    print(f"载荷 {load/1000:.0f}kN: 挠度 {results.max_deflection*1000:.2f}mm")
```

### 技巧3：参数化设计

```python
from src.combined import ParametricStructure

# 创建参数化模型
model = ParametricStructure("portal_frame")
model.set_parameters(width=6.0, height=4.0)
structure = model.generate()
results = structure.solve()
```

## ❓ 常见问题

**Q: 如何选择合适的单元类型？**
- 桁架：只承受轴向力 → 使用 `TrussElement`
- 框架：承受弯矩+剪力+轴力 → 使用 `FrameElement`
- 梁：单向弯曲 → 使用 `SimplySupportedBeam`

**Q: 安全系数多少合适？**
- 一般结构：1.5 ~ 2.0
- 重要结构：2.0 ~ 3.0
- 临时结构：1.2 ~ 1.5

**Q: 如何处理大变形？**
- 当前版本为小变形分析
- 大变形需要使用非线性模块（开发中）
