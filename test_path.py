# -*- coding: utf-8 -*-

""" test_path.py - Test the path module.

This only runs on Posix and NT right now.  I would like to have more
tests.  You can help!  Just add appropriate pathnames for your
platform (os.name) in each place where the p() function is called.
Then send me the result.  If you can't get the test to run at all on
your platform, there's probably a bug in path.py -- please let me
know!

TempDirTestCase.testTouch() takes a while to run.  It sleeps a few
seconds to allow some time to pass between calls to check the modify
time on files.

Authors:
 Jason Orendorff <jason.orendorff\x40gmail\x2ecom>
 Marc Abramowitz <msabramo\x40gmail\x2ecom>
 Others - unfortunately attribution is lost

"""

from __future__ import with_statement  # Needed for Python 2.5

import unittest
import codecs
import os
import sys
import random
import shutil
import tempfile
import time
import ntpath
import posixpath
import textwrap
import platform

import pytest

from path import path, tempdir, u
from path import CaseInsensitivePattern as ci

# Octals for python 2 & 3 support
o750 = 488
o700 = 448


def p(**choices):
    """ Choose a value from several possible values, based on os.name """
    return choices[os.name]


class BasicTestCase(unittest.TestCase):
    def testRelpath(self):
        root = path(p(nt='C:\\', posix='/'))
        foo = root / 'foo'
        quux = foo / 'quux'
        bar = foo / 'bar'
        boz = bar / 'Baz' / 'Boz'
        up = path(os.pardir)

        # basics
        self.assertEqual(root.relpathto(boz), path('foo')/'bar'/'Baz'/'Boz')
        self.assertEqual(bar.relpathto(boz), path('Baz')/'Boz')
        self.assertEqual(quux.relpathto(boz), up/'bar'/'Baz'/'Boz')
        self.assertEqual(boz.relpathto(quux), up/up/up/'quux')
        self.assertEqual(boz.relpathto(bar), up/up)

        # x.relpathto(x) == curdir
        self.assertEqual(root.relpathto(root), os.curdir)
        self.assertEqual(boz.relpathto(boz), os.curdir)
        # Make sure case is properly noted (or ignored)
        self.assertEqual(boz.relpathto(boz.normcase()), os.curdir)

        # relpath()
        cwd = path(os.getcwd())
        self.assertEqual(boz.relpath(), cwd.relpathto(boz))

        if os.name == 'nt':
            # Check relpath across drives.
            d = path('D:\\')
            self.assertEqual(d.relpathto(boz), boz)

    def testConstructionFromNone(self):
        """

        """
        try:
            path(None)
        except TypeError:
            pass
        else:
            raise Exception("DID NOT RAISE")

    def testConstructionFromInt(self):
        """
        path class will construct a path as a string of the number
        """
        self.assert_(path(1) == '1')

    def testStringCompatibility(self):
        """ Test compatibility with ordinary strings. """
        x = path('xyzzy')
        self.assert_(x == 'xyzzy')
        self.assert_(x == u('xyzzy'))

        # sorting
        items = [path('fhj'),
                 path('fgh'),
                 'E',
                 path('d'),
                 'A',
                 path('B'),
                 'c']
        items.sort()
        self.assert_(items == ['A', 'B', 'E', 'c', 'd', 'fgh', 'fhj'])

        # Test p1/p1.
        p1 = path("foo")
        p2 = path("bar")
        self.assertEqual(p1/p2, p(nt='foo\\bar', posix='foo/bar'))

    def testProperties(self):
        # Create sample path object.
        f = p(nt='C:\\Program Files\\Python\\Lib\\xyzzy.py',
              posix='/usr/local/python/lib/xyzzy.py')
        f = path(f)

        # .parent
        self.assertEqual(f.parent, p(nt='C:\\Program Files\\Python\\Lib',
                                     posix='/usr/local/python/lib'))

        # .name
        self.assertEqual(f.name, 'xyzzy.py')
        self.assertEqual(f.parent.name, p(nt='Lib', posix='lib'))

        # .ext
        self.assertEqual(f.ext, '.py')
        self.assertEqual(f.parent.ext, '')

        # .drive
        self.assertEqual(f.drive, p(nt='C:', posix=''))

    def testMethods(self):
        # .abspath()
        self.assertEqual(path(os.curdir).abspath(), os.getcwd())

        # .getcwd()
        cwd = path.getcwd()
        self.assert_(isinstance(cwd, path))
        self.assertEqual(cwd, os.getcwd())

    def testUNC(self):
        if hasattr(os.path, 'splitunc'):
            p = path(r'\\python1\share1\dir1\file1.txt')
            self.assert_(p.uncshare == r'\\python1\share1')
            self.assert_(p.splitunc() == os.path.splitunc(str(p)))

    def testExplicitModule(self):
        """
        The user may specify an explicit path module to use.
        """
        nt_ok = path.using_module(ntpath)(r'foo\bar\baz')
        posix_ok = path.using_module(posixpath)(r'foo/bar/baz')
        posix_wrong = path.using_module(posixpath)(r'foo\bar\baz')

        self.assertEqual(nt_ok.dirname(), r'foo\bar')
        self.assertEqual(posix_ok.dirname(), r'foo/bar')
        self.assertEqual(posix_wrong.dirname(), '')

        self.assertEqual(nt_ok / 'quux', r'foo\bar\baz\quux')
        self.assertEqual(posix_ok / 'quux', r'foo/bar/baz/quux')

    def testExplicitModuleClasses(self):
        """
        Multiple calls to path.using_module should produce the same class.
        """
        nt_path = path.using_module(ntpath)
        self.assert_(nt_path is path.using_module(ntpath))
        self.assertEqual(nt_path.__name__, 'path_ntpath')

    def test_joinpath_on_instance(self):
        res = path('foo')
        foo_bar = res.joinpath('bar')
        assert foo_bar == p(nt='foo\\bar', posix='foo/bar')

    def test_joinpath_to_nothing(self):
        res = path('foo')
        assert res.joinpath() == res

    def test_joinpath_on_class(self):
        "Construct a path from a series of strings"
        foo_bar = path.joinpath('foo', 'bar')
        assert foo_bar == p(nt='foo\\bar', posix='foo/bar')

    def test_joinpath_fails_on_empty(self):
        "It doesn't make sense to join nothing at all"
        try:
            path.joinpath()
        except TypeError:
            pass
        else:
            raise Exception("did not raise")

    def test_joinpath_returns_same_type(self):
        path_posix = path.using_module(posixpath)
        res = path_posix.joinpath('foo')
        assert isinstance(res, path_posix)
        res2 = res.joinpath('bar')
        assert isinstance(res2, path_posix)
        assert res2 == 'foo/bar'


class ReturnSelfTestCase(unittest.TestCase):
    """
    Some methods don't necessarily return any value (e.g. makedirs,
    makedirs_p, rename, mkdir, touch, chroot). These methods should return
    self anyhow to allow methods to be chained.
    """
    def setUp(self):
        # Create a temporary directory.
        f = tempfile.mktemp()
        system_tmp_dir = os.path.dirname(f)
        my_dir = 'testpath_tempdir_' + str(random.random())[2:]
        self.tempdir = os.path.join(system_tmp_dir, my_dir)
        os.mkdir(self.tempdir)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def testMakedirs_pReturnsSelf(self):
        """
        path('foo').makedirs_p() == path('foo')
        """
        p = path(self.tempdir) / "newpath"
        ret = p.makedirs_p()
        self.assertEquals(p, ret)

    def testMakedirs_pReturnsSelfEvenIfExists(self):
        p = path(self.tempdir)
        ret = p.makedirs_p()
        self.assertEquals(p, ret)

    def testRenameReturnsSelf(self):
        p = path(self.tempdir) / "somefile"
        p.touch()
        target = path(self.tempdir) / "otherfile"
        ret = p.rename(target)
        self.assertEquals(target, ret)

    def testMkdirReturnsSelf(self):
        p = path(self.tempdir) / "newdir"
        ret = p.mkdir()
        self.assertEquals(p, ret)

    def testTouchReturnsSelf(self):
        p = path(self.tempdir) / "empty file"
        ret = p.touch()
        self.assertEquals(p, ret)


class ScratchDirTestCase(unittest.TestCase):
    """
    Tests that run in a temporary directory (does not test tempdir class)
    """
    def setUp(self):
        # Create a temporary directory.
        f = tempfile.mktemp()
        system_tmp_dir = os.path.dirname(f)
        my_dir = 'testpath_tempdir_' + str(random.random())[2:]
        self.tempdir = os.path.join(system_tmp_dir, my_dir)
        os.mkdir(self.tempdir)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def testContextManager(self):
        """Can be used as context manager for chdir."""
        d = path(self.tempdir)
        subdir = d / 'subdir'
        subdir.makedirs()
        old_dir = os.getcwd()
        with subdir:
            self.assertEquals(os.getcwd(), os.path.realpath(subdir))
        self.assertEquals(os.getcwd(), old_dir)

    def testTouch(self):
        # NOTE: This test takes a long time to run (~10 seconds).
        # It sleeps several seconds because on Windows, the resolution
        # of a file's mtime and ctime is about 2 seconds.
        #
        # atime isn't tested because on Windows the resolution of atime
        # is something like 24 hours.

        d = path(self.tempdir)
        f = d / 'test.txt'
        t0 = time.time() - 3
        f.touch()
        t1 = time.time() + 3
        try:
            self.assert_(f.exists())
            self.assert_(f.isfile())
            self.assertEqual(f.size, 0)
            self.assert_(t0 <= f.mtime <= t1)
            if hasattr(os.path, 'getctime'):
                ct = f.ctime
                self.assert_(t0 <= ct <= t1)

            time.sleep(5)
            fobj = open(f, 'ab')
            fobj.write('some bytes'.encode('utf-8'))
            fobj.close()

            time.sleep(5)
            t2 = time.time() - 3
            f.touch()
            t3 = time.time() + 3

            assert t0 <= t1 < t2 <= t3  # sanity check

            self.assert_(f.exists())
            self.assert_(f.isfile())
            self.assertEqual(f.size, 10)
            self.assert_(t2 <= f.mtime <= t3)
            if hasattr(os.path, 'getctime'):
                ct2 = f.ctime
                if os.name == 'nt':
                    # On Windows, "ctime" is CREATION time
                    self.assertEqual(ct, ct2)
                    self.assert_(ct2 < t2)
                else:
                    # On other systems, it might be the CHANGE time
                    # (especially on Unix, time of inode changes)
                    self.failUnless(ct == ct2 or ct2 == f.mtime)
        finally:
            f.remove()

    def testListing(self):
        d = path(self.tempdir)
        self.assertEqual(d.listdir(), [])

        f = 'testfile.txt'
        af = d / f
        self.assertEqual(af, os.path.join(d, f))
        af.touch()
        try:
            self.assert_(af.exists())

            self.assertEqual(d.listdir(), [af])

            # .glob()
            self.assertEqual(d.glob('testfile.txt'), [af])
            self.assertEqual(d.glob('test*.txt'), [af])
            self.assertEqual(d.glob('*.txt'), [af])
            self.assertEqual(d.glob('*txt'), [af])
            self.assertEqual(d.glob('*'), [af])
            self.assertEqual(d.glob('*.html'), [])
            self.assertEqual(d.glob('testfile'), [])
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
            self.assertEqual(files, files2)
        finally:
            for f in files:
                try:
                    f.remove()
                except:
                    pass

    def testMakeDirs(self):
        d = path(self.tempdir)

        # Placeholder file so that when removedirs() is called,
        # it doesn't remove the temporary directory itself.
        tempf = d / 'temp.txt'
        tempf.touch()
        try:
            foo = d / 'foo'
            boz = foo / 'bar' / 'baz' / 'boz'
            boz.makedirs()
            try:
                self.assert_(boz.isdir())
            finally:
                boz.removedirs()
            self.failIf(foo.exists())
            self.assert_(d.exists())

            foo.mkdir(o750)
            boz.makedirs(o700)
            try:
                self.assert_(boz.isdir())
            finally:
                boz.removedirs()
            self.failIf(foo.exists())
            self.assert_(d.exists())
        finally:
            os.remove(tempf)

    def assertSetsEqual(self, a, b):
        ad = {}

        for i in a:
            ad[i] = None

        bd = {}

        for i in b:
            bd[i] = None

        self.assertEqual(ad, bd)

    def testShutil(self):
        # Note: This only tests the methods exist and do roughly what
        # they should, neglecting the details as they are shutil's
        # responsibility.

        d = path(self.tempdir)
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
        self.assert_(testCopy.isfile())
        self.assert_(testFile.bytes() == testCopy.bytes())

        # Test copying into a directory.
        testCopy2 = testA / testFile.name
        testFile.copy(testA)
        self.assert_(testCopy2.isfile())
        self.assert_(testFile.bytes() == testCopy2.bytes())

        # Make a link for the next test to use.
        if hasattr(os, 'symlink'):
            testFile.symlink(testLink)
        else:
            testFile.copy(testLink)  # fallback

        # Test copying directory tree.
        testA.copytree(testC)
        self.assert_(testC.isdir())
        self.assertSetsEqual(
            testC.listdir(),
            [testC / testCopy.name,
             testC / testFile.name,
             testCopyOfLink])
        self.assert_(not testCopyOfLink.islink())

        # Clean up for another try.
        testC.rmtree()
        self.assert_(not testC.exists())

        # Copy again, preserving symlinks.
        testA.copytree(testC, True)
        self.assert_(testC.isdir())
        self.assertSetsEqual(
            testC.listdir(),
            [testC / testCopy.name,
             testC / testFile.name,
             testCopyOfLink])
        if hasattr(os, 'symlink'):
            self.assert_(testCopyOfLink.islink())
            self.assert_(testCopyOfLink.readlink() == testFile)

        # Clean up.
        testDir.rmtree()
        self.assert_(not testDir.exists())
        self.assertList(d.listdir(), [])

    def assertList(self, listing, expected):
        listing = list(listing)
        listing.sort()
        expected = list(expected)
        expected.sort()
        self.assertEqual(listing, expected)

    def testPatterns(self):
        d = path(self.tempdir)
        names = ['x.tmp', 'x.xtmp', 'x2g', 'x22', 'x.txt']
        dirs = [d, d/'xdir', d/'xdir.tmp', d/'xdir.tmp'/'xsubdir']

        for e in dirs:
            if not e.isdir():
                e.makedirs()

            for name in names:
                (e/name).touch()
        self.assertList(d.listdir('*.tmp'), [d/'x.tmp', d/'xdir.tmp'])
        self.assertList(d.files('*.tmp'), [d/'x.tmp'])
        self.assertList(d.dirs('*.tmp'), [d/'xdir.tmp'])
        self.assertList(d.walk(), [e for e in dirs
                                   if e != d] + [e/n for e in dirs
                                                 for n in names])
        self.assertList(d.walk('*.tmp'),
                        [e/'x.tmp' for e in dirs] + [d/'xdir.tmp'])
        self.assertList(d.walkfiles('*.tmp'), [e/'x.tmp' for e in dirs])
        self.assertList(d.walkdirs('*.tmp'), [d/'xdir.tmp'])

    def testUnicode(self):
        d = path(self.tempdir)
        p = d/'unicode.txt'

        def test(enc):
            """ Test that path works with the specified encoding,
            which must be capable of representing the entire range of
            Unicode codepoints.
            """

            given = u('Hello world\n'
                      '\u0d0a\u0a0d\u0d15\u0a15\r\n'
                      '\u0d0a\u0a0d\u0d15\u0a15\x85'
                      '\u0d0a\u0a0d\u0d15\u0a15\u2028'
                      '\r'
                      'hanging')
            clean = u('Hello world\n'
                      '\u0d0a\u0a0d\u0d15\u0a15\n'
                      '\u0d0a\u0a0d\u0d15\u0a15\n'
                      '\u0d0a\u0a0d\u0d15\u0a15\n'
                      '\n'
                      'hanging')
            givenLines = [
                u('Hello world\n'),
                u('\u0d0a\u0a0d\u0d15\u0a15\r\n'),
                u('\u0d0a\u0a0d\u0d15\u0a15\x85'),
                u('\u0d0a\u0a0d\u0d15\u0a15\u2028'),
                u('\r'),
                u('hanging')]
            expectedLines = [
                u('Hello world\n'),
                u('\u0d0a\u0a0d\u0d15\u0a15\n'),
                u('\u0d0a\u0a0d\u0d15\u0a15\n'),
                u('\u0d0a\u0a0d\u0d15\u0a15\n'),
                u('\n'),
                u('hanging')]
            expectedLines2 = [
                u('Hello world'),
                u('\u0d0a\u0a0d\u0d15\u0a15'),
                u('\u0d0a\u0a0d\u0d15\u0a15'),
                u('\u0d0a\u0a0d\u0d15\u0a15'),
                u(''),
                u('hanging')]

            # write bytes manually to file
            f = codecs.open(p, 'w', enc)
            f.write(given)
            f.close()

            # test all 3 path read-fully functions, including
            # path.lines() in unicode mode.
            self.assertEqual(p.bytes(), given.encode(enc))
            self.assertEqual(p.text(enc), clean)
            self.assertEqual(p.lines(enc), expectedLines)
            self.assertEqual(p.lines(enc, retain=False), expectedLines2)

            # If this is UTF-16, that's enough.
            # The rest of these will unfortunately fail because append=True
            # mode causes an extra BOM to be written in the middle of the file.
            # UTF-16 is the only encoding that has this problem.
            if enc == 'UTF-16':
                return

            # Write Unicode to file using path.write_text().
            cleanNoHanging = clean + u('\n')  # This test doesn't work with a
                                              # hanging line.
            p.write_text(cleanNoHanging, enc)
            p.write_text(cleanNoHanging, enc, append=True)
            # Check the result.
            expectedBytes = 2 * cleanNoHanging.replace('\n',
                                                       os.linesep).encode(enc)
            expectedLinesNoHanging = expectedLines[:]
            expectedLinesNoHanging[-1] += '\n'
            self.assertEqual(p.bytes(), expectedBytes)
            self.assertEqual(p.text(enc), 2 * cleanNoHanging)
            self.assertEqual(p.lines(enc), 2 * expectedLinesNoHanging)
            self.assertEqual(p.lines(enc, retain=False), 2 * expectedLines2)

            # Write Unicode to file using path.write_lines().
            # The output in the file should be exactly the same as last time.
            p.write_lines(expectedLines, enc)
            p.write_lines(expectedLines2, enc, append=True)
            # Check the result.
            self.assertEqual(p.bytes(), expectedBytes)

            # Now: same test, but using various newline sequences.
            # If linesep is being properly applied, these will be converted
            # to the platform standard newline sequence.
            p.write_lines(givenLines, enc)
            p.write_lines(givenLines, enc, append=True)
            # Check the result.
            self.assertEqual(p.bytes(), expectedBytes)

            # Same test, using newline sequences that are different
            # from the platform default.
            def testLinesep(eol):
                p.write_lines(givenLines, enc, linesep=eol)
                p.write_lines(givenLines, enc, linesep=eol, append=True)
                expected = 2 * cleanNoHanging.replace(u('\n'), eol).encode(enc)
                self.assertEqual(p.bytes(), expected)

            testLinesep(u('\n'))
            testLinesep(u('\r'))
            testLinesep(u('\r\n'))
            testLinesep(u('\x0d\x85'))

            # Again, but with linesep=None.
            p.write_lines(givenLines, enc, linesep=None)
            p.write_lines(givenLines, enc, linesep=None, append=True)
            # Check the result.
            expectedBytes = 2 * given.encode(enc)
            self.assertEqual(p.bytes(), expectedBytes)
            self.assertEqual(p.text(enc), 2 * clean)
            expectedResultLines = expectedLines[:]
            expectedResultLines[-1] += expectedLines[0]
            expectedResultLines += expectedLines[1:]
            self.assertEqual(p.lines(enc), expectedResultLines)

        test('UTF-8')
        test('UTF-16BE')
        test('UTF-16LE')
        test('UTF-16')

    def testChunks(self):
        p = (tempdir() / 'test.txt').touch()
        txt = "0123456789"
        size = 5
        p.write_text(txt)
        for i, chunk in enumerate(p.chunks(size)):
            self.assertEqual(chunk, txt[i * size:i * size + size])

        self.assertEqual(i, len(txt) / size - 1)

    def testSameFile(self):
        f1 = (tempdir() / '1.txt').touch()
        f1.write_text('foo')
        f2 = (tempdir() / '2.txt').touch()
        f1.write_text('foo')
        f3 = (tempdir() / '3.txt').touch()
        f1.write_text('bar')
        f4 = (tempdir() / '4.txt')
        f1.copyfile(f4)

        self.assertEqual(os.path.samefile(f1, f2),
                         f1.samefile(f2))

        self.assertEqual(os.path.samefile(f1, f3),
                         f1.samefile(f3))

        self.assertEqual(os.path.samefile(f1, f4),
                         f1.samefile(f4))

        self.assertEqual(os.path.samefile(f1, f1),
                         f1.samefile(f1))

    def testRmtreeP(self):
        d = path(self.tempdir)
        sub = d / 'subfolder'
        sub.mkdir()
        (sub / 'afile').write_text('something')
        sub.rmtree_p()
        self.assertFalse(sub.exists())
        try:
            sub.rmtree_p()
        except OSError:
            self.fail("Calling `rmtree_p` on non-existent directory "
                      "should not raise an exception.")

    def test_chdir_or_cd(self):
        """ tests the chdir or cd method """
        d = path(self.tempdir)
        cwd = d.getcwd()

        assert str(d) != str(cwd)  # ensure the cwd isn't our tempdir
        d.chdir()  # now, we're going to chdir to tempdir

        assert str(d.getcwd()) == str(self.tempdir)  # we now ensure that our
                                                     # cwd is the tempdir
        d = path(cwd)  # we're resetting our path

        assert str(d.getcwd()) == str(self.tempdir)  # we ensure that our cwd
                                                     # is still set to tempdir

        d.cd()  # we're calling the alias cd method
        assert str(d.getcwd()) == str(cwd)  # now, we ensure cwd isn'r tempdir
        assert str(d.getcwd()) != str(self.tempdir)


class SubclassTestCase(unittest.TestCase):
    class PathSubclass(path):
        pass

    def test_subclass_produces_same_class(self):
        """
        When operations are invoked on a subclass, they should produce another
        instance of that subclass.
        """
        p = self.PathSubclass('/foo')
        subdir = p / 'bar'
        assert isinstance(subdir, self.PathSubclass)


class TempDirTestCase(unittest.TestCase):

    def test_constructor(self):
        """
        One should be able to readily construct a temporary directory
        """
        d = tempdir()
        assert isinstance(d, path)
        assert d.exists()
        assert d.isdir()
        d.rmdir()
        assert not d.exists()

    def test_next_class(self):
        """
        It should be possible to invoke operations on a tempdir and get
        path classes.
        """
        d = tempdir()
        sub = d / 'subdir'
        assert isinstance(sub, path)
        d.rmdir()

    def test_context_manager(self):
        """
        One should be able to use a tempdir object as a context, which will
        clean up the contents after.
        """
        d = tempdir()
        res = d.__enter__()
        assert res is d
        (d / 'somefile.txt').touch()
        assert not isinstance(d / 'somefile.txt', tempdir)
        d.__exit__(None, None, None)
        assert not d.exists()

    def test_context_manager_exception(self):
        """
        The context manager will not clean up if an exception occurs.
        """
        d = tempdir()
        d.__enter__()
        (d / 'somefile.txt').touch()
        assert not isinstance(d / 'somefile.txt', tempdir)
        d.__exit__(TypeError, TypeError('foo'), None)
        assert d.exists()

    def test_context_manager_using_with(self):
        """
        The context manager will allow using the with keyword and
        provide a temporry directory that will be deleted after that.
        """

        with tempdir() as d:
            self.assertTrue(d.isdir())
        self.assertFalse(d.isdir())


class TestUnicodePaths(unittest.TestCase):
    def setup_method(self, method):
        # Create a temporary directory.
        self.tempdir = tempfile.mkdtemp()
        # build a snowman (dir) in the temporary directory
        snowman = os.path.join(self.tempdir, '☃')
        os.mkdir(snowman)

    def teardown_method(self, method):
        shutil.rmtree(self.tempdir)

    def test_walkdirs_with_unicode_name(self):
        p = path(self.tempdir)
        for res in p.walkdirs():
            pass


class TestPatternMatching(object):
    def test_fnmatch_simple(self):
        p = path('FooBar')
        assert p.fnmatch('Foo*')
        assert p.fnmatch('Foo[ABC]ar')

    def test_fnmatch_custom_mod(self):
        p = path('FooBar')
        p.module = ntpath
        assert p.fnmatch('foobar')
        assert p.fnmatch('FOO[ABC]AR')

    def test_fnmatch_custom_normcase(self):
        normcase = lambda path: path.upper()
        p = path('FooBar')
        assert p.fnmatch('foobar', normcase=normcase)
        assert p.fnmatch('FOO[ABC]AR', normcase=normcase)

    def test_listdir_simple(self):
        p = path('.')
        assert len(p.listdir()) == len(os.listdir('.'))

    def test_listdir_empty_pattern(self):
        p = path('.')
        assert p.listdir('') == []

    def test_listdir_patterns(self, tmpdir):
        p = path(tmpdir)
        (p/'sub').mkdir()
        (p/'File').touch()
        assert p.listdir('s*') == [p / 'sub']
        assert len(p.listdir('*')) == 2

    def test_listdir_custom_module(self, tmpdir):
        """
        Listdir patterns should honor the case sensitivity of the path module
        used by that path class.
        """
        always_unix = path.using_module(posixpath)
        p = always_unix(tmpdir)
        (p/'sub').mkdir()
        (p/'File').touch()
        assert p.listdir('S*') == []

        always_win = path.using_module(ntpath)
        p = always_win(tmpdir)
        assert p.listdir('S*') == [p/'sub']
        assert p.listdir('f*') == [p/'File']

    def test_listdir_case_insensitive(self, tmpdir):
        """
        Listdir patterns should honor the case sensitivity of the path module
        used by that path class.
        """
        p = path(tmpdir)
        (p/'sub').mkdir()
        (p/'File').touch()
        assert p.listdir(ci('S*')) == [p/'sub']
        assert p.listdir(ci('f*')) == [p/'File']
        assert p.files(ci('S*')) == []
        assert p.dirs(ci('f*')) == []

    def test_walk_case_insensitive(self, tmpdir):
        p = path(tmpdir)
        (p/'sub1'/'foo').makedirs_p()
        (p/'sub2'/'foo').makedirs_p()
        (p/'sub1'/'foo'/'bar.Txt').touch()
        (p/'sub2'/'foo'/'bar.TXT').touch()
        (p/'sub2'/'foo'/'bar.txt.bz2').touch()
        files = list(p.walkfiles(ci('*.txt')))
        assert len(files) == 2
        assert p/'sub2'/'foo'/'bar.TXT' in files
        assert p/'sub1'/'foo'/'bar.Txt' in files

@pytest.mark.skipif(sys.version_info < (2, 6),
    reason="in_place requires io module in Python 2.6")
class TestInPlace(object):
    reference_content = u(textwrap.dedent("""
        The quick brown fox jumped over the lazy dog.
        """.lstrip()))
    reversed_content = u(textwrap.dedent("""
        .god yzal eht revo depmuj xof nworb kciuq ehT
        """.lstrip()))
    alternate_content = u(textwrap.dedent("""
          Lorem ipsum dolor sit amet, consectetur adipisicing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna
        aliqua. Ut enim ad minim veniam, quis nostrud exercitation
        ullamco laboris nisi ut aliquip ex ea commodo consequat.
        Duis aute irure dolor in reprehenderit in voluptate velit
        esse cillum dolore eu fugiat nulla pariatur. Excepteur
        sint occaecat cupidatat non proident, sunt in culpa qui
        officia deserunt mollit anim id est laborum.
        """.lstrip()))

    @classmethod
    def create_reference(cls, tmpdir):
        p = path(tmpdir)/'document'
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
        assert "some error" in str(exc)
        with doc.open() as stream:
            data = stream.read()
        assert not 'Lorem' in data
        assert 'lazy dog' in data

if __name__ == '__main__':
    unittest.main()
