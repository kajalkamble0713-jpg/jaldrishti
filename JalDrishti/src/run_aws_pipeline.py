"""
JalDrishti AWS Pipeline Runner
Simple wrapper to run the AWS Earth Search pipeline with logging
"""

import sys
import logging
from datetime import datetime
from aws_pipeline import run_aws_pipeline

# Setup logging
log_filename = f"logs/aws_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

import os
os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("Starting JalDrishti AWS Earth Search Pipeline")
    logger.info("=" * 70)
    
    try:
        run_aws_pipeline()
        logger.info("\n✅ Pipeline completed successfully")
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Pipeline interrupted by user")
        logger.info("Progress has been saved. Re-run to resume.")
    except Exception as e:
        logger.error(f"\n❌ Pipeline failed with error: {e}", exc_info=True)
        sys.exit(1)
    
    logger.info(f"\nLog saved to: {log_filename}")
