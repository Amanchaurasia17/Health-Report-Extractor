#!/usr/bin/env python3
"""
Test script for the Health Report Extractor API
"""
import requests
import json
import sys
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_upload_sample_data():
    """Test uploading sample health data"""
    print("\nTesting sample data upload...")
    
    # Create a sample text file with health data
    sample_data = """
    LABORATORY REPORT
    
    Patient: John Doe
    Date: 2025-01-15
    
    TEST RESULTS:
    
    Hemoglobin: 14.2 g/dL (12.0-15.5)
    Glucose: 95 mg/dL (70-100)
    Cholesterol: 185 mg/dL (125-200)
    Creatinine: 1.0 mg/dL (0.7-1.3)
    White Blood Cells: 7.2 k/uL (4.5-11.0)
    Platelets: 250 k/uL (150-450)
    
    All values are within normal limits.
    """
    
    try:
        # Save sample data to a temporary file
        temp_file = Path("sample_health_report.txt")
        temp_file.write_text(sample_data)
        
        # Upload the file
        with open(temp_file, 'rb') as f:
            files = {'file': ('sample_health_report.txt', f, 'text/plain')}
            response = requests.post(f"{BASE_URL}/upload", files=files)
        
        # Clean up
        temp_file.unlink()
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Upload successful: {result.get('records_extracted', 0)} records extracted")
            return True
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Upload test failed: {e}")
        return False

def test_get_records():
    """Test getting all records"""
    print("\nTesting get records endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/records")
        if response.status_code == 200:
            result = response.json()
            records = result.get('records', [])
            print(f"✅ Records retrieved: {len(records)} records found")
            
            # Display first record details if available
            if records:
                first_record = records[0]
                print(f"   Sample record: {first_record.get('name')} = {first_record.get('value')} {first_record.get('unit')}")
                print(f"   Status: {first_record.get('status')}, Severity: {first_record.get('severity')}")
                print(f"   AI Insight: {first_record.get('ai_insight', 'N/A')}")
            
            return True
        else:
            print(f"❌ Get records failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Get records test failed: {e}")
        return False

def test_get_insights():
    """Test getting AI insights"""
    print("\nTesting AI insights endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/insights")
        if response.status_code == 200:
            result = response.json()
            health_summary = result.get('health_summary', {})
            insights = result.get('insights', [])
            recommendations = result.get('recommendations', [])
            
            print(f"✅ Insights retrieved successfully")
            print(f"   Health Score: {health_summary.get('health_score', 'N/A')}")
            print(f"   Overall Status: {health_summary.get('overall_status', 'N/A')}")
            print(f"   Insights: {len(insights)} parameters analyzed")
            print(f"   Recommendations: {len(recommendations)} recommendations")
            
            return True
        else:
            print(f"❌ Get insights failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Get insights test failed: {e}")
        return False

def test_get_stats():
    """Test getting statistics"""
    print("\nTesting statistics endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/stats")
        if response.status_code == 200:
            result = response.json()
            overview = result.get('overview', {})
            distributions = result.get('distributions', {})
            
            print(f"✅ Statistics retrieved successfully")
            print(f"   Total Records: {overview.get('total_records', 0)}")
            print(f"   Normal Percentage: {overview.get('normal_percentage', 0)}%")
            print(f"   Status Distribution: {distributions.get('status_distribution', {})}")
            
            return True
        else:
            print(f"❌ Get statistics failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Get statistics test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Health Report Extractor API Test Suite")
    print("=" * 50)
    
    tests = [
        test_health_check,
        test_upload_sample_data,
        test_get_records,
        test_get_insights,
        test_get_stats
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The API is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the server logs.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
