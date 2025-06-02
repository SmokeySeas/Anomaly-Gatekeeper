# YAML Rule Loader System Documentation

## Overview

The YAML Rule Loader system enables dynamic configuration of the parameter space scanner through human-readable YAML files. This system allows physicists to define complex scanning strategies without modifying Python code, making the tool more accessible and flexible for exploring various BSM physics scenarios.

## Architecture

The system consists of three main components:

### 1. Rule Loader (rule_loader.py)
The core module that parses YAML files and converts rules into scanner-compatible configurations. It provides validation, constraint generation, and physics-motivated set management.

### 2. Scanner Integration (scan_with_rules.py)
The integration layer that connects the rule loader with the existing parameter space scanner. It orchestrates scans based on YAML rules and manages output generation.

### 3. YAML Rule Files
Configuration files that define scanning strategies, constraints, and physics-motivated searches.

## YAML Rule Schema

Each YAML rule file must contain a `rule_sets` key with a list of rule definitions. Each rule supports the following fields:

### Required Fields

```yaml
rule_sets:
  - name: "rule_identifier"
    description: "Human-readable description"
    base_spectrum: "standard_model"  # or "left_right_template", etc.
```

### Optional Fields

#### Blocks Configuration
```yaml
blocks: ["A", "B", "C"]  # Which scanning blocks to enable
# A: Single fermion additions
# B: Vector-like pairs
# C: Chiral pairs (Higgsino-style)
```

#### Constraint Specifications

##### Hypercharge Constraints
```yaml
constraints:
  hypercharge:
    type: "integer"      # Type of constraint
    range: [0, 5]        # Value range
    exclude: [1]         # Values to exclude
```

Supported hypercharge constraint types:
- `integer`: Integer values only (for dark matter candidates)
- `rational`: Rational numbers with specified denominators
- `grid`: Y = k/denominator grid (default k/6)
- `set`: Explicit list of allowed values
- `range`: Continuous range discretized by denominators

##### Representation Constraints
```yaml
constraints:
  su3_rep:
    values: [1, 3, 6, 8]  # Allowed SU(3) representations
  su2_rep:
    values: [1, 2, 3]     # Allowed SU(2) representations
```

#### Symmetry Requirements
```yaml
symmetry_requirements:
  - type: "parity"
    pairs: ["Q_L:Q_R", "L_L:L_R"]
  - type: "discrete"
    constraints:
      Z2_charge: "odd"
```

#### Physics-Motivated Sets
```yaml
physics_motivated_sets:
  - name: "set_identifier"
    description: "Set description"
    fermions:
      - name: "X"
        su3_rep: 1
        su2_rep: 2
        hypercharge: "1/2"
        chirality: 1
```

## Usage Examples

### Basic Command-Line Usage

List available rules:
```bash
python scan_with_rules.py scanner_rules.yaml scan_template.json --list-rules
```

Run a specific rule:
```bash
python scan_with_rules.py scanner_rules.yaml scan_template.json -r vector_like_search
```

Batch scan multiple rules:
```bash
python scan_with_rules.py scanner_rules.yaml scan_template.json -b quick_scan comprehensive_bsm_search
```

### Dark Sector Search Example

Using the dark sector rules file:
```bash
python scan_with_rules.py dark_sector_integer_hypercharges.yaml scan_template.json -r minimal_dark_matter
```

This searches for color-singlet, SU(2)-singlet fermions with integer hypercharges suitable for dark matter candidates.

### Left-Right Symmetric Search

```bash
python scan_with_rules.py scanner_rules.yaml left_right_template.json -r left_right_symmetric
```

This enforces parity constraints while searching for fermions compatible with left-right symmetric models.

## Advanced Features

### Custom Hypercharge Grids

Define non-standard hypercharge grids:
```yaml
hypercharge:
  type: "grid"
  k_max: 9
  denominator: 3  # For Y = k/3 grid
```

### Forbidden Representation Combinations

Exclude specific quantum number combinations:
```yaml
su3_rep:
  values: [1, 3, 6, 8]
  forbidden_combinations:
    - su3: 8
      su2: 3
      hypercharge: "1/2"
```

### Complex Symmetry Requirements

Implement family symmetries or custodial symmetries:
```yaml
symmetry_requirements:
  - type: "family"
    constraints:
      family_group: "SU(3)_F"
      mixing_allowed: true
```

## Integration with Existing Scanner

The YAML rule loader seamlessly integrates with the existing parameter space scanner:

1. **Backward Compatibility**: The original scanner can still be used directly with JSON templates
2. **Dynamic Configuration**: Rules can override any scanner configuration parameter
3. **Result Compatibility**: Output format remains consistent with the original scanner

### Extending the Scanner

To add new constraint types or symmetry requirements:

1. Extend the appropriate Enum in `rule_loader.py`
2. Implement parsing logic in `_parse_*_constraint` methods
3. Add translation logic in `get_scan_configuration`

## Best Practices

### Rule Design

1. **Start Simple**: Begin with restrictive constraints and gradually expand
2. **Use Descriptive Names**: Rule names should indicate their physics motivation
3. **Document Thoroughly**: Include references and motivation in metadata

### Performance Optimization

1. **Limit Search Space**: Use `set` constraints for focused searches
2. **Disable Unused Blocks**: Only enable blocks relevant to your search
3. **Set Reasonable Limits**: Use `--limit` flag for exploratory runs

### Physics Validation

1. **Test Known Models**: Verify rules rediscover known anomaly-free models
2. **Cross-Check Results**: Compare with analytical expectations
3. **Validate Symmetries**: Ensure symmetry requirements are properly enforced

## Troubleshooting

### Common Issues

**Rule Not Found Error**
```
Error loading rule 'nonexistent': Unknown rule: nonexistent
```
Solution: Check rule name spelling and verify it exists in the YAML file

**Invalid YAML Syntax**
```
Error initializing scanner: Invalid YAML in rules.yaml: ...
```
Solution: Validate YAML syntax using an online validator

**Constraint Conflicts**
```
No allowed hypercharge values after applying constraints
```
Solution: Check for contradictory constraints or excessive exclusions

### Debug Mode

Enable verbose output by modifying the scanner:
```python
# In scan_with_rules.py
scanner = RuleBasedScanner(args.rule_file, args.template_file)
scanner.debug = True  # Add debug flag
```

## Example Rule Files

### Minimal Dark Matter Search
```yaml
rule_sets:
  - name: "minimal_dm"
    description: "Minimal dark matter candidate"
    base_spectrum: "standard_model"
    blocks: ["A"]
    constraints:
      hypercharge:
        type: "integer"
        range: [0, 0]  # Only Q=0
      su3_rep:
        values: [1]
      su2_rep:
        values: [1]
```

### Comprehensive Vector-Like Search
```yaml
rule_sets:
  - name: "all_vector_like"
    description: "All possible vector-like fermions"
    base_spectrum: "standard_model"
    blocks: ["B"]
    constraints:
      hypercharge:
        type: "grid"
        k_max: 18
        denominator: 6
      su3_rep:
        values: [1, 3, 6, 8]
      su2_rep:
        values: [1, 2, 3]
```

## Future Extensions

The YAML rule loader system is designed for extensibility. Planned enhancements include:

1. **Constraint Algebra**: Support for complex constraint combinations
2. **Dynamic Blocks**: User-defined scanning strategies beyond A, B, C
3. **Multi-Stage Rules**: Rules that depend on results from previous stages
4. **Parallel Execution**: Support for distributed scanning of rule sets
5. **Web Interface**: Browser-based rule creation and result visualization

## Conclusion

The YAML rule loader transforms the anomaly checker from a fixed-configuration tool into a flexible framework for systematic BSM exploration. By separating physics logic from implementation details, it enables rapid testing of theoretical ideas while maintaining rigorous mathematical verification of anomaly cancellation.