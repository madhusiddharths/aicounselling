#!/usr/bin/env python3
"""
Test Google Cloud Storage, Project, and Generative AI API
This script tests Google Cloud credentials, GCS buckets, and the Generative AI API
"""

import os
import sys
from dotenv import load_dotenv
from google.cloud import storage
from google.api_core.exceptions import GoogleAPIError, PermissionDenied, NotFound
import google.generativeai as genai
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

def test_gcs_connection():
    """Test Google Cloud Storage connection and bucket access"""

    print("\n" + "="*60)
    print("🔍 Testing Google Cloud Storage")
    print("="*60)

    project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
    bucket_name = os.getenv('GCS_BUCKET')

    if not project_id:
        print("❌ ERROR: GOOGLE_CLOUD_PROJECT_ID not found in .env file")
        return False

    if not bucket_name:
        print("❌ ERROR: GCS_BUCKET not found in .env file")
        return False

    print(f"📍 Project ID: {project_id}")
    print(f"📍 Bucket Name: {bucket_name}")

    try:
        # Create a Storage client
        client = storage.Client(project=project_id)

        # Test project access
        print(f"\n✅ Successfully authenticated with Google Cloud")
        print(f"   Using project: {client.project}")

        # Get the bucket
        bucket = client.bucket(bucket_name)

        # Check if bucket exists and is accessible
        if not bucket.exists():
            print(f"❌ ERROR: Bucket '{bucket_name}' does not exist or is not accessible")
            return False

        print(f"✅ Successfully accessed bucket: {bucket_name}")

        # List blobs in the bucket
        blobs = list(client.list_blobs(bucket_name, max_results=10))
        print(f"\n📊 Bucket Contents (showing up to 10 items):")

        if blobs:
            for blob in blobs:
                size_mb = blob.size / (1024 * 1024) if blob.size else 0
                print(f"   - {blob.name} ({size_mb:.2f} MB)")
        else:
            print("   (Bucket is empty or has no accessible items)")

        # Test write permissions by uploading a test file
        print(f"\n🧪 Testing write permissions...")
        test_file_name = f"test/connection_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        test_content = b"Connection test file from test_gcs.py"

        test_blob = bucket.blob(test_file_name)
        test_blob.upload_from_string(test_content, content_type="text/plain")
        print(f"✅ Successfully uploaded test file: {test_file_name}")

        # Test read permissions
        downloaded_content = test_blob.download_as_string()
        if downloaded_content == test_content:
            print(f"✅ Successfully downloaded and verified test file")
        else:
            print(f"⚠️  Downloaded content doesn't match original")

        # Clean up test file
        test_blob.delete()
        print(f"✅ Cleaned up test file")

        return True

    except PermissionDenied as e:
        print(f"❌ ERROR: Permission Denied - {e}")
        print("   Make sure you're authenticated with 'gcloud auth application-default login'")
        return False
    except NotFound as e:
        print(f"❌ ERROR: Resource Not Found - {e}")
        return False
    except GoogleAPIError as e:
        print(f"❌ ERROR: Google API Error - {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        return False


def test_generative_ai_api():
    """Test Google Generative AI API"""

    print("\n" + "="*60)
    print("🔍 Testing Google Generative AI API")
    print("="*60)

    api_key = os.getenv('GOOGLE_GENERATIVE_AI_API_KEY')

    if not api_key:
        print("❌ ERROR: GOOGLE_GENERATIVE_AI_API_KEY not found in .env file")
        return False

    print(f"📍 API Key: {api_key[:20]}...***hidden***")

    try:
        # Configure the API
        genai.configure(api_key=api_key)
        print("✅ Successfully configured Generative AI API")

        # List available models
        models = genai.list_models()
        print(f"\n📊 Available Models:")

        model_count = 0
        for model in models:
            model_count += 1
            # Show only the first few models
            if model_count <= 5:
                print(f"   - {model.name}")

        if model_count > 5:
            print(f"   ... and {model_count - 5} more models")

        print(f"\n   Total available models: {model_count}")

        # Test with a simple prompt
        print(f"\n🧪 Testing API with a simple prompt...")
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content("Say 'Hello from AI Counselling!'")

        if response.text:
            print(f"✅ API Response: {response.text}")
        else:
            print(f"⚠️  No text in response")

        return True

    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        return False


def main():
    """Run all tests"""

    print("\n" + "="*60)
    print("🚀 Google Cloud Integration Test Suite")
    print("="*60)

    results = {
        "Google Cloud Storage": test_gcs_connection(),
        "Generative AI API": test_generative_ai_api(),
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
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())

