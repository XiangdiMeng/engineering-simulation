"""
梁分析模块单元测试
"""

import unittest
import numpy as np
import sys
sys.path.insert(0, '../src')

from beam_analysis import SimplySupportedBeam, CantileverBeam, PointLoad
from materials import Steel


class TestSimplySupportedBeam(unittest.TestCase):
    """简支梁测试"""

    def setUp(self):
        """设置测试用梁"""
        self.steel = Steel("Q345")
        self.beam = SimplySupportedBeam(
            length=5.0,
            width=0.1,
            height=0.2,
            material=self.steel
        )

    def test_beam_creation(self):
        """测试梁创建"""
        self.assertEqual(self.beam.length, 5.0)
        self.assertEqual(self.beam.width, 0.1)
        self.assertEqual(self.beam.height, 0.2)
        self.assertAlmostEqual(self.beam.I, 0.1 * 0.2**3 / 12)
        self.assertAlmostEqual(self.beam.S, 0.1 * 0.2**2 / 6)

    def test_add_point_load(self):
        """测试添加集中载荷"""
        self.beam.add_point_load(force=10000, position=2.5)

        self.assertEqual(len(self.beam.point_loads), 1)
        self.assertEqual(self.beam.point_loads[0].force, 10000)
        self.assertEqual(self.beam.point_loads[0].position, 2.5)

    def test_analyze_with_load(self):
        """测试带载荷的梁分析"""
        self.beam.add_point_load(force=50000, position=2.5)
        results = self.beam.analyze()

        # 检查结果
        self.assertIsNotNone(results)
        self.assertEqual(len(results.x), 100)
        self.assertGreater(results.max_moment, 0)
        self.assertGreater(results.max_stress, 0)

    def test_central_load_moment(self):
        """测试跨中载荷的弯矩"""
        # 跨中集中载荷
        P = 50000  # N
        L = 5.0    # m

        self.beam.add_point_load(force=P, position=L/2)
        results = self.beam.analyze()

        # 跨中弯矩 = P*L/4
        expected_M = P * L / 4

        # 允许5%误差（数值积分）
        self.assertAlmostEqual(results.max_moment, expected_M, delta=expected_M * 0.05)

    def test_deflection_calculation(self):
        """测试挠度计算"""
        P = 50000  # N
        L = 5.0    # m
        E = 206e9  # Pa
        I = 0.1 * 0.2**3 / 12

        # 跨中载荷的跨中挠度 = P*L^3 / (48*E*I)
        expected_delta = P * L**3 / (48 * E * I)

        self.beam.add_point_load(force=P, position=L/2)
        results = self.beam.analyze()

        # 允许5%误差
        self.assertAlmostEqual(results.max_deflection, expected_delta, delta=expected_delta * 0.05)

    def test_safety_factor(self):
        """测试安全系数计算"""
        P = 50000  # N
        self.beam.add_point_load(force=P, position=2.5)
        results = self.beam.analyze()

        self.assertGreater(results.safety_factor, 1.0)


class TestCantileverBeam(unittest.TestCase):
    """悬臂梁测试"""

    def setUp(self):
        """设置测试用梁"""
        self.steel = Steel("Q345")
        self.beam = CantileverBeam(
            length=3.0,
            width=0.1,
            height=0.15,
            material=self.steel
        )

    def test_cantilever_creation(self):
        """测试悬臂梁创建"""
        self.assertEqual(self.beam.length, 3.0)
        self.assertEqual(len(self.beam.point_loads), 0)

    def test_tip_load_moment(self):
        """测试端部载荷的弯矩"""
        P = 10000  # N
        L = 3.0    # m

        # 端部载荷
        self.beam.add_point_load(force=P, position=L)
        results = self.beam.analyze()

        # 固定端弯矩 = P * L
        expected_M = P * L

        self.assertAlmostEqual(results.max_moment, expected_M, delta=expected_M * 0.05)

    def test_tip_load_deflection(self):
        """测试端部载荷的挠度"""
        P = 10000  # N
        L = 3.0    # m
        E = 206e9  # Pa
        I = 0.1 * 0.15**3 / 12

        # 端部载荷的端部挠度 = P*L^3 / (3*E*I)
        expected_delta = P * L**3 / (3 * E * I)

        self.beam.add_point_load(force=P, position=L)
        results = self.beam.analyze()

        # 允许5%误差
        self.assertAlmostEqual(results.max_deflection, expected_delta, delta=expected_delta * 0.05)

    def test_mid_span_load(self):
        """测试跨中载荷"""
        P = 10000  # N
        a = 1.5    # m (跨中)

        self.beam.add_point_load(force=P, position=a)
        results = self.beam.analyze()

        # 应该产生位移
        self.assertGreater(results.max_deflection, 0)
        # 应该产生弯矩
        self.assertGreater(results.max_moment, 0)


class TestBeamResults(unittest.TestCase):
    """梁结果测试"""

    def test_results_creation(self):
        """测试结果对象创建"""
        x = np.linspace(0, 1, 10)
        deflection = np.zeros(10)
        slope = np.zeros(10)
        moment = np.zeros(10)
        shear = np.zeros(10)
        stress = np.zeros(10)

        from beam_analysis import BeamResults
        results = BeamResults(
            x=x,
            deflection=deflection,
            slope=slope,
            moment=moment,
            shear=shear,
            stress=stress,
            max_deflection=0,
            max_moment=0,
            max_stress=0,
            safety_factor=float('inf')
        )

        self.assertEqual(len(results.x), 10)


if __name__ == '__main__':
    unittest.main()
