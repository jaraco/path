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

URL:     http://www.jorendorff.com/articles/python/path
Author:  Jason Orendorff <jason@jorendorff.com>
Date:    7 Mar 2004

"""

import unittest
import codecs, os, random, shutil, tempfile, time
from path import path, __version__ as path_version

# This should match the version of path.py being tested.
__version__ = '2.2'


def p(**choices):
    """ Choose a value from several possible values, based on os.name """
    return choices[os.name]

class BasicTestCase(unittest.TestCase):
    def testRelpath(self):
        root = path(p(nt='C:\\',
                      posix='/'))
        foo = root / 'foo'
        quux =        foo / 'quux'
        bar =         foo / 'bar'
        boz =                bar / 'Baz' / 'Boz'
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

    def testStringCompatibility(self):
        """ Test compatibility with ordinary strings. """
        x = path('xyzzy')
        self.assert_(x == 'xyzzy')
        self.assert_(x == u'xyzzy')

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

class TempDirTestCase(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory.
        f = tempfile.mktemp()
        system_tmp_dir = os.path.dirname(f)
        my_dir = 'testpath_tempdir_' + str(random.random())[2:]
        self.tempdir = os.path.join(system_tmp_dir, my_dir)
        os.mkdir(self.tempdir)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

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
            fobj = file(f, 'ab')
            fobj.write('some bytes')
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
            fobj = file(f, 'w')
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
            boz =      foo / 'bar' / 'baz' / 'boz'
            boz.makedirs()
            try:
                self.assert_(boz.isdir())
            finally:
                boz.removedirs()
            self.failIf(foo.exists())
            self.assert_(d.exists())

            foo.mkdir(0750)
            boz.makedirs(0700)
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
        for i in a: ad[i] = None
        bd = {}
        for i in b: bd[i] = None
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
        names = [ 'x.tmp', 'x.xtmp', 'x2g', 'x22', 'x.txt' ]
        dirs = [d, d/'xdir', d/'xdir.tmp', d/'xdir.tmp'/'xsubdir']

        for e in dirs:
            if not e.isdir():  e.makedirs()
            for name in names:
                (e/name).touch()
        self.assertList(d.listdir('*.tmp'), [d/'x.tmp', d/'xdir.tmp'])
        self.assertList(d.files('*.tmp'), [d/'x.tmp'])
        self.assertList(d.dirs('*.tmp'), [d/'xdir.tmp'])
        self.assertList(d.walk(), [e for e in dirs if e != d] + [e/n for e in dirs for n in names])
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

            given = (u'Hello world\n'
                     u'\u0d0a\u0a0d\u0d15\u0a15\r\n'
                     u'\u0d0a\u0a0d\u0d15\u0a15\x85'
                     u'\u0d0a\u0a0d\u0d15\u0a15\u2028'
                     u'\r'
                     u'hanging')
            clean = (u'Hello world\n'
                     u'\u0d0a\u0a0d\u0d15\u0a15\n'
                     u'\u0d0a\u0a0d\u0d15\u0a15\n'
                     u'\u0d0a\u0a0d\u0d15\u0a15\n'
                     u'\n'
                     u'hanging')
            givenLines = [
                u'Hello world\n',
                u'\u0d0a\u0a0d\u0d15\u0a15\r\n',
                u'\u0d0a\u0a0d\u0d15\u0a15\x85',
                u'\u0d0a\u0a0d\u0d15\u0a15\u2028',
                u'\r',
                u'hanging']
            expectedLines = [
                u'Hello world\n',
                u'\u0d0a\u0a0d\u0d15\u0a15\n',
                u'\u0d0a\u0a0d\u0d15\u0a15\n',
                u'\u0d0a\u0a0d\u0d15\u0a15\n',
                u'\n',
                u'hanging']
            expectedLines2 = [
                u'Hello world',
                u'\u0d0a\u0a0d\u0d15\u0a15',
                u'\u0d0a\u0a0d\u0d15\u0a15',
                u'\u0d0a\u0a0d\u0d15\u0a15',
                u'',
                u'hanging']

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
            # The rest of these will unfortunately fail because append=True mode
            # causes an extra BOM to be written in the middle of the file.
            # UTF-16 is the only encoding that has this problem.
            if enc == 'UTF-16':
                return

            # Write Unicode to file using path.write_text().
            cleanNoHanging = clean + u'\n'  # This test doesn't work with a hanging line.
            p.write_text(cleanNoHanging, enc)
            p.write_text(cleanNoHanging, enc, append=True)
            # Check the result.
            expectedBytes = 2 * cleanNoHanging.replace('\n', os.linesep).encode(enc)
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
                expected = 2 * cleanNoHanging.replace(u'\n', eol).encode(enc)
                self.assertEqual(p.bytes(), expected)

            testLinesep(u'\n')
            testLinesep(u'\r')
            testLinesep(u'\r\n')
            testLinesep(u'\x0d\x85')


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

if __name__ == '__main__':
    if __version__ != path_version:
        print ("Version mismatch:  test_path.py version %s, path version %s" %
               (__version__, path_version))
    unittest.main()
