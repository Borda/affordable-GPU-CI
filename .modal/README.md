# Modal GPU Test Runner

This directory contains the Modal-based GPU test runner. It allows you to run tests on Modal's cloud infrastructure with NVIDIA GPUs, similar to running pytest locally.

## Features

- 🎮 **GPU Testing**: Run tests on NVIDIA GPUs (default: L4 with 24GB VRAM)
- 📊 **CI Integration**: Automatic pytest output capture and artifact upload
- 💬 **PR Comments**: Automatically posts test results to PR when triggered by `gpu-tests` label
- 🔄 **Real-time Streaming**: View test output as it happens
- 📦 **Artifact Upload**: pytest logs saved as GitHub Actions artifacts for 30 days

## Files

- **`test_runner.py`**: Main Modal application that runs tests on GPU
- **`modal.toml.example`**: Template for Modal configuration
- **`README.md`**: This file

## Quick Start (Local)

### 1. Set up Modal credentials

```bash
export MODAL_TOKEN_ID=your_token_id
export MODAL_TOKEN_SECRET=your_token_secret
```

### 2. Run tests

```bash
# Run all tests
python -m modal run .modal/test_runner.py

# Run specific test directory
python -m modal run .modal/test_runner.py --test-path tests/datasets/

# Run with specific pytest args
python -m modal run .modal/test_runner.py --pytest-args "-v -k synthetic"

# Run with custom GPU type
MODAL_GPU=A100 modal run .modal/test_runner.py
```

The test runner will automatically:

- Build the container image with dependencies
- Run tests on the specified GPU (default: L4)
- Stream output in real-time
- Save output to `test-outputs/pytest-output.log`

## CI Integration

### Trigger via PR Label

1. Add the `gpu-tests` label to any PR
2. The workflow will automatically:
    - Run tests on Modal GPU
    - Capture pytest output to a log file
    - Upload the log as an artifact
    - Post a comment on the PR with test results
    - Remove the label after completion

### Workflow Files

- **`.github/workflows/label-gpu-tests.yml`**: Triggered by PR label, includes PR comment and label removal
- **`.github/workflows/run-gpu-tests.yml`**: Manual trigger for main/develop branches
- **`.github/workflows/_modal-gpu-tests.yml`**: Reusable workflow that executes tests and uploads artifacts

### Required Secrets

Set these in your repository settings:

- `MODAL_TOKEN_ID`: Your Modal token ID
- `MODAL_TOKEN_SECRET`: Your Modal token secret

### Optional Variables

- `MODAL_GPU`: GPU type to use (defaults to "L4", options: L4, T4, A10G, A100, etc.)

## How It Works

### Test Execution Flow

1. **Modal builds container image**

    - Base: NVIDIA PyTorch 2.8 with CUDA 12.6
    - Install: uv + project dependencies from `pyproject.toml`
    - Copy: Project files (excluding large/unnecessary files)

2. **Tests run on GPU**

    - NVIDIA GPU (default: L4 with 24GB VRAM)
    - pytest executes with provided arguments
    - Output streams to console in real-time
    - Output also saved to `/root/project/test-outputs/pytest-output.log`

3. **Results handling**

    - **Local**: Output displayed in terminal, log file saved remotely
    - **CI**:
        - pytest output saved to `test-outputs/pytest-output.log`
        - Uploaded as GitHub Actions artifact
        - Posted as PR comment (if triggered by label)

### Output Capture

The test runner captures pytest output in two ways:

- **Console**: Real-time streaming for monitoring
- **File**: Complete log saved to `test-outputs/pytest-output.log`

In CI, the pytest output is uploaded as an artifact and posted to PR comments.

## Configuration

### GPU Type

You can specify the GPU type via environment variable:

```bash
export MODAL_GPU=A100
modal run .modal/test_runner.py
```

Available GPU types: L4, T4, A10G, A100, H100, etc. (see Modal documentation for full list)

### Test Path and Args

You can customize what tests to run:

**Local:**

```bash
modal run .modal/test_runner.py --test-path tests/models/ --pytest-args "-v -x"
```

**CI:**
The reusable workflow runs all tests by default. GPU type can be configured via `MODAL_GPU` repository variable.

## Debugging

### Check GPU availability

The test runner automatically prints GPU information:

```
🎮 GPU Available: True
🎮 GPU Device: NVIDIA L4
🎮 GPU Memory: 24.0 GB
```

### View full logs

If tests fail, check:

1. **Local**: Terminal output
2. **CI**:
    - GitHub Actions logs for full output
    - Download `pytest-output` artifact for clean pytest logs only

### Common Issues

**"Modal credentials not found"**

- Set `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` environment variables

**Tests timeout**

- Default timeout is 1 hour
- Increase in `test_runner.py` if needed: `timeout=7200`

## Development

### Modifying the Test Runner

1. Edit `test_runner.py`
2. Test locally: `modal run .modal/test_runner.py`
3. Modal will rebuild the image automatically

## Support

For issues or questions:

1. Check GitHub Actions logs
2. Review Modal dashboard for infrastructure issues
3. Check pytest-output artifact for clean test logs
