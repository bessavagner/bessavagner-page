import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s (%(lineno)d) - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logging.getLogger('watchfiles.main').setLevel(logging.INFO)
logging.getLogger('aiohttp.access').setLevel(logging.WARNING)
