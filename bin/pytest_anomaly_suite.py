#!/usr/bin/env python3
"""
test_anomaly_checker.py
=======================
Comprehensive test suite for the anomaly cancellation verification system.
Validates mathematical correctness and edge case handling.

Author: Claude
Version: 1.0
"""

import pytest
import fractions
import json
import tempfile
from pathlib import Path

# Import the anomaly checker module
from src.anomaly_checker import (
    Fermion, AnomalyChecker, GaugeGroup, 
    standard_model_spectrum
)


class TestFermionClass:
    """Test the Fermion dataclass functionality"""
    
    def test_fermion_creation_valid(self):
        """Test creation of valid fermion objects"""
        fermion = Fermion(
            name="test_fermion",
            su3_rep=3,
            su2_rep=2,
            hypercharge=fractions.Fraction(1, 6),
            chirality=1,
            generations=1
        )
        assert fermion.name == "test_fermion"
        assert fermion.su3_rep == 3
        assert fermion.su2_rep == 2
        assert fermion.hypercharge == fractions.Fraction(1, 6)
        assert fermion.chirality == 1
        assert fermion.generations == 1
    
    def test_fermion_invalid_su3_rep(self):
        """Test that invalid SU(3) representations raise errors"""
        with pytest.raises(ValueError, match="Unsupported SU\(3\) representation"):
            Fermion("invalid", su3_rep=5, su2_rep=1, 
                   hypercharge=fractions.Fraction(0))
    
    def test_fermion_invalid_su2_rep(self):
        """Test that invalid SU(2) representations raise errors"""
        with pytest.raises(ValueError, match="Unsupported SU\(2\) representation"):
            Fermion("invalid", su3_rep=1, su2_rep=4, 
                   hypercharge=fractions.Fraction(0))
    
    def test_fermion_invalid_chirality(self):
        """Test that invalid chirality values raise errors"""
        with pytest.raises(ValueError, match="Chirality must be ±1"):
            Fermion("invalid", su3_rep=1, su2_rep=1, 
                   hypercharge=fractions.Fraction(0), chirality=0)
    
    def test_fermion_invalid_generations(self):
        """Test that invalid generation numbers raise errors"""
        with pytest.raises(ValueError, match="Generations must be positive"):
            Fermion("invalid", su3_rep=1, su2_rep=1, 
                   hypercharge=fractions.Fraction(0), generations=0)


class TestAnomalyCheckerMethods:
    """Test the AnomalyChecker class methods"""
    
    def test_su2_dynkin_index(self):
        """Test SU(2) Dynkin index calculation"""
        assert AnomalyChecker.su2_dynkin_index(1) == fractions.Fraction(0)
        assert AnomalyChecker.su2_dynkin_index(2) == fractions.Fraction(1, 2)
        assert AnomalyChecker.su2_dynkin_index(3) == fractions.Fraction(2)
    
    def test_su2_cubic_coeff(self):
        """Test that SU(2) cubic coefficient is always zero"""
        for dim in [1, 2, 3]:
            assert AnomalyChecker.su2_cubic_coeff(dim) == fractions.Fraction(0)
    
    def test_su3_dynkin_index(self):
        """Test SU(3) Dynkin index calculation"""
        assert AnomalyChecker.su3_dynkin_index(1) == fractions.Fraction(0)
        assert AnomalyChecker.su3_dynkin_index(3) == fractions.Fraction(1, 2)
        assert AnomalyChecker.su3_dynkin_index(6) == fractions.Fraction(5, 2)
        assert AnomalyChecker.su3_dynkin_index(8) == fractions.Fraction(3)
        assert AnomalyChecker.su3_dynkin_index(10) == fractions.Fraction(0)  # Unknown rep


class TestStandardModelAnomaly:
    """Test Standard Model anomaly cancellation"""
    
    def test_sm_without_right_neutrino(self):
        """Verify that SM without ν_R is anomaly-free"""
        fermions = standard_model_spectrum(include_right_neutrino=False)
        checker = AnomalyChecker(fermions)
        anomalies = checker.compute_anomalies()
        
        # All anomalies must be exactly zero
        for anomaly_type, value in anomalies.items():
            assert value == fractions.Fraction(0), \
                f"{anomaly_type} = {value} (expected 0)"
    
    def test_sm_with_right_neutrino(self):
        """Verify that SM with ν_R is anomaly-free"""
        fermions = standard_model_spectrum(include_right_neutrino=True)
        checker = AnomalyChecker(fermions)
        anomalies = checker.compute_anomalies()
        
        # All anomalies must be exactly zero
        for anomaly_type, value in anomalies.items():
            assert value == fractions.Fraction(0), \
                f"{anomaly_type} = {value} (expected 0)"
    
    def test_verify_cancellation_method(self):
        """Test the verify_cancellation method"""
        fermions = standard_model_spectrum(include_right_neutrino=False)
        checker = AnomalyChecker(fermions)
        all_cancel, failures = checker.verify_cancellation()
        
        assert all_cancel is True
        assert len(failures) == 0


class TestBrokenModels:
    """Test detection of anomalous models"""
    
    def test_wrong_hypercharge(self):
        """Test that wrong hypercharge assignments are detected"""
        fermions = standard_model_spectrum(include_right_neutrino=False)
        # Modify Q_L hypercharge to break anomaly cancellation
        fermions[0].hypercharge = fractions.Fraction(1, 3)
        
        checker = AnomalyChecker(fermions)
        all_cancel, failures = checker.verify_cancellation()
        
        assert all_cancel is False
        assert len(failures) > 0
        # Should detect non-zero U(1) anomalies
        assert any("[U(1)_Y]" in f for f in failures)
    
    def test_missing_fermion(self):
        """Test that missing fermions break anomaly cancellation"""
        fermions = standard_model_spectrum(include_right_neutrino=False)
        # Remove electron right
        fermions = [f for f in fermions if f.name != "e_R"]
        
        checker = AnomalyChecker(fermions)
        all_cancel, failures = checker.verify_cancellation()
        
        assert all_cancel is False
        assert len(failures) > 0
    
    def test_wrong_chirality(self):
        """Test that wrong chirality assignments are detected"""
        fermions = standard_model_spectrum(include_right_neutrino=False)
        # Flip chirality of u_R
        for f in fermions:
            if f.name == "u_R":
                f.chirality = 1  # Should be -1
        
        checker = AnomalyChecker(fermions)
        all_cancel, failures = checker.verify_cancellation()
        
        assert all_cancel is False
        assert len(failures) > 0


class TestBSMModels:
    """Test beyond-Standard Model scenarios"""
    
    def test_vector_like_quarks(self):
        """Test that vector-like quarks preserve anomaly cancellation"""
        fermions = standard_model_spectrum(include_right_neutrino=False)
        
        # Add vector-like quark doublet
        fermions.extend([
            Fermion("Q'_L", su3_rep=3, su2_rep=2, 
                   hypercharge=fractions.Fraction(1, 6), chirality=1),
            Fermion("Q'_R", su3_rep=3, su2_rep=2, 
                   hypercharge=fractions.Fraction(1, 6), chirality=-1),
        ])
        
        checker = AnomalyChecker(fermions)
        all_cancel, failures = checker.verify_cancellation()
        
        assert all_cancel is True
        assert len(failures) == 0
    
    def test_vector_like_leptons(self):
        """Test that vector-like leptons preserve anomaly cancellation"""
        fermions = standard_model_spectrum(include_right_neutrino=False)
        
        # Add vector-like lepton doublet
        fermions.extend([
            Fermion("L'_L", su3_rep=1, su2_rep=2, 
                   hypercharge=fractions.Fraction(-1, 2), chirality=1),
            Fermion("L'_R", su3_rep=1, su2_rep=2, 
                   hypercharge=fractions.Fraction(-1, 2), chirality=-1),
        ])
        
        checker = AnomalyChecker(fermions)
        all_cancel, failures = checker.verify_cancellation()
        
        assert all_cancel is True
        assert len(failures) == 0
    
    def test_mssm_higgsinos(self):
        """Test that MSSM Higgsinos preserve anomaly cancellation"""
        fermions = standard_model_spectrum(include_right_neutrino=False)
        
        # Add MSSM Higgsinos
        fermions.extend([
            Fermion("H_u", su3_rep=1, su2_rep=2, 
                   hypercharge=fractions.Fraction(1, 2), chirality=1),
            Fermion("H_d", su3_rep=1, su2_rep=2, 
                   hypercharge=fractions.Fraction(-1, 2), chirality=1),
        ])
        
        checker = AnomalyChecker(fermions)
        all_cancel, failures = checker.verify_cancellation()
        
        assert all_cancel is True
        assert len(failures) == 0


class TestMultiGeneration:
    """Test multi-generation scenarios"""
    
    def test_three_generations_sm(self):
        """Test three generations of SM fermions"""
        fermions = []
        for gen in range(3):
            gen_fermions = standard_model_spectrum(include_right_neutrino=False)
            # Set generation number
            for f in gen_fermions:
                f.generations = 1
                f.name = f"{f.name}_gen{gen+1}"
            fermions.extend(gen_fermions)
        
        checker = AnomalyChecker(fermions)
        all_cancel, failures = checker.verify_cancellation()
        
        assert all_cancel is True
        assert len(failures) == 0
    
    def test_generation_number_scaling(self):
        """Test that generation number properly scales anomalies"""
        # Single generation
        fermions1 = standard_model_spectrum(include_right_neutrino=False)
        checker1 = AnomalyChecker(fermions1)
        anomalies1 = checker1.compute_anomalies()
        
        # Three generations using generation parameter
        fermions3 = standard_model_spectrum(include_right_neutrino=False)
        for f in fermions3:
            f.generations = 3
        checker3 = AnomalyChecker(fermions3)
        anomalies3 = checker3.compute_anomalies()
        
        # All anomalies should still be zero
        for anomaly_type in anomalies1:
            assert anomalies3[anomaly_type] == fractions.Fraction(0)


class TestReportGeneration:
    """Test report generation functionality"""
    
    def test_report_format(self):
        """Test that reports are properly formatted"""
        fermions = standard_model_spectrum(include_right_neutrino=False)
        checker = AnomalyChecker(fermions)
        report = checker.generate_report()
        
        assert "Anomaly Cancellation Report" in report
        assert "Fermion Content:" in report
        assert "Anomaly Coefficients:" in report
        assert "✓ All anomalies cancel" in report
    
    def test_report_broken_model(self):
        """Test report for broken model"""
        fermions = standard_model_spectrum(include_right_neutrino=False)
        fermions[0].hypercharge = fractions.Fraction(1, 3)  # Break it
        
        checker = AnomalyChecker(fermions)
        report = checker.generate_report()
        
        assert "✗ Anomalies do not cancel" in report
        assert "✗" in report  # Failed anomaly markers


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_empty_spectrum(self):
        """Test empty fermion spectrum"""
        checker = AnomalyChecker([])
        anomalies = checker.compute_anomalies()
        
        # Empty spectrum should have zero anomalies
        for value in anomalies.values():
            assert value == fractions.Fraction(0)
    
    def test_single_fermion(self):
        """Test single fermion (should have anomalies)"""
        fermions = [Fermion("single", su3_rep=3, su2_rep=2, 
                           hypercharge=fractions.Fraction(1, 6), chirality=1)]
        checker = AnomalyChecker(fermions)
        all_cancel, failures = checker.verify_cancellation()
        
        assert all_cancel is False
        assert len(failures) > 0
    
    def test_large_hypercharge(self):
        """Test numerical stability with large hypercharges"""
        fermions = standard_model_spectrum(include_right_neutrino=False)
        # Add fermion with large hypercharge that cancels
        fermions.extend([
            Fermion("X_L", su3_rep=1, su2_rep=1, 
                   hypercharge=fractions.Fraction(1000), chirality=1),
            Fermion("X_R", su3_rep=1, su2_rep=1, 
                   hypercharge=fractions.Fraction(1000), chirality=-1),
        ])
        
        checker = AnomalyChecker(fermions)
        all_cancel, failures = checker.verify_cancellation()
        
        assert all_cancel is True


def test_tolerance_parameter():
    """Test the tolerance parameter in verify_cancellation"""
    fermions = standard_model_spectrum(include_right_neutrino=False)
    checker = AnomalyChecker(fermions)
    
    # With default tolerance
    all_cancel_default, _ = checker.verify_cancellation()
    assert all_cancel_default is True
    
    # With extremely tight tolerance
    all_cancel_tight, _ = checker.verify_cancellation(tolerance=0)
    assert all_cancel_tight is True  # Should still pass for exact zeros
    
    # Create small numerical error
    checker._anomalies = {k: v for k, v in checker.compute_anomalies().items()}
    checker._anomalies['[U(1)_Y]'] = fractions.Fraction(1, 10**20)
    
    # Should fail with tight tolerance
    all_cancel_tight, _ = checker.verify_cancellation(tolerance=0)
    assert all_cancel_tight is False
    
    # Should pass with loose tolerance
    all_cancel_loose, _ = checker.verify_cancellation(tolerance=1e-10)
    assert all_cancel_loose is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
