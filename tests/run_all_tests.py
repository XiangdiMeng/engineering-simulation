"""
运行所有单元测试
"""

import unittest
import sys
import os

# 添加项目根目录到Python路径
src_path = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, src_path)

# 导入所有测试模块
from test_materials import (
    TestMaterial, TestSteel, TestAluminum, TestConcrete, TestMaterialFunctions
)
from test_beam_analysis import TestSimplySupportedBeam, TestCantileverBeam
from test_fea import (
    TestFEMaterial, TestNode, TestTrussElement, TestFEModel, TestTrussStructure
)


def run_tests(verbosity=2):
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试
    suite.addTests(loader.loadTestsFromTestCase(TestMaterial))
    suite.addTests(loader.loadTestsFromTestCase(TestSteel))
    suite.addTests(loader.loadTestsFromTestCase(TestAluminum))
    suite.addTests(loader.loadTestsFromTestCase(TestConcrete))
    suite.addTests(loader.loadTestsFromTestCase(TestMaterialFunctions))

    suite.addTests(loader.loadTestsFromTestCase(TestSimplySupportedBeam))
    suite.addTests(loader.loadTestsFromTestCase(TestCantileverBeam))

    suite.addTests(loader.loadTestsFromTestCase(TestFEMaterial))
    suite.addTests(loader.loadTestsFromTestCase(TestNode))
    suite.addTests(loader.loadTestsFromTestCase(TestTrussElement))
    suite.addTests(loader.loadTestsFromTestCase(TestFEModel))
    suite.addTests(loader.loadTestsFromTestCase(TestTrussStructure))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    # 打印摘要
    print("\n" + "="*60)
    print("测试摘要")
    print("="*60)
    print(f"总测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print("="*60)

    return result


if __name__ == '__main__':
    result = run_tests()

    # 如果有失败或错误，返回非零退出码
    sys.exit(0 if result.wasSuccessful() else 1)
