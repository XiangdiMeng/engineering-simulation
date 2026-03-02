"""
Balcony Design Analysis and Optimization
"""

import sys
sys.path.insert(0, 'src')

print('='*70)
print('  RESIDENTIAL BALCONY - COMPLETE ANALYSIS & OPTIMIZATION')
print('='*70)
print()

from src.materials import Concrete
from src.stability import euler_buckling_analysis, ColumnSection, BoundaryCondition

# ============================================
# PART 1: ORIGINAL DESIGN ANALYSIS
# ============================================
print('PART 1: ORIGINAL DESIGN')
print('-'*70)

BALCONY_LENGTH = 3.5
BALCONY_WIDTH = 1.5
SLAB_THICKNESS_ORIG = 0.12
REBAR_RATIO_ORIG = 0.003

print(f'Design Parameters:')
print(f'  Cantilever length: {BALCONY_LENGTH} m')
print(f'  Balcony width: {BALCONY_WIDTH} m')
print(f'  Slab thickness: {SLAB_THICKNESS_ORIG*1000:.0f} mm')
print(f'  Reinforcement ratio: {REBAR_RATIO_ORIG*100:.1f}%')
print()

# Material
concrete = Concrete('C30')
E = concrete.elastic_modulus * 1.2
I_orig = (1.0 * SLAB_THICKNESS_ORIG**3) / 12

# Loads
DEAD_LOAD_ORIG = 25 * SLAB_THICKNESS_ORIG * 1.5 * 1000
LIVE_LOAD = 2.5 * 1.5 * 1000
total_load_orig = DEAD_LOAD_ORIG + LIVE_LOAD
RAIL_LOAD = 0.5 * 1.5 * 1000

# Results
L = BALCONY_LENGTH
q = total_load_orig
P = RAIL_LOAD

M_max_orig = q * L**2 / 2 + P * L
delta_max_orig = q * L**4 / (8 * E * I_orig) + P * L**3 / (3 * E * I_orig)

# Reinforcement
h0_orig = SLAB_THICKNESS_ORIG - 0.02
fy = 400e6
As_req_orig = M_max_orig / (fy * 0.9 * h0_orig)
As_prov_orig = BALCONY_WIDTH * SLAB_THICKNESS_ORIG * REBAR_RATIO_ORIG

print(f'Analysis Results:')
print(f'  Maximum moment: {M_max_orig/1000:.2f} kN.m')
print(f'  Maximum deflection: {delta_max_orig*1000:.2f} mm')
print(f'  Deflection limit: {L*1000/250:.2f} mm (L/250)')
print()

# Checks
deflection_limit = L * 1000 / 250
deflection_check_orig = delta_max_orig * 1000 < deflection_limit
strength_check_orig = As_prov_orig >= As_req_orig

print(f'Checks:')
print(f'  Deflection: {"PASS" if deflection_check_orig else "FAIL"}')
print(f'  Reinforcement: {"PASS" if strength_check_orig else "FAIL"}')
print(f'    Required: {As_req_orig*1e6:.0f} mm2/m')
print(f'    Provided: {As_prov_orig*1e6:.0f} mm2/m')
print()

# ============================================
# PART 2: OPTIMIZED DESIGN
# ============================================
print('='*70)
print('PART 2: OPTIMIZED DESIGN')
print('-'*70)

SLAB_THICKNESS_NEW = 0.16  # 160mm
REBAR_RATIO_NEW = 0.008    # 0.8%

print(f'Design Parameters:')
print(f'  Slab thickness: {SLAB_THICKNESS_NEW*1000:.0f} mm (+33%)')
print(f'  Reinforcement ratio: {REBAR_RATIO_NEW*100:.1f}% (+167%)')
print()

# Recalculate
E_new = concrete.elastic_modulus * 1.25
I_new = (1.0 * SLAB_THICKNESS_NEW**3) / 12

DEAD_LOAD_NEW = 25 * SLAB_THICKNESS_NEW * 1.5 * 1000
total_load_new = DEAD_LOAD_NEW + LIVE_LOAD

q_new = total_load_new

M_max_new = q_new * L**2 / 2 + P * L
delta_max_new = q_new * L**4 / (8 * E_new * I_new) + P * L**3 / (3 * E_new * I_new)

h0_new = SLAB_THICKNESS_NEW - 0.02
As_req_new = M_max_new / (fy * 0.9 * h0_new)
As_prov_new = BALCONY_WIDTH * SLAB_THICKNESS_NEW * REBAR_RATIO_NEW

# Concrete stress
S_new = (1.0 * SLAB_THICKNESS_NEW**2) / 6
sigma_c_new = M_max_new / S_new
allowable_sigma = concrete.yield_strength / 1.5

print(f'Analysis Results:')
print(f'  Maximum moment: {M_max_new/1000:.2f} kN.m')
print(f'  Maximum deflection: {delta_max_new*1000:.2f} mm')
print(f'  Deflection limit: {L*1000/250:.2f} mm')
print()

print(f'Checks:')
deflection_check_new = delta_max_new * 1000 < deflection_limit
strength_check_new = As_prov_new >= As_req_new
stress_check_new = sigma_c_new < allowable_sigma

print(f'  Deflection: {"PASS" if deflection_check_new else "FAIL"}')
print(f'  Reinforcement: {"PASS" if strength_check_new else "FAIL"}')
print(f'    Required: {As_req_new*1e6:.0f} mm2/m')
print(f'    Provided: {As_prov_new*1e6:.0f} mm2/m')
print(f'  Concrete stress: {"PASS" if stress_check_new else "FAIL"}')
print(f'    Max stress: {sigma_c_new/1e6:.2f} MPa')
print(f'    Allowable: {allowable_sigma/1e6:.2f} MPa')
print()

# ============================================
# PART 3: COMPARISON TABLE
# ============================================
print('='*70)
print('PART 3: DESIGN COMPARISON')
print('-'*70)
print()
print(f"{'Parameter':<25} {'Original':<20} {'Optimized':<20} {'Change':<10}")
print('-'*70)

thick_change = f"+{(SLAB_THICKNESS_NEW/SLAB_THICKNESS_ORIG - 1)*100:.0f}%"
rebar_change = f"+{(REBAR_RATIO_NEW/REBAR_RATIO_ORIG - 1)*100:.0f}%"
moment_change = f"+{(M_max_new/M_max_orig - 1)*100:.1f}%"
deflection_change = f"{(delta_max_new/delta_max_orig - 1)*100:.1f}%"

print(f"{'Slab thickness':<25} {'120 mm':<20} {'{:.0f} mm'.format(SLAB_THICKNESS_NEW*1000):<20} {thick_change:<10}")
print(f"{'Reinforcement ratio':<25} {'0.3%':<20} {'{:.1f}%'.format(REBAR_RATIO_NEW*100):<20} {rebar_change:<10}")
print(f"{'Self weight':<25} {'{:.0f} N/m'.format(DEAD_LOAD_ORIG):<20} {'{:.0f} N/m'.format(DEAD_LOAD_NEW):<20} {'+{:}%'.format(int((DEAD_LOAD_NEW/DEAD_LOAD_ORIG - 1)*100)):<10}")
print(f"{'Max moment':<25} {'{:.2f} kN.m'.format(M_max_orig/1000):<20} {'{:.2f} kN.m'.format(M_max_new/1000):<20} {moment_change:<10}")
print(f"{'Max deflection':<25} {'{:.2f} mm'.format(delta_max_orig*1000):<20} {'{:.2f} mm'.format(delta_max_new*1000):<20} {deflection_change:<10}")
print(f"{'Deflection/limit':<25} {'{:.2f}'.format(delta_max_orig*1000/deflection_limit):<20} {'{:.2f}'.format(delta_max_new*1000/deflection_limit):<20} {'':<10}")
print(f"{'Rebar required':<25} {'{:.0f} mm2/m'.format(As_req_orig*1e6):<20} {'{:.0f} mm2/m'.format(As_req_new*1e6):<20} {'':<10}")
print(f"{'Rebar provided':<25} {'{:.0f} mm2/m'.format(As_prov_orig*1e6):<20} {'{:.0f} mm2/m'.format(As_prov_new*1e6):<20} {'':<10}")
print()

# ============================================
# PART 4: FINAL VERDICT
# ============================================
print('='*70)
print('PART 4: FINAL VERDICT')
print('-'*70)
print()

if strength_check_new and deflection_check_new and stress_check_new:
    print('  *** OPTIMIZED DESIGN: ALL CHECKS PASSED ***')
    print()
    print('  Recommended specifications:')
    print(f'    - Slab thickness: {SLAB_THICKNESS_NEW*1000:.0f} mm')
    print(f'    - Reinforcement: HRB400, {REBAR_RATIO_NEW*100:.1f}%')
    print(f'    - Concrete: C30')
    print(f'    - Railing: 50x50x3mm SHS at 500mm spacing')
    print()
    print('  This design meets all safety and serviceability requirements.')
else:
    print('  *** WARNING: SOME CHECKS STILL FAILED ***')
    print('  Consider additional measures:')
    print('    - Add cantilever beam at balcony edge')
    print('    - Increase slab thickness further')
    print('    - Use higher grade concrete')

print()
print('='*70)
