"""
Shared logger
"""
import logging
import sys

import config

log_levels = {'DEBUG': logging.DEBUG,
              'INFO': logging.INFO,
              'WARNING': logging.WARNING,
              'ERROR': logging.ERROR,
              'CRITICAL': logging.CRITICAL}

logger = logging.getLogger('gage')
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(log_levels.get(config.STDOUT_LOG_LEVEL, logging.WARNING))
ch.setFormatter(formatter)
logger.addHandler(ch)

if config.SENTRY_DSN:
    logger.info('setting up Sentry logging')
    from raven import Client as Raven_Client
    from raven.handlers.logging import SentryHandler

    raven_client = Raven_Client(config.SENTRY_DSN,
                                name=config.RESIN_DEVICE_NAME,
                                environment=config.RESIN_APP_NAME,
                                auto_log_stacks=True,
                                tags={
                                    'python version': config.RESIN_PYTHON_VERSION,
                                    'supervisor version': config.RESIN_SUPERVISOR_VERSION,
                                    'resin app release': config.RESIN_APP_RELEASE
                                })
    raven_handler = SentryHandler(raven_client)
    raven_handler.setLevel(log_levels.get(config.SENTRY_LOG_LEVEL, logging.WARNING))

    logger.addHandler(raven_handler)
