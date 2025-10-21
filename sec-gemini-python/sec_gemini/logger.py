import logging

_LOGGER = None


def get_logger():
  global _LOGGER
  if _LOGGER is None:
    _LOGGER = logging.getLogger("secgemini")
    _LOGGER.setLevel(level=logging.WARNING)
  return _LOGGER
