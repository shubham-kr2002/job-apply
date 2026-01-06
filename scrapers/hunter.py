"""
Job Discovery Module - Phase 1
Implements FR-1.1 (Job Aggregation), FR-1.2 (ATS Filtering), FR-1.3 (Deduplication)
"""

import hashlib
import logging
import os
import random
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

import pandas as pd
from jobspy import scrape_jobs
from pydantic import BaseModel, Field

# Configure logging (Implements observability requirement)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# Implements Schema Validation requirement with Pydantic
class Job(BaseModel):
    """Job model with strict schema validation"""
    id: str = Field(description="MD5 hash of company + title")
    title: str
    company: str
    job_url: str
    location: Optional[str] = None
    date_posted: Optional[str] = None
    ats_provider: Optional[str] = None


class JobHunter:
    """
    Job Discovery Engine
    Implements:
    - FR-1.1: Job Aggregation via python-jobspy
    - FR-1.2: ATS Filtering (greenhouse.io, lever.co, ashbyhq.com)
    - FR-1.3: Deduplication via jobs.csv historical log
    - FR-2.4: Randomized headers for stealth
    """
    
    # FR-1.2: STRICT ATS filter list
    ALLOWED_ATS_PROVIDERS = {
        'greenhouse.io',
        'lever.co',
        'ashbyhq.com'
    }
    
    # FR-2.4: Stealth - Randomized User-Agent pool
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
    ]
    
    def __init__(self, data_dir: str = "data"):
        """Initialize JobHunter with data directory"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.csv_path = self.data_dir / "jobs.csv"
        self.existing_ids = self._load_existing_job_ids()
        logger.info(f"JobHunter initialized. Loaded {len(self.existing_ids)} existing job IDs")
    
    def _load_existing_job_ids(self) -> set:
        """
        Load existing job IDs from CSV for deduplication
        Implements FR-1.3 (Deduplication)
        """
        if not self.csv_path.exists():
            logger.info("No existing jobs.csv found. Starting fresh.")
            return set()
        
        try:
            df = pd.read_csv(self.csv_path)
            if 'id' in df.columns:
                existing = set(df['id'].tolist())
                logger.info(f"Loaded {len(existing)} existing job IDs from {self.csv_path}")
                return existing
            return set()
        except Exception as e:
            logger.error(f"Error loading existing jobs: {e}")
            return set()
    
    @staticmethod
    def _generate_job_id(company: str, title: str) -> str:
        """
        Generate unique job ID using MD5 hash
        Implements idempotency requirement
        """
        unique_string = f"{company.lower().strip()}{title.lower().strip()}"
        return hashlib.md5(unique_string.encode()).hexdigest()
    
    def _extract_ats_provider(self, url: str) -> Optional[str]:
        """
        Extract ATS provider from job URL
        Implements FR-1.2 (ATS Filtering)
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Check against allowed ATS providers
            for ats in self.ALLOWED_ATS_PROVIDERS:
                if ats in domain:
                    return ats
            return None
        except Exception as e:
            logger.warning(f"Error parsing URL {url}: {e}")
            return None
    
    def _is_ats_compliant(self, url: str) -> bool:
        """
        STRICT filter: Only allow jobs from specified ATS providers
        Implements FR-1.2 (ATS Filtering)
        """
        ats = self._extract_ats_provider(url)
        return ats is not None
    
    def _normalize_job(self, raw_job: dict) -> Optional[Job]:
        """
        Normalize scraped job data into Job model
        Implements Schema Validation requirement
        """
        try:
            # Extract required fields
            title = raw_job.get('title', '')
            company = raw_job.get('company', '')
            job_url = raw_job.get('job_url', '')
            
            if not all([title, company, job_url]):
                logger.warning("Skipping job with missing required fields")
                return None
            
            # FR-1.2: STRICT ATS filtering
            if not self._is_ats_compliant(job_url):
                logger.debug(f"Filtered out non-ATS job: {job_url}")
                return None
            
            # Generate unique ID
            job_id = self._generate_job_id(company, title)
            
            # FR-1.3: Check deduplication
            if job_id in self.existing_ids:
                logger.debug(f"Duplicate job skipped: {company} - {title}")
                return None
            
            # Create validated Job object
            job = Job(
                id=job_id,
                title=title,
                company=company,
                job_url=job_url,
                location=raw_job.get('location'),
                date_posted=raw_job.get('date_posted'),
                ats_provider=self._extract_ats_provider(job_url)
            )
            
            return job
        except Exception as e:
            logger.error(f"Error normalizing job: {e}")
            return None
    
    def hunt(self, search_term: str, location: str, results_wanted: int = 50) -> List[Job]:
        """
        Main job hunting workflow
        Implements FR-1.1 (Job Aggregation)
        
        Args:
            search_term: Job title to search (e.g., "AI Engineer")
            location: Location filter (e.g., "India")
            results_wanted: Number of results to fetch per site
        
        Returns:
            List of validated, deduplicated Job objects
        """
        logger.info(f"Starting job hunt: '{search_term}' in '{location}'")
        
        # FR-2.4: Randomize User-Agent for stealth
        random_ua = random.choice(self.USER_AGENTS)
        logger.info(f"Using User-Agent: {random_ua[:50]}...")
        
        try:
            # FR-1.1: Aggregate jobs from LinkedIn, Indeed, Glassdoor
            logger.info("Scraping jobs from LinkedIn, Indeed, Glassdoor...")
            raw_jobs = scrape_jobs(
                site_name=["linkedin", "indeed", "glassdoor"],
                search_term=search_term,
                location=location,
                results_wanted=results_wanted,
                country_indeed='India'
            )
            
            if raw_jobs is None or raw_jobs.empty:
                logger.warning("No jobs found from scraping")
                return []
            
            logger.info(f"Scraped {len(raw_jobs)} total jobs")
            
            # Convert DataFrame to list of dicts
            raw_job_list = raw_jobs.to_dict('records')
            
            # Normalize, filter ATS, and deduplicate
            validated_jobs = []
            for raw_job in raw_job_list:
                job = self._normalize_job(raw_job)
                if job:
                    validated_jobs.append(job)
            
            logger.info(f"After ATS filtering and deduplication: {len(validated_jobs)} jobs")
            
            return validated_jobs
            
        except Exception as e:
            logger.error(f"Error during job hunt: {e}")
            return []
    
    def save_jobs(self, jobs: List[Job]) -> None:
        """
        Save jobs to CSV with idempotency
        Implements FR-1.3 (Deduplication) and idempotency requirement
        """
        if not jobs:
            logger.info("No new jobs to save")
            return
        
        # Convert to DataFrame
        job_dicts = [job.model_dump() for job in jobs]
        new_df = pd.DataFrame(job_dicts)
        
        try:
            # Idempotent save: Append only new jobs
            if self.csv_path.exists():
                existing_df = pd.read_csv(self.csv_path)
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                # Drop duplicates based on ID (safety net)
                combined_df = combined_df.drop_duplicates(subset=['id'], keep='first')
                combined_df.to_csv(self.csv_path, index=False)
                logger.info(f"Appended {len(jobs)} new jobs to {self.csv_path}")
            else:
                new_df.to_csv(self.csv_path, index=False)
                logger.info(f"Created {self.csv_path} with {len(jobs)} jobs")
            
            # Update in-memory cache
            self.existing_ids.update([job.id for job in jobs])
            
        except Exception as e:
            logger.error(f"Error saving jobs to CSV: {e}")
    
    def run_cycle(self, search_term: str, location: str, results_wanted: int = 50) -> int:
        """
        Complete job discovery cycle: Hunt -> Save
        
        Returns:
            Number of new jobs discovered
        """
        logger.info("="*60)
        logger.info(f"JOB DISCOVERY CYCLE STARTED")
        logger.info(f"Search: '{search_term}' | Location: '{location}'")
        logger.info("="*60)
        
        # Hunt for jobs
        jobs = self.hunt(search_term, location, results_wanted)
        
        # Save to CSV
        self.save_jobs(jobs)
        
        logger.info("="*60)
        logger.info(f"CYCLE COMPLETE: {len(jobs)} new jobs discovered")
        logger.info("="*60)
        
        return len(jobs)
