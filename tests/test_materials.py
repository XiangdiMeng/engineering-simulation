"""
材料模块单元测试
"""

import unittest
import numpy as np
import sys
sys.path.insert(0, '../src')

from materials import Material, Steel, Aluminum, Concrete, safety_factor, calculate_stress_strain


class TestMaterial(unittest.TestCase):
    """材料基类测试"""

    def test_material_creation(self):
        """测试材料创建"""
        mat = Material(
            name="测试材料",
            density=7850,
            elastic_modulus=200e9,
            poissons_ratio=0.3,
            yield_strength=345e6,
            ultimate_strength=510e6
        )

        self.assertEqual(mat.name, "测试材料")
        self.assertEqual(mat.density, 7850)
        self.assertEqual(mat.elastic_modulus, 200e9)

    def test_shear_modulus(self):
        """测试剪切模量计算"""
        mat = Material("测试", 7850, 200e9, 0.3, 345e6, 510e6)
        expected_G = 200e9 / (2 * (1 + 0.3))
        self.assertAlmostEqual(mat.shear_modulus, expected_G)

    def test_bulk_modulus(self):
        """测试体积模量计算"""
        mat = Material("测试", 7850, 200e9, 0.3, 345e6, 510e6)
        expected_K = 200e9 / (3 * (1 - 2 * 0.3))
        self.assertAlmostEqual(mat.bulk_modulus, expected_K)


class TestSteel(unittest.TestCase):
    """钢材测试"""

    def test_q235_steel(self):
        """测试Q235钢"""
        steel = Steel("Q235")

        self.assertEqual(steel.density, 7850)
        self.assertEqual(steel.elastic_modulus, 200e9)
        self.assertEqual(steel.yield_strength, 235e6)
        self.assertEqual(steel.ultimate_strength, 375e6)

    def test_q345_steel(self):
        """测试Q345钢"""
        steel = Steel("Q345")

        self.assertEqual(steel.elastic_modulus, 206e9)
        self.assertEqual(steel.yield_strength, 345e6)
        self.assertEqual(steel.ultimate_strength, 510e6)

    def test_45_steel(self):
        """测试45#钢"""
        steel = Steel("45#")

        self.assertEqual(steel.elastic_modulus, 210e9)
        self.assertEqual(steel.poissons_ratio, 0.29)


class TestAluminum(unittest.TestCase):
    """铝合金测试"""

    def test_6061_t6(self):
        """测试6061-T6铝合金"""
        aluminum = Aluminum("6061-T6")

        self.assertEqual(aluminum.density, 2700)
        self.assertEqual(aluminum.elastic_modulus, 68.9e9)
        self.assertEqual(aluminum.yield_strength, 276e6)

    def test_7075_t6(self):
        """测试7075-T6铝合金"""
        aluminum = Aluminum("7075-T6")

        self.assertEqual(aluminum.density, 2810)
        self.assertEqual(aluminum.elastic_modulus, 71.7e9)
        self.assertEqual(aluminum.yield_strength, 503e6)


class TestConcrete(unittest.TestCase):
    """混凝土测试"""

    def test_c30_concrete(self):
        """测试C30混凝土"""
        concrete = Concrete("C30")

        self.assertEqual(concrete.density, 2400)
        self.assertEqual(concrete.elastic_modulus, 30e9)
        self.assertEqual(concrete.yield_strength, 20e6)

    def test_c50_concrete(self):
        """测试C50混凝土"""
        concrete = Concrete("C50")

        self.assertEqual(concrete.density, 2450)
        self.assertEqual(concrete.elastic_modulus, 34.5e9)
        self.assertEqual(concrete.yield_strength, 32e6)


class TestMaterialFunctions(unittest.TestCase):
    """材料功能函数测试"""

    def test_calculate_stress_strain(self):
        """测试应力应变计算"""
        steel = Steel("Q345")
        strain = 0.001  # 0.1% 应变

        stress = calculate_stress_strain(steel, strain)
        expected = 200e9 * 0.001

        self.assertAlmostEqual(stress, expected)

    def test_calculate_stress_strain_array(self):
        """测试数组输入的应力应变计算"""
        steel = Steel("Q345")
        strains = np.array([0.001, 0.002, 0.003])

        stresses = calculate_stress_strain(steel, strains)
        expected = 200e9 * strains

        np.testing.assert_array_almost_equal(stresses, expected)

    def test_safety_factor(self):
        """测试安全系数计算"""
        steel = Steel("Q345")
        working_stress = 100e6  # 100 MPa

        sf = safety_factor(steel, working_stress)
        expected = 345e6 / 100e6

        self.assertAlmostEqual(sf, expected)

    def test_safety_factor_zero_stress(self):
        """测试零应力的安全系数"""
        steel = Steel("Q345")

        sf = safety_factor(steel, 0)

        self.assertEqual(sf, float('inf'))


if __name__ == '__main__':
    unittest.main()
