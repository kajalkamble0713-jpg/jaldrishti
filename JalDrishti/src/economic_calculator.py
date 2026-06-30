"""
JalDrishti Economic Burden Calculator
Translates outbreak probability to district-level economic costs
Based on published Indian health economics literature
"""

def calculate_economic_burden(district_name, state_name, disease, probability, population=500000):
    """
    Calculate economic burden of waterborne disease outbreak
    
    Parameters:
    -----------
    district_name : str
        Name of the district
    state_name : str
        Name of the state
    disease : str
        Disease type ('ADD', 'Cholera', or 'Typhoid')
    probability : float
        Outbreak probability (0-1)
    population : int
        District population (default: 500,000)
    
    Returns:
    --------
    dict with keys:
        - direct_cost_crore: Direct medical costs (₹ crore)
        - indirect_cost_crore: Indirect economic losses (₹ crore)
        - total_cost_crore: Total economic burden (₹ crore)
        - lives_at_risk: Estimated number of cases
        - cost_of_intervention_crore: Cost to prevent outbreak (₹ crore)
        - prevention_roi: Return on investment of prevention
    """
    
    # Base rates per case (in ₹)
    # Source: Indian health economics literature + IDSP data
    economic_params = {
        'ADD': {
            'direct_cost_per_case': 3200,      # Hospitalization + treatment
            'indirect_cost_per_case': 1800,    # Lost workdays + productivity
            'case_rate': 0.025                 # 2.5% of population during outbreak
        },
        'Cholera': {
            'direct_cost_per_case': 8500,
            'indirect_cost_per_case': 4200,
            'case_rate': 0.012                 # 1.2% of population
        },
        'Typhoid': {
            'direct_cost_per_case': 6100,
            'indirect_cost_per_case': 3500,
            'case_rate': 0.018                 # 1.8% of population
        }
    }
    
    if disease not in economic_params:
        raise ValueError(f"Unknown disease: {disease}. Must be 'ADD', 'Cholera', or 'Typhoid'")
    
    params = economic_params[disease]
    
    # Calculate expected cases (scaled by probability)
    people_at_risk = int(population * params['case_rate'])
    expected_cases = int(people_at_risk * probability)
    
    # Calculate direct costs (hospitalization, treatment, diagnostics)
    direct_cost = expected_cases * params['direct_cost_per_case']
    direct_cost_crore = round(direct_cost / 10000000, 2)  # Convert to crore
    
    # Calculate indirect costs (lost workdays, productivity loss, caregiver time)
    indirect_cost = expected_cases * params['indirect_cost_per_case']
    indirect_cost_crore = round(indirect_cost / 10000000, 2)
    
    # Total economic burden
    total_cost_crore = round(direct_cost_crore + indirect_cost_crore, 2)
    
    # Cost of intervention (early warning + preventive action)
    # Includes: water quality monitoring, chlorination, health camps, awareness
    cost_per_person_at_risk = 45  # ₹45 per person at risk
    intervention_cost = people_at_risk * cost_per_person_at_risk
    intervention_cost_crore = round(intervention_cost / 10000000, 2)
    
    # ROI of prevention
    if intervention_cost_crore > 0:
        prevention_roi = round(total_cost_crore / intervention_cost_crore, 1)
    else:
        prevention_roi = 0.0
    
    return {
        'district_name': district_name,
        'state_name': state_name,
        'disease': disease,
        'probability': round(probability, 3),
        'population': population,
        'direct_cost_crore': direct_cost_crore,
        'indirect_cost_crore': indirect_cost_crore,
        'total_cost_crore': total_cost_crore,
        'lives_at_risk': expected_cases,
        'people_at_risk': people_at_risk,
        'cost_of_intervention_crore': intervention_cost_crore,
        'prevention_roi': prevention_roi
    }


def calculate_multi_disease_burden(district_name, state_name, disease_probabilities, population=500000):
    """
    Calculate economic burden for multiple diseases
    
    Parameters:
    -----------
    district_name : str
        Name of the district
    state_name : str
        Name of the state
    disease_probabilities : dict
        Dictionary mapping disease names to probabilities
        Example: {'ADD': 0.45, 'Cholera': 0.32, 'Typhoid': 0.28}
    population : int
        District population
    
    Returns:
    --------
    dict with aggregated costs and individual disease breakdowns
    """
    
    results = {}
    total_direct = 0
    total_indirect = 0
    total_intervention = 0
    total_lives_at_risk = 0
    
    for disease, probability in disease_probabilities.items():
        burden = calculate_economic_burden(
            district_name, state_name, disease, probability, population
        )
        results[disease] = burden
        
        total_direct += burden['direct_cost_crore']
        total_indirect += burden['indirect_cost_crore']
        total_intervention += burden['cost_of_intervention_crore']
        total_lives_at_risk += burden['lives_at_risk']
    
    total_cost = total_direct + total_indirect
    
    return {
        'district_name': district_name,
        'state_name': state_name,
        'population': population,
        'total_direct_cost_crore': round(total_direct, 2),
        'total_indirect_cost_crore': round(total_indirect, 2),
        'total_cost_crore': round(total_cost, 2),
        'total_intervention_cost_crore': round(total_intervention, 2),
        'total_lives_at_risk': total_lives_at_risk,
        'overall_roi': round(total_cost / total_intervention, 1) if total_intervention > 0 else 0.0,
        'disease_breakdown': results
    }


# Example usage
if __name__ == "__main__":
    print("=" * 70)
    print("JalDrishti Economic Calculator - Example")
    print("=" * 70)
    
    # Single disease calculation
    print("\n1. Single Disease Calculation:")
    result = calculate_economic_burden(
        district_name="Patna",
        state_name="Bihar",
        disease="ADD",
        probability=0.45,
        population=500000
    )
    
    print(f"\nDistrict: {result['district_name']}, {result['state_name']}")
    print(f"Disease: {result['disease']}")
    print(f"Outbreak Probability: {result['probability']*100:.1f}%")
    print(f"Population: {result['population']:,}")
    print(f"\nEconomic Impact:")
    print(f"  Direct Medical Costs: ₹{result['direct_cost_crore']:.2f} crore")
    print(f"  Indirect Economic Loss: ₹{result['indirect_cost_crore']:.2f} crore")
    print(f"  Total Economic Burden: ₹{result['total_cost_crore']:.2f} crore")
    print(f"\nPrevention:")
    print(f"  Cost of Intervention: ₹{result['cost_of_intervention_crore']:.2f} crore")
    print(f"  ROI of Prevention: ₹{result['prevention_roi']:.1f} saved per ₹1 spent")
    print(f"  Lives at Risk: {result['lives_at_risk']:,} cases")
    
    # Multi-disease calculation
    print("\n" + "=" * 70)
    print("2. Multi-Disease Calculation:")
    
    multi_result = calculate_multi_disease_burden(
        district_name="Patna",
        state_name="Bihar",
        disease_probabilities={
            'ADD': 0.45,
            'Cholera': 0.32,
            'Typhoid': 0.28
        },
        population=500000
    )
    
    print(f"\nDistrict: {multi_result['district_name']}, {multi_result['state_name']}")
    print(f"Population: {multi_result['population']:,}")
    print(f"\nAggregated Economic Impact:")
    print(f"  Total Direct Costs: ₹{multi_result['total_direct_cost_crore']:.2f} crore")
    print(f"  Total Indirect Costs: ₹{multi_result['total_indirect_cost_crore']:.2f} crore")
    print(f"  Total Economic Burden: ₹{multi_result['total_cost_crore']:.2f} crore")
    print(f"  Total Intervention Cost: ₹{multi_result['total_intervention_cost_crore']:.2f} crore")
    print(f"  Overall ROI: ₹{multi_result['overall_roi']:.1f} saved per ₹1 spent")
    print(f"  Total Lives at Risk: {multi_result['total_lives_at_risk']:,} cases")
    
    print("\n" + "=" * 70)
