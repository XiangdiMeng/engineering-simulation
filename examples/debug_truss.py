"""
Simple truss test - debug version
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib.pyplot as plt
from src.fea import FEModel, TrussElement, FEMaterial, FEAResults


def test_simple_triangle_truss():
    """Test simple triangle truss"""
    print("=== Simple Triangle Truss Test ===\n")

    # Create FE model
    model = FEModel(name="Triangle Truss")

    # Material
    steel = FEMaterial("Q345", 206e9, 0.0001, 7850)

    # Nodes: (0,0), (4,3), (8,0)
    node0 = model.add_node(0, 0, fixity=(True, True, False))   # Left fixed
    node1 = model.add_node(4, 3, fixity=(False, False, False)) # Top free
    node2 = model.add_node(8, 0, fixity=(False, True, False))   # Right fixed Y

    print("Node coordinates:")
    print(f"  Node 0: (0, 0) - Fixed X and Y")
    print(f"  Node 1: (4, 3) - Free")
    print(f"  Node 2: (8, 0) - Fixed Y")

    # Elements
    elem0 = model.add_truss_element(0, 1, steel)   # Left side
    elem1 = model.add_truss_element(1, 2, steel)   # Right side
    elem2 = model.add_truss_element(0, 2, steel)   # Bottom

    print(f"\nElements:")
    print(f"  Element 0: Node 0 -> Node 1 (left side)")
    print(f"  Element 1: Node 1 -> Node 2 (right side)")
    print(f"  Element 2: Node 0 -> Node 2 (bottom chord)")

    # Apply load: 50kN downward at top node
    model.nodes[1].loads = (0, -50000, 0)
    print(f"\nLoad: 50 kN downward at Node 1")

    # Analyze
    print(f"\nStarting analysis...")
    try:
        results = model.solve()
        print("Analysis successful!\n")

        print(f"Node displacements (mm):")
        for i, node in enumerate(results.nodes):
            u = results.displacements[i*2] * 1000
            v = results.displacements[i*2+1] * 1000
            print(f"  Node {i}: u={u:.3f} mm, v={v:.3f} mm")

        print(f"\nElement stresses:")
        for elem_id, stress in results.stresses.items():
            print(f"  Element {elem_id}: {stress/1e6:.2f} MPa")

        print(f"\nElement forces:")
        for elem_id in results.stresses.keys():
            stress = results.stresses[elem_id]
            force = stress * steel.A  # F = stress * A
            print(f"  Element {elem_id}: {force/1000:.2f} kN")

        print(f"\nReactions:")
        for node_id, (rx, ry) in results.reactions.items():
            print(f"  Node {node_id}: Rx={rx/1000:.2f} kN, Ry={ry/1000:.2f} kN")

        # Plot
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # Original structure
        for elem in model.elements:
            if isinstance(elem, TrussElement):
                ni, nj = model.nodes[elem.node_i], model.nodes[elem.node_j]
                ax1.plot([ni.x, nj.x], [ni.y, nj.y], 'b-o', linewidth=3, markersize=10)

        # Nodes
        for node in model.nodes:
            marker = '^' if node.fixity[0] or node.fixity[1] else 'o'
            color = 'red' if (node.fixity[0] or node.fixity[1]) else 'black'
            ax1.plot(node.x, node.y, marker, markersize=12, color=color, zorder=5)
            ax1.text(node.x, node.y - 0.2, f'{node.id}', fontsize=10, ha='center')

        # Load
        fx, fy, _ = model.nodes[1].loads
        if abs(fx) > 0 or abs(fy) > 0:
            ax1.arrow(4, 3, fx/10000, fy/10000,
                     head_width=0.15, head_length=0.2,
                     fc='red', ec='red', linewidth=2)

        ax1.set_aspect('equal')
        ax1.grid(True, alpha=0.3)
        ax1.set_title('Truss Structure')
        ax1.set_xlabel('X (m)')
        ax1.set_ylabel('Y (m)')

        # Stress plot
        elem_ids = list(results.stresses.keys())
        stresses = [results.stresses[i]/1e6 for i in elem_ids]
        colors = ['red' if s > 0 else 'blue' for s in stresses]

        ax2.bar(elem_ids, stresses, color=colors, alpha=0.7)
        ax2.axhline(0, color='k', linestyle='--', linewidth=1)
        ax2.set_xlabel('Element ID')
        ax2.set_ylabel('Stress (MPa)')
        ax2.set_title('Element Stress Distribution')
        ax2.grid(True, alpha=0.3, axis='y')

        for i, bar in enumerate(ax2.patches):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}',
                   ha='center', va='bottom' if height > 0 else 'top')

        plt.tight_layout()
        plt.savefig("results/simple_triangle_truss.png", dpi=150, bbox_inches='tight')
        print(f"\nFigure saved: results/simple_triangle_truss.png")
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

    success = test_simple_triangle_truss()

    if success:
        print("\n=== Test Passed! ===")
    else:
        print("\n=== Test Failed ===")
