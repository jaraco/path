"""
Tests for the path module.

This suite runs on Linux, macOS, and Windows. To extend the
platform support, just add appropriate pathnames for your
platform (os.name) in each place where the p() function is called.
Then report the result. If you can't get the test to run at all on
your platform, there's probably a bug -- please report the issue
in the issue tracker.

TestScratchDir.test_touch() takes a while to run. It sleeps a few
seconds to allow some time to pass between calls to check the modify
time on files.
"""

import io
import os
import sys
import shutil
import time
import types
import ntpath
import posixpath
import textwrap
import platform
import importlib
import datetime
import subprocess
import re
import contextlib

import pytest

import path
from path import Path
from path import TempDir
from path import matchers
from path import SpecialResolver
from path import Multi


def os_choose(**choices):
    """Choose a value from several possible values, based on os.name"""
    return choices[os.name]


class TestBasics:
    def test_relpath(self):
        root = Path(os_choose(nt='C:\\', posix='/'))
        foo = root / 'foo'
        quux = foo / 'quux'
        bar = foo / 'bar'
        boz = bar / 'Baz' / 'Boz'
        up = Path(os.pardir)

        # basics
        assert root.relpathto(boz) == Path('foo') / 'bar' / 'Baz' / 'Boz'
        assert bar.relpathto(boz) == Path('Baz') / 'Boz'
        assert quux.relpathto(boz) == up / 'bar' / 'Baz' / 'Boz'
        assert boz.relpathto(quux) == up / up / up / 'quux'
        assert boz.relpathto(bar) == up / up

        # Path is not the first element in concatenation
        assert root.relpathto(boz) == 'foo' / Path('bar') / 'Baz' / 'Boz'

        # x.relpathto(x) == curdir
        assert root.relpathto(root) == os.curdir
        assert boz.relpathto(boz) == os.curdir
        # Make sure case is properly noted (or ignored)
        assert boz.relpathto(boz.normcase()) == os.curdir

        # relpath()
        cwd = Path(os.getcwd())
        assert boz.relpath() == cwd.relpathto(boz)

        if os.name == 'nt':
            # Check relpath across drives.
            d = Path('D:\\')
            assert d.relpathto(boz) == boz

    def test_construction_from_none(self):
        """ """
        with pytest.raises(TypeError):
            Path(None)

    def test_construction_from_int(self):
        """
        Path class will construct a path as a string of the number
        """
        assert Path(1) == '1'

    def test_string_compatibility(self):
        """Test compatibility with ordinary strings."""
        x = Path('xyzzy')
        assert x == 'xyzzy'
        assert x == str('xyzzy')

        # sorting
        items = [Path('fhj'), Path('fgh'), 'E', Path('d'), 'A', Path('B'), 'c']
        items.sort()
        assert items == ['A', 'B', 'E', 'c', 'd', 'fgh', 'fhj']

        # Test p1/p1.
        p1 = Path("foo")
        p2 = Path("bar")
        assert p1 / p2 == os_choose(nt='foo\\bar', posix='foo/bar')

    def test_properties(self):
        # Create sample path object.
        f = Path(
            os_choose(
                nt='C:\\Program Files\\Python\\Lib\\xyzzy.py',
                posix='/usr/local/python/lib/xyzzy.py',
            )
        )

        # .parent
        nt_lib = 'C:\\Program Files\\Python\\Lib'
        posix_lib = '/usr/local/python/lib'
        expected = os_choose(nt=nt_lib, posix=posix_lib)
        assert f.parent == expected

        # .name
        assert f.name == 'xyzzy.py'
        assert f.parent.name == os_choose(nt='Lib', posix='lib')

        # .ext
        assert f.ext == '.py'
        assert f.parent.ext == ''

        # .drive
        assert f.drive == os_choose(nt='C:', posix='')

    def test_methods(self):
        # .abspath()
        assert Path(os.curdir).abspath() == os.getcwd()

        # .getcwd()
        cwd = Path.getcwd()
        assert isinstance(cwd, Path)
        assert cwd == os.getcwd()

    @pytest.mark.skipif('not hasattr(os.path, "splitunc")')
    def test_UNC(self):
        p = Path(r'\\python1\share1\dir1\file1.txt')
        assert p.uncshare == r'\\python1\share1'
        assert p.splitunc() == os.path.splitunc(str(p))

    def test_explicit_module(self):
        """
        The user may specify an explicit path module to use.
        """
        nt_ok = Path.using_module(ntpath)(r'foo\bar\baz')
        posix_ok = Path.using_module(posixpath)(r'foo/bar/baz')
        posix_wrong = Path.using_module(posixpath)(r'foo\bar\baz')

        assert nt_ok.dirname() == r'foo\bar'
        assert posix_ok.dirname() == r'foo/bar'
        assert posix_wrong.dirname() == ''

        assert nt_ok / 'quux' == r'foo\bar\baz\quux'
        assert posix_ok / 'quux' == r'foo/bar/baz/quux'

    def test_explicit_module_classes(self):
        """
        Multiple calls to path.using_module should produce the same class.
        """
        nt_path = Path.using_module(ntpath)
        assert nt_path is Path.using_module(ntpath)
        assert nt_path.__name__ == 'Path_ntpath'

    def test_joinpath_on_instance(self):
        res = Path('foo')
        foo_bar = res.joinpath('bar')
        assert foo_bar == os_choose(nt='foo\\bar', posix='foo/bar')

    def test_joinpath_to_nothing(self):
        res = Path('foo')
        assert res.joinpath() == res

    def test_joinpath_on_class(self):
        "Construct a path from a series of strings"
        foo_bar = Path.joinpath('foo', 'bar')
        assert foo_bar == os_choose(nt='foo\\bar', posix='foo/bar')

    def test_joinpath_fails_on_empty(self):
        "It doesn't make sense to join nothing at all"
        with pytest.raises(TypeError):
            Path.joinpath()

    def test_joinpath_returns_same_type(self):
        path_posix = Path.using_module(posixpath)
        res = path_posix.joinpath('foo')
        assert isinstance(res, path_posix)
        res2 = res.joinpath('bar')
        assert isinstance(res2, path_posix)
        assert res2 == 'foo/bar'


class TestReadWriteText:
    def test_read_write(self, tmpdir):
        file = path.Path(tmpdir) / 'filename'
        file.write_text('hello world')
        assert file.read_text() == 'hello world'
        assert file.read_bytes() == b'hello world'


class TestPerformance:
    @staticmethod
    def get_command_time(cmd):
        args = [sys.executable, '-m', 'timeit', '-n', '1', '-r', '1', '-u', 'usec'] + [
            cmd
        ]
        res = subprocess.check_output(args, universal_newlines=True)
        dur = re.search(r'(\d+) usec per loop', res).group(1)
        return datetime.timedelta(microseconds=int(dur))

    def test_import_time(self, monkeypatch):
        """
        Import should take less than some limit.

        Run tests in a subprocess to isolate from test suite overhead.
        """
        limit = datetime.timedelta(milliseconds=20)
        baseline = self.get_command_time('pass')
        measure = self.get_command_time('import path')
        duration = measure - baseline
        assert duration < limit


class TestSymbolicLinksWalk:
    def test_skip_symlinks(self, tmpdir):
        root = Path(tmpdir)
        sub = root / 'subdir'
        sub.mkdir()
        sub.symlink(root / 'link')
        (sub / 'file').touch()
        assert len(list(root.walk())) == 4

        skip_links = path.Traversal(
            lambda item: item.isdir() and not item.islink(),
        )
        assert len(list(skip_links(root.walk()))) == 3


class TestSelfReturn:
    """
    Some methods don't necessarily return any value (e.g. makedirs,
    makedirs_p, rename, mkdir, touch, chroot). These methods should return
    self anyhow to allow methods to be chained.
    """

    def test_makedirs_p(self, tmpdir):
        """
        Path('foo').makedirs_p() == Path('foo')
        """
        p = Path(tmpdir) / "newpath"
        ret = p.makedirs_p()
        assert p == ret

    def test_makedirs_p_extant(self, tmpdir):
        p = Path(tmpdir)
        ret = p.makedirs_p()
        assert p == ret

    def test_rename(self, tmpdir):
        p = Path(tmpdir) / "somefile"
        p.touch()
        target = Path(tmpdir) / "otherfile"
        ret = p.rename(target)
        assert target == ret

    def test_mkdir(self, tmpdir):
        p = Path(tmpdir) / "newdir"
        ret = p.mkdir()
        assert p == ret

    def test_touch(self, tmpdir):
        p = Path(tmpdir) / "empty file"
        ret = p.touch()
        assert p == ret


class TestScratchDir:
    """
    Tests that run in a temporary directory (does not test TempDir class)
    """

    def test_context_manager(self, tmpdir):
        """Can be used as context manager for chdir."""
        d = Path(tmpdir)
        subdir = d / 'subdir'
        subdir.makedirs()
        old_dir = os.getcwd()
        with subdir:
            assert os.getcwd() == os.path.realpath(subdir)
        assert os.getcwd() == old_dir

    def test_touch(self, tmpdir):
        # NOTE: This test takes a long time to run (~10 seconds).
        # It sleeps several seconds because on Windows, the resolution
        # of a file's mtime and ctime is about 2 seconds.
        #
        # atime isn't tested because on Windows the resolution of atime
        # is something like 24 hours.

        threshold = 1

        d = Path(tmpdir)
        f = d / 'test.txt'
        t0 = time.time() - threshold
        f.touch()
        t1 = time.time() + threshold

        assert f.exists()
        assert f.isfile()
        assert f.size == 0
        assert t0 <= f.mtime <= t1
        if hasattr(os.path, 'getctime'):
            ct = f.ctime
            assert t0 <= ct <= t1

        time.sleep(threshold * 2)
        fobj = open(f, 'ab')
        fobj.write('some bytes'.encode('utf-8'))
        fobj.close()

        time.sleep(threshold * 2)
        t2 = time.time() - threshold
        f.touch()
        t3 = time.time() + threshold

        assert t0 <= t1 < t2 <= t3  # sanity check

        assert f.exists()
        assert f.isfile()
        assert f.size == 10
        assert t2 <= f.mtime <= t3
        if hasattr(os.path, 'getctime'):
            ct2 = f.ctime
            if os.name == 'nt':
                # On Windows, "ctime" is CREATION time
                assert ct == ct2
                assert ct2 < t2
            else:
                assert (
                    # ctime is unchanged
                    ct == ct2
                    or
                    # ctime is approximately the mtime
                    ct2 == pytest.approx(f.mtime, 0.001)
                )

    def test_listing(self, tmpdir):
        d = Path(tmpdir)
        assert d.listdir() == []

        f = 'testfile.txt'
        af = d / f
        assert af == os.path.join(d, f)
        af.touch()
        try:
            assert af.exists()

            assert d.listdir() == [af]

            # .glob()
            assert d.glob('testfile.txt') == [af]
            assert d.glob('test*.txt') == [af]
            assert d.glob('*.txt') == [af]
            assert d.glob('*txt') == [af]
            assert d.glob('*') == [af]
            assert d.glob('*.html') == []
            assert d.glob('testfile') == []

            # .iglob matches .glob but as an iterator.
            assert list(d.iglob('*')) == d.glob('*')
            assert isinstance(d.iglob('*'), types.GeneratorType)

        finally:
            af.remove()

        # Try a test with 20 files
        files = [d / ('%d.txt' % i) for i in range(20)]
        for f in files:
            fobj = open(f, 'w')
            fobj.write('some text\n')
            fobj.close()
        try:
            files2 = d.listdir()
            files.sort()
            files2.sort()
            assert files == files2
        finally:
            for f in files:
                with contextlib.suppress(Exception):
                    f.remove()

    @pytest.mark.skipif(
        platform.system() != "Linux",
        reason="Only Linux allows writing invalid encodings",
    )
    def test_listdir_other_encoding(self, tmpdir):
        """
        Some filesystems allow non-character sequences in path names.
        ``.listdir`` should still function in this case.
        See issue #61 for details.
        """
        assert Path(tmpdir).listdir() == []
        tmpdir_bytes = str(tmpdir).encode('ascii')

        filename = 'r\xe9\xf1emi'.encode('latin-1')
        pathname = os.path.join(tmpdir_bytes, filename)
        with open(pathname, 'wb'):
            pass
        # first demonstrate that os.listdir works
        assert os.listdir(tmpdir_bytes)

        # now try with path
        results = Path(tmpdir).listdir()
        assert len(results) == 1
        (res,) = results
        assert isinstance(res, Path)
        # OS X seems to encode the bytes in the filename as %XX characters.
        if platform.system() == 'Darwin':
            assert res.basename() == 'r%E9%F1emi'
            return
        assert len(res.basename()) == len(filename)

    def test_makedirs(self, tmpdir):
        d = Path(tmpdir)

        # Placeholder file so that when removedirs() is called,
        # it doesn't remove the temporary directory itself.
        tempf = d / 'temp.txt'
        tempf.touch()
        try:
            foo = d / 'foo'
            boz = foo / 'bar' / 'baz' / 'boz'
            boz.makedirs()
            try:
                assert boz.isdir()
            finally:
                boz.removedirs()
            assert not foo.exists()
            assert d.exists()

            foo.mkdir(0o750)
            boz.makedirs(0o700)
            try:
                assert boz.isdir()
            finally:
                boz.removedirs()
            assert not foo.exists()
            assert d.exists()
        finally:
            os.remove(tempf)

    def assertSetsEqual(self, a, b):
        ad = {}

        for i in a:
            ad[i] = None

        bd = {}

        for i in b:
            bd[i] = None

        assert ad == bd

    def test_shutil(self, tmpdir):
        # Note: This only tests the methods exist and do roughly what
        # they should, neglecting the details as they are shutil's
        # responsibility.

        d = Path(tmpdir)
        testDir = d / 'testdir'
        testFile = testDir / 'testfile.txt'
        testA = testDir / 'A'
        testCopy = testA / 'testcopy.txt'
        testLink = testA / 'testlink.txt'
        testB = testDir / 'B'
        testC = testB / 'C'
        testCopyOfLink = testC / testA.relpathto(testLink)

        # Create test dirs and a file
        testDir.mkdir()
        testA.mkdir()
        testB.mkdir()

        f = open(testFile, 'w')
        f.write('x' * 10000)
        f.close()

        # Test simple file copying.
        testFile.copyfile(testCopy)
        assert testCopy.isfile()
        assert testFile.bytes() == testCopy.bytes()

        # Test copying into a directory.
        testCopy2 = testA / testFile.name
        testFile.copy(testA)
        assert testCopy2.isfile()
        assert testFile.bytes() == testCopy2.bytes()

        # Make a link for the next test to use.
        if hasattr(os, 'symlink'):
            testFile.symlink(testLink)
        else:
            testFile.copy(testLink)  # fallback

        # Test copying directory tree.
        testA.copytree(testC)
        assert testC.isdir()
        self.assertSetsEqual(
            testC.listdir(),
            [testC / testCopy.name, testC / testFile.name, testCopyOfLink],
        )
        assert not testCopyOfLink.islink()

        # Clean up for another try.
        testC.rmtree()
        assert not testC.exists()

        # Copy again, preserving symlinks.
        testA.copytree(testC, True)
        assert testC.isdir()
        self.assertSetsEqual(
            testC.listdir(),
            [testC / testCopy.name, testC / testFile.name, testCopyOfLink],
        )
        if hasattr(os, 'symlink'):
            assert testCopyOfLink.islink()
            assert testCopyOfLink.realpath() == testFile

        # Clean up.
        testDir.rmtree()
        assert not testDir.exists()
        self.assertList(d.listdir(), [])

    def assertList(self, listing, expected):
        assert sorted(listing) == sorted(expected)

    def test_patterns(self, tmpdir):
        d = Path(tmpdir)
        names = ['x.tmp', 'x.xtmp', 'x2g', 'x22', 'x.txt']
        dirs = [d, d / 'xdir', d / 'xdir.tmp', d / 'xdir.tmp' / 'xsubdir']

        for e in dirs:
            if not e.isdir():
                e.makedirs()

            for name in names:
                (e / name).touch()
        self.assertList(d.listdir('*.tmp'), [d / 'x.tmp', d / 'xdir.tmp'])
        self.assertList(d.files('*.tmp'), [d / 'x.tmp'])
        self.assertList(d.dirs('*.tmp'), [d / 'xdir.tmp'])
        self.assertList(
            d.walk(), [e for e in dirs if e != d] + [e / n for e in dirs for n in names]
        )
        self.assertList(d.walk('*.tmp'), [e / 'x.tmp' for e in dirs] + [d / 'xdir.tmp'])
        self.assertList(d.walkfiles('*.tmp'), [e / 'x.tmp' for e in dirs])
        self.assertList(d.walkdirs('*.tmp'), [d / 'xdir.tmp'])

    encodings = 'UTF-8', 'UTF-16BE', 'UTF-16LE', 'UTF-16'

    @pytest.mark.parametrize("encoding", encodings)
    def test_unicode(self, tmpdir, encoding):
        """Test that path works with the specified encoding,
        which must be capable of representing the entire range of
        Unicode codepoints.
        """
        d = Path(tmpdir)
        p = d / 'unicode.txt'

        givenLines = [
            'Hello world\n',
            '\u0d0a\u0a0d\u0d15\u0a15\r\n',
            '\u0d0a\u0a0d\u0d15\u0a15\x85',
            '\u0d0a\u0a0d\u0d15\u0a15\u2028',
            '\r',
            'hanging',
        ]
        given = ''.join(givenLines)
        expectedLines = [
            'Hello world\n',
            '\u0d0a\u0a0d\u0d15\u0a15\n',
            '\u0d0a\u0a0d\u0d15\u0a15\n',
            '\u0d0a\u0a0d\u0d15\u0a15\n',
            '\n',
            'hanging',
        ]
        clean = ''.join(expectedLines)
        stripped = [line.replace('\n', '') for line in expectedLines]

        # write bytes manually to file
        with io.open(p, 'wb') as strm:
            strm.write(given.encode(encoding))

        # test all 3 path read-fully functions, including
        # path.lines() in unicode mode.
        assert p.bytes() == given.encode(encoding)
        with pytest.deprecated_call():
            assert p.text(encoding) == clean
        assert p.lines(encoding) == expectedLines
        assert p.lines(encoding, retain=False) == stripped

        # If this is UTF-16, that's enough.
        # The rest of these will unfortunately fail because append=True
        # mode causes an extra BOM to be written in the middle of the file.
        # UTF-16 is the only encoding that has this problem.
        if encoding == 'UTF-16':
            return

        # Write Unicode to file using path.write_text().
        # This test doesn't work with a hanging line.
        cleanNoHanging = clean + '\n'

        p.write_text(cleanNoHanging, encoding)
        p.write_text(cleanNoHanging, encoding, append=True)
        # Check the result.
        expectedBytes = 2 * cleanNoHanging.replace('\n', os.linesep).encode(encoding)
        expectedLinesNoHanging = expectedLines[:]
        expectedLinesNoHanging[-1] += '\n'
        assert p.bytes() == expectedBytes
        with pytest.deprecated_call():
            assert p.text(encoding) == 2 * cleanNoHanging
        assert p.lines(encoding) == 2 * expectedLinesNoHanging
        assert p.lines(encoding, retain=False) == 2 * stripped

        # Write Unicode to file using path.write_lines().
        # The output in the file should be exactly the same as last time.
        p.write_lines(expectedLines, encoding)
        p.write_lines(stripped, encoding, append=True)
        # Check the result.
        assert p.bytes() == expectedBytes

        # Now: same test, but using various newline sequences.
        # If linesep is being properly applied, these will be converted
        # to the platform standard newline sequence.
        p.write_lines(givenLines, encoding)
        p.write_lines(givenLines, encoding, append=True)
        # Check the result.
        assert p.bytes() == expectedBytes

        # Same test, using newline sequences that are different
        # from the platform default.
        def testLinesep(eol):
            p.write_lines(givenLines, encoding, linesep=eol)
            p.write_lines(givenLines, encoding, linesep=eol, append=True)
            expected = 2 * cleanNoHanging.replace('\n', eol).encode(encoding)
            assert p.bytes() == expected

        testLinesep('\n')
        testLinesep('\r')
        testLinesep('\r\n')
        testLinesep('\x0d\x85')

        # Again, but with linesep=None.
        p.write_lines(givenLines, encoding, linesep=None)
        p.write_lines(givenLines, encoding, linesep=None, append=True)
        # Check the result.
        expectedBytes = 2 * given.encode(encoding)
        assert p.bytes() == expectedBytes
        with pytest.deprecated_call():
            assert p.text(encoding) == 2 * clean
        expectedResultLines = expectedLines[:]
        expectedResultLines[-1] += expectedLines[0]
        expectedResultLines += expectedLines[1:]
        assert p.lines(encoding) == expectedResultLines

    def test_chunks(self, tmpdir):
        p = (TempDir() / 'test.txt').touch()
        txt = "0123456789"
        size = 5
        p.write_text(txt)
        for i, chunk in enumerate(p.chunks(size)):
            assert chunk == txt[i * size : i * size + size]

        assert i == len(txt) / size - 1

    @pytest.mark.skipif(not hasattr(os.path, 'samefile'), reason="samefile not present")
    def test_samefile(self, tmpdir):
        f1 = (TempDir() / '1.txt').touch()
        f1.write_text('foo')
        f2 = (TempDir() / '2.txt').touch()
        f1.write_text('foo')
        f3 = (TempDir() / '3.txt').touch()
        f1.write_text('bar')
        f4 = TempDir() / '4.txt'
        f1.copyfile(f4)

        assert os.path.samefile(f1, f2) == f1.samefile(f2)
        assert os.path.samefile(f1, f3) == f1.samefile(f3)
        assert os.path.samefile(f1, f4) == f1.samefile(f4)
        assert os.path.samefile(f1, f1) == f1.samefile(f1)

    def test_rmtree_p(self, tmpdir):
        d = Path(tmpdir)
        sub = d / 'subfolder'
        sub.mkdir()
        (sub / 'afile').write_text('something')
        sub.rmtree_p()
        assert not sub.exists()

    def test_rmtree_p_nonexistent(self, tmpdir):
        d = Path(tmpdir)
        sub = d / 'subfolder'
        assert not sub.exists()
        sub.rmtree_p()

    def test_rmdir_p_exists(self, tmpdir):
        """
        Invocation of rmdir_p on an existant directory should
        remove the directory.
        """
        d = Path(tmpdir)
        sub = d / 'subfolder'
        sub.mkdir()
        sub.rmdir_p()
        assert not sub.exists()

    def test_rmdir_p_nonexistent(self, tmpdir):
        """
        A non-existent file should not raise an exception.
        """
        d = Path(tmpdir)
        sub = d / 'subfolder'
        assert not sub.exists()
        sub.rmdir_p()

    def test_rmdir_p_sub_sub_dir(self, tmpdir):
        """
        A non-empty folder should not raise an exception.
        """
        d = Path(tmpdir)
        sub = d / 'subfolder'
        sub.mkdir()
        subsub = sub / 'subfolder'
        subsub.mkdir()

        sub.rmdir_p()


class TestMergeTree:
    @pytest.fixture(autouse=True)
    def testing_structure(self, tmpdir):
        self.test_dir = Path(tmpdir)
        self.subdir_a = self.test_dir / 'A'
        self.test_file = self.subdir_a / 'testfile.txt'
        self.test_link = self.subdir_a / 'testlink.txt'
        self.subdir_b = self.test_dir / 'B'

        self.subdir_a.mkdir()
        self.subdir_b.mkdir()

        with open(self.test_file, 'w') as f:
            f.write('x' * 10000)

        if hasattr(os, 'symlink'):
            self.test_file.symlink(self.test_link)
        else:
            self.test_file.copy(self.test_link)

    def check_link(self):
        target = Path(self.subdir_b / self.test_link.name)
        check = target.islink if hasattr(os, 'symlink') else target.isfile
        assert check()

    def test_with_nonexisting_dst_kwargs(self):
        self.subdir_a.merge_tree(self.subdir_b, symlinks=True)
        assert self.subdir_b.isdir()
        expected = set(
            (self.subdir_b / self.test_file.name, self.subdir_b / self.test_link.name)
        )
        assert set(self.subdir_b.listdir()) == expected
        self.check_link()

    def test_with_nonexisting_dst_args(self):
        self.subdir_a.merge_tree(self.subdir_b, True)
        assert self.subdir_b.isdir()
        expected = set(
            (self.subdir_b / self.test_file.name, self.subdir_b / self.test_link.name)
        )
        assert set(self.subdir_b.listdir()) == expected
        self.check_link()

    def test_with_existing_dst(self):
        self.subdir_b.rmtree()
        self.subdir_a.copytree(self.subdir_b, True)

        self.test_link.remove()
        test_new = self.subdir_a / 'newfile.txt'
        test_new.touch()
        with open(self.test_file, 'w') as f:
            f.write('x' * 5000)

        self.subdir_a.merge_tree(self.subdir_b, True)

        assert self.subdir_b.isdir()
        expected = set(
            (
                self.subdir_b / self.test_file.name,
                self.subdir_b / self.test_link.name,
                self.subdir_b / test_new.name,
            )
        )
        assert set(self.subdir_b.listdir()) == expected
        self.check_link()
        assert len(Path(self.subdir_b / self.test_file.name).bytes()) == 5000

    def test_copytree_parameters(self):
        """
        merge_tree should accept parameters to copytree, such as 'ignore'
        """
        ignore = shutil.ignore_patterns('testlink*')
        self.subdir_a.merge_tree(self.subdir_b, ignore=ignore)

        assert self.subdir_b.isdir()
        assert self.subdir_b.listdir() == [self.subdir_b / self.test_file.name]

    def test_only_newer(self):
        """
        merge_tree should accept a copy_function in which only
        newer files are copied and older files do not overwrite
        newer copies in the dest.
        """
        target = self.subdir_b / 'testfile.txt'
        target.write_text('this is newer')
        self.subdir_a.merge_tree(
            self.subdir_b, copy_function=path.only_newer(shutil.copy2)
        )
        assert target.read_text() == 'this is newer'


class TestChdir:
    def test_chdir_or_cd(self, tmpdir):
        """tests the chdir or cd method"""
        d = Path(str(tmpdir))
        cwd = d.getcwd()

        # ensure the cwd isn't our tempdir
        assert str(d) != str(cwd)
        # now, we're going to chdir to tempdir
        d.chdir()

        # we now ensure that our cwd is the tempdir
        assert str(d.getcwd()) == str(tmpdir)
        # we're resetting our path
        d = Path(cwd)

        # we ensure that our cwd is still set to tempdir
        assert str(d.getcwd()) == str(tmpdir)

        # we're calling the alias cd method
        d.cd()
        # now, we ensure cwd isn'r tempdir
        assert str(d.getcwd()) == str(cwd)
        assert str(d.getcwd()) != str(tmpdir)


class TestSubclass:
    def test_subclass_produces_same_class(self):
        """
        When operations are invoked on a subclass, they should produce another
        instance of that subclass.
        """

        class PathSubclass(Path):
            pass

        p = PathSubclass('/foo')
        subdir = p / 'bar'
        assert isinstance(subdir, PathSubclass)


class TestTempDir:
    def test_constructor(self):
        """
        One should be able to readily construct a temporary directory
        """
        d = TempDir()
        assert isinstance(d, path.Path)
        assert d.exists()
        assert d.isdir()
        d.rmdir()
        assert not d.exists()

    def test_next_class(self):
        """
        It should be possible to invoke operations on a TempDir and get
        Path classes.
        """
        d = TempDir()
        sub = d / 'subdir'
        assert isinstance(sub, path.Path)
        d.rmdir()

    def test_context_manager(self):
        """
        One should be able to use a TempDir object as a context, which will
        clean up the contents after.
        """
        d = TempDir()
        res = d.__enter__()
        assert res == path.Path(d)
        (d / 'somefile.txt').touch()
        assert not isinstance(d / 'somefile.txt', TempDir)
        d.__exit__(None, None, None)
        assert not d.exists()

    def test_context_manager_using_with(self):
        """
        The context manager will allow using the with keyword and
        provide a temporary directory that will be deleted after that.
        """

        with TempDir() as d:
            assert d.isdir()
        assert not d.isdir()

    def test_cleaned_up_on_interrupt(self):
        with contextlib.suppress(KeyboardInterrupt):
            with TempDir() as d:
                raise KeyboardInterrupt()

        assert not d.exists()


class TestUnicode:
    @pytest.fixture(autouse=True)
    def unicode_name_in_tmpdir(self, tmpdir):
        # build a snowman (dir) in the temporary directory
        Path(tmpdir).joinpath('☃').mkdir()

    def test_walkdirs_with_unicode_name(self, tmpdir):
        for res in Path(tmpdir).walkdirs():
            pass


class TestPatternMatching:
    def test_fnmatch_simple(self):
        p = Path('FooBar')
        assert p.fnmatch('Foo*')
        assert p.fnmatch('Foo[ABC]ar')

    def test_fnmatch_custom_mod(self):
        p = Path('FooBar')
        p.module = ntpath
        assert p.fnmatch('foobar')
        assert p.fnmatch('FOO[ABC]AR')

    def test_fnmatch_custom_normcase(self):
        def normcase(path):
            return path.upper()

        p = Path('FooBar')
        assert p.fnmatch('foobar', normcase=normcase)
        assert p.fnmatch('FOO[ABC]AR', normcase=normcase)

    def test_listdir_simple(self):
        p = Path('.')
        assert len(p.listdir()) == len(os.listdir('.'))

    def test_listdir_empty_pattern(self):
        p = Path('.')
        assert p.listdir('') == []

    def test_listdir_patterns(self, tmpdir):
        p = Path(tmpdir)
        (p / 'sub').mkdir()
        (p / 'File').touch()
        assert p.listdir('s*') == [p / 'sub']
        assert len(p.listdir('*')) == 2

    def test_listdir_custom_module(self, tmpdir):
        """
        Listdir patterns should honor the case sensitivity of the path module
        used by that Path class.
        """
        always_unix = Path.using_module(posixpath)
        p = always_unix(tmpdir)
        (p / 'sub').mkdir()
        (p / 'File').touch()
        assert p.listdir('S*') == []

        always_win = Path.using_module(ntpath)
        p = always_win(tmpdir)
        assert p.listdir('S*') == [p / 'sub']
        assert p.listdir('f*') == [p / 'File']

    def test_listdir_case_insensitive(self, tmpdir):
        """
        Listdir patterns should honor the case sensitivity of the path module
        used by that Path class.
        """
        p = Path(tmpdir)
        (p / 'sub').mkdir()
        (p / 'File').touch()
        assert p.listdir(matchers.CaseInsensitive('S*')) == [p / 'sub']
        assert p.listdir(matchers.CaseInsensitive('f*')) == [p / 'File']
        assert p.files(matchers.CaseInsensitive('S*')) == []
        assert p.dirs(matchers.CaseInsensitive('f*')) == []

    def test_walk_case_insensitive(self, tmpdir):
        p = Path(tmpdir)
        (p / 'sub1' / 'foo').makedirs_p()
        (p / 'sub2' / 'foo').makedirs_p()
        (p / 'sub1' / 'foo' / 'bar.Txt').touch()
        (p / 'sub2' / 'foo' / 'bar.TXT').touch()
        (p / 'sub2' / 'foo' / 'bar.txt.bz2').touch()
        files = list(p.walkfiles(matchers.CaseInsensitive('*.txt')))
        assert len(files) == 2
        assert p / 'sub2' / 'foo' / 'bar.TXT' in files
        assert p / 'sub1' / 'foo' / 'bar.Txt' in files


class TestInPlace:
    reference_content = textwrap.dedent(
        """
        The quick brown fox jumped over the lazy dog.
        """.lstrip()
    )
    reversed_content = textwrap.dedent(
        """
        .god yzal eht revo depmuj xof nworb kciuq ehT
        """.lstrip()
    )
    alternate_content = textwrap.dedent(
        """
          Lorem ipsum dolor sit amet, consectetur adipisicing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna
        aliqua. Ut enim ad minim veniam, quis nostrud exercitation
        ullamco laboris nisi ut aliquip ex ea commodo consequat.
        Duis aute irure dolor in reprehenderit in voluptate velit
        esse cillum dolore eu fugiat nulla pariatur. Excepteur
        sint occaecat cupidatat non proident, sunt in culpa qui
        officia deserunt mollit anim id est laborum.
        """.lstrip()
    )

    @classmethod
    def create_reference(cls, tmpdir):
        p = Path(tmpdir) / 'document'
        with p.open('w') as stream:
            stream.write(cls.reference_content)
        return p

    def test_line_by_line_rewrite(self, tmpdir):
        doc = self.create_reference(tmpdir)
        # reverse all the text in the document, line by line
        with doc.in_place() as (reader, writer):
            for line in reader:
                r_line = ''.join(reversed(line.strip())) + '\n'
                writer.write(r_line)
        with doc.open() as stream:
            data = stream.read()
        assert data == self.reversed_content

    def test_exception_in_context(self, tmpdir):
        doc = self.create_reference(tmpdir)
        with pytest.raises(RuntimeError) as exc:
            with doc.in_place() as (reader, writer):
                writer.write(self.alternate_content)
                raise RuntimeError("some error")
        assert "some error" in str(exc.value)
        with doc.open() as stream:
            data = stream.read()
        assert 'Lorem' not in data
        assert 'lazy dog' in data


class TestSpecialPaths:
    @pytest.fixture(autouse=True, scope='class')
    def appdirs_installed(cls):
        pytest.importorskip('appdirs')

    @pytest.fixture
    def feign_linux(self, monkeypatch):
        monkeypatch.setattr("platform.system", lambda: "Linux")
        monkeypatch.setattr("sys.platform", "linux")
        monkeypatch.setattr("os.pathsep", ":")
        # remove any existing import of appdirs, as it sets up some
        # state during import.
        sys.modules.pop('appdirs')

    def test_basic_paths(self):
        appdirs = importlib.import_module('appdirs')

        expected = appdirs.user_config_dir()
        assert SpecialResolver(Path).user.config == expected

        expected = appdirs.site_config_dir()
        assert SpecialResolver(Path).site.config == expected

        expected = appdirs.user_config_dir('My App', 'Me')
        assert SpecialResolver(Path, 'My App', 'Me').user.config == expected

    def test_unix_paths(self, tmpdir, monkeypatch, feign_linux):
        fake_config = tmpdir / '_config'
        monkeypatch.setitem(os.environ, 'XDG_CONFIG_HOME', str(fake_config))
        expected = str(tmpdir / '_config')
        assert SpecialResolver(Path).user.config == expected

    def test_unix_paths_fallback(self, tmpdir, monkeypatch, feign_linux):
        "Without XDG_CONFIG_HOME set, ~/.config should be used."
        fake_home = tmpdir / '_home'
        monkeypatch.delitem(os.environ, 'XDG_CONFIG_HOME', raising=False)
        monkeypatch.setitem(os.environ, 'HOME', str(fake_home))
        expected = Path('~/.config').expanduser()
        assert SpecialResolver(Path).user.config == expected

    def test_property(self):
        assert isinstance(Path.special().user.config, Path)
        assert isinstance(Path.special().user.data, Path)
        assert isinstance(Path.special().user.cache, Path)

    def test_other_parameters(self):
        """
        Other parameters should be passed through to appdirs function.
        """
        res = Path.special(version="1.0", multipath=True).site.config
        assert isinstance(res, Path)

    def test_multipath(self, feign_linux, monkeypatch, tmpdir):
        """
        If multipath is provided, on Linux return the XDG_CONFIG_DIRS
        """
        fake_config_1 = str(tmpdir / '_config1')
        fake_config_2 = str(tmpdir / '_config2')
        config_dirs = os.pathsep.join([fake_config_1, fake_config_2])
        monkeypatch.setitem(os.environ, 'XDG_CONFIG_DIRS', config_dirs)
        res = Path.special(multipath=True).site.config
        assert isinstance(res, Multi)
        assert fake_config_1 in res
        assert fake_config_2 in res
        assert '_config1' in str(res)

    def test_reused_SpecialResolver(self):
        """
        Passing additional args and kwargs to SpecialResolver should be
        passed through to each invocation of the function in appdirs.
        """
        appdirs = importlib.import_module('appdirs')

        adp = SpecialResolver(Path, version="1.0")
        res = adp.user.config

        expected = appdirs.user_config_dir(version="1.0")
        assert res == expected


class TestMultiPath:
    def test_for_class(self):
        """
        Multi.for_class should return a subclass of the Path class provided.
        """
        cls = Multi.for_class(Path)
        assert issubclass(cls, Path)
        assert issubclass(cls, Multi)
        expected_name = 'Multi' + Path.__name__
        assert cls.__name__ == expected_name

    def test_detect_no_pathsep(self):
        """
        If no pathsep is provided, multipath detect should return an instance
        of the parent class with no Multi mix-in.
        """
        path = Multi.for_class(Path).detect('/foo/bar')
        assert isinstance(path, Path)
        assert not isinstance(path, Multi)

    def test_detect_with_pathsep(self):
        """
        If a pathsep appears in the input, detect should return an instance
        of a Path with the Multi mix-in.
        """
        inputs = '/foo/bar', '/baz/bing'
        input = os.pathsep.join(inputs)
        path = Multi.for_class(Path).detect(input)

        assert isinstance(path, Multi)

    def test_iteration(self):
        """
        Iterating over a MultiPath should yield instances of the
        parent class.
        """
        inputs = '/foo/bar', '/baz/bing'
        input = os.pathsep.join(inputs)
        path = Multi.for_class(Path).detect(input)

        items = iter(path)
        first = next(items)
        assert first == '/foo/bar'
        assert isinstance(first, Path)
        assert not isinstance(first, Multi)
        assert next(items) == '/baz/bing'
        assert path == input


def test_no_dependencies():
    """
    Path pie guarantees that the path module can be
    transplanted into an environment without any dependencies.
    """
    cmd = [sys.executable, '-S', '-c', 'import path']
    subprocess.check_call(cmd)
