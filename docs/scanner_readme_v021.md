# Anomaly-Free Model Scanner v0.2.1

## 🎯 Project Status: Functionally Spec-Complete

The parameter space scanner has reached version 0.2.1 with full implementation of the agreed specification. All critical features are working and the scanner successfully rediscovers known anomaly-free models.

## ✅ What's Working

### Core Functionality
- **Block A**: Single fermion additions with |Y| ≤ 1 constraint
- **Block B**: Exhaustive vector-like pair search
- **Block B-prime**: Optional vector-like partners of Block A hits
- **Block C**: Higgsino-style chiral pairs (restricted to correct quantum numbers)

### Infrastructure
- ✓ CLI options: `--hyper-max`, `--limit`, `--quick`, `--max-display`
- ✓ Y = k/6 hypercharge grid with configurable range
- ✓ Per-model JSON export with SHA1-based naming
- ✓ Machine-friendly (su3,su2,Y,ch) signatures
- ✓ All 25 unit tests passing
- ✓ Rediscovers ν_R, vector-like doublets, and MSSM Higgsinos

## 📁 Project Structure

```
anomaly-checker/
├── anomaly_checker.py          # Core anomaly verification (v0.1)
├── test_anomaly_checker.py     # Comprehensive test suite
├── scripts/
│   └── scan_param_space.py     # Parameter scanner (v0.2.1)
├── scan_templates/
│   ├── standard_scan.json      # Standard Model base
│   └── left-right-template.json # L-R symmetric template
└── results/                    # Output directory for models
```

## 🚀 Quick Start

```bash
# Basic scan
cd scripts
python scan_param_space.py ../scan_templates/standard_scan.json

# Quick test with limits
python scan_param_space.py ../scan_templates/standard_scan.json --quick --limit 50

# Extended hypercharge range
python scan_param_space.py ../scan_templates/standard_scan.json --hyper-max 12
```

## 📊 Typical Results

A standard scan finds approximately:
- ~10-20 single fermion additions (Block A)
- ~80-100 vector-like pairs (Block B)
- ~3 Higgsino-style pairs (Block C)

All models are verified to have exact anomaly cancellation using fraction arithmetic.

## 🔄 Changes in v0.2.1

1. **Refined Block A constraint**: |Y| ≤ 1 (configurable via `abs_max`)
2. **Added Block B-prime**: Optional scan using Block A hits as seeds
3. **Fixed mutation issue**: Fermion names set before storage
4. **Configurable Y limit**: `abs_max` parameter in scan config

## 🎉 Team Acknowledgments

This project was completed in a single day through effective collaboration:
- **Bryan Roy**: Project lead and integration
- **Claude**: Implementation and testing infrastructure
- **Charlie**: Architecture and specification refinement
- **Gemini**: Cross-validation and alternative approaches

## 📈 Next Steps

The scanner is ready for:
1. YAML rule loader implementation
2. Dark sector exploration with integer hypercharges
3. Left-right symmetric model investigation
4. Large-scale parameter space mapping

---

**Version**: 0.2.1  
**Status**: Production Ready  
**Date**: [Current Date]  
**License**: [Your License]