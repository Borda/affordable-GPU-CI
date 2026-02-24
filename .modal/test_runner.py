"""
GPU Test Runner
Run tests on Modal's GPU infrastructure with pytest interface similar to local execution.

Usage:
    modal run .modal/test_runner.py --test-path tests/ --pytest-args "-v"
    modal run .modal/test_runner.py --test-path tests/datasets/ --pytest-args "-v -k synthetic"

Environment Variables:
    MODAL_GPU: GPU type to use (default: L4, options: L4, T4, A10G, A100, etc.)
"""

import os
import sys
from pathlib import Path

import modal

# Create Modal app with a fixed, descriptive name
app = modal.App("ci-gpu-tests")

# Get GPU type from environment or default to L4
GPU_TYPE = os.environ.get("MODAL_GPU", "L4")

# Start with PyTorch public image for faster builds
# Using PyTorch 2.8 with CUDA 12.6
# Note: copy=True is required when running build commands after add_local_dir
image = (
    modal.Image.from_registry(
        "nvcr.io/nvidia/pytorch:25.01-py3",  # PyTorch 2.8 with CUDA 12.6
        add_python="3.10",
    )
    .apt_install("git")
    .pip_install("uv")
    # Copy project files, excluding large/unnecessary files using .gitignore patterns
    # Using copy=True so we can install dependencies during build
    .add_local_dir(
        ".",
        remote_path="/root/project",
        copy=True,
        # todo: improve this ignoring to be dynamic
        ignore=[
            ".git",
            "__pycache__",
            "*.pyc",
            ".pytest_cache",
            ".venv",
            "venv",
            "*.egg-info",
            ".DS_Store",
            "*.log",
            ".modal",
            "debugging",
            "docs",
            "uv.lock",
        ],
    )
    .workdir("/root/project")
    # Install dependencies during image build for faster execution
    # Note: tests dependencies are in [dependency-groups] not [project.optional-dependencies]
    .run_commands("uv pip install -e . --group tests --system")
)


@app.function(
    image=image,
    gpu=GPU_TYPE,  # GPU type from environment variable
    timeout=3600,  # Hard 1 hour timeout safety limit
)
def run_tests(test_path: str = "tests/", pytest_args: str = "-v") -> dict[str, object]:
    """Run pytest on Modal GPU infrastructure."""
    import os
    import subprocess

    # Change to project directory
    os.chdir("/root/project")

    # Verify GPU availability
    try:
        import torch

        gpu_info = f"\n{'=' * 80}\nGPU ENVIRONMENT CHECK\n{'=' * 80}\n🎮 GPU Available: {torch.cuda.is_available()}\n"
        if torch.cuda.is_available():
            gpu_info += (
                f"🎮 GPU Device: {torch.cuda.get_device_name(0)}\n"
                f"🎮 GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB\n"
            )
        gpu_info += f"{'=' * 80}\n"
        print(gpu_info)
    except Exception as e:
        print(f"\n{'=' * 80}\nGPU ENVIRONMENT CHECK\n{'=' * 80}\n⚠️  GPU check failed: {e}\n{'=' * 80}\n")

    # Build pytest command
    pytest_cmd = ["pytest", test_path]

    # Add user-provided pytest arguments
    if pytest_args:
        # Split args properly, handling quoted strings
        import shlex

        pytest_cmd.extend(shlex.split(pytest_args))

    # Disable colored output for clean logs (especially for CI)
    pytest_cmd.append("--color=no")

    print(
        f"{'=' * 80}\n"
        f"RUNNING TESTS\n"
        f"{'=' * 80}\n"
        f"Command: {' '.join(pytest_cmd)}\n"
        f"Working directory: {os.getcwd()}\n"
        f"{'=' * 80}\n"
    )

    # Create output directory for pytest logs
    output_dir = Path("/root/project/test-outputs")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "pytest-output.log"

    # Run pytest and stream output to both console and file
    try:
        output_lines: list[str] = []
        with open(output_file, "w") as log_file:
            process = subprocess.Popen(  # noqa: S603
                pytest_cmd,
                cwd="/root/project",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            # Stream output line by line in real time while persisting it.
            if process.stdout is None:
                raise RuntimeError("Failed to capture pytest output stream.")
            for line in process.stdout:
                print(line, end="")
                log_file.write(line)
                output_lines.append(line)
            process.wait()

        print(
            f"\n{'=' * 80}\n"
            f"TEST EXECUTION COMPLETE\n"
            f"{'=' * 80}\n"
            f"Exit code: {process.returncode}\n"
            f"📄 Test output saved to: {output_file}\n"
            f"{'=' * 80}\n"
        )

        return {
            "returncode": process.returncode,
            "success": process.returncode == 0,
            "pytest_output": "".join(output_lines),
            "output_file": str(output_file),
        }

    except Exception as e:
        print(f"\n{'=' * 80}\nERROR DURING TEST EXECUTION\n{'=' * 80}\nError: {e}\n{'=' * 80}\n")

        return {
            "returncode": 1,
            "success": False,
            "error": str(e),
            "pytest_output": "",
        }


@app.local_entrypoint()
def main(
    test_path: str = "tests/",
    pytest_args: str = "-v",
) -> None:
    """Local entrypoint to run tests on Modal GPU."""
    print(
        f"\n{'=' * 80}\n"
        f"GPU TEST RUNNER\n"
        f"{'=' * 80}\n"
        f"📁 Test Path: {test_path}\n"
        f"⚙️  Pytest Args: {pytest_args}\n"
        f"🎮 GPU: {GPU_TYPE}\n"
        f"⏱️  Timeout: 1 hour\n"
        f"{'=' * 80}\n"
    )

    # Run tests remotely and collect output after completion
    result = run_tests.remote(test_path=test_path, pytest_args=pytest_args)

    # Save output to local file
    local_output_dir = Path("test-outputs")
    local_output_dir.mkdir(exist_ok=True)
    local_output_file = local_output_dir / "pytest-output.log"

    if result.get("pytest_output"):
        with open(local_output_file, "w") as f:
            f.write(result["pytest_output"])
        print(f"📄 Test output saved to: {local_output_file}")

    final_status = (
        f"\n{'=' * 80}\nFINAL RESULTS\n{'=' * 80}\nReturn Code: {result['returncode']}\nSuccess: {result['success']}\n"
    )

    if not result["success"]:
        if "error" in result:
            final_status += f"Error: {result['error']}\n"
        final_status += f"{'=' * 80}\n"
        print(final_status)
        sys.exit(result["returncode"])

    final_status += f"{'=' * 80}\n\n✅ All tests passed!"
    print(final_status)
