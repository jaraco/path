import sys


if sys.version_info < (3, 9):
	def removesuffix(self, suffix):
	    # suffix='' should not call self[:-0].
	    if suffix and self.endswith(suffix):
	        return self[:-len(suffix)]
	    else:
	        return self[:]
else:
    def removesuffix(self, suffix):
        return self.removesuffix(suffix)
