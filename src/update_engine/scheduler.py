import logging
from apscheduler.schedulers.background import BackgroundScheduler
from .updater import KnowledgeBaseUpdater

logger = logging.getLogger(__name__)

class UpdateScheduler:
    def __init__(self, updater: KnowledgeBaseUpdater, interval_minutes: int):
        self.updater = updater
        self.interval_minutes = interval_minutes
        self.scheduler = BackgroundScheduler()
        
    def start(self):
        """Start the background scheduler."""
        logger.info(f"Starting scheduler. Update interval: {self.interval_minutes} minutes.")
        self.scheduler.add_job(
            self.updater.run_update,
            'interval',
            minutes=self.interval_minutes,
            id='kb_update_job',
            replace_existing=True
        )
        self.scheduler.start()
        
    def stop(self):
        """Stop the background scheduler."""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped.")
