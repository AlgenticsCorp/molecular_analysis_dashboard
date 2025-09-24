"""Test script for the ExecuteDockingTaskUseCase.

This script demonstrates the complete workflow for executing GNINA docking
tasks using the new use case layer, connecting the adapters to a clean
application service interface.
"""

import asyncio
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up the path for imports
import sys
sys.path.insert(0, '/Users/ahb/Documents/Incorp Algentics/projects/Molecular_Analysis_Dashboard/molecular_analysis_dashboard/src')

async def test_docking_use_case():
    """Test the complete docking workflow via use case."""

    try:
        # Import required components
        from molecular_analysis_dashboard.use_cases.commands.execute_docking_task import (
            ExecuteDockingTaskUseCase,
            DockingTaskRequest
        )
        from molecular_analysis_dashboard.adapters.external.neurosnap_adapter import NeuroSnapAdapter
        from molecular_analysis_dashboard.adapters.external.ligand_prep_adapter import RDKitLigandPrepAdapter

        # Check for API key
        api_key = os.getenv('NEUROSNAP_API_KEY')
        if not api_key:
            logger.error("❌ NEUROSNAP_API_KEY environment variable not set")
            logger.info("Set your API key with: export NEUROSNAP_API_KEY='your-key-here'")
            return

        logger.info("🧪 Testing ExecuteDockingTaskUseCase")
        logger.info("=" * 60)

        # Initialize adapters
        logger.info("🔧 Initializing adapters...")
        neurosnap_adapter = NeuroSnapAdapter(api_key=api_key)
        ligand_prep_adapter = RDKitLigandPrepAdapter()

        # Initialize use case
        use_case = ExecuteDockingTaskUseCase(
            docking_adapter=neurosnap_adapter,
            ligand_prep_adapter=ligand_prep_adapter,
            neurosnap_adapter=neurosnap_adapter
        )

        logger.info("✅ Use case initialized successfully")

        # Create a test request
        logger.info("📋 Creating docking task request...")

        # Example receptor (simplified - would normally be PDB data)
        receptor_data = {
            'name': 'EGFR Kinase Domain',
            'format': 'pdb',
            'data': 'HEADER    TRANSFERASE                             01-JUN-05   1M17'  # Simplified
        }

        request = DockingTaskRequest(
            receptor=receptor_data,
            ligand="osimertinib",  # Drug name - will be prepared automatically
            binding_site={
                'center_x': 25.5,
                'center_y': 10.2,
                'center_z': 15.8,
                'size_x': 20.0,
                'size_y': 20.0,
                'size_z': 20.0
            },
            job_note="Use case integration test",
            max_poses=5,
            energy_range=2.0,
            timeout_minutes=15,
            organization_id="test-org",
            user_id="test-user"
        )

        logger.info("✅ Task request created")
        logger.info(f"   Receptor: {request.receptor['name']}")
        logger.info(f"   Ligand: {request.ligand}")
        logger.info(f"   Max poses: {request.max_poses}")

        # Execute the workflow
        logger.info("🚀 Starting docking execution...")
        start_time = datetime.utcnow()

        execution = await use_case.execute(request)

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Display results
        logger.info("=" * 60)
        logger.info("📊 EXECUTION RESULTS")
        logger.info("=" * 60)
        logger.info(f"✅ Execution Status: {execution.status.value}")
        logger.info(f"🆔 Execution ID: {execution.execution_id}")
        logger.info(f"🔗 Job ID: {execution.job_id}")
        logger.info(f"⏱️  Duration: {duration:.1f} seconds")

        if execution.results:
            logger.info(f"🧬 Poses Generated: {len(execution.results.poses)}")
            if execution.results.best_pose:
                logger.info(f"🏆 Best Affinity: {execution.results.best_pose.affinity:.2f} kcal/mol")
                logger.info(f"🥇 Best Rank: {execution.results.best_pose.rank}")

            logger.info("📈 Top 3 Poses:")
            top_poses = execution.results.get_top_poses(3)
            for i, pose in enumerate(top_poses, 1):
                logger.info(f"   {i}. Rank {pose.rank}: {pose.affinity:.2f} kcal/mol")
        else:
            logger.warning("⚠️  No results available")

        if execution.error_message:
            logger.error(f"❌ Error: {execution.error_message}")

        logger.info("=" * 60)
        logger.info("🎉 Use case test completed successfully!")

        # Clean up
        await neurosnap_adapter.close()

    except Exception as e:
        logger.error(f"❌ Use case test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_docking_use_case())
