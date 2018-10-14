from __future__ import absolute_import

import zipfile
import operator

import path


class ZipAware:
    """
    Mix-in for Path to add awareness and traversal support for
    zip files in the path.
    """
    container = None

    @property
    def _next_class(self):
        if not self.archive:
            return super(ZipAware, self)._next_class

        def constructor(*args, **kwargs):
            ob = self.__class__(*args, **kwargs)
            ob.container = self
            return ob
        return constructor

    @property
    def archive(self):
        if self.container:
            return self.container.archive
        try:
            return self._archive
        except AttributeError:
            try:
                self._archive = zipfile.ZipFile(self)
            except Exception:
                self._archive = None
        return self._archive

    def listdir(self):
        if not self.archive:
            return super(ZipAware, self).listdir()

        paths = map(operator.attrgetter('filename'), self.archive.infolist())

        def is_child(path):
            pre, _, rest = path.partition(self)
            return not pre and '/' not in rest.rstrip('/')
        return [
            self._next_class(path)
            for path in paths
            if is_child(path)
        ]


class ZipPath(ZipAware, path.Path):
    pass
