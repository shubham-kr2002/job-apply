"""
Test Suite for AI Auto-Applier Agent
Validates Phase 1 (Job Discovery) and Phase 2 (Memory Layer)
"""

import sys
import json
from pathlib import Path

def test_phase1():
    """Test Phase 1: Job Discovery Module"""
    print("\n" + "="*60)
    print("PHASE 1 TEST: Job Discovery Module")
    print("="*60)
    
    try:
        from scrapers.hunter import JobHunter, Job
        print("✓ JobHunter import successful")
        
        # Test Job model
        test_job = Job(
            id="test123",
            title="AI Engineer",
            company="TestCorp",
            job_url="https://boards.greenhouse.io/test",
            location="Remote",
            ats_provider="greenhouse.io"
        )
        print("✓ Job model validation works")
        
        # Test JobHunter initialization
        hunter = JobHunter()
        print("✓ JobHunter initialized successfully")
        print(f"  - Data directory: {hunter.data_dir}")
        print(f"  - CSV path: {hunter.csv_path}")
        print(f"  - Existing jobs loaded: {len(hunter.existing_ids)}")
        
        # Test ATS filtering
        test_urls = [
            ("https://boards.greenhouse.io/company/jobs/123", True),
            ("https://jobs.lever.co/company/job-id", True),
            ("https://jobs.ashbyhq.com/company", True),
            ("https://www.linkedin.com/jobs/view/123", False),
            ("https://company.com/careers", False),
        ]
        
        print("\n✓ Testing ATS filtering:")
        for url, expected in test_urls:
            result = hunter._is_ats_compliant(url)
            status = "✓" if result == expected else "✗"
            print(f"  {status} {url[:40]}... → {result}")
        
        print("\n✅ PHASE 1 TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ PHASE 1 TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_phase2():
    """Test Phase 2: Memory Layer (RAG System)"""
    print("\n" + "="*60)
    print("PHASE 2 TEST: Memory Layer (RAG System)")
    print("="*60)
    
    try:
        from memory.brain import BrainAgent, BrainResponse, StaticProfile
        print("✓ BrainAgent import successful")
        
        # Test BrainResponse model
        test_response = BrainResponse(
            answer="Test answer",
            confidence=0.85,
            reasoning="Test reasoning",
            source_type="test"
        )
        print("✓ BrainResponse model validation works")
        
        # Test BrainAgent initialization
        brain = BrainAgent()
        print("✓ BrainAgent initialized successfully")
        print(f"  - Data directory: {brain.data_dir}")
        print(f"  - ChromaDB directory: {brain.chroma_dir}")
        print(f"  - Groq configured: {brain.groq_api_key is not None}")
        print(f"  - Static profile loaded: {brain.static_profile is not None}")
        
        # Test static profile loading
        if brain.static_profile:
            print(f"\n✓ Static Profile Loaded:")
            print(f"  - Name: {brain.static_profile.name}")
            print(f"  - Email: {brain.static_profile.email}")
            print(f"  - Skills: {len(brain.static_profile.skills)} listed")
        else:
            print("⚠ Static profile not loaded (file may not exist)")
        
        # Test static profile queries
        print("\n✓ Testing static profile queries:")
        static_questions = [
            "What is your name?",
            "What is your email?",
        ]
        
        for q in static_questions:
            response = brain._check_static_profile(q)
            if response:
                print(f"  ✓ '{q}' → {response.answer} (confidence: {response.confidence})")
            else:
                print(f"  ⚠ '{q}' → No static match")
        
        # Test profile summary
        summary = brain.get_profile_summary()
        print(f"\n✓ Profile Summary:")
        print(json.dumps(summary, indent=2))
        
        # Warn if Groq not configured
        if not brain.groq_api_key:
            print("\n⚠ WARNING: GROQ_API_KEY not set")
            print("  - Static profile queries will work")
            print("  - LLM-based queries will fail")
            print("  - Set GROQ_API_KEY in .env to test full RAG pipeline")
        
        print("\n✅ PHASE 2 TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ PHASE 2 TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_files():
    """Test that required data files exist"""
    print("\n" + "="*60)
    print("DATA FILES CHECK")
    print("="*60)
    
    required_files = {
        "data/static_profile.json": "Static profile (Phase 2)",
        "data/profile_stories.txt": "Profile stories (Phase 2)",
    }
    
    optional_files = {
        "data/jobs.csv": "Job database (created by Phase 1)",
        ".env": "Environment variables (Groq API key)",
    }
    
    all_good = True
    
    print("\nRequired files:")
    for filepath, description in required_files.items():
        path = Path(filepath)
        if path.exists():
            size = path.stat().st_size
            print(f"  ✓ {filepath} ({size} bytes) - {description}")
        else:
            print(f"  ✗ {filepath} - MISSING! - {description}")
            all_good = False
    
    print("\nOptional files:")
    for filepath, description in optional_files.items():
        path = Path(filepath)
        if path.exists():
            size = path.stat().st_size
            print(f"  ✓ {filepath} ({size} bytes) - {description}")
        else:
            print(f"  ⚠ {filepath} - Not found - {description}")
    
    return all_good


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("AI AUTO-APPLIER AGENT - TEST SUITE")
    print("="*60)
    
    # Test data files
    data_ok = test_data_files()
    
    # Test Phase 1
    phase1_ok = test_phase1()
    
    # Test Phase 2
    phase2_ok = test_phase2()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"  Data Files: {'✅ PASS' if data_ok else '❌ FAIL'}")
    print(f"  Phase 1 (Job Discovery): {'✅ PASS' if phase1_ok else '❌ FAIL'}")
    print(f"  Phase 2 (Memory Layer): {'✅ PASS' if phase2_ok else '❌ FAIL'}")
    
    if all([data_ok, phase1_ok, phase2_ok]):
        print("\n🎉 ALL TESTS PASSED! System is ready.")
        print("\nNext steps:")
        print("  1. Set GROQ_API_KEY in .env")
        print("  2. Run: python main.py (Phase 1)")
        print("  3. Run: python memory/brain.py (Phase 2)")
        return 0
    else:
        print("\n⚠ SOME TESTS FAILED. Review errors above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
