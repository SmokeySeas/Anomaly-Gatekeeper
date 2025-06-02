#!/usr/bin/env python3
"""
rule_loader.py
==============
YAML-based rule loading system for dynamic parameter space scanning.
Enables physics-motivated search strategies without code modification.

Author: Bryan Roy & Claude
Version: 1.0
"""

import yaml
import json
import fractions
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
import sys

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.anomaly_checker import Fermion
except ImportError:
    print("Warning: anomaly_checker.py not found. Some functionality may be limited.")


class ConstraintType(Enum):
    """Types of constraints that can be applied in rules"""
    EXACT = "exact"
    RANGE = "range"
    SET = "set"
    INTEGER = "integer"
    RATIONAL = "rational"
    GRID = "grid"
    EXCLUDE = "exclude"


class SymmetryType(Enum):
    """Types of symmetries that can be enforced"""
    PARITY = "parity"
    CHARGE_CONJUGATION = "charge_conjugation"
    FAMILY = "family"
    CUSTODIAL = "custodial"
    DISCRETE = "discrete"


@dataclass
class HyperchargeConstraint:
    """Hypercharge constraint specification"""
    type: ConstraintType
    values: Optional[List[fractions.Fraction]] = None
    range: Optional[Tuple[float, float]] = None
    denominators: Optional[List[int]] = None
    grid_spec: Optional[Dict[str, Any]] = None
    exclude: Optional[List[fractions.Fraction]] = None
    
    def generate_values(self) -> List[fractions.Fraction]:
        """Generate allowed hypercharge values based on constraint type"""
        if self.type == ConstraintType.EXACT:
            return self.values or []
            
        elif self.type == ConstraintType.SET:
            return self.values or []
            
        elif self.type == ConstraintType.INTEGER:
            if self.range:
                return [fractions.Fraction(i) for i in 
                       range(int(self.range[0]), int(self.range[1]) + 1)]
            return []
            
        elif self.type == ConstraintType.RATIONAL:
            values = []
            if self.range and self.denominators:
                for den in self.denominators:
                    for num in range(int(self.range[0] * den), 
                                   int(self.range[1] * den) + 1):
                        values.append(fractions.Fraction(num, den))
            return list(set(values))
            
        elif self.type == ConstraintType.GRID:
            if self.grid_spec:
                k_max = self.grid_spec.get('k_max', 6)
                denominator = self.grid_spec.get('denominator', 6)
                values = []
                for k in range(-k_max, k_max + 1):
                    values.append(fractions.Fraction(k, denominator))
                return values
            return []
            
        elif self.type == ConstraintType.RANGE:
            # For continuous ranges, discretize with common denominators
            values = []
            if self.range:
                for den in (self.denominators or [1, 2, 3, 6]):
                    for num in range(int(self.range[0] * den), 
                                   int(self.range[1] * den) + 1):
                        val = fractions.Fraction(num, den)
                        if self.range[0] <= float(val) <= self.range[1]:
                            values.append(val)
            return list(set(values))
            
        return []
    
    def apply_exclusions(self, values: List[fractions.Fraction]) -> List[fractions.Fraction]:
        """Remove excluded values from the list"""
        if self.exclude:
            return [v for v in values if v not in self.exclude]
        return values


@dataclass
class RepresentationConstraint:
    """Gauge group representation constraint"""
    allowed_values: List[int]
    forbidden_combinations: Optional[List[Tuple[int, int, int]]] = None
    
    def is_allowed(self, su3: int, su2: int) -> bool:
        """Check if a representation combination is allowed"""
        if self.forbidden_combinations:
            for f_su3, f_su2, _ in self.forbidden_combinations:
                if su3 == f_su3 and su2 == f_su2:
                    return False
        return True


@dataclass 
class SymmetryRequirement:
    """Symmetry enforcement specification"""
    type: SymmetryType
    pairs: Optional[List[Tuple[str, str]]] = None
    group_action: Optional[Dict[str, Any]] = None
    constraints: Optional[Dict[str, Any]] = None


@dataclass
class ScanRule:
    """Complete scanning rule specification"""
    name: str
    description: str
    base_spectrum: str
    blocks: List[str] = field(default_factory=list)
    hypercharge_constraints: Optional[HyperchargeConstraint] = None
    su3_constraints: Optional[RepresentationConstraint] = None
    su2_constraints: Optional[RepresentationConstraint] = None
    symmetry_requirements: List[SymmetryRequirement] = field(default_factory=list)
    physics_motivated_sets: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class YAMLRuleLoader:
    """
    Loads and manages scanning rules from YAML configuration files.
    Provides translation between human-readable YAML rules and 
    scanner-compatible configurations.
    """
    
    def __init__(self, rule_file: Union[str, Path]):
        """Initialize the rule loader with a YAML file"""
        self.rule_file = Path(rule_file)
        if not self.rule_file.exists():
            raise FileNotFoundError(f"Rule file not found: {self.rule_file}")
        
        self.rules: Dict[str, ScanRule] = {}
        self._load_rules()
    
    def _parse_fraction(self, value: Union[str, int, float]) -> fractions.Fraction:
        """Parse various fraction representations"""
        if isinstance(value, str):
            # Handle formats like "1/3", "-2/3", etc.
            if '/' in value:
                parts = value.split('/')
                return fractions.Fraction(int(parts[0]), int(parts[1]))
            else:
                return fractions.Fraction(int(value))
        elif isinstance(value, (int, float)):
            return fractions.Fraction(value).limit_denominator(100)
        else:
            raise ValueError(f"Cannot parse fraction from: {value}")
    
    def _parse_hypercharge_constraint(self, constraint_dict: Dict[str, Any]) -> HyperchargeConstraint:
        """Parse hypercharge constraint from YAML data"""
        constraint_type = ConstraintType(constraint_dict.get('type', 'range'))
        
        hc = HyperchargeConstraint(type=constraint_type)
        
        # Parse based on type
        if constraint_type in [ConstraintType.EXACT, ConstraintType.SET]:
            values = constraint_dict.get('values', [])
            hc.values = [self._parse_fraction(v) for v in values]
            
        elif constraint_type == ConstraintType.INTEGER:
            hc.range = tuple(constraint_dict.get('range', [0, 5]))
            
        elif constraint_type == ConstraintType.RATIONAL:
            hc.range = tuple(constraint_dict.get('range', [-2, 2]))
            hc.denominators = constraint_dict.get('denominators', [1, 2, 3, 6])
            
        elif constraint_type == ConstraintType.GRID:
            hc.grid_spec = {
                'k_max': constraint_dict.get('k_max', 6),
                'denominator': constraint_dict.get('denominator', 6)
            }
            
        elif constraint_type == ConstraintType.RANGE:
            hc.range = tuple(constraint_dict.get('range', [-2, 2]))
            hc.denominators = constraint_dict.get('denominators', [1, 2, 3, 6])
        
        # Handle exclusions
        if 'exclude' in constraint_dict:
            hc.exclude = [self._parse_fraction(v) for v in constraint_dict['exclude']]
        
        return hc
    
    def _parse_representation_constraint(self, constraint_dict: Dict[str, Any]) -> RepresentationConstraint:
        """Parse representation constraint from YAML data"""
        allowed = constraint_dict.get('values', [1, 2, 3])
        
        rc = RepresentationConstraint(allowed_values=allowed)
        
        # Parse forbidden combinations if present
        if 'forbidden_combinations' in constraint_dict:
            forbidden = []
            for combo in constraint_dict['forbidden_combinations']:
                if isinstance(combo, dict):
                    forbidden.append((
                        combo.get('su3', 0),
                        combo.get('su2', 0),
                        self._parse_fraction(combo.get('hypercharge', 0))
                    ))
            rc.forbidden_combinations = forbidden
        
        return rc
    
    def _parse_symmetry_requirement(self, sym_dict: Dict[str, Any]) -> SymmetryRequirement:
        """Parse symmetry requirement from YAML data"""
        sym_type = SymmetryType(sym_dict['type'])
        
        req = SymmetryRequirement(type=sym_type)
        
        if 'pairs' in sym_dict:
            req.pairs = [(p.split(':')[0], p.split(':')[1]) 
                        for p in sym_dict['pairs']]
        
        if 'group_action' in sym_dict:
            req.group_action = sym_dict['group_action']
        
        if 'constraints' in sym_dict:
            req.constraints = sym_dict['constraints']
        
        return req
    
    def _load_rules(self) -> None:
        """Load and parse all rules from the YAML file"""
        try:
            with open(self.rule_file, 'r') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {self.rule_file}: {e}")
        
        if not data or 'rule_sets' not in data:
            raise ValueError("YAML file must contain 'rule_sets' key")
        
        for rule_data in data['rule_sets']:
            rule = self._parse_rule(rule_data)
            self.rules[rule.name] = rule
    
    def _parse_rule(self, rule_data: Dict[str, Any]) -> ScanRule:
        """Parse a single rule from YAML data"""
        # Required fields
        name = rule_data.get('name')
        if not name:
            raise ValueError("Rule must have a 'name' field")
        
        description = rule_data.get('description', '')
        base_spectrum = rule_data.get('base_spectrum', 'standard_model')
        
        # Create rule object
        rule = ScanRule(
            name=name,
            description=description,
            base_spectrum=base_spectrum,
            blocks=rule_data.get('blocks', ['A', 'B', 'C'])
        )
        
        # Parse constraints
        if 'constraints' in rule_data:
            constraints = rule_data['constraints']
            
            if 'hypercharge' in constraints:
                rule.hypercharge_constraints = self._parse_hypercharge_constraint(
                    constraints['hypercharge']
                )
            
            if 'su3_rep' in constraints:
                rule.su3_constraints = self._parse_representation_constraint(
                    constraints['su3_rep']
                )
            
            if 'su2_rep' in constraints:
                rule.su2_constraints = self._parse_representation_constraint(
                    constraints['su2_rep']
                )
        
        # Parse symmetry requirements
        if 'symmetry_requirements' in rule_data:
            for sym_data in rule_data['symmetry_requirements']:
                rule.symmetry_requirements.append(
                    self._parse_symmetry_requirement(sym_data)
                )
        
        # Parse physics-motivated sets
        if 'physics_motivated_sets' in rule_data:
            rule.physics_motivated_sets = rule_data['physics_motivated_sets']
        
        # Store any additional metadata
        rule.metadata = {k: v for k, v in rule_data.items() 
                        if k not in ['name', 'description', 'base_spectrum', 
                                    'blocks', 'constraints', 'symmetry_requirements',
                                    'physics_motivated_sets']}
        
        return rule
    
    def get_scan_configuration(self, rule_name: str) -> Dict[str, Any]:
        """
        Convert a rule into a configuration compatible with ParameterSpaceScanner.
        
        Args:
            rule_name: Name of the rule to convert
            
        Returns:
            Dictionary compatible with scan_config parameter
        """
        if rule_name not in self.rules:
            raise ValueError(f"Unknown rule: {rule_name}")
        
        rule = self.rules[rule_name]
        config = {}
        
        # Convert hypercharge constraints
        if rule.hypercharge_constraints:
            hc = rule.hypercharge_constraints
            
            if hc.type == ConstraintType.GRID:
                config['hypercharge'] = {
                    'use_k_over_6': True,
                    'k_max': hc.grid_spec.get('k_max', 6)
                }
            elif hc.type == ConstraintType.INTEGER:
                # Special handling for integer-only hypercharges
                config['hypercharge'] = {
                    'include_standard': False,
                    'range': hc.range,
                    'denominators': [1]
                }
            else:
                values = hc.generate_values()
                values = hc.apply_exclusions(values)
                config['hypercharge'] = {
                    'custom_values': [str(v) for v in values]
                }
        
        # Convert representation constraints
        if rule.su3_constraints:
            config['su3_rep'] = {'values': rule.su3_constraints.allowed_values}
        
        if rule.su2_constraints:
            config['su2_rep'] = {'values': rule.su2_constraints.allowed_values}
        
        # Add block configuration
        config['enabled_blocks'] = rule.blocks
        
        # Add metadata
        config['rule_metadata'] = {
            'name': rule.name,
            'description': rule.description,
            'base_spectrum': rule.base_spectrum
        }
        
        return config
    
    def get_physics_sets(self, rule_name: str) -> List[List[Fermion]]:
        """
        Get pre-defined physics-motivated fermion sets for a rule.
        
        Args:
            rule_name: Name of the rule
            
        Returns:
            List of fermion sets to test
        """
        if rule_name not in self.rules:
            raise ValueError(f"Unknown rule: {rule_name}")
        
        rule = self.rules[rule_name]
        fermion_sets = []
        
        for set_data in rule.physics_motivated_sets:
            fermions = []
            for f_data in set_data.get('fermions', []):
                fermion = Fermion(
                    name=f_data['name'],
                    su3_rep=f_data['su3_rep'],
                    su2_rep=f_data['su2_rep'],
                    hypercharge=self._parse_fraction(f_data['hypercharge']),
                    chirality=f_data.get('chirality', 1),
                    generations=f_data.get('generations', 1)
                )
                fermions.append(fermion)
            
            if fermions:
                fermion_sets.append(fermions)
        
        return fermion_sets
    
    def validate_fermion_set(self, fermions: List[Fermion], rule_name: str) -> Tuple[bool, List[str]]:
        """
        Validate that a fermion set satisfies rule constraints.
        
        Args:
            fermions: List of fermions to validate
            rule_name: Name of rule to validate against
            
        Returns:
            Tuple of (is_valid, list_of_violations)
        """
        if rule_name not in self.rules:
            raise ValueError(f"Unknown rule: {rule_name}")
        
        rule = self.rules[rule_name]
        violations = []
        
        # Check representation constraints
        for fermion in fermions:
            if rule.su3_constraints:
                if fermion.su3_rep not in rule.su3_constraints.allowed_values:
                    violations.append(
                        f"{fermion.name}: SU(3) rep {fermion.su3_rep} not allowed"
                    )
            
            if rule.su2_constraints:
                if fermion.su2_rep not in rule.su2_constraints.allowed_values:
                    violations.append(
                        f"{fermion.name}: SU(2) rep {fermion.su2_rep} not allowed"
                    )
            
            if rule.hypercharge_constraints:
                allowed_values = rule.hypercharge_constraints.generate_values()
                allowed_values = rule.hypercharge_constraints.apply_exclusions(allowed_values)
                if fermion.hypercharge not in allowed_values:
                    violations.append(
                        f"{fermion.name}: Hypercharge {fermion.hypercharge} not allowed"
                    )
        
        # Check symmetry requirements
        for sym_req in rule.symmetry_requirements:
            if sym_req.type == SymmetryType.PARITY and sym_req.pairs:
                # Check that specified pairs exist with matching quantum numbers
                fermion_dict = {f.name: f for f in fermions}
                for left_name, right_name in sym_req.pairs:
                    if left_name not in fermion_dict or right_name not in fermion_dict:
                        violations.append(
                            f"Parity pair ({left_name}, {right_name}) incomplete"
                        )
                    else:
                        left = fermion_dict[left_name]
                        right = fermion_dict[right_name]
                        # Check quantum number matching for parity
                        if (left.su3_rep != right.su3_rep or 
                            left.su2_rep != right.su2_rep):
                            violations.append(
                                f"Parity pair ({left_name}, {right_name}) "
                                f"has mismatched representations"
                            )
        
        return len(violations) == 0, violations
    
    def list_rules(self) -> List[Tuple[str, str]]:
        """Get list of available rules with descriptions"""
        return [(name, rule.description) for name, rule in self.rules.items()]
    
    def export_rule(self, rule_name: str, output_file: Union[str, Path]) -> None:
        """Export a rule configuration to JSON for archival"""
        if rule_name not in self.rules:
            raise ValueError(f"Unknown rule: {rule_name}")
        
        config = self.get_scan_configuration(rule_name)
        
        with open(output_file, 'w') as f:
            json.dump(config, f, indent=2)


def create_example_rules():
    """Create example YAML rule files for demonstration"""
    
    # Dark sector rules
    dark_sector_yaml = """# Dark Sector Search Rules
# Focused on integer hypercharge candidates for dark matter

rule_sets:
  - name: "minimal_dark_sector"
    description: "Minimal dark sector with integer electric charges"
    base_spectrum: "standard_model"
    blocks: ["A", "B"]  # Single additions and vector-like pairs only
    constraints:
      hypercharge:
        type: "integer"
        range: [0, 5]
        exclude: [1]  # Exclude Q=1 (would be electromagnetically charged)
      su3_rep:
        values: [1, 8]  # Color singlets and octets
      su2_rep:
        values: [1]  # SU(2) singlets for stability
    physics_motivated_sets:
      - name: "dark_fermion_singlet"
        fermions:
          - name: "chi"
            su3_rep: 1
            su2_rep: 1
            hypercharge: 0
            chirality: 1
            
  - name: "extended_dark_sector"
    description: "Dark sector with SU(2) structure"
    base_spectrum: "standard_model"
    blocks: ["A", "B", "C"]
    constraints:
      hypercharge:
        type: "integer"
        range: [-2, 2]
      su3_rep:
        values: [1]  # Color singlets only
      su2_rep:
        values: [1, 2]  # Allow doublets
    symmetry_requirements:
      - type: "discrete"
        constraints:
          Z2_charge: "odd"  # Dark parity
"""
    
    # Scanner rules for general searches
    scanner_rules_yaml = """# General Scanner Rules
# Configurable search patterns for BSM physics

rule_sets:
  - name: "vector_like_search"
    description: "Comprehensive vector-like fermion search"
    base_spectrum: "standard_model"
    blocks: ["B"]  # Vector-like pairs only
    constraints:
      hypercharge:
        type: "grid"
        k_max: 12
        denominator: 6
      su3_rep:
        values: [1, 3, 6, 8]
      su2_rep:
        values: [1, 2, 3]
        
  - name: "left_right_symmetric"
    description: "Left-right symmetric model building"
    base_spectrum: "left_right_template"
    blocks: ["A", "B"]
    constraints:
      hypercharge:
        type: "rational"
        range: [-2, 2]
        denominators: [1, 2, 3, 6]
    symmetry_requirements:
      - type: "parity"
        pairs: ["Q_L:Q_R", "L_L:L_R", "u_L:u_R", "d_L:d_R", "e_L:e_R"]
        
  - name: "331_model_search"
    description: "Search for 3-3-1 model compatible fermions"
    base_spectrum: "standard_model"
    blocks: ["A", "B", "C"]
    constraints:
      hypercharge:
        type: "rational"
        range: [-4/3, 4/3]
        denominators: [3]
      su3_rep:
        values: [1, 3, 6]
      su2_rep:
        values: [1, 3]  # Extended to SU(3) representations
    physics_motivated_sets:
      - name: "exotic_quarks"
        fermions:
          - name: "D"
            su3_rep: 3
            su2_rep: 1
            hypercharge: "-4/3"
            chirality: 1
          - name: "S"
            su3_rep: 3
            su2_rep: 1
            hypercharge: "5/3"
            chirality: 1
            
  - name: "family_unified"
    description: "Family unification inspired search"
    base_spectrum: "standard_model"
    blocks: ["A", "B", "C"]
    constraints:
      hypercharge:
        type: "set"
        values: ["0", "1/3", "2/3", "-1/3", "-2/3", "1/2", "-1/2"]
    symmetry_requirements:
      - type: "family"
        constraints:
          family_group: "SU(3)_F"
          mixing_allowed: true
"""
    
    return dark_sector_yaml, scanner_rules_yaml


# Example usage and testing
if __name__ == "__main__":
    # Create example rule files
    dark_yaml, scanner_yaml = create_example_rules()
    
    # Save example files
    with open("dark_sector_rules_example.yaml", "w") as f:
        f.write(dark_yaml)
    
    with open("scanner_rules_example.yaml", "w") as f:
        f.write(scanner_yaml)
    
    print("Example YAML rule files created!")
    
    # Test loading
    try:
        loader = YAMLRuleLoader("scanner_rules_example.yaml")
        print("\nAvailable rules:")
        for name, desc in loader.list_rules():
            print(f"  - {name}: {desc}")
        
        # Test configuration generation
        config = loader.get_scan_configuration("vector_like_search")
        print("\nVector-like search configuration:")
        print(json.dumps(config, indent=2))
        
    except Exception as e:
        print(f"Error testing rule loader: {e}")
