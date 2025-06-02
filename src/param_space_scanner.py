#!/usr/bin/env python3
"""
scan_param_space.py
===================
Systematic parameter space scanner for finding anomaly-free fermion spectra.
Varies hypercharge, SU(N) representations, and generations to discover
consistent gauge theories beyond the Standard Model.

Author: Bryan Roy & Claude
Version: 1.0
"""

import json
import fractions
import itertools
import argparse
import sys
import hashlib
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from copy import deepcopy

# Add parent directory to path for anomaly_checker import
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.anomaly_checker import Fermion, AnomalyChecker
except ImportError:
    print("Error: anomaly_checker.py not found. Please ensure it's in the parent directory.")
    sys.exit(1)


@dataclass
class ScanResult:
    """Container for scan results"""
    spectrum: List[Fermion]
    anomalies: Dict[str, fractions.Fraction]
    is_anomaly_free: bool
    description: str


class ParameterSpaceScanner:
    """
    Scanner for systematically exploring fermion parameter space.
    """
    
    def __init__(self, base_spectrum: List[Dict], scan_config: Dict):
        """
        Initialize scanner with base spectrum and configuration.
        
        Args:
            base_spectrum: List of fermion dictionaries from JSON
            scan_config: Configuration for parameter variations
        """
        self.base_spectrum = base_spectrum
        self.scan_config = scan_config
        self.results = []
        self.anomaly_free_models = []
        self.block_a_hits = []  # Store single fermion additions that work
        
        # Create results directory if it doesn't exist
        os.makedirs('results', exist_ok=True)
        
    def create_fermion_from_dict(self, fdict: Dict) -> Fermion:
        """Convert dictionary to Fermion object"""
        try:
            hypercharge = fractions.Fraction(fdict['hypercharge'])
        except (ValueError, TypeError):
            # Handle cases where hypercharge might already be a Fraction
            hypercharge = fdict['hypercharge']
            
        return Fermion(
            name=fdict['name'],
            su3_rep=fdict['su3_rep'],
            su2_rep=fdict['su2_rep'],
            hypercharge=hypercharge,
            chirality=fdict.get('chirality', 1),
            generations=fdict.get('generations', 1)
        )
    
    def dump_result(self, spectrum: List[Fermion], tag: str) -> None:
        """
        Save anomaly-free spectrum to JSON file with SHA1-based naming.
        
        Args:
            spectrum: List of Fermion objects
            tag: Human-readable tag for the file
        """
        # Convert spectrum to JSON-serializable format
        spec_json = []
        for f in spectrum:
            fdict = {
                'name': f.name,
                'su3_rep': f.su3_rep,
                'su2_rep': f.su2_rep,
                'hypercharge': str(f.hypercharge),
                'chirality': f.chirality,
                'generations': f.generations
            }
            spec_json.append(fdict)
        
        # Create SHA1 hash of the spectrum
        spec_str = json.dumps(spec_json, sort_keys=True)
        h = hashlib.sha1(spec_str.encode()).hexdigest()[:10]
        
        # Save to file
        path = f"results/{tag}_{h}.json"
        with open(path, "w") as f:
            json.dump({
                'tag': tag,
                'is_anomaly_free': True,
                'fermions': spec_json
            }, f, indent=2)
    
    def generate_hypercharge_values(self, hyper_max: Optional[int] = None) -> List[fractions.Fraction]:
        """Generate rational hypercharge values to scan"""
        values = []
        
        # Get configuration
        config = self.scan_config.get('hypercharge', {})
        
        # Default to k/6 grid
        if config.get('use_k_over_6', True):
            k_max = hyper_max if hyper_max is not None else 6
            abs_y_max = config.get('abs_max', 2.0)  # Default to 2.0 for general use
            
            for k in range(-k_max, k_max + 1):
                Y = fractions.Fraction(k, 6)
                if abs(float(Y)) <= abs_y_max:
                    values.append(Y)
        
        # Standard fractional values (if requested)
        elif config.get('include_standard', True):
            standard_values = [
                fractions.Fraction(0),
                fractions.Fraction(1, 6), fractions.Fraction(-1, 6),
                fractions.Fraction(1, 3), fractions.Fraction(-1, 3),
                fractions.Fraction(1, 2), fractions.Fraction(-1, 2),
                fractions.Fraction(2, 3), fractions.Fraction(-2, 3),
                fractions.Fraction(1), fractions.Fraction(-1),
                fractions.Fraction(5, 6), fractions.Fraction(-5, 6),
            ]
            values.extend(standard_values)
        
        # Custom range
        if 'range' in config:
            num_range = config['range']
            den_range = config.get('denominators', [1, 2, 3, 6])
            
            for num in range(num_range[0], num_range[1] + 1):
                for den in den_range:
                    if den != 0:
                        values.append(fractions.Fraction(num, den))
        
        # Remove duplicates
        return list(set(values))
    
    def generate_su3_representations(self) -> List[int]:
        """Generate SU(3) representation dimensions to scan"""
        config = self.scan_config.get('su3_rep', {})
        
        if 'values' in config:
            return config['values']
        else:
            return [1, 3, 6, 8]  # Standard representations
    
    def generate_su2_representations(self) -> List[int]:
        """Generate SU(2) representation dimensions to scan"""
        config = self.scan_config.get('su2_rep', {})
        
        if 'values' in config:
            return config['values']
        else:
            return [1, 2, 3]  # Standard representations
    
    def scan_single_additions(self, hyper_max: Optional[int] = None) -> List[ScanResult]:
        """
        Block A: Scan single fermion additions to the base spectrum.
        
        Args:
            hyper_max: Maximum k value for Y = k/6 grid
            
        Returns:
            List of ScanResult objects
        """
        results = []
        base = [self.create_fermion_from_dict(f) for f in self.base_spectrum]
        
        # Define the representation combinations to scan
        # [(1,1), (1,2), (1,3), (3,1), (3,2), (6,1), (8,1)]
        rep_combinations = (
            [(1, x) for x in (1, 2, 3)] +
            [(3, x) for x in (1, 2)] +
            [(6, 1), (8, 1)]
        )
        
        k_max = hyper_max if hyper_max is not None else 6
        
        # Get absolute Y max from config, default to 1.0 for Block A
        abs_y_max = self.scan_config.get('hypercharge', {}).get('abs_max', 1.0)
        
        count = 0
        for su3, su2 in rep_combinations:
            for k in range(-k_max, k_max + 1):
                Y = fractions.Fraction(k, 6)
                if abs(float(Y)) > abs_y_max:
                    continue
                    
                for chi in (1, -1):
                    # Create fermion with proper name upfront
                    chi_str = "L" if chi == 1 else "R"
                    F = Fermion(f"X_{su3}{su2}_{k}_{chi_str}", su3, su2, Y, chi)
                    test_spectrum = base + [F]
                    
                    checker = AnomalyChecker(test_spectrum)
                    all_cancel, failures = checker.verify_cancellation()
                    
                    if all_cancel:
                        # Save the successful single fermion (make a copy to avoid mutation issues)
                        self.block_a_hits.append(deepcopy(F))
                        
                        # Save to file
                        tag = f"single_{su3}{su2}_{k}_{chi}"
                        self.dump_result(test_spectrum, tag)
                        
                        # Create result object
                        desc = f"Single fermion: ({su3}, {su2})_{Y} × {chi}"
                        result = ScanResult(
                            spectrum=test_spectrum,
                            anomalies=checker.compute_anomalies(),
                            is_anomaly_free=True,
                            description=desc
                        )
                        
                        results.append(result)
                        self.anomaly_free_models.append(result)
                        count += 1
        
        print(f"Block A: Found {count} anomaly-free single fermion additions")
        return results
    
    def scan_vector_like_pairs(self, use_block_a: bool = False, hyper_max: Optional[int] = None) -> List[ScanResult]:
        """
        Block B: Scan for vector-like fermion pairs that preserve anomaly cancellation.
        
        Args:
            use_block_a: If True, use Block A hits as seeds. If False, do full scan.
            hyper_max: Maximum k value for Y = k/6 grid
        """
        results = []
        base_spectrum_fermions = [
            self.create_fermion_from_dict(f) for f in self.base_spectrum
        ]
        
        if use_block_a and self.block_a_hits:
            # Use Block A results as seeds
            for F in self.block_a_hits:
                Fbar = Fermion(
                    name=F.name + "bar",
                    su3_rep=F.su3_rep,
                    su2_rep=F.su2_rep,
                    hypercharge=F.hypercharge,
                    chirality=-F.chirality
                )
                
                # Create test spectrum
                test_spectrum = base_spectrum_fermions + [F, Fbar]
                
                # Check anomalies
                checker = AnomalyChecker(test_spectrum)
                anomalies = checker.compute_anomalies()
                all_cancel, failures = checker.verify_cancellation()
                
                if all_cancel:
                    # Save to file
                    tag = f"vector_like_{F.su3_rep}{F.su2_rep}_{F.hypercharge.numerator}_{F.hypercharge.denominator}"
                    self.dump_result(test_spectrum, tag)
                    
                    # Create result
                    desc = f"Vector-like pair from Block A: ({F.su3_rep}, {F.su2_rep})_{F.hypercharge}"
                    result = ScanResult(
                        spectrum=test_spectrum,
                        anomalies=anomalies,
                        is_anomaly_free=all_cancel,
                        description=desc
                    )
                    
                    results.append(result)
                    self.anomaly_free_models.append(result)
        else:
            # Full scan
            hypercharges = self.generate_hypercharge_values(hyper_max)
            su3_reps = self.generate_su3_representations()
            su2_reps = self.generate_su2_representations()
            
            for Y, su3, su2 in itertools.product(hypercharges, su3_reps, su2_reps):
                # Create vector-like pair
                left_fermion = Fermion(
                    name=f"X_L",
                    su3_rep=su3,
                    su2_rep=su2,
                    hypercharge=Y,
                    chirality=1
                )
                
                right_fermion = Fermion(
                    name=f"X_R",
                    su3_rep=su3,
                    su2_rep=su2,
                    hypercharge=Y,
                    chirality=-1
                )
                
                # Create test spectrum
                test_spectrum = base_spectrum_fermions + [left_fermion, right_fermion]
                
                # Check anomalies
                checker = AnomalyChecker(test_spectrum)
                anomalies = checker.compute_anomalies()
                all_cancel, failures = checker.verify_cancellation()
                
                if all_cancel:
                    # Save to file
                    tag = f"vector_like_{su3}{su2}_{Y.numerator}_{Y.denominator}"
                    self.dump_result(test_spectrum, tag)
                    
                    # Create result
                    desc = f"Vector-like pair: ({su3}, {su2})_{Y}"
                    result = ScanResult(
                        spectrum=test_spectrum,
                        anomalies=anomalies,
                        is_anomaly_free=all_cancel,
                        description=desc
                    )
                    
                    results.append(result)
                    self.anomaly_free_models.append(result)
        
        return results
    
    def scan_chiral_pairs(self) -> List[ScanResult]:
        """
        Block C: Scan for Higgsino-style chiral fermion pairs.
        Restricted to (su3=1, su2=2, chi=+1) with Y in {1/2, 1, 3/2}.
        """
        results = []
        base_spectrum_fermions = [
            self.create_fermion_from_dict(f) for f in self.base_spectrum
        ]
        
        # Higgsino-specific hypercharges
        for Y in [fractions.Fraction(1, 2), fractions.Fraction(1), fractions.Fraction(3, 2)]:
            # Create Higgsino-style pair
            F1 = Fermion("Hu", su3_rep=1, su2_rep=2, hypercharge=Y, chirality=1)
            F2 = Fermion("Hd", su3_rep=1, su2_rep=2, hypercharge=-Y, chirality=1)
            
            # Create test spectrum
            test_spectrum = base_spectrum_fermions + [F1, F2]
            
            # Check anomalies
            checker = AnomalyChecker(test_spectrum)
            anomalies = checker.compute_anomalies()
            all_cancel, failures = checker.verify_cancellation()
            
            if all_cancel:
                # Save to file
                tag = f"higgsino_{Y.numerator}_{Y.denominator}"
                self.dump_result(test_spectrum, tag)
                
                # Create result
                desc = f"Chiral pair: (1, 2)_[+{Y}, -{Y}]"
                result = ScanResult(
                    spectrum=test_spectrum,
                    anomalies=anomalies,
                    is_anomaly_free=all_cancel,
                    description=desc
                )
                
                results.append(result)
                self.anomaly_free_models.append(result)
        
        return results
    
    def run_comprehensive_scan(self, hyper_max: Optional[int] = None, limit: Optional[int] = None) -> None:
        """
        Run comprehensive parameter space scan following the block structure.
        
        Args:
            hyper_max: Maximum k value for Y = k/6 grid
            limit: Maximum number of models to find before stopping
        """
        print("Starting comprehensive parameter space scan...")
        print("=" * 60)
        
        # Block A: Single fermion additions
        print("\nBlock A: Scanning single fermion additions...")
        single_results = self.scan_single_additions(hyper_max)
        self.results.extend(single_results)
        
        if limit and len(self.anomaly_free_models) >= limit:
            print(f"Reached limit of {limit} models. Stopping scan.")
            return
        
        # Block B: Vector-like pairs (exhaustive)
        print("\nBlock B: Scanning vector-like fermion pairs (exhaustive)...")
        vl_results = self.scan_vector_like_pairs(use_block_a=False, hyper_max=hyper_max)
        self.results.extend(vl_results)
        print(f"Found {len([r for r in vl_results if r.is_anomaly_free])} "
              f"anomaly-free vector-like models")
        
        if limit and len(self.anomaly_free_models) >= limit:
            print(f"Reached limit of {limit} models. Stopping scan.")
            return
        
        # Block B-prime: Vector-like pairs from Block A hits (optional)
        if self.block_a_hits and self.scan_config.get('scan_block_a_pairs', True):
            print("\nBlock B-prime: Vector-like partners of Block A hits...")
            vl_from_a = self.scan_vector_like_pairs(use_block_a=True, hyper_max=hyper_max)
            self.results.extend(vl_from_a)
            print(f"Found {len([r for r in vl_from_a if r.is_anomaly_free])} "
                  f"additional vector-like models from Block A seeds")
            
            if limit and len(self.anomaly_free_models) >= limit:
                print(f"Reached limit of {limit} models. Stopping scan.")
                return
        
        # Block C: Higgsino-style chiral pairs
        print("\nBlock C: Scanning Higgsino-style chiral pairs...")
        chiral_results = self.scan_chiral_pairs()
        self.results.extend(chiral_results)
        print(f"Found {len([r for r in chiral_results if r.is_anomaly_free])} "
              f"anomaly-free Higgsino models")
        
        print(f"\nTotal configurations scanned: {len(self.results)}")
        print(f"Anomaly-free models found: {len(self.anomaly_free_models)}")
        print(f"Results saved to: results/ directory")
    
    def print_anomaly_free_models(self, max_display: int = 20) -> None:
        """
        Print summary of anomaly-free models found.
        """
        print("\n" + "=" * 60)
        print("ANOMALY-FREE MODELS DISCOVERED")
        print("=" * 60)
        
        if not self.anomaly_free_models:
            print("No anomaly-free models found in the scan range.")
            return
        
        # Group by type
        single_additions = []
        vector_like = []
        higgsino_style = []
        
        for model in self.anomaly_free_models:
            if "Single fermion:" in model.description:
                single_additions.append(model)
            elif "Vector-like" in model.description:
                vector_like.append(model)
            elif "Chiral pair:" in model.description:
                higgsino_style.append(model)
        
        # Print single fermion additions (Block A)
        if single_additions:
            print("\nBlock A - Single fermion additions:")
            print("-" * 40)
            for i, model in enumerate(single_additions[:max_display]):
                print(f"{i+1}. {model.description}")
            if len(single_additions) > max_display:
                print(f"   ... and {len(single_additions) - max_display} more")
        
        # Print vector-like models (Block B)
        if vector_like:
            print("\nBlock B - Vector-like fermion pairs:")
            print("-" * 40)
            for i, model in enumerate(vector_like[:max_display]):
                print(f"{i+1}. {model.description}")
            if len(vector_like) > max_display:
                print(f"   ... and {len(vector_like) - max_display} more")
        
        # Print Higgsino-style pairs (Block C)
        if higgsino_style:
            print("\nBlock C - Higgsino-style chiral pairs:")
            print("-" * 40)
            for i, model in enumerate(higgsino_style[:max_display]):
                print(f"{i+1}. {model.description}")
            if len(higgsino_style) > max_display:
                print(f"   ... and {len(higgsino_style) - max_display} more")
        
        # Highlight known models
        print("\n" + "=" * 60)
        print("VERIFICATION OF KNOWN MODELS")
        print("=" * 60)
        
        # Check for right-handed neutrino (Block A)
        nu_r = next((m for m in self.anomaly_free_models 
                    if "Single fermion:" in m.description and 
                    "(1, 1)_0 × -1" in m.description), None)
        if nu_r:
            print("✓ Found right-handed neutrino: (1, 1)_0 × -1")
        
        # Check for standard vector-like lepton (Block B)
        vl_lepton = next((m for m in self.anomaly_free_models 
                          if "Vector-like" in m.description and 
                          "(1, 2)_-1/2" in m.description), None)
        if vl_lepton:
            print("✓ Found vector-like lepton doublet: (1, 2)_-1/2")
        
        # Check for MSSM Higgsinos (Block C)
        higgsinos = next((m for m in self.anomaly_free_models 
                         if "Chiral pair:" in m.description and 
                         "(1, 2)_[+1/2, -1/2]" in m.description), None)
        if higgsinos:
            print("✓ Found MSSM Higgsino pair: (1, 2)_[+1/2, -1/2]")
        
        # Check for vector-like quark (Block B)
        vl_quark = next((m for m in self.anomaly_free_models 
                        if "Vector-like" in m.description and 
                        "(3, 2)_1/6" in m.description), None)
        if vl_quark:
            print("✓ Found vector-like quark doublet: (3, 2)_1/6")
    
    def export_results(self, filename: str) -> None:
        """
        Export anomaly-free models to JSON file.
        """
        export_data = {
            "scan_config": self.scan_config,
            "base_spectrum": self.base_spectrum,
            "anomaly_free_models": []
        }
        
        for model in self.anomaly_free_models:
            # Extract new fermions (those not in base spectrum)
            base_names = {f['name'] for f in self.base_spectrum}
            new_fermions = [f for f in model.spectrum if f.name not in base_names]
            
            # Create machine-friendly signature
            signature = []
            for f in new_fermions:
                sig = f"({f.su3_rep},{f.su2_rep},{f.hypercharge},{f.chirality})"
                signature.append(sig)
            
            model_data = {
                "description": model.description,
                "signature": signature,  # Machine-friendly format
                "fermions": [
                    {
                        "name": f.name,
                        "su3_rep": f.su3_rep,
                        "su2_rep": f.su2_rep,
                        "hypercharge": str(f.hypercharge),
                        "chirality": f.chirality,
                        "generations": f.generations
                    }
                    for f in model.spectrum
                ],
                "is_anomaly_free": True
            }
            export_data["anomaly_free_models"].append(model_data)
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"\nResults exported to {filename}")


def main():
    """Main entry point for parameter space scanner."""
    parser = argparse.ArgumentParser(
        description="Scan parameter space for anomaly-free fermion spectra"
    )
    
    parser.add_argument(
        "template",
        help="JSON template file defining base spectrum and scan configuration"
    )
    
    parser.add_argument(
        "--output",
        default="anomaly_free_models.json",
        help="Output file for anomaly-free models (default: anomaly_free_models.json)"
    )
    
    parser.add_argument(
        "--max-display",
        type=int,
        default=20,
        help="Maximum number of models to display per category (default: 20)"
    )
    
    parser.add_argument(
        "--hyper-max",
        type=int,
        default=None,
        help="Maximum k value for Y = k/6 hypercharge grid (default: 6)"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of anomaly-free models to find before stopping"
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick scan with limited parameter range"
    )
    
    args = parser.parse_args()
    
    # Load template
    try:
        with open(args.template, 'r') as f:
            template_data = json.load(f)
    except Exception as e:
        print(f"Error loading template file: {e}")
        sys.exit(1)
    
    # Extract base spectrum and scan configuration
    base_spectrum = template_data.get('base_spectrum', [])
    scan_config = template_data.get('scan_config', {})
    
    # Apply quick scan limits if requested
    if args.quick:
        scan_config['hypercharge'] = {
            'use_k_over_6': True,
            'include_standard': False
        }
        scan_config['su3_rep'] = {'values': [1, 3]}
        scan_config['su2_rep'] = {'values': [1, 2]}
        if args.hyper_max is None:
            args.hyper_max = 3  # Smaller default for quick scan
    
    # Ensure we use k/6 grid by default
    if 'hypercharge' not in scan_config:
        scan_config['hypercharge'] = {'use_k_over_6': True}
    
    # Create and run scanner
    scanner = ParameterSpaceScanner(base_spectrum, scan_config)
    scanner.run_comprehensive_scan(hyper_max=args.hyper_max, limit=args.limit)
    scanner.print_anomaly_free_models(max_display=args.max_display)
    
    # Export results
    if scanner.anomaly_free_models:
        scanner.export_results(args.output)
    
    print("\nScan complete!")
    print(f"Individual model files saved in: results/")


if __name__ == "__main__":
    main()
