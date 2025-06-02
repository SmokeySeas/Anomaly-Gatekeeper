#!/usr/bin/env python3
"""
Anomaly Cancellation Verification System
========================================
A comprehensive framework for checking gauge and gravitational anomalies
in particle physics models, starting with the Standard Model.

Authors: Bryan Roy (lead), Claude (implementation), Charlie (architect), Gemini (validation)
Version: 1.0
"""

import fractions
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import json


class GaugeGroup(Enum):
    """Enumeration of gauge groups"""
    SU3 = "SU(3)"
    SU2 = "SU(2)"
    U1 = "U(1)"


@dataclass
class Fermion:
    """
    Represents a chiral fermion with quantum numbers.
    
    Attributes:
        name: Field identifier
        su3_rep: SU(3) representation dimension
        su2_rep: SU(2) representation dimension
        hypercharge: U(1)_Y charge
        chirality: +1 for left-handed, -1 for right-handed (sign convention)
        generations: Number of generations (default: 1)
    """
    name: str
    su3_rep: int
    su2_rep: int
    hypercharge: fractions.Fraction
    chirality: int = 1
    generations: int = 1
    
    def __post_init__(self):
        """Validate input parameters"""
        if self.su3_rep not in [1, 3, 6, 8]:
            raise ValueError(f"Unsupported SU(3) representation: {self.su3_rep}")
        if self.su2_rep not in [1, 2, 3]:
            raise ValueError(f"Unsupported SU(2) representation: {self.su2_rep}")
        if self.chirality not in [-1, 1]:
            raise ValueError(f"Chirality must be ±1, got {self.chirality}")
        if self.generations < 1:
            raise ValueError(f"Generations must be positive, got {self.generations}")


class AnomalyChecker:
    """Main class for computing and verifying anomaly cancellation conditions"""
    
    def __init__(self, fermions: List[Fermion]):
        """
        Initialize with a list of fermions.
        
        Args:
            fermions: List of Fermion objects defining the spectrum
        """
        self.fermions = fermions
        self._anomalies: Optional[Dict[str, fractions.Fraction]] = None
    
    @staticmethod
    def su2_dynkin_index(dimension: int) -> fractions.Fraction:
        """
        Calculate the Dynkin index T(R) for SU(2) representations.
        
        Args:
            dimension: Representation dimension
            
        Returns:
            Dynkin index as a fraction
        """
        if dimension == 1:
            return fractions.Fraction(0)
        elif dimension == 2:
            return fractions.Fraction(1, 2)
        elif dimension == 3:
            return fractions.Fraction(2)
        else:
            # General formula: T(R) = (dimension³ - dimension) / 12
            return fractions.Fraction(dimension**3 - dimension, 12)
    
    @staticmethod
    def su2_cubic_coeff(dimension: int) -> fractions.Fraction:
        """
        Calculate the cubic anomaly coefficient for SU(2) representations.
        
        For SU(2), the cubic anomaly coefficient is always zero for all representations
        due to group-theoretic properties.
        
        Args:
            dimension: Representation dimension
            
        Returns:
            Always returns 0
        """
        return fractions.Fraction(0)
    
    @staticmethod
    def su3_dynkin_index(dimension: int) -> fractions.Fraction:
        """Dynkin index T(R) for SU(3) reps."""
        table = {1: fractions.Fraction(0),
                 3: fractions.Fraction(1, 2),
                 6: fractions.Fraction(5, 2),
                 8: fractions.Fraction(3)}
        return table.get(dimension, fractions.Fraction(0))
        """
        Calculate the Dynkin index T(R) for SU(3) representations.
        
        Args:
            dimension: Representation dimension
            
        Returns:
            Dynkin index as a fraction
        """
        indices = {
            1: fractions.Fraction(0),      # Singlet
            3: fractions.Fraction(1, 2),   # Fundamental
            6: fractions.Fraction(5, 2),   # Symmetric
            8: fractions.Fraction(3)       # Adjoint
        }
        return indices.get(dimension, fractions.Fraction(0))
    
    def compute_anomalies(self) -> Dict[str, fractions.Fraction]:
        """
        Compute all relevant anomaly coefficients.
        
        Returns:
            Dictionary containing all anomaly coefficients
        """
        anomalies = {}
        
        # U(1)_Y anomalies
        anomalies['[U(1)_Y]'] = sum(
            f.hypercharge * f.chirality * f.generations * f.su3_rep * f.su2_rep
            for f in self.fermions
        )
        
        anomalies['[U(1)_Y]³'] = sum(
            f.hypercharge**3 * f.chirality * f.generations * f.su3_rep * f.su2_rep
            for f in self.fermions
        )
        
        # Mixed U(1)_Y - SU(2)² anomaly
        anomalies['[U(1)_Y][SU(2)]²'] = sum(
            f.hypercharge * f.chirality * f.generations * f.su3_rep * 
            self.su2_dynkin_index(f.su2_rep)
            for f in self.fermions
        )
        
        # Mixed U(1)_Y - SU(3)² anomaly
        anomalies['[U(1)_Y][SU(3)]²'] = sum(
            f.hypercharge * f.chirality * f.generations * f.su2_rep * 
            self.su3_dynkin_index(f.su3_rep)
            for f in self.fermions
        )
        
        # Pure non-abelian anomalies
        anomalies['[SU(2)]³'] = sum(
            f.chirality * f.generations * f.su3_rep * 
            self.su2_cubic_coeff(f.su2_rep)
            for f in self.fermions
        )
        
        anomalies['[SU(3)]³'] = sum(
            f.chirality * f.generations * f.su2_rep * 
            self.su3_dynkin_index(f.su3_rep)
            for f in self.fermions
        )
        
        # Gravitational anomalies
        anomalies['[Gravity]²[U(1)_Y]'] = sum(
            f.hypercharge * f.chirality * f.generations * f.su3_rep * f.su2_rep
            for f in self.fermions
        )
        
        self._anomalies = anomalies
        return anomalies
    
    def verify_cancellation(self, tolerance: float = 1e-10) -> Tuple[bool, List[str]]:
        """
        Check if all anomalies cancel.
        
        Args:
            tolerance: Numerical tolerance for zero comparison
            
        Returns:
            Tuple of (all_cancel, list_of_non_cancelling_anomalies)
        """
        if self._anomalies is None:
            self.compute_anomalies()
        
        non_cancelling: List[str] = []
        for anomaly_type, value in self._anomalies.items():
            if abs(float(value)) > tolerance:
                non_cancelling.append(f"{anomaly_type} = {value}")
        
        return len(non_cancelling) == 0, non_cancelling
    
    def generate_report(self) -> str:
        """Generate a comprehensive anomaly cancellation report"""
        if self._anomalies is None:
            self.compute_anomalies()
        
        report = ["Anomaly Cancellation Report", "=" * 30, ""]
        
        # Fermion content
        report.append("Fermion Content:")
        report.append("-" * 20)
        for f in self.fermions:
            report.append(
                f"{f.name}: ({f.su3_rep}, {f.su2_rep})_{f.hypercharge} "
                f"× {f.generations} gen"
            )
        report.append("")
        
        # Anomaly coefficients
        report.append("Anomaly Coefficients:")
        report.append("-" * 20)
        for anomaly_type, value in self._anomalies.items():
            status = "✓" if abs(float(value)) < 1e-10 else "✗"
            report.append(f"{status} {anomaly_type:20} = {value}")
        report.append("")
        
        # Summary
        all_cancel, non_cancelling = self.verify_cancellation()
        if all_cancel:
            report.append("✓ All anomalies cancel - Model is consistent!")
        else:
            report.append("✗ Anomalies do not cancel:")
            for nc in non_cancelling:
                report.append(f"  - {nc}")
        
        return "\n".join(report)


def standard_model_spectrum(include_right_neutrino: bool = False) -> List[Fermion]:
    """
    Generate the Standard Model fermion spectrum for one generation.
    
    Args:
        include_right_neutrino: Whether to include right-handed neutrino
        
    Returns:
        List of Fermion objects
    """
    # Helper for creating fractions
    def fr(n, d=1):
        return fractions.Fraction(n, d)
    
    fermions = [
        # Quarks
        Fermion("Q_L", su3_rep=3, su2_rep=2, hypercharge=fr(1, 6), chirality=1),
        Fermion("u_R", su3_rep=3, su2_rep=1, hypercharge=fr(2, 3), chirality=-1),
        Fermion("d_R", su3_rep=3, su2_rep=1, hypercharge=fr(-1, 3), chirality=-1),
        
        # Leptons
        Fermion("L_L", su3_rep=1, su2_rep=2, hypercharge=fr(-1, 2), chirality=1),
        Fermion("e_R", su3_rep=1, su2_rep=1, hypercharge=fr(-1), chirality=-1),
    ]
    
    if include_right_neutrino:
        fermions.append(
            Fermion("ν_R", su3_rep=1, su2_rep=1, hypercharge=fr(0), chirality=-1)
        )
    
    return fermions


def test_variations():
    """Test various model variations and extensions"""
    print("Testing Model Variations")
    print("=" * 40)
    
    # Test 1: Standard Model without ν_R
    print("\n1. Standard Model (no ν_R):")
    checker1 = AnomalyChecker(standard_model_spectrum(False))
    print(checker1.generate_report())
    
    # Test 2: Standard Model with ν_R
    print("\n2. Standard Model (with ν_R):")
    checker2 = AnomalyChecker(standard_model_spectrum(True))
    print(checker2.generate_report())
    
    # Test 3: Add vector-like quark
    print("\n3. SM + Vector-like quark doublet:")
    spectrum3 = standard_model_spectrum(False)
    spectrum3.extend([
        Fermion("Q'_L", su3_rep=3, su2_rep=2, hypercharge=fractions.Fraction(1, 6), chirality=1),
        Fermion("Q'_R", su3_rep=3, su2_rep=2, hypercharge=fractions.Fraction(1, 6), chirality=-1),
    ])
    checker3 = AnomalyChecker(spectrum3)
    print(checker3.generate_report())
    
    # Test 4: Broken hypercharge assignment
    print("\n4. Broken model (wrong hypercharge):")
    spectrum4 = standard_model_spectrum(False)
    spectrum4[0].hypercharge = fractions.Fraction(1, 3)  # Wrong Q_L hypercharge
    checker4 = AnomalyChecker(spectrum4)
    all_cancel, failures = checker4.verify_cancellation()
    print(f"Anomalies cancel: {all_cancel}")
    if not all_cancel:
        print("Failed anomalies:", failures[:3])  # Show first 3


def main():
    """Main entry point for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Check anomaly cancellation in particle physics models"
    )
    parser.add_argument(
        "--model", 
        choices=["sm", "sm-nu", "custom"], 
        default="sm",
        help="Model to check"
    )
    parser.add_argument(
        "--json", 
        type=str, 
        help="Path to JSON file with custom fermion spectrum"
    )
    parser.add_argument(
        "--test", 
        action="store_true", 
        help="Run test variations"
    )
    
    args = parser.parse_args()
    
    if args.test:
        test_variations()
        return
    
    if args.model == "sm":
        fermions = standard_model_spectrum(False)
    elif args.model == "sm-nu":
        fermions = standard_model_spectrum(True)
    elif args.model == "custom" and args.json:
        # Load custom spectrum from JSON
        with open(args.json, 'r') as f:
            data = json.load(f)
            fermions = [
                Fermion(
                    name=f['name'],
                    su3_rep=f['su3_rep'],
                    su2_rep=f['su2_rep'],
                    hypercharge=fractions.Fraction(f['hypercharge']),
                    chirality=f.get('chirality', 1),
                    generations=f.get('generations', 1)
                )
                for f in data['fermions']
            ]
    else:
        parser.error("Custom model requires --json parameter")
        return
    
    checker = AnomalyChecker(fermions)
    print(checker.generate_report())


if __name__ == "__main__":
    main()
