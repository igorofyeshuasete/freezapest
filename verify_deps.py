import sys
import pkg_resources
import subprocess

def verify_and_fix_dependencies():
    """Verify dependencies and attempt to fix missing packages"""
    required_packages = {
        'numpy': '2.2.4',
        'scipy': '1.15.2',
        'pandas': '2.2.3',
        'scikit-learn': '1.6.1',
        'lightgbm': '4.6.0',
        'nltk': '3.9.1',
        'plotly': '6.0.1',
        'prophet': '1.1.6'
    }
    
    missing_packages = []
    version_mismatches = []
    
    print(f"Python {sys.version}")
    print("\nChecking dependencies...")
    print("-" * 60)
    print(f"{'Package':<15} {'Required':<10} {'Installed':<10} {'Status':<15}")
    print("-" * 60)
    
    for package, required_version in required_packages.items():
        try:
            installed = pkg_resources.working_set.by_key[package]
            installed_version = installed.version
            if installed_version == required_version:
                status = 'OK'
            else:
                status = 'VERSION MISMATCH'
                version_mismatches.append((package, required_version))
        except KeyError:
            installed_version = 'NOT FOUND'
            status = 'MISSING'
            missing_packages.append((package, required_version))
            
        print(f"{package:<15} {required_version:<10} {installed_version:<10} {status:<15}")
    
    if missing_packages or version_mismatches:
        print("\nRequired actions:")
        
        if missing_packages:
            print("\nInstall missing packages:")
            for package, version in missing_packages:
                print(f"pip install --only-binary :all: {package}=={version}")
        
        if version_mismatches:
            print("\nFix version mismatches:")
            for package, version in version_mismatches:
                print(f"pip install --only-binary :all: {package}=={version} --force-reinstall")
                
        proceed = input("\nWould you like to automatically fix these issues? (y/n): ")
        if proceed.lower() == 'y':
            print("\nAttempting to fix dependencies...")
            for package, version in missing_packages + version_mismatches:
                try:
                    cmd = f"pip install --only-binary :all: {package}=={version}"
                    print(f"\nExecuting: {cmd}")
                    subprocess.check_call(cmd.split())
                except subprocess.CalledProcessError as e:
                    print(f"Error installing {package}: {str(e)}")
                    print("Try installing manually using the commands above.")

if __name__ == "__main__":
    verify_and_fix_dependencies()