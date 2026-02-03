import sys
import os
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.tasks import process_document
from app.config import settings

if __name__ == "__main__":
    from rq import Worker, Queue, Connection
    from redis import Redis
    
    try:
        logger.info(f"Connecting to Redis at {settings.redis_url}")
        redis_conn = Redis.from_url(settings.redis_url)
        
        # Test connection
        redis_conn.ping()
        logger.info("Redis connection successful")
        
        with Connection(redis_conn):
            queue = Queue("default", connection=redis_conn)
            logger.info("Starting RQ worker for queue 'default'")
            worker = Worker(queue)
            worker.work()
    except Exception as e:
        logger.error(f"Worker failed to start: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

