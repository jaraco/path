Reject directory separators in ``Path.with_suffix`` so replacing an extension cannot change the parent directory. Use the path's configured module to distinguish Windows and POSIX separators.
