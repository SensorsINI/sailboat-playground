#!/usr/bin/env python3
"""
Test script to verify Windows virtual environment setup
Run this after setting up the Windows virtual environment
"""

import sys
import os
import importlib

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing module imports...")
    
    required_modules = [
        'numpy',
        'pyglet', 
        'pandas',
        'cython',
        'tqdm'
    ]
    
    failed_imports = []
    
    for module in required_modules:
        try:
            importlib.import_module(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module}: {e}")
            failed_imports.append(module)
    
    return failed_imports

def test_sailboat_playground():
    """Test that sailboat_playground modules can be imported"""
    print("\nTesting sailboat_playground modules...")
    
    try:
        from sailboat_playground.engine import Manager, Boat, Environment
        print("✓ Core engine modules")
    except ImportError as e:
        print(f"✗ Core engine modules: {e}")
        return False
    
    try:
        from sailboat_playground.visualization import Viewer, Sailboat
        print("✓ Visualization modules")
    except ImportError as e:
        print(f"✗ Visualization modules: {e}")
        return False
    
    return True

def test_cython_compilation():
    """Test that Cython extensions are compiled"""
    print("\nTesting Cython compilation...")
    
    # Check for compiled .so files (or .pyd on Windows)
    compiled_files = []
    for root, dirs, files in os.walk('sailboat_playground'):
        for file in files:
            if file.endswith(('.so', '.pyd', '.cpython')):
                compiled_files.append(os.path.join(root, file))
    
    if compiled_files:
        print(f"✓ Found {len(compiled_files)} compiled Cython files")
        for file in compiled_files[:5]:  # Show first 5
            print(f"  - {file}")
        if len(compiled_files) > 5:
            print(f"  ... and {len(compiled_files) - 5} more")
    else:
        print("✗ No compiled Cython files found")
        return False
    
    return True

def test_basic_functionality():
    """Test basic functionality of the sailboat playground"""
    print("\nTesting basic functionality...")
    
    try:
        from sailboat_playground.engine import Manager
        
        # Test Manager initialization
        manager = Manager("boats/sample_boat.json", "environments/playground.json")
        print("✓ Manager initialization")
        
        # Test state access
        state = manager.state
        print(f"✓ State access: {type(state)}")
        
        # Test agent state access
        agent_state = manager.agent_state
        print(f"✓ Agent state access: {type(agent_state)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("Sailboat Playground - Windows Environment Test")
    print("=" * 50)
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Current directory: {os.getcwd()}")
    print()
    
    # Run tests
    failed_imports = test_imports()
    sailboat_ok = test_sailboat_playground()
    cython_ok = test_cython_compilation()
    functionality_ok = test_basic_functionality()
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    if not failed_imports and sailboat_ok and cython_ok and functionality_ok:
        print("✓ All tests passed! Windows environment is ready.")
        return 0
    else:
        print("✗ Some tests failed:")
        if failed_imports:
            print(f"  - Failed imports: {', '.join(failed_imports)}")
        if not sailboat_ok:
            print("  - Sailboat playground modules")
        if not cython_ok:
            print("  - Cython compilation")
        if not functionality_ok:
            print("  - Basic functionality")
        return 1

if __name__ == "__main__":
    exit_code = main()
    input("\nPress Enter to exit...")
    sys.exit(exit_code)



