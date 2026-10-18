``Path.with_name`` now rejects empty names, ``'.'``, and names containing
directory or drive components, matching pathlib's replacement-name validation.
``Path.with_stem`` also rejects stems containing path components.
