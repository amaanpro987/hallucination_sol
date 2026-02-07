"""
Evaluation API Endpoints
========================
Run evaluations and get metrics.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.evaluation import run_evaluation, analyze_errors

log = logging.getLogger(__name__)
router = APIRouter(prefix="/evaluation", tags=["evaluation"])

# Store evaluation results in memory (in production, use database)
_evaluation_results = {}
_evaluation_jobs = {}


class EvaluationRequest(BaseModel):
    dataset_path: Optional[str] = None
    use_synthetic: bool = True
    task: Optional[str] = None  # qa, dialogue, summarization, general
    max_samples: Optional[int] = None


class EvaluationJob(BaseModel):
    job_id: str
    status: str  # pending | running | done | failed
    progress: float = 0.0
    error: Optional[str] = None


class EvaluationResponse(BaseModel):
    job_id: str
    status: str


@router.post("/run", response_model=EvaluationResponse)
async def start_evaluation(request: EvaluationRequest, background_tasks: BackgroundTasks):
    """
    Start an evaluation job in the background.
    
    Args:
        request: Evaluation configuration
        background_tasks: FastAPI background tasks
        
    Returns:
        Job ID to check status
    """
    import uuid
    job_id = uuid.uuid4().hex[:12]
    
    _evaluation_jobs[job_id] = {
        "status": "pending",
        "progress": 0.0,
        "error": None,
    }
    
    background_tasks.add_task(
        _run_evaluation_task,
        job_id,
        request.dataset_path,
        request.use_synthetic,
        request.max_samples,
    )
    
    return EvaluationResponse(job_id=job_id, status="pending")


async def _run_evaluation_task(
    job_id: str,
    dataset_path: Optional[str],
    use_synthetic: bool,
    max_samples: Optional[int],
):
    """Background task to run evaluation."""
    try:
        _evaluation_jobs[job_id]["status"] = "running"
        
        results = await run_evaluation(
            dataset_path=dataset_path,
            use_synthetic=use_synthetic,
            max_samples=max_samples,
        )
        
        # Add error analysis
        error_analysis = analyze_errors(results)
        results["error_analysis"] = error_analysis
        
        _evaluation_results[job_id] = results
        _evaluation_jobs[job_id]["status"] = "done"
        _evaluation_jobs[job_id]["progress"] = 100.0
        
    except Exception as e:
        log.exception(f"Evaluation job {job_id} failed")
        _evaluation_jobs[job_id]["status"] = "failed"
        _evaluation_jobs[job_id]["error"] = str(e)


@router.get("/jobs/{job_id}", response_model=EvaluationJob)
async def get_evaluation_job(job_id: str):
    """Get evaluation job status."""
    if job_id not in _evaluation_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = _evaluation_jobs[job_id]
    return EvaluationJob(
        job_id=job_id,
        status=job["status"],
        progress=job.get("progress", 0.0),
        error=job.get("error"),
    )


@router.get("/results/{job_id}")
async def get_evaluation_results(job_id: str):
    """Get evaluation results."""
    if job_id not in _evaluation_results:
        # Check if job exists but not done
        if job_id in _evaluation_jobs:
            job = _evaluation_jobs[job_id]
            if job["status"] == "running":
                raise HTTPException(status_code=202, detail="Evaluation still running")
            elif job["status"] == "failed":
                raise HTTPException(status_code=500, detail=job.get("error", "Evaluation failed"))
            else:
                raise HTTPException(status_code=404, detail="Results not ready")
        raise HTTPException(status_code=404, detail="Job not found")
    
    return _evaluation_results[job_id]


@router.get("/quick-synthetic")
async def quick_synthetic_evaluation():
    """
    Run a quick evaluation on synthetic dataset (synchronous for testing).
    """
    try:
        results = await run_evaluation(use_synthetic=True, max_samples=8)
        error_analysis = analyze_errors(results)
        results["error_analysis"] = error_analysis
        return results
    except Exception as e:
        log.exception("Quick evaluation failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/halueval/download")
async def download_halueval(task: str = "qa"):
    """
    Download HaluEval dataset for specified task.
    
    Args:
        task: Task type (qa, dialogue, summarization, general)
        
    Returns:
        Download status and file info
    """
    try:
        from app.evaluation.halueval import download_halueval_dataset
        from app.config import get_settings
        
        settings = get_settings()
        data_dir = settings.DATA_DIR / "halueval"
        
        filepath = download_halueval_dataset(task, data_dir)
        
        # Get file size
        file_size = filepath.stat().st_size
        
        return {
            "status": "success",
            "task": task,
            "filepath": str(filepath),
            "size_bytes": file_size,
            "size_mb": round(file_size / 1024 / 1024, 2),
        }
    except Exception as e:
        log.exception(f"Failed to download HaluEval {task}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/halueval/test")
async def test_halueval(task: str = "qa", max_samples: int = 10):
    """
    Test with HaluEval dataset (downloads if needed).
    
    Args:
        task: Task type (qa, dialogue, summarization, general)
        max_samples: Number of samples to test (default 10, max 100)
        
    Returns:
        Evaluation metrics
    """
    try:
        from app.evaluation.halueval import load_halueval_dataset
        
        # Limit max samples
        max_samples = min(max_samples, 100)
        
        # Load dataset (auto-downloads if needed)
        samples = load_halueval_dataset(task=task, max_samples=max_samples//2, auto_download=True)
        
        log.info(f"Testing with {len(samples)} HaluEval samples from {task} task")
        
        # Run evaluation with HaluEval data
        results = await run_evaluation(halueval_samples=samples, use_synthetic=False)
        error_analysis = analyze_errors(results)
        results["error_analysis"] = error_analysis
        results["dataset_info"] = {
            "source": "HaluEval",
            "task": task,
            "samples_tested": len(samples),
        }
        
        return results
    except Exception as e:
        log.exception(f"HaluEval test failed for {task}")
        raise HTTPException(status_code=500, detail=str(e))
