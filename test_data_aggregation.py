#!/usr/bin/env python3
"""
Test script for Data Aggregation Module

Tests the data aggregation layer functionality.
"""
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.data_aggregation import data_aggregator, get_patient_data_summary


def test_data_aggregator_initialization():
    """Test data aggregator initialization"""
    print("🧪 Testing data aggregator initialization...")
    
    try:
        assert data_aggregator is not None
        assert hasattr(data_aggregator, 'aggregate_patient_data')
        assert hasattr(data_aggregator, 'get_cross_disciplinary_summary')
        print("    ✅ Data aggregator initialized correctly")
        
        # Test convenience function
        assert callable(get_patient_data_summary)
        print("    ✅ Convenience functions available")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Data aggregator initialization test failed: {e}")
        return False


def test_patient_data_aggregation():
    """Test patient data aggregation"""
    print("🧪 Testing patient data aggregation...")
    
    try:
        # Test with non-existent patient (should handle gracefully)
        summary = data_aggregator.aggregate_patient_data("TEST_PATIENT_001")
        
        assert summary is not None
        assert summary.patient_id == "TEST_PATIENT_001"
        assert isinstance(summary.demographics, dict)
        assert isinstance(summary.treatment_notes, list)
        assert isinstance(summary.outcome_measures, list)
        assert isinstance(summary.disciplines_involved, list)
        assert isinstance(summary.data_completeness, dict)
        
        print("    ✅ Patient data aggregation working")
        print(f"    ✅ Demographics keys: {list(summary.demographics.keys())}")
        print(f"    ✅ Data completeness: {summary.data_completeness}")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Patient data aggregation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_extraction_methods():
    """Test individual data extraction methods"""
    print("🧪 Testing data extraction methods...")
    
    try:
        # Test demographics extraction
        demographics = data_aggregator._get_patient_demographics("TEST_PATIENT")
        assert isinstance(demographics, dict)
        assert 'patient_id' in demographics
        print("    ✅ Demographics extraction working")
        
        # Test treatment notes extraction  
        notes = data_aggregator._get_treatment_notes("TEST_PATIENT")
        assert isinstance(notes, list)
        print("    ✅ Treatment notes extraction working")
        
        # Test outcome measures extraction
        measures = data_aggregator._get_outcome_measures("TEST_PATIENT")
        assert isinstance(measures, list)
        print("    ✅ Outcome measures extraction working")
        
        # Test appointments extraction
        appointments = data_aggregator._get_appointments("TEST_PATIENT")
        assert isinstance(appointments, list)
        print("    ✅ Appointments extraction working")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Data extraction methods test failed: {e}")
        return False


def test_cross_disciplinary_summary():
    """Test cross-disciplinary summary functionality"""
    print("🧪 Testing cross-disciplinary summary...")
    
    try:
        summary = data_aggregator.get_cross_disciplinary_summary("TEST_PATIENT")
        
        assert isinstance(summary, dict)
        assert 'patient_id' in summary
        assert 'disciplines_involved' in summary
        assert 'discipline_breakdown' in summary
        assert 'collaborative_indicators' in summary
        
        print("    ✅ Cross-disciplinary summary working")
        print(f"    ✅ Summary keys: {list(summary.keys())}")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Cross-disciplinary summary test failed: {e}")
        return False


def test_data_completeness_assessment():
    """Test data completeness assessment"""
    print("🧪 Testing data completeness assessment...")
    
    try:
        # Test with empty data
        demographics = {'patient_id': 'TEST', 'name': 'Test Patient'}
        treatment_notes = []
        outcome_measures = []
        assessments = []
        appointments = []
        
        completeness = data_aggregator._assess_data_completeness(
            demographics, treatment_notes, outcome_measures, assessments, appointments
        )
        
        assert isinstance(completeness, dict)
        assert 'has_demographics' in completeness
        assert 'has_treatment_notes' in completeness
        assert 'has_outcome_measures' in completeness
        assert completeness['has_demographics'] is True  # Has name
        assert completeness['has_treatment_notes'] is False  # No notes
        
        print("    ✅ Data completeness assessment working")
        print(f"    ✅ Completeness assessment: {completeness}")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Data completeness assessment test failed: {e}")
        return False


def test_discipline_extraction():
    """Test discipline extraction from data"""
    print("🧪 Testing discipline extraction...")
    
    try:
        # Test with sample data
        treatment_notes = [
            {'profession': 'Physiotherapy'},
            {'profession': 'Occupational Therapy'},
            {'profession': 'Physiotherapy'}
        ]
        outcome_measures = [
            {'profession': 'Speech Therapy'}
        ]
        assessments = [
            {'profession': 'Psychology'}
        ]
        
        disciplines = data_aggregator._extract_disciplines(treatment_notes, outcome_measures, assessments)
        
        assert isinstance(disciplines, list)
        expected_disciplines = ['Occupational Therapy', 'Physiotherapy', 'Psychology', 'Speech Therapy']
        assert set(disciplines) == set(expected_disciplines)
        
        print("    ✅ Discipline extraction working")
        print(f"    ✅ Extracted disciplines: {disciplines}")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Discipline extraction test failed: {e}")
        return False


def main():
    """Run all data aggregation tests"""
    print("🚀 Starting Data Aggregation Layer Tests")
    print("=" * 60)
    
    tests = [
        test_data_aggregator_initialization,
        test_patient_data_aggregation,
        test_data_extraction_methods,
        test_cross_disciplinary_summary,
        test_data_completeness_assessment,
        test_discipline_extraction
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
        print("-" * 40)
    
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All data aggregation tests passed!")
        return True
    else:
        print("💥 Some data aggregation tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)