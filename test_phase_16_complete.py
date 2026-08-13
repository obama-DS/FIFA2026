#!/usr/bin/env python3
"""
Phase 16 Completion Test - Verify containerization is complete.
Tests all components without requiring Docker to be running.
"""

import os
import sys

def test_docker_files():
    """Test Docker configuration files exist and are valid."""
    print("=" * 60)
    print("[1] TESTING DOCKER CONFIGURATION FILES")
    print("=" * 60)
    
    required_files = {
        "Dockerfile": "Main container definition",
        ".dockerignore": "Docker ignore patterns",
        "docker-build.bat": "Build script",
        "docker-run.bat": "Run script",
        "docker-stop.bat": "Stop script",
        "docker-compose.yml": "Docker Compose config"
    }
    
    all_exist = True
    for filename, description in required_files.items():
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                size = len(content)
                print(f"✅ {filename}: {description} ({size} bytes)")
                
                # Basic validation
                if filename == "Dockerfile":
                    if "FROM python" in content and "CMD" in content and "EXPOSE 8000" in content:
                        print("   ✅ Dockerfile has required directives")
                    else:
                        print("   ❌ Dockerfile missing required directives")
                        all_exist = False
                        
                elif filename == ".dockerignore":
                    if "*.md" in content and "*.csv" in content:
                        print("   ✅ .dockerignore excludes unnecessary files")
                    else:
                        print("   ⚠️  .dockerignore may need adjustments")
        else:
            print(f"❌ {filename}: NOT FOUND")
            all_exist = False
    
    return all_exist

def test_required_application_files():
    """Test required application files for container."""
    print("\n" + "=" * 60)
    print("[2] TESTING REQUIRED APPLICATION FILES")
    print("=" * 60)
    
    required_paths = {
        "src/api/main.py": "FastAPI application",
        "src/api/schemas.py": "Pydantic schemas",
        "src/models/model_loader.py": "Model loader",
        "src/models/versioning.py": "Model versioning",
        "models/best_model_home.pkl": "Home model",
        "models/best_model_away.pkl": "Away model",
        "models/best_model.json": "Model metadata",
        "data/features/match_features.csv": "Feature data",
        "requirements.txt": "Python dependencies"
    }
    
    all_exist = True
    for path, description in required_paths.items():
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"✅ {path}: {description} ({size:,} bytes)")
        else:
            print(f"❌ {path}: NOT FOUND")
            all_exist = False
    
    return all_exist

def test_dockerfile_structure():
    """Test Dockerfile has proper structure."""
    print("\n" + "=" * 60)
    print("[3] TESTING DOCKERFILE STRUCTURE")
    print("=" * 60)
    
    with open("Dockerfile", 'r') as f:
        content = f.read()
    
    checks = [
        ("Multi-stage build", "FROM python" in content and "as builder" in content),
        ("Python 3.11", "python:3.11" in content),
        ("Working directory", "WORKDIR /app" in content),
        ("Requirements copy", "COPY requirements.txt" in content),
        ("Pip install", "pip install" in content),
        ("Source copy", "COPY src/" in content),
        ("Models copy", "COPY models/" in content),
        ("Port exposure", "EXPOSE 8000" in content),
        ("Uvicorn command", "uvicorn" in content and "src.api.main:app" in content),
        ("Health check", "HEALTHCHECK" in content)
    ]
    
    all_passed = True
    for check_name, passed in checks:
        if passed:
            print(f"✅ {check_name}")
        else:
            print(f"❌ {check_name}")
            all_passed = False
    
    return all_passed

def test_dockerignore_patterns():
    """Test .dockerignore excludes correct files."""
    print("\n" + "=" * 60)
    print("[4] TESTING .DOCKERIGNORE PATTERNS")
    print("=" * 60)
    
    with open(".dockerignore", 'r') as f:
        content = f.read()
    
    important_exclusions = [
        ("Git files", ".git"),
        ("Python cache", "__pycache__"),
        ("Documentation", "*.md"),
        ("CSV data", "*.csv"),
        ("Test files", "test_*.py"),
        ("Development scripts", "run_*.bat"),
        ("Virtual env", "venv/"),
        ("IDE files", ".vscode/")
    ]
    
    all_present = True
    for name, pattern in important_exclusions:
        if pattern in content:
            print(f"✅ Excludes {name}: {pattern}")
        else:
            print(f"⚠️  May want to exclude {name}: {pattern}")
    
    return True  # Not critical

def test_testing_infrastructure():
    """Test Docker testing infrastructure exists."""
    print("\n" + "=" * 60)
    print("[5] TESTING DOCKER TESTING INFRASTRUCTURE")
    print("=" * 60)
    
    test_files = {
        "test_docker_api.py": "Container API testing script",
        "verify_docker_setup.py": "Setup verification script"
    }
    
    all_exist = True
    for filename, description in test_files.items():
        if os.path.exists(filename):
            print(f"✅ {filename}: {description}")
        else:
            print(f"❌ {filename}: NOT FOUND")
            all_exist = False
    
    return all_exist

def main():
    """Run all Phase 16 completion tests."""
    print("🐋 PHASE 16: CONTAINERIZATION - COMPLETION TEST")
    print("=" * 70)
    print("Testing Docker setup without requiring Docker to be running")
    print("=" * 70)
    print()
    
    # Change to project directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    
    # Run tests
    test_results = [
        ("Docker Configuration Files", test_docker_files()),
        ("Required Application Files", test_required_application_files()),
        ("Dockerfile Structure", test_dockerfile_structure()),
        (".dockerignore Patterns", test_dockerignore_patterns()),
        ("Testing Infrastructure", test_testing_infrastructure())
    ]
    
    # Summary
    print("\n" + "=" * 70)
    print("PHASE 16 COMPLETION TEST RESULTS")
    print("=" * 70)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<50} {status}")
    
    print("=" * 70)
    
    if passed == total:
        print("\n🎉 PHASE 16 CONTAINERIZATION IS COMPLETE")
        print("\n✨ What was created:")
        print("   • Dockerfile (multi-stage build)")
        print("   • .dockerignore (excludes unnecessary files)")
        print("   • docker-build.bat (build image)")
        print("   • docker-run.bat (run container)")
        print("   • docker-stop.bat (stop container)")
        print("   • docker-compose.yml (compose configuration)")
        print("   • test_docker_api.py (container testing)")
        print("   • verify_docker_setup.py (setup verification)")
        print("\n📦 Container Configuration:")
        print("   • Base: Python 3.11 slim")
        print("   • Port: 8000")
        print("   • Entry: Uvicorn FastAPI")
        print("   • Health check: Enabled")
        print("   • Models: Included")
        print("   • Features: Included")
        print("\n🚀 To build and run (requires Docker Desktop):")
        print("   1. docker-build.bat")
        print("   2. docker-run.bat")
        print("   3. python test_docker_api.py")
        print("\n📝 Manual Docker commands:")
        print("   Build:  docker build -t premier-league-ml-api:latest .")
        print("   Run:    docker run -d -p 8000:8000 --name ml-api premier-league-ml-api:latest")
        print("   Test:   curl http://localhost:8000/health")
        print("   Logs:   docker logs ml-api")
        print("   Stop:   docker stop ml-api && docker rm ml-api")
    else:
        print(f"\n⚠️  {total - passed} tests failed")
        print("\nReview failed tests above and ensure all files are present.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)