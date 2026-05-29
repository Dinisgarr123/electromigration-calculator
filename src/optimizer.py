import em_formulas as em

# Add this to optimizer.py

def sweep_best_metal_width(stack_rules, selected_stack, max_temp, current_per_unit, 
                           num_cols, h_metal_comb, h_space_w, device_w_used, 
                           metal_pairs, w_coeff, l_coeff):
    """
    Performs a linear sweep to find the minimum stripe width that satisfies EM constraints.

    Iterates through a range of metal widths to identify the smallest value that 
    maintains a PASS status while respecting the total device footprint constraint.

    Args:
        stack_rules (dict): PDK ruleset for capacity calculations.
        selected_stack (str): Target process technology stack.
        max_temp (int): Operating temperature in Celsius.
        current_per_unit (float): Current requirement per array unit cell (mA).
        num_cols (int): Number of columns in the power array.
        h_metal_comb (str): The horizontal metal stack combination string.
        h_space_w (float): Spacing between horizontal stripes (µm).
        device_w_used (float): Total physical device width available (µm).
        metal_pairs (int): Number of parallel routing pairs.
        w_coeff (float): Width derating coefficient.
        l_coeff (float): Length/loading derating coefficient.

    Returns:
        dict: A dictionary containing 'best_metal_width'. Returns 0.0 if no 
              valid width is found within the sweep range.
    """
    
    
    best_width = 0.0
    # Increase range if needed, but start checking from a safe minimum
    # Check if the device width is even large enough to support the minimum spacing
    if (h_space_w * 2) >= device_w_used:
        return {"best_metal_width": 0.0}

    for current_w in [i * 0.05 for i in range(2, 401)]: # Sweep up to 20.0um
        
        # 1. Footprint Constraint
        if ((current_w * 2) + h_space_w) > device_w_used:
            continue
            
        # 2. EM Constraint
        res = em.calculate_horizontal_configuration(
            stack_rules, selected_stack, max_temp, current_per_unit, num_cols, 
            h_metal_comb, current_w, h_space_w, metal_pairs, w_coeff, l_coeff
        )
        
        if res.get('pass', False):
            best_width = round(current_w, 2)
            break 
            
    return {"best_metal_width": best_width}

def is_combination_valid(h_comb_name, v_comb_name):
    """
    Validates metal stack compatibility by checking for layer overlap.

    Simulates the vertical stack inclusion of M1 to ensure that the chosen 
    horizontal and vertical combinations do not conflict on common layers.

    Args:
        h_comb_name (str): Key for the horizontal metal combination.
        v_comb_name (str): Key for the vertical metal combination.

    Returns:
        bool: True if the combination is valid (no layer conflict), False otherwise.
    """
    h_metals = em.METAL_STACK_MAP.get(h_comb_name, [])
    # DYNAMIC: Create a virtual vertical stack that includes M1
    # without actually changing the original data.
    base_v_metals = em.METAL_STACK_MAP.get(v_comb_name, [])
    v_metals_virtual = list(set(base_v_metals + ["M1"]))
    
    # 1. Short-circuit check: Ensure no overlap between H and V
    for m in h_metals:
        if m in v_metals_virtual:
            return False
            
    return True

def find_global_best_configuration(stack_rules, selected_stack, max_temp, current_per_unit, 
                                   num_cols, h_space_w, device_w_used, metal_pairs, 
                                   w_coeff, l_coeff):
    """
    Orchestrates a global design space exploration to find the most efficient stack.

    Iterates through all defined combinations in METAL_STACK_MAP, filters for 
    valid layouts using is_combination_valid, and executes a sweep for each 
    to identify the combination yielding the minimum stripe width.

    Args:
        (Same as sweep_best_metal_width, excluding h_metal_comb)

    Returns:
        dict: The best configuration dictionary containing 'h', 'v', and 'width'.
              Returns None if no viable configuration is found.
    """
    
    best_config = None
    min_width_overall = 999.0
    
    # Iterate through all possible combinations in your map
    for h_name in em.METAL_STACK_MAP.keys():
        for v_name in em.METAL_STACK_MAP.keys():
            
            if is_combination_valid(h_name, v_name):
                # FIX: Pass all required arguments to the function
                result_dict = sweep_best_metal_width(
                    stack_rules=stack_rules, 
                    selected_stack=selected_stack, 
                    max_temp=max_temp, 
                    current_per_unit=current_per_unit, 
                    num_cols=num_cols, 
                    h_metal_comb=h_name, 
                    h_space_w=h_space_w, 
                    device_w_used=device_w_used, 
                    metal_pairs=metal_pairs, 
                    w_coeff=w_coeff, 
                    l_coeff=l_coeff
                )
                
                # Extract the numeric value safely
                width_val = result_dict.get('best_metal_width', 0.0)
                
                # NOW compare the number
                if width_val > 0 and width_val < min_width_overall:
                    min_width_overall = width_val
                    best_config = {"h": h_name, "v": v_name, "width": width_val}
                    
    return best_config