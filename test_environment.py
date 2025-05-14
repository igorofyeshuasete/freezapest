import sys
import pkg_resources
import platform

def check_environment():
    print("\n=== Environment Check ===")
    
    # Check Python version
    print(f"\nPython Version: {sys.version}")
    
    # Check Virtual Environment
    print(f"\nVirtual Environment Path: {sys.prefix}")
    
    # Check installed packages
    print("\nInstalled Packages:")
    installed_packages = [f"{pkg.key} {pkg.version}" for pkg 
                        in pkg_resources.working_set]
    for pkg in sorted(installed_packages):
        print(f"  - {pkg}")
    
    # Check system information
    print("\nSystem Information:")
    print(f"  OS: {platform.system()} {platform.version()}")
    print(f"  Machine: {platform.machine()}")
    
    # Check required packages
    required_packages = [
        'streamlit',
        'pandas',
        'werkzeug',
        'psutil'
    ]
    
    print("\nRequired Packages Check:")
    for package in required_packages:
        try:
            pkg_resources.require(package)
            print(f"  ✅ {package}: Installed")
        except pkg_resources.DistributionNotFound:
            print(f"  ❌ {package}: Missing")

if __name__ == "__main__":
    check_environment()