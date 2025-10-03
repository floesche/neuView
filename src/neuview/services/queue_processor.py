"""
Queue Processor for neuView.

This service handles processing of queue files, including popping
and executing queued generation commands.
"""

import logging
from pathlib import Path
import yaml

from ..result import Result, Ok, Err
from ..commands import PopCommand, GeneratePageCommand
from ..models import NeuronTypeName

logger = logging.getLogger(__name__)


class QueueProcessor:
    """Service for handling processing of queue files."""

    def __init__(self, config):
        """Initialize queue processor.

        Args:
            config: Configuration object
        """
        self.config = config

    async def pop_and_process_queue(self, command: PopCommand) -> Result[str, str]:
        """Pop and process a queue file."""
        try:
            # Get the queue directory
            queue_dir = Path(self.config.output.directory) / ".queue"

            # Check if queue directory exists
            if not queue_dir.exists():
                return Err("Queue directory does not exist")

            # Try to claim a file - keep trying until we succeed or run out of files
            while True:
                # Find all .yaml files in queue directory (refresh the list each time)
                # Cache manifest is now in .cache/manifest.json, so no exclusion needed
                yaml_files = list(queue_dir.glob("*.yaml"))

                if not yaml_files:
                    return Ok("No more queue files to process.")

                # Try to claim the first yaml file
                yaml_file = yaml_files[0]
                lock_file = yaml_file.with_suffix(".lock")

                try:
                    # Attempt to rename to .lock to claim it
                    yaml_file.rename(lock_file)
                    # Success! We claimed this file, break out of the loop
                    break
                except FileNotFoundError:
                    # File was deleted/renamed by another process, try next file
                    continue

            try:
                # Read the YAML content
                with open(lock_file, "r") as f:
                    queue_data = yaml.safe_load(f)

                if not queue_data or "options" not in queue_data:
                    raise ValueError("Invalid queue file format")

                options = queue_data["options"]
                stored_config_file = queue_data.get("config_file")

                # Convert YAML options back to GeneratePageCommand
                generate_command = GeneratePageCommand(
                    neuron_type=NeuronTypeName(options["neuron-type"]),
                    output_directory=command.output_directory
                    or options.get("output-dir"),
                    image_format=options.get("image-format", "svg"),
                    embed_images=options.get("embed", True),
                    minify=command.minify,
                )

                # Process the command
                result = await self._process_generate_command(
                    generate_command, stored_config_file
                )

                if result.is_ok():
                    # Success - delete the lock file
                    lock_file.unlink()
                    return Ok(
                        f"Generated {result.unwrap()} from queue file {yaml_file.name}"
                    )
                else:
                    # Failure - rename back to .yaml
                    lock_file.rename(yaml_file)
                    return Err(f"Generation failed: {result.unwrap_err()}")

            except Exception as e:
                # Any error during processing - rename back to .yaml
                if lock_file.exists():
                    lock_file.rename(yaml_file)
                raise e

        except Exception as e:
            return Err(f"Failed to pop queue: {str(e)}")

    async def _process_generate_command(
        self, generate_command: GeneratePageCommand, stored_config_file: str = None
    ) -> Result[str, str]:
        """Process a generate command from the queue."""
        try:
            # Get page service from container (we need access to it)
            from ..neuprint_connector import NeuPrintConnector
            from ..config import Config
            from ..page_generator import PageGenerator

            # Use the stored config file if available, otherwise use current config
            if stored_config_file:
                config = Config.load(stored_config_file)
            else:
                config = self.config

            # Create services with the appropriate config
            connector = NeuPrintConnector(config)

            # Create queue service to check for queued neuron types
            from ..core_services import QueueService
            from ..cache import create_cache_manager

            queue_service = QueueService(config)
            cache_manager = create_cache_manager(config.output.directory)
            generator = PageGenerator.create_with_factory(
                config,
                config.output.directory,
                queue_service,
                cache_manager,
                "check_exists",
            )

            # Import the simplified PageGenerationService
            from .page_generation_service import PageGenerationService

            page_service = PageGenerationService(connector, generator, config)

            # Generate the page
            result = await page_service.generate_page(generate_command)
            return result

        except Exception as e:
            return Err(f"Failed to process generate command: {str(e)}")

    def get_queue_status(self) -> dict:
        """Get status information about the queue."""
        queue_dir = Path(self.config.output.directory) / ".queue"

        if not queue_dir.exists():
            return {
                "queue_exists": False,
                "pending_files": 0,
                "locked_files": 0,
                "total_files": 0,
            }

        # Count different types of files
        yaml_files = list(queue_dir.glob("*.yaml"))
        lock_files = list(queue_dir.glob("*.lock"))

        # No need to exclude cache manifest since it's now in .cache directory
        pending_files = yaml_files

        return {
            "queue_exists": True,
            "pending_files": len(pending_files),
            "locked_files": len(lock_files),
            "total_files": len(pending_files) + len(lock_files),
            "manifest_exists": (queue_dir.parent / ".cache" / "manifest.json").exists(),
        }

    def clear_locked_files(self) -> int:
        """Clear any orphaned lock files (useful for cleanup after crashes).

        Returns:
            int: Number of lock files cleared
        """
        queue_dir = Path(self.config.output.directory) / ".queue"

        if not queue_dir.exists():
            return 0

        lock_files = list(queue_dir.glob("*.lock"))
        cleared_count = 0

        for lock_file in lock_files:
            try:
                # Try to rename back to .yaml
                yaml_file = lock_file.with_suffix(".yaml")
                lock_file.rename(yaml_file)
                cleared_count += 1
                logger.info(f"Cleared orphaned lock file: {lock_file.name}")
            except Exception as e:
                logger.warning(f"Failed to clear lock file {lock_file.name}: {e}")

        return cleared_count
