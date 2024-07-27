import sys


def pytest_configure(config):
    disable_broken_doctests(config)


def disable_broken_doctests(config):
    """
    Workaround for python/cpython#117692.
    """
    if (3, 11, 9) <= sys.version_info < (3, 12):
        config.option.doctestmodules = False
