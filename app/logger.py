import logging


def setup_logger():
    _logger = logging.getLogger('ecr-deployman')
    _logger.setLevel(logging.DEBUG)
    _handler = logging.StreamHandler()
    _handler.setFormatter(
        logging.Formatter(
            '%(asctime)s %(thread)d %(name)s %(levelname)s %(message)s'
        )
    )
    _logger.addHandler(_handler)
    return _logger


logger = setup_logger()
