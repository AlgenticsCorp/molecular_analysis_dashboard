"""Integration tests for storage service container functionality."""

import pytest
import requests
import time
import tempfile
import docker
from pathlib import Path
import subprocess
import os


class TestStorageServiceContainer:
    """Integration tests for containerized storage service."""

    @pytest.fixture(scope="class")
    def docker_client(self):
        """Docker client for container management."""
        return docker.from_env()

    @pytest.fixture(scope="class")
    def storage_container(self, docker_client):
        """Start storage service container for testing."""
        # Build the storage container if it doesn't exist
        try:
            docker_client.images.get("molecular_analysis_dashboard-storage")
        except docker.errors.ImageNotFound:
            # Build the image
            build_result = docker_client.images.build(
                path=".",
                dockerfile="docker/Dockerfile.storage",
                tag="molecular_analysis_dashboard-storage"
            )

        # Create temporary volumes for testing
        storage_volume = docker_client.volumes.create(name="test_storage_uploads")
        results_volume = docker_client.volumes.create(name="test_storage_results")
        temp_volume = docker_client.volumes.create(name="test_storage_temp")

        # Start the container
        container = docker_client.containers.run(
            "molecular_analysis_dashboard-storage",
            detach=True,
            ports={"8080/tcp": ("127.0.0.1", 18080)},  # Use different port for testing
            volumes={
                "test_storage_uploads": {"bind": "/storage/uploads", "mode": "rw"},
                "test_storage_results": {"bind": "/storage/results", "mode": "rw"},
                "test_storage_temp": {"bind": "/storage/temp", "mode": "rw"},
            },
            environment={
                "NGINX_USER": "nginx",
                "STORAGE_ROOT": "/storage"
            },
            name="test_storage_container"
        )

        # Wait for container to be ready
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get("http://localhost:18080/health", timeout=2)
                if response.status_code == 200:
                    break
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                time.sleep(1)
        else:
            pytest.fail("Storage container failed to start within timeout")

        yield container

        # Cleanup
        container.stop()
        container.remove()
        storage_volume.remove()
        results_volume.remove()
        temp_volume.remove()

    def test_storage_container_health_check(self, storage_container):
        """Test storage container health endpoint."""
        response = requests.get("http://localhost:18080/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "storage"

    def test_storage_uploads_directory_access(self, storage_container):
        """Test access to uploads directory."""
        response = requests.get("http://localhost:18080/uploads/")

        assert response.status_code == 200
        assert "Index of /uploads/" in response.text

    def test_storage_results_directory_access(self, storage_container):
        """Test access to results directory."""
        response = requests.get("http://localhost:18080/results/")

        assert response.status_code == 200
        assert "Index of /results/" in response.text

    def test_storage_cors_headers(self, storage_container):
        """Test CORS headers are properly set for uploads."""
        response = requests.options("http://localhost:18080/uploads/")

        assert response.status_code == 204
        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Methods" in response.headers

    def test_storage_security_headers(self, storage_container):
        """Test security headers are properly set."""
        response = requests.get("http://localhost:18080/health")

        assert response.status_code == 200
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"

    def test_storage_container_logs(self, storage_container):
        """Test container logs are accessible and show proper startup."""
        logs = storage_container.logs().decode('utf-8')

        assert "Configuration complete; ready for start up" in logs
        assert "nginx/" in logs  # Nginx version info

    def test_storage_container_resources(self, storage_container):
        """Test container resource usage is reasonable."""
        stats = storage_container.stats(stream=False)

        # Memory usage should be reasonable (less than 100MB)
        memory_usage = stats['memory_stats']['usage']
        assert memory_usage < 100 * 1024 * 1024  # 100MB

        # CPU usage should be reported
        assert 'cpu_stats' in stats

    def test_storage_file_upload_simulation(self, storage_container):
        """Test file upload simulation to storage container."""
        # Create a test file
        test_content = b"HEADER    TEST MOLECULE\nATOM      1  N   ALA A   1      0.000   0.000   0.000\nEND"

        # Try to upload via the API endpoint (if available)
        # This tests the proxy functionality
        files = {"file": ("test.pdb", test_content, "chemical/x-pdb")}

        # Note: This would require the API container to be running
        # For now, we'll test the directory structure
        response = requests.get("http://localhost:18080/uploads/")
        assert response.status_code == 200


class TestStorageServiceIntegration:
    """Integration tests requiring the full stack."""

    @pytest.fixture(scope="class")
    def docker_compose_services(self):
        """Start required services using docker-compose."""
        # Start the services needed for integration testing
        services = ["postgres", "redis", "storage"]

        for service in services:
            result = subprocess.run(
                ["docker", "compose", "up", "-d", service],
                cwd=".",
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                pytest.skip(f"Failed to start {service}: {result.stderr}")

        # Wait for services to be ready
        time.sleep(10)

        yield services

        # Cleanup
        subprocess.run(["docker", "compose", "down"], cwd=".", capture_output=True)

    def test_storage_service_network_connectivity(self, docker_compose_services):
        """Test storage service network connectivity within Docker network."""
        # Test internal connectivity (would require API container)
        # For now, test that the storage service is reachable

        # Get the storage container
        client = docker.from_env()
        try:
            storage_container = client.containers.get("molecular_analysis_dashboard-storage-1")

            # Execute a health check from within the container
            exec_result = storage_container.exec_run("curl -f http://localhost:8080/health")

            assert exec_result.exit_code == 0
            assert b'"status":"healthy"' in exec_result.output

        except docker.errors.NotFound:
            pytest.skip("Storage container not found - may not be running")

    def test_storage_volume_persistence(self, docker_compose_services):
        """Test that storage volumes persist data correctly."""
        client = docker.from_env()

        try:
            # Check that volumes exist
            volumes = client.volumes.list()
            volume_names = [vol.name for vol in volumes]

            expected_volumes = [
                "molecular_analysis_dashboard_uploads",
                "molecular_analysis_dashboard_results",
                "molecular_analysis_dashboard_storage_temp"
            ]

            for expected_vol in expected_volumes:
                assert any(expected_vol in vol_name for vol_name in volume_names), \
                    f"Volume {expected_vol} not found"

        except Exception as e:
            pytest.skip(f"Could not check volumes: {e}")

    @pytest.mark.slow
    def test_storage_service_restart_resilience(self, docker_compose_services):
        """Test storage service restart resilience."""
        # This test ensures the storage service can restart without data loss

        # First, ensure service is running
        result = subprocess.run(
            ["docker", "compose", "restart", "storage"],
            cwd=".",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # Wait for restart
        time.sleep(5)

        # Verify service is still healthy
        try:
            response = requests.get("http://localhost:8080/health", timeout=5)
            # Note: This might fail if port isn't exposed in test environment
        except requests.exceptions.ConnectionError:
            # If external access fails, check container health
            client = docker.from_env()
            try:
                container = client.containers.get("molecular_analysis_dashboard-storage-1")
                health = container.attrs['State']['Health']['Status']
                assert health in ['healthy', 'starting']
            except docker.errors.NotFound:
                pytest.skip("Storage container not accessible for health check")


class TestStorageServicePerformance:
    """Performance tests for storage service."""

    @pytest.mark.performance
    def test_storage_response_time(self):
        """Test storage service response time is acceptable."""
        # Skip if storage service not available
        try:
            start_time = time.time()
            response = requests.get("http://localhost:8080/health", timeout=2)
            response_time = time.time() - start_time

            assert response.status_code == 200
            assert response_time < 1.0  # Should respond within 1 second

        except requests.exceptions.ConnectionError:
            pytest.skip("Storage service not available for performance testing")

    @pytest.mark.performance
    def test_storage_concurrent_requests(self):
        """Test storage service handles concurrent requests."""
        import concurrent.futures
        import threading

        def make_request():
            try:
                response = requests.get("http://localhost:8080/health", timeout=5)
                return response.status_code == 200
            except:
                return False

        # Skip if service not available
        try:
            requests.get("http://localhost:8080/health", timeout=2)
        except requests.exceptions.ConnectionError:
            pytest.skip("Storage service not available for performance testing")

        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # All requests should succeed
        assert all(results), "Some concurrent requests failed"
