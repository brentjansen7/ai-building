"""
RQ Worker — start met: python -m app.queue.worker
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from redis import Redis
from rq import Worker, Queue
from rq_scheduler import Scheduler
import structlog
from datetime import datetime, timedelta

from app.config import settings

logger = structlog.get_logger()


def get_redis():
    return Redis.from_url(settings.redis_url)


def start_worker():
    """Start RQ worker."""
    redis_conn = get_redis()
    queues = [
        Queue("high", connection=redis_conn),
        Queue("default", connection=redis_conn),
        Queue("low", connection=redis_conn),
    ]

    logger.info("Worker gestart", queues=["high", "default", "low"])
    worker = Worker(queues, connection=redis_conn)
    worker.work(with_scheduler=True)


def setup_scheduled_jobs():
    """Stel periodieke jobs in via rq-scheduler."""
    redis_conn = get_redis()
    scheduler = Scheduler(connection=redis_conn)

    # Verwijder oude jobs
    for job in scheduler.get_jobs():
        scheduler.cancel(job)

    logger.info("Scheduled jobs instellen")

    # Pararius: dagelijks om 6:00
    scheduler.cron(
        "0 6 * * *",
        func="app.queue.jobs.scrape_pararius",
        kwargs={"max_pages": 15},
        queue_name="default",
        id="daily_pararius",
        repeat=None,
    )

    # Jaap: dagelijks om 8:00
    scheduler.cron(
        "0 8 * * *",
        func="app.queue.jobs.scrape_jaap",
        kwargs={"max_pages": 15},
        queue_name="default",
        id="daily_jaap",
        repeat=None,
    )

    # Huislijn: dagelijks om 10:00
    scheduler.cron(
        "0 10 * * *",
        func="app.queue.jobs.scrape_huislijn",
        kwargs={"max_pages": 15},
        queue_name="default",
        id="daily_huislijn",
        repeat=None,
    )

    # Analyseer pending listings: elk uur
    scheduler.cron(
        "15 * * * *",
        func="app.queue.jobs.analyze_pending_listings",
        kwargs={"limit": 100},
        queue_name="default",
        id="hourly_analyze",
        repeat=None,
    )

    # Alerts: elk uur
    scheduler.cron(
        "45 * * * *",
        func="app.queue.jobs.check_and_send_alerts",
        queue_name="high",
        id="hourly_alerts",
        repeat=None,
    )

    logger.info("5 scheduled jobs ingesteld")


def enqueue_job(func_name: str, queue_name: str = "default", **kwargs):
    """Voeg een job toe aan de queue."""
    redis_conn = get_redis()
    q = Queue(queue_name, connection=redis_conn)

    import importlib
    module_path, func_name_only = func_name.rsplit(".", 1)
    module = importlib.import_module(module_path)
    func = getattr(module, func_name_only)

    job = q.enqueue(func, **kwargs)
    logger.info("Job toegevoegd aan queue", job_id=job.id, func=func_name)
    return job.id


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "schedule":
        setup_scheduled_jobs()
    else:
        start_worker()
