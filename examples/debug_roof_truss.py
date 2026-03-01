"""
Debug roof truss structure
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.truss import create_roof_truss

def debug_roof_truss():
    """Debug roof truss creation"""
    print("=== Debug Roof Truss ===\n")

    truss = create_roof_truss(
        span=12.0,
        height=3.0,
        n_bays=6,
        chord_A=0.0005,
        web_A=0.0003,
        snow_load=2000
    )

    print(f"Total nodes: {len(truss.nodes)}")
    print("\nNodes:")
    for i, node in enumerate(truss.nodes):
        print(f"  Node {i}: ({node.x:.2f}, {node.y:.2f}) - fixity={node.fixity}")

    print(f"\nTotal elements: {len(truss.elements)}")
    print("\nElements:")
    for i, elem in enumerate(truss.elements):
        ni, nj = truss.nodes[elem.node_i], truss.nodes[elem.node_j]
        print(f"  Element {i}: Node {elem.node_i}({ni.x:.1f},{ni.y:.1f}) -> Node {elem.node_j}({nj.x:.1f},{nj.y:.1f})")

    print(f"\nTotal loads: {len(truss.loads)}")
    print("\nLoads (non-self-weight):")
    for load in truss.loads:
        if load.load_type.value != "dead":
            print(f"  Node {load.node_id}: {load.magnitude:.1f} N {load.load_type.value}")

    # Check for structural stability
    print("\n=== Stability Check ===")
    fixed_dof = 0
    for node in truss.nodes:
        if node.fixity[0]:  # fix_x
            fixed_dof += 1
        if node.fixity[1]:  # fix_y
            fixed_dof += 1
    print(f"Fixed DOF: {fixed_dof}")

    total_dof = len(truss.nodes) * 2
    free_dof = total_dof - fixed_dof
    print(f"Total DOF: {total_dof}")
    print(f"Free DOF: {free_dof}")
    print(f"Elements: {len(truss.elements)}")

    # Check for singular elements (zero length)
    print("\nZero-length elements:")
    for i, elem in enumerate(truss.elements):
        ni, nj = truss.nodes[elem.node_i], truss.nodes[elem.node_j]
        length = ((nj.x - ni.x)**2 + (nj.y - ni.y)**2)**0.5
        if length < 0.001:
            print(f"  Element {i}: ZERO LENGTH!")

if __name__ == "__main__":
    debug_roof_truss()
