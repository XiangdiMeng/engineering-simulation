# 工程仿真项目 (Engineering Simulation)

Python 机械/结构工程仿真工具包

## 功能特性

- ✅ 有限元分析 (FEA)
- ✅ 梁结构分析
- ✅ 材料属性计算
- ✅ 应力应变分析
- ✅ 数值优化
- ✅ 结果可视化

## 安装

### 环境要求
- Python 3.9+
- pip 或 conda

### 安装依赖

```bash
pip install -r requirements.txt
```

或使用 conda:

```bash
conda env create -f environment.yml
conda activate engineering-sim
```

## 快速开始

### 示例 1: 简支梁受力分析

```python
from src.beam_analysis import SimplySupportedBeam
from src.materials import Steel

# 创建简支梁
beam = SimplySupportedBeam(
    length=5.0,           # 长度 (m)
    width=0.1,            # 宽度 (m)
    height=0.2,           # 高度 (m)
    material=Steel()      # 材料
)

# 施加集中载荷
beam.add_point_load(force=10000, position=2.5)

# 计算结果
results = beam.analyze()
results.plot()
```

### 示例 2: 有限元分析

```python
from src.fea import Truss2D
import numpy as np

# 创建桁架结构
truss = Truss2D()

# 添加节点
truss.add_node(0, 0)      # 节点 0
truss.add_node(3, 0)      # 节点 1
truss.add_node(1.5, 2)   # 节点 2

# 添加单元
truss.add_element(0, 1, E=200e9, A=0.001)
truss.add_element(1, 2, E=200e9, A=0.001)
truss.add_element(0, 2, E=200e9, A=0.001)

# 添加边界条件和载荷
truss.add_fixity(0, ux=True, uy=True)
truss.add_load(2, Fx=0, Fy=-50000)

# 求解
truss.solve()
truss.plot_deformation()
```

## 项目结构

```
engineering-simulation/
├── src/                    # 源代码
│   ├── materials.py        # 材料属性
│   ├── beam_analysis.py    # 梁分析
│   ├── fea.py             # 有限元分析
│   ├── stress.py          # 应力计算
│   └── visualization.py   # 可视化
├── examples/              # 示例代码
├── tests/                 # 测试
├── data/                  # 输入数据
├── results/               # 仿真结果
└── docs/                  # 文档
```

## 主要库

- [NumPy](https://numpy.org/) - 数值计算
- [SciPy](https://scipy.org/) - 科学计算
- [Matplotlib](https://matplotlib.org/) - 绘图
- [FEniCS](https://fenicsproject.org/) - 有限元分析（可选）

## 许可证

MIT License

## 作者

Xiangdi Meng
