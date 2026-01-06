"""
AI Auto-Applier Agent (Groq Edition) - Phase 1 Entry Point
Job Discovery Module
"""

import logging
from scrapers.hunter import JobHunter

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


def main():
    """
    Phase 1: Job Discovery
    Run job aggregation cycle for "Generative AI Engineer" in "India"
    """
    try:
        # Initialize JobHunter
        hunter = JobHunter(data_dir="data")
        
        # Run discovery cycle
        search_term = "Generative AI Engineer"
        location = "India"
        results_per_site = 50
        
        logger.info("Starting AI Auto-Applier Agent - Phase 1")
        logger.info(f"Target: {search_term} | Location: {location}")
        
        # Execute hunt and save cycle
        new_jobs_count = hunter.run_cycle(
            search_term=search_term,
            location=location,
            results_wanted=results_per_site
        )
        
        logger.info(f"Phase 1 Complete: Discovered {new_jobs_count} new ATS-compliant jobs")
        logger.info(f"Results saved to: data/jobs.csv")
        
    except Exception as e:
        logger.error(f"Critical error in main: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
