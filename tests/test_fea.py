"""
有限元分析模块单元测试
"""

import unittest
import numpy as np
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from src.fea import FEModel, TrussElement, FEMaterial, Node


class TestFEMaterial(unittest.TestCase):
    """有限元材料测试"""

    def test_material_creation(self):
        """测试材料创建"""
        mat = FEMaterial(
            name="测试材料",
            E=200e9,
            A=0.001,
            density=7850
        )

        self.assertEqual(mat.name, "测试材料")
        self.assertEqual(mat.E, 200e9)
        self.assertEqual(mat.A, 0.001)


class TestNode(unittest.TestCase):
    """节点测试"""

    def test_node_creation(self):
        """测试节点创建"""
        node = Node(
            id=0,
            x=1.0,
            y=2.0,
            fixity=(True, False, True),
            loads=(1000, -2000, 0)
        )

        self.assertEqual(node.id, 0)
        self.assertEqual(node.x, 1.0)
        self.assertEqual(node.y, 2.0)
        self.assertTrue(node.fixity[0])
        self.assertFalse(node.fixity[1])
        self.assertEqual(node.loads[0], 1000)


class TestTrussElement(unittest.TestCase):
    """桁架单元测试"""

    def setUp(self):
        """设置测试用单元"""
        self.material = FEMaterial("Q345", E=206e9, A=0.001, density=7850)
        self.nodes = [
            Node(0, 0.0, 0.0),
            Node(1, 3.0, 0.0),
            Node(2, 1.5, 2.0)
        ]

    def test_element_creation(self):
        """测试单元创建"""
        elem = TrussElement(0, 0, 1, self.material)

        self.assertEqual(elem.id, 0)
        self.assertEqual(elem.node_i, 0)
        self.assertEqual(elem.node_j, 1)

    def test_length_horizontal(self):
        """测试水平单元长度"""
        elem = TrussElement(0, 0, 1, self.material)
        length = elem.length(self.nodes)

        self.assertEqual(length, 3.0)

    def test_length_diagonal(self):
        """测试斜单元长度"""
        elem = TrussElement(1, 0, 2, self.material)
        length = elem.length(self.nodes)

        expected = np.sqrt(1.5**2 + 2**2)
        self.assertAlmostEqual(length, expected)

    def test_local_stiffness_matrix(self):
        """测试局部刚度矩阵"""
        elem = TrussElement(0, 0, 1, self.material)
        K_local = elem.stiffness_matrix(self.nodes)

        self.assertEqual(K_local.shape, (2, 2))

        # 检查对称性
        np.testing.assert_array_almost_equal(K_local, K_local.T)

        # 检查对角线元素
        self.assertGreater(K_local[0, 0], 0)
        self.assertGreater(K_local[1, 1], 0)

    def test_global_stiffness_matrix(self):
        """测试全局刚度矩阵"""
        elem = TrussElement(0, 0, 1, self.material)
        K_global = elem.global_stiffness_matrix(self.nodes)

        self.assertEqual(K_global.shape, (4, 4))

        # 检查对称性
        np.testing.assert_array_almost_equal(K_global, K_global.T)

    def test_stress_calculation(self):
        """测试应力计算"""
        elem = TrussElement(0, 0, 1, self.material)

        # 模拟拉伸变形 - 节点1向右移动，节点0固定
        displacements = np.array([0, 0, 0.001, 0])  # 节点1向右移动1mm
        stress = elem.get_stress(self.nodes, displacements)

        # 应该产生拉应力
        self.assertGreater(stress, 0)


class TestFEModel(unittest.TestCase):
    """有限元模型测试"""

    def setUp(self):
        """设置测试模型"""
        self.model = FEModel(name="测试模型")
        self.material = FEMaterial("Q345", E=200e9, A=0.001, density=7850)

    def test_model_creation(self):
        """测试模型创建"""
        self.assertEqual(self.model.name, "测试模型")
        self.assertEqual(len(self.model.nodes), 0)
        self.assertEqual(len(self.model.elements), 0)

    def test_add_node(self):
        """测试添加节点"""
        node_id = self.model.add_node(0, 0)
        self.assertEqual(node_id, 0)
        self.assertEqual(len(self.model.nodes), 1)

    def test_add_element(self):
        """测试添加单元"""
        self.model.add_node(0, 0, fixity=(True, True, False))
        self.model.add_node(1, 0, fixity=(False, True, False))

        elem_id = self.model.add_truss_element(0, 1, self.material)
        self.assertEqual(elem_id, 0)
        self.assertEqual(len(self.model.elements), 1)

    def test_assemble_stiffness_matrix(self):
        """测试刚度矩阵组装"""
        # 创建简单杆
        self.model.add_node(0, 0, fixity=(True, True, False))
        self.model.add_node(1, 1, fixity=(False, False, False), loads=(0, -1000, 0))

        self.model.add_truss_element(0, 1, self.material)

        K = self.model.assemble_stiffness_matrix()

        # 2个节点，每个2个自由度
        self.assertEqual(K.shape, (4, 4))
        # 检查对称性
        np.testing.assert_array_almost_equal(K, K.T)

    def test_solve_simple_bar(self):
        """测试简单杆求解"""
        # 创建拉伸杆
        self.model.add_node(0, 0, fixity=(True, True, False))
        self.model.add_node(1, 1, fixity=(False, True, False), loads=(50000, 0, 0))

        self.model.add_truss_element(0, 1, self.material)

        results = self.model.solve()

        self.assertIsNotNone(results)
        self.assertGreater(len(results.displacements), 0)

    def test_reactions(self):
        """测试支座反力计算"""
        self.model.add_node(0, 0, fixity=(True, True, False))
        self.model.add_node(1, 1, fixity=(False, True, False), loads=(50000, 0, 0))

        self.model.add_truss_element(0, 1, self.material)

        results = self.model.solve()

        # 应该有支座反力
        self.assertTrue(len(results.reactions) > 0 or 0 in results.reactions)


class TestTrussStructure(unittest.TestCase):
    """桁架结构测试"""

    def test_simple_triangle_truss(self):
        """测试简单三角形桁架"""
        model = FEModel(name="三角形桁架")
        material = FEMaterial("Q345", E=200e9, A=0.001, density=7850)

        # 创建三角形
        model.add_node(0, 0, fixity=(True, True, False))
        model.add_node(1, 0, fixity=(True, True, False))
        model.add_node(0.5, 1, fixity=(False, False, False), loads=(0, -10000, 0))

        model.add_truss_element(0, 2, material)
        model.add_truss_element(1, 2, material)
        model.add_truss_element(0, 1, material)

        results = model.solve()

        self.assertIsNotNone(results)
        self.assertGreater(len(results.stresses), 0)

    def test_stress_sign_convention(self):
        """测试应力符号约定"""
        model = FEModel(name="符号测试")
        material = FEMaterial("Q345", E=200e9, A=0.001, density=7850)

        # 创建受拉杆
        model.add_node(0, 0, fixity=(True, True, False))
        model.add_node(1, 1, fixity=(False, True, False), loads=(10000, 0, 0))

        model.add_truss_element(0, 1, material)

        results = model.solve()

        # 拉伸应该产生正应力
        for stress in results.stresses.values():
            self.assertGreater(stress, 0)


if __name__ == '__main__':
    unittest.main()
