# PROJECT_SUMMARY.md
## Purpose
A two–stage tool‑chain to scan BSM fermion spectra for gauge/gravitational
anomaly cancellation:

1. **anomaly_checker.py**  
   – Core math (already rock‑solid, tested, 25 pytest cases).

2. **param_space_scanner.py v0.2.1**  
   – Implements three scan blocks  
     A  single‑fermion additions (|Y|≤1, k/6 grid)  
     B  vector‑like pairs (exhaustive) + optional B′ (Block‑A seeds)  
     C  Higgsino‑style chiral doublets (SU3 = 1, SU2 = 2, Y∈{½,1,3⁄2})  
   – CLI: `--hyper-max`, `--limit`, `--quick`  
   – Saves **one JSON per anomaly‑free spectrum** in `results/`, file name
     `tag_SHA10.json` + machine‑readable `"signature"` list.

3. **yaml_rule_loader.py**  
   – Parses `scanner_rules.yaml`‑style files into `ScanRule` objects.  
   – Constraint types: `integer`, `rational`, `grid (k/6)`, `range`, `set`.  
   – Optional representation / symmetry constraints.  
   – Exposes `get_scan_configuration()` (→scanner config) and
     `get_physics_sets()` (hand‑crafted spectra).

4. **scan_with_rules.py** (integration wrapper)  
   – CLI: `--rule-file`, `--rule`, `--batch`, passes `--hyper-max/limit` down.  
   – Builds base spectrum (e.g. SM no ν_R) and runs the blocks selected in the
     YAML rule.  
   – Exports per‑rule results + batch summary.

## Confirmed working
* All 25 pytest tests green.  
* Example runs reproduce ν_R, vector‑like lepton doublet, MSSM Higgsinos.  
* YAML demos (`configs/dark_sector_integer_hypercharges.yaml`,
  `scanner_rules.yaml`) load & scan.

## Open TODOs before a rock‑solid v0.3
1. **Hypercharge hand‑off** – ensure `ConstraintType.SET/RANGE`
   becomes something `generate_hypercharge_values()` consumes
   (`custom_values` vs `include_standard+use_k_over_6`).
2. **Expose Block B′ flag** – pass `scan_block_a_pairs` via YAML
   (`block_options:`).
3. **Robust fraction parsing** – guard against “1/0”, stray chars.
4. Stable ordering & dedup of hypercharge grids (`sorted(set(...))`).
5. Reject malformed YAML early (missing keys, wrong types).
6. SHA‑duplicate filter to avoid silent overwrite.
7. Add three micro‑pytest tests for the rule loader.

## How to run quick sanity scans
```bash
# Standard template, quick
python scan_param_space.py scan_template.json --quick --limit 20

# YAML rule example
python scan_with_rules.py --rule-file scanner_rules.yaml --rule SM_Plus_VectorLike_Pair_BlockB --limit 50
