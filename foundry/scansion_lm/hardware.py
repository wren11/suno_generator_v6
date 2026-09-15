"""Hardware acceleration and multi-GPU optimization engine.

Auto-detects NVIDIA GPUs (including RTX 2080 Dual-GPU / SLI / NVLink setups),
configures Tensor Cores, half-precision (FP16), cuDNN benchmarking, and
distributes inference/training across available devices.
"""

from __future__ import annotations

import os
import sys
from typing import Any

# Default cache
_HARDWARE_INFO: dict[str, Any] | None = None


def get_hardware_info(refresh: bool = False) -> dict[str, Any]:
    """Inspect and return hardware capabilities, detecting multi-GPU and SLI configurations."""
    global _HARDWARE_INFO
    if _HARDWARE_INFO is not None and not refresh:
        return _HARDWARE_INFO

    info: dict[str, Any] = {
        "cuda_available": False,
        "device_count": 0,
        "devices": [],
        "multi_gpu": False,
        "is_sli_or_dual": False,
        "primary_device": "cpu",
        "recommended_dtype": "fp32",
        "tensor_cores": False,
        "total_vram_gb": 0.0,
        "summary": "CPU execution (PyTorch CPU)",
    }

    try:
        import torch

        if torch.cuda.is_available():
            count = torch.cuda.device_count()
            info["cuda_available"] = True
            info["device_count"] = count
            devices = []
            total_vram = 0.0

            for i in range(count):
                name = torch.cuda.get_device_name(i)
                mem_bytes = torch.cuda.get_device_properties(i).total_memory
                mem_gb = round(mem_bytes / (1024**3), 1)
                total_vram += mem_gb
                major, minor = torch.cuda.get_device_capability(i)
                devices.append({
                    "index": i,
                    "name": name,
                    "vram_gb": mem_gb,
                    "compute_capability": f"{major}.{minor}",
                    "has_tensor_cores": major >= 7,
                })

            info["devices"] = devices
            info["total_vram_gb"] = round(total_vram, 1)
            info["multi_gpu"] = count > 1
            info["primary_device"] = "cuda:0"
            info["recommended_dtype"] = "fp16"

            # Check if all GPUs are identical (common in SLI / dual setups like 2x RTX 2080)
            if count >= 2:
                names = [d["name"] for d in devices]
                is_identical = len(set(names)) == 1
                info["is_sli_or_dual"] = is_identical
                d_name = devices[0]["name"]
                info["summary"] = f"🚀 {count}x {d_name} Detected (Multi-GPU/SLI, {info['total_vram_gb']}GB Total VRAM, FP16 Tensor Cores Active)"
            else:
                d_name = devices[0]["name"]
                info["summary"] = f"🚀 {d_name} Detected ({info['total_vram_gb']}GB VRAM, FP16 Active)"

            # Optimize PyTorch CUDA backends
            try:
                if hasattr(torch.backends.cuda.matmul, "allow_tf32"):
                    torch.backends.cuda.matmul.allow_tf32 = True
                if hasattr(torch.backends.cudnn, "benchmark"):
                    torch.backends.cudnn.benchmark = True
                if hasattr(torch.backends.cudnn, "allow_tf32"):
                    torch.backends.cudnn.allow_tf32 = True
            except Exception:
                pass
        else:
            # Check if NVIDIA-SMI shows hardware is physically present but CPU torch is installed
            try:
                import subprocess
                res = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"], capture_output=True, text=True, timeout=2)
                if res.returncode == 0 and res.stdout.strip():
                    lines = [ln.strip() for ln in res.stdout.strip().splitlines() if ln.strip()]
                    info["devices"] = [{"name": ln.split(",")[0].strip()} for ln in lines]
                    info["device_count"] = len(lines)
                    info["multi_gpu"] = len(lines) > 1
                    info["is_sli_or_dual"] = len(lines) >= 2
                    info["summary"] = f"⚠️ {len(lines)}x NVIDIA GPU(s) present ({lines[0].split(',')[0].strip()}), but PyTorch is CPU-only. Run enable_gpu.bat to enable CUDA acceleration."
            except Exception:
                pass
    except Exception as e:
        info["summary"] = f"CPU execution ({e})"

    _HARDWARE_INFO = info
    return info


def get_optimal_device() -> Any:
    """Return optimal torch.device (cuda:0 or cpu)."""
    try:
        import torch
        if torch.cuda.is_available():
            return torch.device("cuda:0")
    except Exception:
        pass
    import torch
    return torch.device("cpu")


def optimize_model_for_hardware(model: Any) -> Any:
    """Move PyTorch model to GPU, cast to FP16, and apply DataParallel if multi-GPU."""
    try:
        import torch
        hw = get_hardware_info()
        if not hw["cuda_available"]:
            return model

        # Move to CUDA and use FP16 for Tensor Cores on RTX 2080
        device = get_optimal_device()
        model = model.to(device)

        try:
            model = model.half()
        except Exception:
            pass

        # Multi-GPU distribution (SLI / Dual RTX 2080)
        if hw["multi_gpu"] and hw["device_count"] > 1:
            try:
                # Wrap with DataParallel for parallel execution across all GPUs
                if not isinstance(model, torch.nn.DataParallel):
                    model = torch.nn.DataParallel(model)
            except Exception:
                pass

        return model
    except Exception:
        return model
