"""End-to-end tests for complete containerized storage workflow."""

import pytest
import requests
import time
import tempfile
import docker
import subprocess
import os
from pathlib import Path
import json
from typing import Dict, Any


class TestStorageWorkflowE2E:
    """End-to-end tests for complete storage containerization workflow."""

    @pytest.fixture(scope="class")
    def docker_client(self):
        """Docker client for container management."""
        return docker.from_env()

    @pytest.fixture(scope="class")
    def sample_molecules(self):
        """Sample molecular files for testing."""
        return {
            "small.pdb": """HEADER    TEST MOLECULE                           01-JAN-24   1ABC
ATOM      1  N   ALA A   1      20.154  16.967  14.365  1.00 20.00           N
ATOM      2  CA  ALA A   1      21.155  17.999  14.618  1.00 20.00           C
ATOM      3  C   ALA A   1      22.593  17.506  14.897  1.00 20.00           C
ATOM      4  O   ALA A   1      23.047  16.651  14.154  1.00 20.00           O
END""",
            "glucose.sdf": """
  Mrv2311 01012400002D

  12 11  0  0  0  0            999 V2000
   -2.1434    0.7500    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
   -1.4289    0.3375    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
   -0.7145    0.7500    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
    0.0000    0.3375    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    0.7145    0.7500    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    1.4289    0.3375    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
    0.0000   -0.4875    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
   -0.7145   -0.9000    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
   -1.4289   -0.4875    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
   -2.1434   -0.9000    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
    0.7145   -0.9000    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
   -2.8579    0.3375    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
  1  2  1  0  0  0  0
  2  3  1  0  0  0  0
  3  4  1  0  0  0  0
  4  5  1  0  0  0  0
  5  6  1  0  0  0  0
  4  7  1  0  0  0  0
  7  8  1  0  0  0  0
  8  9  1  0  0  0  0
  9  2  1  0  0  0  0
  9 10  1  0  0  0  0
  7 11  1  0  0  0  0
  1 12  1  0  0  0  0
M  END
$$$$
"""
        }

    @pytest.fixture(scope="class")
    def full_stack_deployment(self, docker_client):
        """Deploy full containerized stack for E2E testing."""
        # Start required services
        services = [
            "postgres", "redis", "storage", "api", "frontend"
        ]

        # Check if services are already running
        containers = docker_client.containers.list()
        running_services = [
            container.name for container in containers
            if any(service in container.name for service in services)
        ]

        if len(running_services) < len(services):
            # Start the full stack
            result = subprocess.run(
                ["docker", "compose", "up", "-d"] + services,
                cwd=".",
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                pytest.skip(f"Failed to start services: {result.stderr}")

            # Wait for services to be ready
            max_wait = 120  # 2 minutes
            start_time = time.time()

            while time.time() - start_time < max_wait:
                try:
                    # Check frontend health
                    frontend_response = requests.get(
                        "http://localhost:3000/health",
                        timeout=5
                    )

                    # Check storage health
                    storage_response = requests.get(
                        "http://localhost:8080/health",
                        timeout=5
                    )

                    if (frontend_response.status_code == 200 and
                        storage_response.status_code == 200):
                        break

                except (requests.exceptions.ConnectionError,
                        requests.exceptions.Timeout):
                    time.sleep(5)
            else:
                pytest.skip("Services failed to start within timeout")

        yield services

        # Optional cleanup (comment out for debugging)
        # subprocess.run(["docker", "compose", "down"], cwd=".", capture_output=True)

    def test_complete_storage_workflow_pdb(self, full_stack_deployment, sample_molecules):
        """Test complete workflow: upload PDB -> store -> retrieve -> verify."""

        # Step 1: Verify storage service is accessible
        storage_health = requests.get("http://localhost:8080/health")
        assert storage_health.status_code == 200
        assert storage_health.json()["status"] == "healthy"

        # Step 2: Check frontend proxy to storage
        frontend_health = requests.get("http://localhost:3000/health")
        assert frontend_health.status_code == 200

        # Step 3: Upload molecule via API (simulated - we'll test direct storage)
        molecule_content = sample_molecules["small.pdb"]

        # Direct storage upload to test storage service functionality
        upload_response = requests.put(
            "http://localhost:8080/uploads/org-test-e2e/molecules/small.pdb",
            data=molecule_content.encode('utf-8'),
            headers={"Content-Type": "chemical/x-pdb"}
        )

        # Should succeed or already exist
        assert upload_response.status_code in [201, 204, 409]

        # Step 4: Verify file is stored and accessible
        retrieve_response = requests.get(
            "http://localhost:8080/uploads/org-test-e2e/molecules/small.pdb"
        )
        assert retrieve_response.status_code == 200
        assert "HEADER" in retrieve_response.text
        assert "ATOM" in retrieve_response.text

        # Step 5: Verify file content integrity
        retrieved_content = retrieve_response.text.strip()
        original_content = molecule_content.strip()
        assert retrieved_content == original_content

    def test_complete_storage_workflow_sdf(self, full_stack_deployment, sample_molecules):
        """Test complete workflow with SDF format."""

        molecule_content = sample_molecules["glucose.sdf"]

        # Upload SDF file
        upload_response = requests.put(
            "http://localhost:8080/uploads/org-test-e2e/molecules/glucose.sdf",
            data=molecule_content.encode('utf-8'),
            headers={"Content-Type": "chemical/x-mdl-sdfile"}
        )

        assert upload_response.status_code in [201, 204, 409]

        # Retrieve and verify
        retrieve_response = requests.get(
            "http://localhost:8080/uploads/org-test-e2e/molecules/glucose.sdf"
        )
        assert retrieve_response.status_code == 200
        assert "V2000" in retrieve_response.text
        assert "M  END" in retrieve_response.text
        assert "$$$$" in retrieve_response.text

    def test_storage_service_cors_integration(self, full_stack_deployment):
        """Test CORS headers work correctly for cross-origin requests."""

        # Test preflight request
        options_response = requests.options(
            "http://localhost:8080/uploads/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "PUT",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )

        assert options_response.status_code == 204
        assert "Access-Control-Allow-Origin" in options_response.headers
        assert "Access-Control-Allow-Methods" in options_response.headers
        assert "PUT" in options_response.headers["Access-Control-Allow-Methods"]

    def test_storage_directory_organization(self, full_stack_deployment, sample_molecules):
        """Test storage maintains proper directory structure."""

        # Upload files to different organizations
        orgs = ["org-alpha", "org-beta"]

        for org in orgs:
            for filename, content in sample_molecules.items():
                upload_response = requests.put(
                    f"http://localhost:8080/uploads/{org}/molecules/{filename}",
                    data=content.encode('utf-8'),
                    headers={"Content-Type": "chemical/x-pdb"}
                )
                assert upload_response.status_code in [201, 204, 409]

        # Verify organization separation
        for org in orgs:
            org_listing = requests.get(f"http://localhost:8080/uploads/{org}/")
            assert org_listing.status_code == 200

            molecules_listing = requests.get(f"http://localhost:8080/uploads/{org}/molecules/")
            assert molecules_listing.status_code == 200

            # Check both files exist for this org
            for filename in sample_molecules.keys():
                file_response = requests.get(
                    f"http://localhost:8080/uploads/{org}/molecules/{filename}"
                )
                assert file_response.status_code == 200

    def test_storage_volume_persistence(self, full_stack_deployment, sample_molecules, docker_client):
        """Test storage persists across container restarts."""

        # Upload a test file
        test_content = sample_molecules["small.pdb"]
        upload_response = requests.put(
            "http://localhost:8080/uploads/org-persistence/molecules/test-persist.pdb",
            data=test_content.encode('utf-8'),
            headers={"Content-Type": "chemical/x-pdb"}
        )
        assert upload_response.status_code in [201, 204, 409]

        # Restart storage container
        result = subprocess.run(
            ["docker", "compose", "restart", "storage"],
            cwd=".",
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

        # Wait for storage to be ready again
        max_wait = 30
        for _ in range(max_wait):
            try:
                health_response = requests.get("http://localhost:8080/health", timeout=2)
                if health_response.status_code == 200:
                    break
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                time.sleep(1)
        else:
            pytest.fail("Storage service failed to restart")

        # Verify file still exists after restart
        retrieve_response = requests.get(
            "http://localhost:8080/uploads/org-persistence/molecules/test-persist.pdb"
        )
        assert retrieve_response.status_code == 200
        assert retrieve_response.text.strip() == test_content.strip()

    @pytest.mark.performance
    def test_storage_concurrent_operations(self, full_stack_deployment, sample_molecules):
        """Test storage handles concurrent file operations."""
        import concurrent.futures
        import threading

        def upload_file(org_id: str, file_id: str, content: str) -> bool:
            """Upload a file and return success status."""
            try:
                response = requests.put(
                    f"http://localhost:8080/uploads/{org_id}/molecules/{file_id}.pdb",
                    data=content.encode('utf-8'),
                    headers={"Content-Type": "chemical/x-pdb"},
                    timeout=10
                )
                return response.status_code in [201, 204, 409]
            except Exception:
                return False

        # Prepare concurrent operations
        operations = []
        content = sample_molecules["small.pdb"]

        for i in range(10):
            operations.append((f"org-concurrent-{i % 3}", f"file-{i}", content))

        # Execute concurrent uploads
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(upload_file, org_id, file_id, content)
                for org_id, file_id, content in operations
            ]

            results = [
                future.result()
                for future in concurrent.futures.as_completed(futures, timeout=30)
            ]

        # All operations should succeed
        assert all(results), f"Some concurrent operations failed: {results.count(False)} failures"

        # Verify all files were stored
        for org_id, file_id, _ in operations:
            response = requests.get(
                f"http://localhost:8080/uploads/{org_id}/molecules/{file_id}.pdb"
            )
            assert response.status_code == 200

    def test_frontend_storage_proxy_integration(self, full_stack_deployment):
        """Test frontend correctly proxies requests to storage service."""

        # Test health check proxy
        proxy_health = requests.get("http://localhost:3000/storage/health")
        direct_health = requests.get("http://localhost:8080/health")

        # Both should work and return same content
        assert proxy_health.status_code == 200
        assert direct_health.status_code == 200
        assert proxy_health.json() == direct_health.json()

        # Test directory listing proxy
        proxy_uploads = requests.get("http://localhost:3000/storage/uploads/")
        direct_uploads = requests.get("http://localhost:8080/uploads/")

        assert proxy_uploads.status_code == 200
        assert direct_uploads.status_code == 200

    def test_storage_error_handling(self, full_stack_deployment):
        """Test storage service error handling and responses."""

        # Test invalid file path (directory traversal attempt)
        invalid_response = requests.put(
            "http://localhost:8080/uploads/../../../etc/passwd",
            data="malicious content",
            headers={"Content-Type": "text/plain"}
        )
        assert invalid_response.status_code in [400, 403, 404]

        # Test non-existent file retrieval
        not_found_response = requests.get(
            "http://localhost:8080/uploads/non-existent-org/molecules/missing.pdb"
        )
        assert not_found_response.status_code == 404

        # Test invalid content type
        invalid_content = requests.put(
            "http://localhost:8080/uploads/org-test/molecules/test.pdb",
            data="<html>not a molecule</html>",
            headers={"Content-Type": "text/html"}
        )
        # Should either reject or accept but not crash
        assert invalid_content.status_code in [200, 201, 204, 400, 415]

    def test_storage_monitoring_endpoints(self, full_stack_deployment):
        """Test storage service monitoring and metrics endpoints."""

        # Health check with detailed info
        health_response = requests.get("http://localhost:8080/health")
        assert health_response.status_code == 200

        health_data = health_response.json()
        required_fields = ["status", "service", "timestamp"]
        for field in required_fields:
            assert field in health_data

        assert health_data["status"] == "healthy"
        assert health_data["service"] == "storage"

    def teardown_method(self):
        """Clean up test files after each test."""
        # Optional: clean up test files
        # This could be implemented to remove test files from storage
        pass
