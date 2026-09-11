"""ARQ worker settings"""

from arq.connections import RedisSettings

# Redis connection for background jobs
redis_settings = RedisSettings(
    host='localhost',
    port=6379,
    database=0
)

# Background functions to run
functions = [
    'pipeline.tasks.scrape_marktplaats',
    'pipeline.tasks.scrape_vinted',
    'pipeline.tasks.estimate_price',
]

# Worker settings
max_jobs = 10
job_timeout = 3600  # 1 hour
