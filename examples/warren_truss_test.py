"""
Working truss example - manual node-by-node creation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib.pyplot as plt
from src.fea import FEModel, TrussElement, FEMaterial, FEAResults


def create_simple_warren_truss():
    """Create Warren truss manually"""
    print("=== Warren Truss Example ===\n")

    # Create FE model
    model = FEModel(name="Warren Truss")

    # Material
    steel = FEMaterial("Q345", 206e9, 0.001, 7850)

    # Create nodes for Warren truss (4 panels)
    # Bottom chord: (0,0), (3,0), (6,0), (9,0), (12,0)
    # Top chord: (1.5,4), (4.5,4), (7.5,4), (10.5,4)
    node_data = [
        (0, 0, True, True),    # 0: (0,0) - fix
        (3, 0, False, True),   # 1: (3,0) - fix Y
        (6, 0, False, True),   # 2: (6,0) - fix Y
        (9, 0, False, True),   # 3: (9,0) - fix Y
        (12, 0, True, True),  # 4: (12,0) - fix
        (1.5, 4, False, False), # 5: (1.5,4)
        (4.5, 4, False, False), # 6: (4.5,4)
        (7.5, 4, False, False), # 7: (7.5,4)
        (10.5, 4, False, False) # 8: (10.5,4)
    ]

    print("Creating nodes:")
    for i, (x, y, fx, fy) in enumerate(node_data):
        node_id = model.add_node(x, y, fixity=(fx, fy, False))
        print(f"  Node {node_id}: ({x:.1f}, {y:.1f}) - " +
              ("Fixed" if (fx or fy) else "Free"))

    # Create elements (Warren truss)
    # Bottom chord (4 elements for 5 nodes)
    for i in range(4):
        model.add_truss_element(i, i + 1, steel)

    # Top chord (3 elements for 4 nodes)
    for i in range(3):
        model.add_truss_element(5 + i, 5 + i + 1, steel)

    # Web members - Warren truss W pattern (diagonals only)
    # Alternating diagonals create the W shape
    web_connections = [
        (5, 1),    # Top-left diagonal down to bottom
        (1, 6),    # Bottom diagonal up to top
        (6, 2),    # Top diagonal down to bottom
        (2, 7),    # Bottom diagonal up to top
        (7, 3),    # Top diagonal down to bottom
        (3, 8),    # Bottom diagonal up to top
    ]

    print(f"\nCreating {len(web_connections)} web members:")
    for i, (ni, nj) in enumerate(web_connections):
        elem_id = model.add_truss_element(ni, nj, steel)
        print(f"  Element {elem_id}: Node {ni} -> Node {nj}")

    # Add loads
    model.nodes[6].loads = (0, -100000, 0)  # Apply load at node 6
    print(f"\nLoad: 100 kN downward at Node 6")

    print(f"\nModel summary:")
    print(f"  Nodes: {len(model.nodes)}")
    print(f"  Elements: {len(model.elements)}")

    # Analyze
    print(f"\nSolving...")
    try:
        results = model.solve()
        print("Solution successful!\n")

        # Print results
        print(f"Node displacements (mm):")
        for i, node in enumerate(results.nodes):
            u = results.displacements[i*2] * 1000
            v = results.displacements[i*2+1] * 1000
            print(f"  Node {i} ({node.x:.1f}, {node.y:.1f}):")
            print(f"    u={u:.3f} mm, v={v:.3f} mm")

        print(f"\nElement stresses:")
        for elem_id, stress in results.stresses.items():
            print(f"  Element {elem_id}: {stress/1e6:.2f} MPa")

        print(f"\nElement forces:")
        for elem_id, force in results.element_forces.items():
            print(f"  Element {elem_id}: {force/1000:.2f} kN")

        print(f"\nReactions:")
        for node_id, (rx, ry) in results.reactions.items():
            print(f"  Node {node_id}: Rx={rx/1000:.2f} kN, Ry={ry/1000:.2f} kN")

        # Plot
        fig = results.plot_structure(figsize=(12, 8))
        plt.savefig("results/warren_truss_12m.png", dpi=150, bbox_inches='tight')
        print(f"\nFigure saved: results/warren_truss_12m.png")
        plt.close()

        return True

    except Exception as e:
        print(f"Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    success = create_simple_warren_truss()

    if success:
        print("\n=== Warren Truss Test Passed! ===")
    else:
        print("\n=== Warren Truss Test Failed ===")
