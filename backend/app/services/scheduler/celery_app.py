"""
Celery application for background tasks and scheduling
"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "trading_system",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(['app.services.scheduler'])

# Periodic tasks schedule
celery_app.conf.beat_schedule = {
    # Every 5 minutes - Quick analysis (M5, M15)
    'quick-analysis-5min': {
        'task': 'app.services.scheduler.tasks.run_quick_analysis',
        'schedule': crontab(minute='*/5'),
    },
    # Every 15 minutes - Medium timeframes (M15, H1)
    'medium-analysis-15min': {
        'task': 'app.services.scheduler.tasks.run_medium_analysis',
        'schedule': crontab(minute='*/15'),
    },
    # Every hour - Higher timeframes (H4, D1)
    'high-analysis-hourly': {
        'task': 'app.services.scheduler.tasks.run_high_timeframe_analysis',
        'schedule': crontab(minute=0),
    },
    # Every 4 hours - News sentiment update
    'news-sentiment-4h': {
        'task': 'app.services.scheduler.tasks.update_news_sentiment',
        'schedule': crontab(minute=0, hour='*/4'),
    },
    # Daily at midnight - Cleanup old data
    'cleanup-daily': {
        'task': 'app.services.scheduler.tasks.cleanup_old_data',
        'schedule': crontab(minute=0, hour=0),
    },
    # Daily at 8 AM - Market summary
    'daily-market-summary': {
        'task': 'app.services.scheduler.tasks.send_daily_summary',
        'schedule': crontab(minute=0, hour=8),
    },
}
