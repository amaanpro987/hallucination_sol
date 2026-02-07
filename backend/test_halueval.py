"""
Test script for HaluEval integration
=====================================
Download and test with real HaluEval dataset.
"""
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


async def test_halueval_download():
    """Test downloading HaluEval dataset."""
    from app.evaluation.halueval import download_halueval_dataset
    from pathlib import Path
    
    data_dir = Path("data/halueval")
    
    for task in ["qa", "dialogue", "summarization"]:
        log.info(f"\n{'='*60}")
        log.info(f"Testing {task} task")
        log.info(f"{'='*60}")
        
        try:
            filepath = download_halueval_dataset(task, data_dir)
            file_size = filepath.stat().st_size / 1024 / 1024  # MB
            log.info(f"✅ Downloaded {task}: {filepath} ({file_size:.2f} MB)")
        except Exception as e:
            log.error(f"❌ Failed to download {task}: {e}")


async def test_halueval_loading():
    """Test loading and parsing HaluEval dataset."""
    from app.evaluation.halueval import load_halueval_dataset
    
    for task in ["qa", "dialogue", "summarization"]:
        log.info(f"\n{'='*60}")
        log.info(f"Testing {task} dataset loading")
        log.info(f"{'='*60}")
        
        try:
            samples = load_halueval_dataset(task=task, max_samples=5, auto_download=True)
            log.info(f"✅ Loaded {len(samples)} samples from {task}")
            
            # Show first sample
            if samples:
                sample = samples[0]
                log.info(f"\nSample ID: {sample.id}")
                log.info(f"Task: {sample.task}")
                log.info(f"Label: {sample.label}")
                log.info(f"Knowledge (first 200 chars): {sample.knowledge[:200]}...")
                log.info(f"Response (first 200 chars): {sample.response[:200]}...")
        except Exception as e:
            log.error(f"❌ Failed to load {task}: {e}")


async def test_quick_evaluation():
    """Run quick evaluation with HaluEval data."""
    from app.evaluation.halueval import load_halueval_dataset
    from app.evaluation.evaluator import run_evaluation
    
    log.info(f"\n{'='*60}")
    log.info("Running quick evaluation with QA task (5 samples)")
    log.info(f"{'='*60}")
    
    try:
        # Load small sample
        samples = load_halueval_dataset(task="qa", max_samples=5, auto_download=True)
        log.info(f"Loaded {len(samples)} samples")
        
        # Run evaluation
        results = await run_evaluation(halueval_samples=samples, use_synthetic=False)
        
        log.info("\n📊 Evaluation Results:")
        if 'f1' in results:
            log.info(f"F1 Score: {results['f1']:.2%}")
            log.info(f"Precision: {results['precision']:.2%}")
            log.info(f"Recall: {results['recall']:.2%}")
            log.info(f"Accuracy: {results['accuracy']:.2%}")
        else:
            log.info(f"Results keys: {list(results.keys())}")
            log.info(f"Full results: {results}")
        
        log.info(f"\n✅ Evaluation completed successfully!")
        
    except Exception as e:
        log.error(f"❌ Evaluation failed: {e}", exc_info=True)


async def main():
    """Run all tests."""
    log.info("="*60)
    log.info("HaluEval Integration Test Suite")
    log.info("="*60)
    
    # Test 1: Download
    log.info("\n🔽 TEST 1: Download datasets")
    await test_halueval_download()
    
    # Test 2: Loading
    log.info("\n📖 TEST 2: Load and parse datasets")
    await test_halueval_loading()
    
    # Test 3: Evaluation
    log.info("\n🎯 TEST 3: Run evaluation")
    await test_quick_evaluation()
    
    log.info("\n" + "="*60)
    log.info("All tests completed!")
    log.info("="*60)


if __name__ == "__main__":
    asyncio.run(main())
