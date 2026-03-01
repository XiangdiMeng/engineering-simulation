"""
Truss Structure Examples - Simplified
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib.pyplot as plt
from src.truss import TrussStructure, TrussAnalysisResults, create_roof_truss, FEMaterial


def example_roof_truss():
    """Example: Roof truss for a house"""
    print("\n" + "="*60)
    print("Example: Roof Truss for a 12m Span House")
    print("="*60)

    # Create 12m span roof truss
    truss = create_roof_truss(
        span=12.0,
        height=3.0,
        n_bays=6,
        chord_A=0.0005,    # 500 mm^2
        web_A=0.0003,     # 300 mm^2
        E=206e9,          # Q345 steel
        snow_load=2000     # 2 kN/m snow load
    )

    print("\nTruss parameters:")
    print(f"  Span: 12.0 m")
    print(f"  Height: 3.0 m")
    print(f"  Bays: 6")
    print(f"  Material: Q345 Steel")
    print(f"  Loads: Self-weight + Snow (2 kN/m)")

    # Analyze
    results = truss.analyze()
    analysis = TrussAnalysisResults(results, truss)

    # Print summary
    analysis.print_summary()

    # Plot results
    fig = analysis.plot_detailed(figsize=(14, 8))
    plt.savefig("results/roof_truss_12m.png", dpi=150, bbox_inches='tight')
    print(f"\nFigure saved: results/roof_truss_12m.png")
    plt.close()

    return analysis


def example_bridge_comparison():
    """Example: Compare different span bridges"""
    print("\n" + "="*60)
    print("Example: Bridge Truss - Span Comparison")
    print("="*60)

    spans = [10, 15, 20, 25]
    results_data = []

    for span in spans:
        # Modify create_bridge_truss to accept variable span
        from src.truss import create_bridge_truss

        # Create bridge with this span
        bridge = create_bridge_truss(
            span=span,
            height=span/5,  # Height = span/5
            n_panels=int(span/2.5),
            chord_A=0.002,
            web_A=0.001,
            E=200e9,
            traffic_load=50000
        )

        results = bridge.analyze()
        analysis = TrussAnalysisResults(results, bridge)

        max_disp = np.max(np.abs(results.displacements)) * 1000
        max_stress = analysis.max_stress / 1e6
        min_stress = analysis.min_stress / 1e6

        results_data.append({
            "span": span,
            "max_disp": max_disp,
            "max_stress": max_stress,
            "min_stress": min_stress
        })

    # Print table
    print(f"\n{'Span(m)':<12} {'Max Disp(mm)':<15} {'Max Stress(MPa)':<15} {'Min Stress(MPa)':<15}")
    print("-" * 60)
    for r in results_data:
        print(f"{r['span']:<12.0f} {r['max_disp']:<15.2f} {r['max_stress']:<15.2f} {r['min_stress']:<15.2f}")

    # Plot
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    spans = [r["span"] for r in results_data]

    # Displacement
    disps = [r["max_disp"] for r in results_data]
    axes[0, 0].plot(spans, disps, 'o-', linewidth=2, markersize=8)
    axes[0, 0].set_xlabel('Span (m)')
    axes[0, 0].set_ylabel('Max Displacement (mm)')
    axes[0, 0].set_title('Displacement vs Span')
    axes[0, 0].grid(True, alpha=0.3)

    # Max stress
    max_stresses = [r["max_stress"] for r in results_data]
    axes[0, 1].plot(spans, max_stresses, 's-', linewidth=2, markersize=8, color='red')
    axes[0, 1].axhline(yield_strength_steel/1e6, color='r', linestyle='--', label='Yield')
    axes[0, 1].set_xlabel('Span (m)')
    axes[0, 1].set_ylabel('Max Stress (MPa)')
    axes[0, 1].set_title('Max Stress vs Span')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)

    # Min stress
    min_stresses = [r["min_stress"] for r in results_data]
    axes[1, 0].plot(spans, [-s for s in min_stresses], '^-', linewidth=2, markersize=8, color='blue')
    axes[1, 0].set_xlabel('Span (m)')
    axes[1, 0].set_ylabel('Min Stress (MPa)')
    axes[1, 0].set_title('Min Stress vs Span (Compression)')
    axes[1, 0].grid(True, alpha=0.3)

    # Stress range
    stress_range = [max_stresses[i] - min_stresses[i] for i in range(len(spans))]
    axes[1, 1].bar(spans, stress_range, color='purple', alpha=0.7)
    axes[1, 1].set_xlabel('Span (m)')
    axes[1, 1].set_ylabel('Stress Range (MPa)')
    axes[1, 1].set_title('Stress Range vs Span')
    axes[1, 1].grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig("results/bridge_span_comparison.png", dpi=150, bbox_inches='tight')
    print(f"\nFigure saved: results/bridge_span_comparison.png")
    plt.close()


if __name__ == "__main__":
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    yield_strength_steel = 345e6  # Q345 yield strength

    # Run examples
    example_roof_truss()
    example_bridge_comparison()

    print("\n" + "="*60)
    print("All truss examples completed!")
    print("="*60)
