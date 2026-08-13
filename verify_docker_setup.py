#!/usr/bin/env python3
"""
Verify Docker setup is complete for Phase 16.
Checks all required files exist without building or running containers.
"""

import os
import sys

def check_file_exists(filepath, description):
    """Check if a file exists and report."""
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"✅ {description}: {os.path.basename(filepath)} ({size:,} bytes)")
        return True
    else:
        print(f"❌ {description}: {filepath} NOT FOUND")
        return False

def check_directory_exists(dirpath, description):
    """Check if a directory exists and report."""
    if os.path.exists(dirpath) and os.path.isdir(dirpath):
        count = len(os.listdir(dirpath))
        print(f"✅ {description}: {os.path.basename(dirpath)} ({count} items)")
        return True
    else:
        print(f"❌ {description}: {dirpath} NOT FOUND")
        return False

def main():
    """Verify Docker setup completeness."""
    print("=" * 60)
    print("PHASE 16: DOCKER SETUP VERIFICATION")
    print("=" * 60)
    print()
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    
    checks = []
    
    # Docker files
    print("[1] Docker Configuration Files")
    checks.append(check_file_exists("Dockerfile", "Dockerfile"))
    checks.append(check_file_exists(".dockerignore", "Docker ignore file"))
    checks.append(check_file_exists("docker-build.bat", "Docker build script"))
    checks.append(check_file_exists("docker-run.bat", "Docker run script"))
    checks.append(check_file_exists("docker-stop.bat", "Docker stop script"))
    
    # Required application files
    print("\n[2] Application Files")
    checks.append(check_directory_exists("src", "Source code directory"))
    checks.append(check_directory_exists("src/api", "API directory"))
    checks.append(check_file_exists("src/api/main.py", "FastAPI main"))
    checks.append(check_file_exists("src/api/schemas.py", "API schemas"))
    checks.append(check_file_exists("requirements.txt", "Requirements file"))
    
    # Model files
    print("\n[3] Model Files")
    checks.append(check_directory_exists("models", "Models directory"))
    checks.append(check_file_exists("models/best_model.json", "Model metadata"))
    checks.append(check_file_exists("models/best_model_home.pkl", "Home model"))
    checks.append(check_file_exists("models/best_model_away.pkl", "Away model"))
    checks.append(check_file_exists("models/model_registry.json", "Model registry"))
    
    # Feature data
    print("\n[4] Feature Data")
    checks.append(check_file_exists("data/features/match_features.csv", "Match features"))
    
    # Testing files
    print("\n[5] Testing Files")
    checks.append(check_file_exists("test_docker_api.py", "Docker API test script"))
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = sum(checks)
    total = len(checks)
    
    print(f"\nChecks passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL CHECKS PASSED")
        print("\n🐋 Docker setup is complete!")
        print("\nNext steps:")
        print("  1. Ensure Docker Desktop is running")
        print("  2. Build image: docker-build.bat")
        print("  3. Run container: docker-run.bat")
        print("  4. Test API: python test_docker_api.py")
        print("\nManual Docker commands:")
        print("  Build:  docker build -t premier-league-ml-api:latest .")
        print("  Run:    docker run -d -p 8000:8000 --name ml-api premier-league-ml-api:latest")
        print("  Test:   curl http://localhost:8000/health")
        print("  Logs:   docker logs ml-api")
        print("  Stop:   docker stop ml-api && docker rm ml-api")
    else:
        print(f"\n❌ {total - passed} checks failed")
        print("\nPlease ensure all required files exist before building Docker image.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)