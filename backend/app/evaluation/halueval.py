"""
HaluEval Dataset Loader
=======================
Loads and processes HaluEval benchmark dataset for hallucination detection.
Format: https://github.com/RUCAIBox/HaluEval
"""
from __future__ import annotations

import json
import logging
import urllib.request
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

log = logging.getLogger(__name__)

# HaluEval dataset URLs
HALUEVAL_DATA_URLS = {
    "qa": "https://raw.githubusercontent.com/RUCAIBox/HaluEval/main/data/qa_data.json",
    "dialogue": "https://raw.githubusercontent.com/RUCAIBox/HaluEval/main/data/dialogue_data.json",
    "summarization": "https://raw.githubusercontent.com/RUCAIBox/HaluEval/main/data/summarization_data.json",
    "general": "https://raw.githubusercontent.com/RUCAIBox/HaluEval/main/data/general_data.json",
}


@dataclass
class HaluEvalSample:
    """Single sample from HaluEval dataset."""
    id: str
    knowledge: str          # Source/reference text
    response: str           # LLM-generated response to verify
    label: str             # hallucination | faithful
    task: str              # qa | dialogue | summarization
    
    def to_verification_label(self) -> str:
        """Convert HaluEval label to our system's labels."""
        if self.label == "hallucination":
            return "CONTRADICTED"
        elif self.label == "faithful":
            return "SUPPORTED"
        else:
            return "UNVERIFIABLE"


def download_halueval_dataset(task: str, data_dir: Path) -> Path:
    """
    Download HaluEval dataset from GitHub if not already cached.
    
    Args:
        task: Task type (qa, dialogue, summarization, general)
        data_dir: Directory to store downloaded data
        
    Returns:
        Path to downloaded file
    """
    data_dir.mkdir(parents=True, exist_ok=True)
    filepath = data_dir / f"{task}_data.json"
    
    if filepath.exists():
        log.info(f"Using cached dataset: {filepath}")
        return filepath
    
    if task not in HALUEVAL_DATA_URLS:
        raise ValueError(f"Unknown task: {task}. Valid: {list(HALUEVAL_DATA_URLS.keys())}")
    
    url = HALUEVAL_DATA_URLS[task]
    log.info(f"Downloading HaluEval {task} dataset from {url}...")
    
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = response.read()
        
        with open(filepath, 'wb') as f:
            f.write(data)
        
        log.info(f"Downloaded {len(data)} bytes to {filepath}")
        return filepath
    
    except Exception as e:
        log.error(f"Failed to download dataset: {e}")
        raise


def load_halueval_dataset(
    task: str = "qa",
    data_dir: Optional[Path] = None,
    max_samples: Optional[int] = None,
    auto_download: bool = True
) -> List[HaluEvalSample]:
    """
    Load HaluEval dataset from JSON file.
    
    Args:
        task: Task type (qa, dialogue, summarization, general)
        data_dir: Directory containing data files (default: backend/data/halueval)
        max_samples: Maximum number of samples to load
        auto_download: Download from GitHub if not found locally
        
    Returns:
        List of HaluEvalSample objects
    """
    if data_dir is None:
        from app.config import get_settings
        settings = get_settings()
        data_dir = settings.DATA_DIR / "halueval"
    
    # Download if needed
    if auto_download:
        filepath = download_halueval_dataset(task, data_dir)
    else:
        filepath = data_dir / f"{task}_data.json"
        if not filepath.exists():
            raise FileNotFoundError(f"Dataset not found: {filepath}")
    
    # Load JSONL data (one JSON object per line)
    data_list = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data_list.append(json.loads(line))
    
    log.info(f"Loaded {len(data_list)} records from {filepath}")
    
    samples = []
    for idx, data in enumerate(data_list):
        if max_samples and idx >= max_samples:
            break
        
        try:
            # Parse based on task type
            if task == "qa":
                knowledge = data.get("knowledge", "")
                question = data.get("question", "")
                # Test both hallucinated and correct answers
                hallucinated = HaluEvalSample(
                    id=f"qa_{idx}_hal",
                    knowledge=knowledge,
                    response=data.get("hallucinated_answer", ""),
                    label="hallucination",
                    task="qa",
                )
                faithful = HaluEvalSample(
                    id=f"qa_{idx}_faithful",
                    knowledge=knowledge,
                    response=data.get("right_answer", ""),
                    label="faithful",
                    task="qa",
                )
                samples.extend([hallucinated, faithful])
                
            elif task == "dialogue":
                knowledge = data.get("knowledge", "")
                hallucinated = HaluEvalSample(
                    id=f"dialogue_{idx}_hal",
                    knowledge=knowledge,
                    response=data.get("hallucinated_response", ""),
                    label="hallucination",
                    task="dialogue",
                )
                faithful = HaluEvalSample(
                    id=f"dialogue_{idx}_faithful",
                    knowledge=knowledge,
                    response=data.get("right_response", ""),
                    label="faithful",
                    task="dialogue",
                )
                samples.extend([hallucinated, faithful])
                
            elif task == "summarization":
                document = data.get("document", "")
                hallucinated = HaluEvalSample(
                    id=f"summarization_{idx}_hal",
                    knowledge=document,
                    response=data.get("hallucinated_summary", ""),
                    label="hallucination",
                    task="summarization",
                )
                faithful = HaluEvalSample(
                    id=f"summarization_{idx}_faithful",
                    knowledge=document,
                    response=data.get("right_summary", ""),
                    label="faithful",
                    task="summarization",
                )
                samples.extend([hallucinated, faithful])
                
            elif task == "general":
                sample = HaluEvalSample(
                    id=f"general_{idx}",
                    knowledge="",  # No reference for general queries
                    response=data.get("chatgpt_response", ""),
                    label="hallucination" if data.get("hallucination_label") == "Yes" else "faithful",
                    task="general",
                )
                samples.append(sample)
                
        except Exception as e:
            log.warning(f"Failed to parse sample {idx}: {e}")
            continue
    
    log.info(f"Loaded {len(samples)} samples from {filepath}")
    return samples


def load_synthetic_dataset() -> List[HaluEvalSample]:
    """
    Create a small synthetic dataset for testing when real data unavailable.
    
    Returns:
        List of synthetic samples
    """
    return [
        HaluEvalSample(
            id="syn_001",
            knowledge="The company reported revenue of $100 million in Q4 2023.",
            response="The company's Q4 2023 revenue was $100 million.",
            label="faithful",
            task="qa",
        ),
        HaluEvalSample(
            id="syn_002",
            knowledge="The company reported revenue of $100 million in Q4 2023.",
            response="The company's Q4 2023 revenue exceeded $150 million.",
            label="hallucination",
            task="qa",
        ),
        HaluEvalSample(
            id="syn_003",
            knowledge="The patient has Type 1 diabetes and takes insulin daily.",
            response="The patient does not have diabetes.",
            label="hallucination",
            task="summarization",
        ),
        HaluEvalSample(
            id="syn_004",
            knowledge="The treatment plan includes physical therapy twice a week.",
            response="The treatment includes physical therapy sessions twice weekly.",
            label="faithful",
            task="summarization",
        ),
        HaluEvalSample(
            id="syn_005",
            knowledge="The law was enacted in 1995 and revised in 2010.",
            response="The law was originally enacted in 2010.",
            label="hallucination",
            task="qa",
        ),
        HaluEvalSample(
            id="syn_006",
            knowledge="The experiment used a double-blind methodology with 200 participants.",
            response="The study employed a double-blind approach with 200 subjects.",
            label="faithful",
            task="summarization",
        ),
        HaluEvalSample(
            id="syn_007",
            knowledge="The medication should be taken with food, not on an empty stomach.",
            response="This medication can be taken on an empty stomach.",
            label="hallucination",
            task="qa",
        ),
        HaluEvalSample(
            id="syn_008",
            knowledge="The building height is 250 meters with 60 floors.",
            response="The building stands at 250 meters tall.",
            label="faithful",
            task="qa",
        ),
    ]


def prepare_for_ingestion(samples: List[HaluEvalSample]) -> tuple[List[str], List[str]]:
    """
    Prepare samples for our verification system.
    
    Args:
        samples: List of HaluEvalSample objects
        
    Returns:
        Tuple of (knowledge_texts, responses) for batch processing
    """
    knowledge_texts = [s.knowledge for s in samples]
    responses = [s.response for s in samples]
    return knowledge_texts, responses
