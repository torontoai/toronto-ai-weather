"""
Utility functions for testing and validating the Toronto AI Weather codebase.
"""

import logging
import os
import sys
import unittest
from typing import Dict, Any, List

# Set up logging
logger = logging.getLogger(__name__)

def validate_project_structure() -> Dict[str, Any]:
    """
    Validate the project directory structure.
    
    Returns:
        Dict containing validation results
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    expected_dirs = [
        'api',
        'config',
        'data',
        'docs',
        'frontend',
        'models',
        'tests',
        'utils'
    ]
    
    expected_files = [
        os.path.join('config', 'config.py'),
        os.path.join('data', 'db.py'),
        os.path.join('data', 'ingestion.py'),
        os.path.join('api', 'auth.py'),
        os.path.join('api', 'main.py'),
        os.path.join('models', 'models.py'),
        os.path.join('docs', 'project_plan.md')
    ]
    
    # Check directories
    missing_dirs = []
    for dir_name in expected_dirs:
        dir_path = os.path.join(base_dir, dir_name)
        if not os.path.isdir(dir_path):
            missing_dirs.append(dir_name)
    
    # Check files
    missing_files = []
    for file_path in expected_files:
        full_path = os.path.join(base_dir, file_path)
        if not os.path.isfile(full_path):
            missing_files.append(file_path)
    
    return {
        'base_dir': base_dir,
        'expected_dirs': expected_dirs,
        'expected_files': expected_files,
        'missing_dirs': missing_dirs,
        'missing_files': missing_files,
        'is_valid': len(missing_dirs) == 0 and len(missing_files) == 0
    }

def validate_imports() -> Dict[str, Any]:
    """
    Validate that all required packages can be imported.
    
    Returns:
        Dict containing validation results
    """
    required_packages = [
        'fastapi',
        'sqlalchemy',
        'tensorflow',
        'numpy',
        'pandas',
        'scikit-learn',
        'aiohttp',
        'jose',
        'passlib',
        'pyotp',
        'joblib'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    return {
        'required_packages': required_packages,
        'missing_packages': missing_packages,
        'is_valid': len(missing_packages) == 0
    }

def validate_code_modules() -> Dict[str, List[str]]:
    """
    Validate that all code modules can be imported without errors.
    
    Returns:
        Dict containing validation results
    """
    # Add project root to path
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, base_dir)
    
    modules_to_test = [
        'toronto_ai_weather.config.config',
        'toronto_ai_weather.data.db',
        'toronto_ai_weather.data.ingestion',
        'toronto_ai_weather.api.auth',
        'toronto_ai_weather.api.main',
        'toronto_ai_weather.models.models'
    ]
    
    failed_modules = []
    for module in modules_to_test:
        try:
            __import__(module)
        except Exception as e:
            failed_modules.append(f"{module}: {str(e)}")
    
    return {
        'modules_tested': modules_to_test,
        'failed_modules': failed_modules,
        'is_valid': len(failed_modules) == 0
    }

def run_validation() -> Dict[str, Any]:
    """
    Run all validation checks and return results.
    
    Returns:
        Dict containing all validation results
    """
    structure_validation = validate_project_structure()
    import_validation = validate_imports()
    module_validation = validate_code_modules()
    
    is_valid = (
        structure_validation['is_valid'] and
        import_validation['is_valid'] and
        module_validation['is_valid']
    )
    
    return {
        'structure_validation': structure_validation,
        'import_validation': import_validation,
        'module_validation': module_validation,
        'is_valid': is_valid
    }

if __name__ == "__main__":
    results = run_validation()
    if results['is_valid']:
        print("✅ All validation checks passed!")
    else:
        print("❌ Some validation checks failed:")
        
        if not results['structure_validation']['is_valid']:
            print("\nProject structure issues:")
            if results['structure_validation']['missing_dirs']:
                print(f"  Missing directories: {', '.join(results['structure_validation']['missing_dirs'])}")
            if results['structure_validation']['missing_files']:
                print(f"  Missing files: {', '.join(results['structure_validation']['missing_files'])}")
        
        if not results['import_validation']['is_valid']:
            print("\nMissing packages:")
            print(f"  {', '.join(results['import_validation']['missing_packages'])}")
        
        if not results['module_validation']['is_valid']:
            print("\nModule import issues:")
            for error in results['module_validation']['failed_modules']:
                print(f"  {error}")
