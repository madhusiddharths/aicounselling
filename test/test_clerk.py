#!/usr/bin/env python3
"""
Test Clerk Authentication Configuration
This script validates your Clerk API keys and configuration
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def test_clerk_keys_exist():
    """Check if Clerk keys exist in environment"""

    print("\n" + "="*60)
    print("🔍 Testing Clerk Key Configuration")
    print("="*60)

    publishable_key = os.getenv('NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY')
    secret_key = os.getenv('CLERK_SECRET_KEY')

    if not publishable_key:
        print("❌ ERROR: NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY not found in .env")
        return False

    if not secret_key:
        print("❌ ERROR: CLERK_SECRET_KEY not found in .env")
        return False

    # Validate key format
    if not publishable_key.startswith('pk_'):
        print(f"⚠️  WARNING: NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY doesn't start with 'pk_'")
        print(f"   Got: {publishable_key[:20]}...")
        return False

    if not secret_key.startswith('sk_'):
        print(f"⚠️  WARNING: CLERK_SECRET_KEY doesn't start with 'sk_'")
        print(f"   Got: {secret_key[:20]}...")
        return False

    print("✅ Publishable Key found and valid format")
    print(f"   {publishable_key[:30]}...")
    print("✅ Secret Key found and valid format")
    print(f"   {secret_key[:30]}...")

    return True


def test_clerk_api_connection():
    """Test connection to Clerk API using the secret key"""

    print("\n" + "="*60)
    print("🔍 Testing Clerk API Connection")
    print("="*60)

    secret_key = os.getenv('CLERK_SECRET_KEY')

    if not secret_key:
        print("❌ ERROR: CLERK_SECRET_KEY not found")
        return False

    try:
        # Test basic API connection by fetching users
        headers = {
            'Authorization': f'Bearer {secret_key}',
            'Content-Type': 'application/json'
        }

        response = requests.get(
            'https://api.clerk.com/v1/users',
            headers=headers,
            timeout=5
        )

        if response.status_code == 200:
            print("✅ Successfully connected to Clerk API")
            users_data = response.json()

            # Handle paginated response
            if isinstance(users_data, list):
                user_count = len(users_data)
            else:
                user_count = users_data.get('total_count', len(users_data.get('data', [])))

            print(f"✅ Retrieved user data")
            print(f"   Total users in your Clerk instance: {user_count}")
            return True

        elif response.status_code == 401:
            print("❌ ERROR: Authentication failed (401 Unauthorized)")
            print("   Check that your CLERK_SECRET_KEY is correct")
            return False

        elif response.status_code == 403:
            print("❌ ERROR: Permission denied (403 Forbidden)")
            return False

        else:
            print(f"❌ ERROR: API returned status code {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False

    except requests.exceptions.Timeout:
        print("❌ ERROR: API request timed out")
        return False

    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to Clerk API")
        print("   Check your internet connection")
        return False

    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        return False


def test_clerk_env_urls():
    """Verify Clerk redirect URLs are configured"""

    print("\n" + "="*60)
    print("🔍 Testing Clerk Environment URLs")
    print("="*60)

    sign_in_url = os.getenv('NEXT_PUBLIC_CLERK_SIGN_IN_URL', '/sign-in')
    sign_up_url = os.getenv('NEXT_PUBLIC_CLERK_SIGN_UP_URL', '/sign-up')
    after_sign_in = os.getenv('NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL', '/')
    after_sign_up = os.getenv('NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL', '/')

    print(f"✅ Sign In URL: {sign_in_url}")
    print(f"✅ Sign Up URL: {sign_up_url}")
    print(f"✅ After Sign In URL: {after_sign_in}")
    print(f"✅ After Sign Up URL: {after_sign_up}")

    # Verify they follow expected patterns
    if not sign_in_url.startswith('/'):
        print(f"⚠️  WARNING: SIGN_IN_URL should be a relative path (starting with /)")

    if not sign_up_url.startswith('/'):
        print(f"⚠️  WARNING: SIGN_UP_URL should be a relative path (starting with /)")

    return True


def main():
    """Run all Clerk tests"""

    print("\n" + "="*60)
    print("🚀 Clerk Authentication Test Suite")
    print("="*60)

    results = {
        "Key Configuration": test_clerk_keys_exist(),
        "API Connection": test_clerk_api_connection(),
        "Environment URLs": test_clerk_env_urls(),
    }

    # Summary
    print("\n" + "="*60)
    print("📋 Test Summary")
    print("="*60)

    all_passed = True
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False

    print("="*60)

    if all_passed:
        print("\n🎉 All Clerk tests passed!")
        print("\n📝 Next steps:")
        print("   1. Your Clerk keys are valid and connected to the API")
        print("   2. Run: npm install")
        print("   3. Run: npm run dev")
        print("   4. Visit: http://localhost:3000/sign-in")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())

