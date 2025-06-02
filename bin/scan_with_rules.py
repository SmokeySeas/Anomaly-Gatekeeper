#!/usr/bin/env python3
"""
scan_with_rules.py
==================
Integration module that enables YAML rule-based scanning using the 
parameter space scanner with dynamic configuration.

Author: Bryan Roy & Claude
Version: 1.0
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import time

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.param_space_scanner import ParameterSpaceScanner, ScanResult
    from src.yaml_rule_loader import YAMLRuleLoader
    from src.anomaly_checker import Fermion, AnomalyChecker
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Ensure scan_param_space.py, rule_loader.py, and anomaly_checker.py are available")
    sys.exit(1)


class RuleBasedScanner:
    """
    Enhanced scanner that uses YAML rules for configuration.
    Integrates YAMLRuleLoader with ParameterSpaceScanner.
    """
    
    def __init__(self, rule_file: Path, template_file: Path):
        """
        Initialize the rule-based scanner.
        
        Args:
            rule_file: Path to YAML rule file
            template_file: Path to base spectrum template JSON
        """
        self.rule_loader = YAMLRuleLoader(rule_file)
        self.template_file = template_file
        
        # Load base template
        with open(template_file, 'r') as f:
            self.template_data = json.load(f)
    
    def scan_with_rule(self, rule_name: str, output_dir: Path = None,
                      hyper_max: Optional[int] = None,
                      limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Run a scan using a specific rule from the YAML file.
        
        Args:
            rule_name: Name of the rule to use
            output_dir: Directory for output files
            hyper_max: Override maximum k value for hypercharge grid
            limit: Maximum number of models to find
            
        Returns:
            Dictionary with scan results and statistics
        """
        # Get scan configuration from rule
        try:
            scan_config = self.rule_loader.get_scan_configuration(rule_name)
        except ValueError as e:
            print(f"Error loading rule '{rule_name}': {e}")
            return {}
        
        # Get the appropriate base spectrum
        rule = self.rule_loader.rules[rule_name]
        base_spectrum = self._get_base_spectrum(rule.base_spectrum)
        
        # Override scan configuration with rule-based config
        if 'hypercharge' in scan_config:
            # Handle custom values from rule
            if 'custom_values' in scan_config['hypercharge']:
                # Convert to standard format
                values = scan_config['hypercharge']['custom_values']
                scan_config['hypercharge'] = {
                    'include_standard': False,
                    'custom_values': values
                }
        
        # Apply any command-line overrides
        if hyper_max is not None and 'hypercharge' in scan_config:
            if 'use_k_over_6' in scan_config['hypercharge']:
                scan_config['hypercharge']['k_max'] = hyper_max
        
        # Create scanner with rule-based configuration
        scanner = ParameterSpaceScanner(base_spectrum, scan_config)
        
        # Disable blocks not specified in rule
        enabled_blocks = scan_config.get('enabled_blocks', ['A', 'B', 'C'])
        
        # Start timing
        start_time = time.time()
        
        # Run scans based on enabled blocks
        print(f"\nRunning scan with rule: {rule_name}")
        print(f"Description: {rule.description}")
        print(f"Enabled blocks: {', '.join(enabled_blocks)}")
        print("=" * 60)
        
        if 'A' in enabled_blocks:
            print("\nBlock A: Scanning single fermion additions...")
            scanner.scan_single_additions(hyper_max)
            
            if limit and len(scanner.anomaly_free_models) >= limit:
                print(f"Reached limit of {limit} models.")
        
        if 'B' in enabled_blocks and (not limit or len(scanner.anomaly_free_models) < limit):
            print("\nBlock B: Scanning vector-like fermion pairs...")
            scanner.scan_vector_like_pairs(use_block_a=False, hyper_max=hyper_max)
            
            if limit and len(scanner.anomaly_free_models) >= limit:
                print(f"Reached limit of {limit} models.")
        
        if 'C' in enabled_blocks and (not limit or len(scanner.anomaly_free_models) < limit):
            print("\nBlock C: Scanning chiral fermion pairs...")
            scanner.scan_chiral_pairs()
        
        # Test physics-motivated sets if available
        physics_sets = self.rule_loader.get_physics_sets(rule_name)
        if physics_sets:
            print(f"\nTesting {len(physics_sets)} physics-motivated sets...")
            self._test_physics_sets(scanner, physics_sets)
        
        # Calculate statistics
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # Prepare results
        results = {
            'rule_name': rule_name,
            'rule_description': rule.description,
            'base_spectrum': rule.base_spectrum,
            'total_configurations_tested': scanner.tested_configurations_count,
            'anomaly_free_models_found': len(scanner.anomaly_free_models),
            'scan_time_seconds': elapsed_time,
            'blocks_used': enabled_blocks,
            'models_by_type': self._categorize_models(scanner.anomaly_free_models)
        }
        
        # Save results
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(exist_ok=True)
            
            # Save summary
            summary_file = output_dir / f"scan_summary_{rule_name}.json"
            with open(summary_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            # Save detailed models
            if scanner.anomaly_free_models:
                models_file = output_dir / f"models_{rule_name}.json"
                scanner.export_results(str(models_file))
        
        # Print summary
        self._print_summary(results)
        
        return results
    
    def _get_base_spectrum(self, spectrum_name: str) -> List[Dict]:
        """Get base spectrum by name"""
        if spectrum_name == "standard_model":
            # Use the standard template base_spectrum
            return self.template_data.get('base_spectrum', [])
        elif spectrum_name == "left_right_template":
            # Load from left-right template if available
            lr_template = Path(self.template_file).parent / "left_right_template.json"
            if lr_template.exists():
                with open(lr_template, 'r') as f:
                    lr_data = json.load(f)
                return lr_data.get('base_spectrum', [])
        
        # Default to standard model
        return self.template_data.get('base_spectrum', [])
    
    def _test_physics_sets(self, scanner: ParameterSpaceScanner, 
                          physics_sets: List[List[Fermion]]) -> None:
        """Test pre-defined physics-motivated fermion sets"""
        base_fermions = [scanner.create_fermion_from_dict(f) 
                        for f in scanner.base_spectrum]
        
        for i, fermion_set in enumerate(physics_sets):
            test_spectrum = base_fermions + fermion_set
            checker = AnomalyChecker(test_spectrum)
            all_cancel, failures = checker.verify_cancellation()
            
            if all_cancel:
                # Create ScanResult
                desc = f"Physics-motivated set {i+1}"
                result = ScanResult(
                    spectrum=test_spectrum,
                    anomalies=checker.compute_anomalies(),
                    is_anomaly_free=True,
                    description=desc
                )
                scanner.results.append(result)
                scanner.anomaly_free_models.append(result)
                
                # Save to file
                tag = f"physics_set_{i+1}"
                scanner.dump_result(test_spectrum, tag)
    
    def _categorize_models(self, models: List[ScanResult]) -> Dict[str, int]:
        """Categorize models by type"""
        categories = {
            'single_fermion': 0,
            'vector_like': 0,
            'chiral_pair': 0,
            'physics_motivated': 0
        }
        
        for model in models:
            desc = model.description.lower()
            if "single fermion" in desc:
                categories['single_fermion'] += 1
            elif "vector-like" in desc:
                categories['vector_like'] += 1
            elif "chiral pair" in desc:
                categories['chiral_pair'] += 1
            elif "physics-motivated" in desc:
                categories['physics_motivated'] += 1
        
        return categories
    
    def _print_summary(self, results: Dict[str, Any]) -> None:
        """Print a formatted summary of scan results"""
        print("\n" + "=" * 60)
        print("SCAN COMPLETE")
        print("=" * 60)
        print(f"Rule: {results['rule_name']}")
        print(f"Description: {results['rule_description']}")
        print(f"Base spectrum: {results['base_spectrum']}")
        print(f"Total configurations tested: {results['total_configurations_tested']}")
        print(f"Anomaly-free models found: {results['anomaly_free_models_found']}")
        print(f"Scan time: {results['scan_time_seconds']:.2f} seconds")
        
        print("\nModels by type:")
        for category, count in results['models_by_type'].items():
            if count > 0:
                print(f"  {category.replace('_', ' ').title()}: {count}")
    
    def batch_scan(self, rule_names: List[str], output_dir: Path = None,
                  **kwargs) -> List[Dict[str, Any]]:
        """
        Run multiple scans in sequence.
        
        Args:
            rule_names: List of rule names to scan
            output_dir: Directory for output files
            **kwargs: Additional arguments passed to scan_with_rule
            
        Returns:
            List of results for each scan
        """
        all_results = []
        
        for rule_name in rule_names:
            print(f"\n{'#' * 60}")
            print(f"# Batch scan: {rule_name}")
            print(f"{'#' * 60}")
            
            results = self.scan_with_rule(rule_name, output_dir, **kwargs)
            if results:
                all_results.append(results)
        
        # Save batch summary
        if output_dir and all_results:
            batch_file = Path(output_dir) / "batch_scan_summary.json"
            with open(batch_file, 'w') as f:
                json.dump({
                    'batch_scan_results': all_results,
                    'total_models': sum(r['anomaly_free_models_found'] 
                                      for r in all_results),
                    'total_time': sum(r['scan_time_seconds'] for r in all_results)
                }, f, indent=2)
        
        return all_results


def main():
    """Main entry point for rule-based scanning"""
    parser = argparse.ArgumentParser(
        description="Run anomaly-free model scans using YAML rules"
    )
    
    parser.add_argument(
        "rule_file",
        type=Path,
        help="YAML file containing scanning rules"
    )
    
    parser.add_argument(
        "template_file",
        type=Path,
        help="JSON template file with base spectrum"
    )
    
    parser.add_argument(
        "-r", "--rule",
        help="Name of specific rule to use (otherwise lists available rules)"
    )
    
    parser.add_argument(
        "-b", "--batch",
        nargs="+",
        help="Run batch scan with multiple rules"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default="rule_scan_results",
        help="Output directory for results"
    )
    
    parser.add_argument(
        "--hyper-max",
        type=int,
        help="Override maximum k value for hypercharge grid"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of models to find"
    )
    
    parser.add_argument(
        "--list-rules",
        action="store_true",
        help="List available rules and exit"
    )
    
    args = parser.parse_args()
    
    # Verify files exist
    if not args.rule_file.exists():
        print(f"Error: Rule file not found: {args.rule_file}")
        sys.exit(1)
    
    if not args.template_file.exists():
        print(f"Error: Template file not found: {args.template_file}")
        sys.exit(1)
    
    # Create scanner
    try:
        scanner = RuleBasedScanner(args.rule_file, args.template_file)
    except Exception as e:
        print(f"Error initializing scanner: {e}")
        sys.exit(1)
    
    # List rules if requested
    if args.list_rules or (not args.rule and not args.batch):
        print("\nAvailable rules:")
        print("=" * 60)
        for name, desc in scanner.rule_loader.list_rules():
            print(f"\n{name}:")
            print(f"  {desc}")
        
        if not args.list_rules:
            print("\nUse -r RULE_NAME to run a specific rule")
            print("Use -b RULE1 RULE2 ... for batch scanning")
        sys.exit(0)
    
    # Create output directory
    args.output.mkdir(exist_ok=True)
    
    # Run scan(s)
    if args.batch:
        # Batch mode
        scanner.batch_scan(
            args.batch,
            output_dir=args.output,
            hyper_max=args.hyper_max,
            limit=args.limit
        )
    else:
        # Single rule mode
        scanner.scan_with_rule(
            args.rule,
            output_dir=args.output,
            hyper_max=args.hyper_max,
            limit=args.limit
        )
    
    print(f"\nResults saved to: {args.output}/")


if __name__ == "__main__":
    main()
