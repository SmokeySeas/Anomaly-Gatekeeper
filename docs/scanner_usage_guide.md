# Parameter Space Scanner Usage Guide - v0.2.1

## Overview

The parameter space scanner systematically explores fermion quantum number assignments to discover anomaly-free extensions to the Standard Model. It follows a structured block approach:
- **Block A**: Single fermion additions with |Y| ≤ 1
- **Block B**: Exhaustive vector-like pair search
- **Block B-prime**: Optional vector-like partners of Block A hits
- **Block C**: Higgsino-style chiral pairs

The scanner automatically rediscovers known consistent models (right-handed neutrino, vector-like fermions, MSSM Higgsinos) and can find novel anomaly-free combinations.

## Installation

1. Place the scanner in a `scripts/` directory within your project:
```
anomaly-checker/
├── anomaly_checker.py
├── scripts/
│   └── scan_param_space.py
└── scan_templates/
    └── standard_scan.json
```

2. Ensure the scanner can import the anomaly checker module (the script automatically adds the parent directory to the Python path).

## Basic Usage

### Quick Scan

For a rapid scan with limited parameter range:

```bash
cd scripts
python scan_param_space.py ../scan_templates/standard_scan.json --quick
```

This will:
- Scan hypercharges with k ∈ [-3, 3] (Y = k/6)
- Check only SU(3) representations {1, 3}
- Check only SU(2) representations {1, 2}

### Full Scan

For a comprehensive scan:

```bash
python scan_param_space.py ../scan_templates/standard_scan.json
```

This explores:
- Block A: Single fermions with k ∈ [-6, 6] (|Y| ≤ 1)
- Block B: All vector-like pairs
- Block B-prime: Vector-like partners of Block A hits
- Block C: Higgsino-style pairs

### Extended Hypercharge Range

To explore larger hypercharge values:

```bash
python scan_param_space.py ../scan_templates/standard_scan.json --hyper-max 12
```

This extends the k range to [-12, 12] for Y = k/6.

### Limited Scan

To stop after finding a specific number of models:

```bash
python scan_param_space.py ../scan_templates/standard_scan.json --limit 100
```

### Custom Output

To specify the output file and display limits:

```bash
python scan_param_space.py template.json --output results.json --max-display 50
```

## Expected Output

The scanner will produce output like:

```
Starting comprehensive parameter space scan...
============================================================

Scanning vector-like fermion pairs...
Found 89 anomaly-free vector-like models

Scanning chiral fermion pairs...
Found 24 anomaly-free chiral models

Total configurations scanned: 432
Anomaly-free models found: 113

============================================================
ANOMALY-FREE MODELS DISCOVERED
============================================================

Vector-like fermion pairs:
----------------------------------------
1. Vector-like pair: (1, 1)_0
2. Vector-like pair: (1, 1)_1
3. Vector-like pair: (1, 2)_-1/2
4. Vector-like pair: (1, 2)_1/2
5. Vector-like pair: (3, 1)_1/3
...

Chiral fermion pairs (MSSM-like):
----------------------------------------
1. Chiral pair: (1, 2)_{+1/2, -1/2}
2. Chiral pair: (1, 1)_{+1, -1}
3. Chiral pair: (3, 1)_{+1/3, -1/3}
...

============================================================
VERIFICATION OF KNOWN MODELS
============================================================
✓ Found vector-like lepton doublet: (1, 2)_-1/2
✓ Found MSSM Higgsino pair: (1, 2)_{+1/2, -1/2}
✓ Found vector-like quark doublet: (3, 2)_1/6

Results exported to anomaly_free_models.json
```

## JSON Template Structure

The template file controls the scan parameters:

```json
{
  "base_spectrum": [
    // Standard Model fermions
  ],
  "scan_config": {
    "hypercharge": {
      "use_k_over_6": true,          // Use Y = k/6 grid
      "abs_max": 1.0,                // |Y| ≤ abs_max for Block A
      "comment": "..."               // Documentation
    },
    "su3_rep": {
      "values": [1, 3, 6, 8]         // SU(3) representations
    },
    "su2_rep": {
      "values": [1, 2, 3]            // SU(2) representations
    },
    "scan_block_a_pairs": true       // Enable Block B-prime
  }
}
```

### Configuration Options

- **`use_k_over_6`**: When true, generates hypercharges as Y = k/6
- **`abs_max`**: Maximum absolute value of Y for Block A (default: 1.0)
- **`scan_block_a_pairs`**: When true, also searches for vector-like partners of Block A hits

## Output File Format

The scanner exports results to JSON:

```json
{
  "scan_config": { ... },
  "base_spectrum": [ ... ],
  "anomaly_free_models": [
    {
      "description": "Vector-like pair: (1, 2)_-1/2",
      "fermions": [
        // Complete fermion spectrum including SM + new particles
      ],
      "is_anomaly_free": true
    }
  ]
}
```

## Advanced Features

### Modifying Existing Fermions

To scan variations of existing SM fermions:

```json
{
  "scan_config": {
    "modify_existing": true,
    "skip_fermions": ["Q_L", "L_L"]  // Don't modify these
  }
}
```

### Custom Hypercharge Ranges

For focused searches:

```json
{
  "scan_config": {
    "hypercharge": {
      "include_standard": false,
      "range": [0, 3],
      "denominators": [1, 3, 9]  // For Z3 symmetric models
    }
  }
}
```

## Physics Applications

### Finding Left-Right Symmetric Models

Modify the template to include parity-paired fermions and scan for models that respect left-right symmetry.

### Searching for Dark Sector Candidates

Look for fermions with integer hypercharge that could be dark matter candidates:

```json
{
  "scan_config": {
    "hypercharge": {
      "include_standard": false,
      "range": [0, 5],
      "denominators": [1]  // Integer charges only
    }
  }
}
```

## Performance Considerations

- Quick scan: ~50-100 configurations, < 1 second
- Standard scan: ~300-500 configurations, ~2-5 seconds  
- Full scan with extended range: ~1000-2000 configurations, ~10-20 seconds

The scanner uses exact fraction arithmetic to avoid numerical errors in anomaly calculations. Individual model files are saved to `results/` directory for detailed analysis.

## Version History

### v0.2.1 (Current)
- Refined |Y| ≤ 1 constraint for Block A
- Added configurable `abs_max` parameter
- Added optional Block B-prime scan using Block A hits
- Fixed fermion name mutation issue
- Improved machine-friendly signatures in export

### v0.2
- Implemented structured block approach (A, B, C)
- Added CLI options for `--hyper-max` and `--limit`
- SHA1-based file naming for results
- Machine-friendly (su3,su2,Y,ch) signatures

## Next Steps

With v0.2.1 complete and spec-compliant, the next major milestone is:

1. **YAML Rule Loader**: Implement dynamic pattern loading from YAML configuration files
2. **Dark Sector Exploration**: Use integer hypercharge grids for dark matter candidates
3. **Left-Right Symmetric Models**: Explore parity-symmetric extensions
4. **Parameter Space Visualization**: Add plotting capabilities for the anomaly landscape
5. **Parallel Processing**: Implement multiprocessing for large-scale scans

The scanner now provides a robust foundation for systematic BSM exploration!