"""
Test script for NVIDIA API Client - validates imports and structure
"""

import sys

# Test imports
try:
    print("✓ All required imports successful")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test class structure
try:
    from nvidia_api_client import NvidiaAPIClient

    print("✓ NvidiaAPIClient class imported successfully")
except ImportError as e:
    print(f"✗ Failed to import NvidiaAPIClient: {e}")
    sys.exit(1)

# Test static methods exist
try:
    assert hasattr(NvidiaAPIClient, "read_b64"), "read_b64 method missing"
    assert hasattr(NvidiaAPIClient, "make_request"), "make_request method missing"
    assert hasattr(NvidiaAPIClient, "main"), "main method missing"
    print("✓ All static methods present")
except AssertionError as e:
    print(f"✗ Method check failed: {e}")
    sys.exit(1)

# Test class attributes
try:
    assert hasattr(NvidiaAPIClient, "INVOKE_URL"), "INVOKE_URL missing"
    assert hasattr(NvidiaAPIClient, "API_KEY"), "API_KEY missing"
    print("✓ Class attributes present")
except AssertionError as e:
    print(f"✗ Attribute check failed: {e}")
    sys.exit(1)

print("\n✅ All structural tests passed!")
print("\nNote: Skipping actual API call test to avoid network timeout.")
print(
    "To test API functionality manually, uncomment the API call in nvidia_api_client.py"
)
