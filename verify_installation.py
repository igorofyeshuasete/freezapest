import sys
from importlib import import_module

def verify_installations():
    """Verify all required packages are installed correctly"""
    required_packages = {
        'numpy': '2.2.4',
        'scipy': '1.15.2',
        'lightgbm': '4.6.0',
        'scikit-learn': '1.6.1',
        'nltk': '3.9.1',
        'gensim': '0.10.1',
        'plotly': '6.0.1',
        'prophet': '1.1.6'
    }
    
    results = []
    for package, required_version in required_packages.items():
        try:
            module = import_module(package)
            installed_version = getattr(module, '__version__', 'unknown')
            status = 'OK' if installed_version == required_version else 'VERSION MISMATCH'
            results.append({
                'package': package,
                'required': required_version,
                'installed': installed_version,
                'status': status
            })
        except ImportError:
            results.append({
                'package': package,
                'required': required_version,
                'installed': 'NOT FOUND',
                'status': 'MISSING'
            })
    
    return results

if __name__ == "__main__":
    print("Python version:", sys.version)
    print("\nPackage Installation Status:")
    print("-" * 80)
    print(f"{'Package':<15} {'Required':<10} {'Installed':<10} {'Status':<15}")
    print("-" * 80)
    
    for result in verify_installations():
        print(
            f"{result['package']:<15} "
            f"{result['required']:<10} "
            f"{result['installed']:<10} "
            f"{result['status']:<15}"
        )