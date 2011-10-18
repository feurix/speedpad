# Copyright (C) 2011 John Feuerstein <john@feurix.com>
#
# This file is part of the speedpad project.
#
# speedpad is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# speedpad is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import curses
import curses.ascii
import imp
import sys
import unittest

imp.load_source('speedpad', '../bin/speedpad')
import speedpad

stdscr = None

def start_curses():
    global stdscr
    if stdscr: return
    stdscr = curses.initscr()
    curses.savetty()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(1)
    curses.start_color()

def stop_curses():
    global stdscr
    if not stdscr: return
    curses.resetty()
    curses.endwin()


#########################################################################


class TestCase(unittest.TestCase):
    pass


class CursesTestCase(unittest.TestCase):
    pass


class CursesTestResult(unittest.TextTestResult):

    def _setupStdout(self):
        start_curses()
        super(CursesTestResult, self)._setupStdout()

    def _restoreStdout(self):
        stop_curses()
        super(CursesTestResult, self)._restoreStdout()


class TestRunner(unittest.TextTestRunner):

    def run(self, *args, **kwargs):
        self.stream.writeln("\nRunning normal tests...\n")
        return super(TestRunner, self).run(*args, **kwargs)


class CursesTestRunner(unittest.TextTestRunner):

    resultclass = CursesTestResult

    def run(self, *args, **kwargs):
        self.stream.writeln("\nRunning curses tests...\n")
        return super(CursesTestRunner, self).run(*args, **kwargs)


class CursesTestLoader(unittest.TestLoader):

    def loadTestsFromModule(self, module, **kwargs):
        tests = []
        for name in dir(module):
            obj = getattr(module, name)
            if (isinstance(obj, type) and
                issubclass(obj, CursesTestCase)):
                tests.append(self.loadTestsFromTestCase(obj))
        return self.suiteClass(tests)


class TestLoader(unittest.TestLoader):

    def loadTestsFromModule(self, module, **kwargs):
        tests = []
        for name in dir(module):
            obj = getattr(module, name)
            if (isinstance(obj, type) and
                issubclass(obj, TestCase) and not
                issubclass(obj, CursesTestCase)):
                tests.append(self.loadTestsFromTestCase(obj))
        return self.suiteClass(tests)


#########################################################################

class TestSpeedUnits(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.one = speedpad.Speed(1.0)
        cls.two = speedpad.Speed(2.0)

    def test_cps(self):
        self.assertEqual(speedpad.cps(self.one), 1.0)
        self.assertEqual(speedpad.cps(self.two), 2.0)
        self.assertEqual(str(speedpad.cps), 'CPS')

    def test_cpm(self):
        self.assertEqual(speedpad.cpm(self.one), 60.0)
        self.assertEqual(speedpad.cpm(self.two), 120.0)
        self.assertEqual(str(speedpad.cpm), 'CPM')

    def test_wpm(self):
        self.assertEqual(speedpad.wpm(self.one), 60.0 / 5.0)
        self.assertEqual(speedpad.wpm(self.two), 120.0 / 5.0)
        self.assertEqual(str(speedpad.wpm), 'WPM')

    def test_ppm(self):
        self.assertEqual(speedpad.ppm(self.one), 60.0 / 250.0)
        self.assertEqual(speedpad.ppm(self.two), 120.0 / 250.0)
        self.assertEqual(str(speedpad.ppm), 'PPM')

    def test_cph(self):
        self.assertEqual(speedpad.cph(self.one), 3600.0)
        self.assertEqual(speedpad.cph(self.two), 7200.0)
        self.assertEqual(str(speedpad.cph), 'CPH')


class TestQuote(TestCase):

    def test_inrange(self):
        quote = speedpad.Quote([
                "foo bar",
                "foo bar",
        ])
        self.assertTrue(quote.inrange(0, 0))
        self.assertTrue(quote.inrange(1, 0))
        self.assertTrue(quote.inrange(0, 1))
        self.assertTrue(quote.inrange(1, 6))
        self.assertFalse(quote.inrange(-1, -1))
        self.assertFalse(quote.inrange(2, 0))
        self.assertFalse(quote.inrange(1, 7))


    def test_strpos(self):
        quote = speedpad.Quote([
                "foo bar",
                "xxx xxx",
                "qux bux",
        ])
        self.assertEqual(quote.strpos(0, 0), 0)
        self.assertEqual(quote.strpos(1, 0), 7)
        self.assertEqual(quote.strpos(0, 1), 1)
        self.assertEqual(quote.strpos(2, 5), 7 + 7 + 5)
        self.assertRaises(IndexError, quote.strpos, -1, -1)
        self.assertEqual(quote.strpos(9, 9), quote.strlen)

    def test_istypo(self):
        quote = speedpad.Quote([
                "foo bar",
                "xxx xxx",
                "qux bux",
        ])
        self.assertTrue(quote.istypo(-1, -1, 'x', record=False))
        self.assertTrue(quote.istypo(0, 0, 'x', record=False))
        self.assertTrue(quote.istypo(9, 9, 'x', record=False))
        self.assertFalse(quote.istypo(0, 0, 'f', record=False))
        self.assertFalse(quote.istypo(1, 3, ' ', record=False))
        self.assertFalse(quote.stats.typos)
        # recording
        self.assertTrue(quote.istypo(-1, -1, 'x', record=True))
        self.assertTrue(quote.istypo(9, 9, 'x', record=True))
        self.assertFalse(quote.stats.typos)
        ypos, xpos = 0, 0
        self.assertTrue(quote.istypo(ypos, xpos, 'x', record=True))
        self.assertIn((ypos, xpos), quote.stats.typos)
        self.assertTrue(quote.stats.typos[ypos, xpos])
        self.assertFalse(quote.istypo(ypos, xpos, 'f', record=True))
        self.assertIn((ypos, xpos), quote.stats.typos)
        self.assertFalse(quote.stats.typos[ypos, xpos])
        ypos, xpos = 2, 6
        self.assertTrue(quote.istypo(ypos, xpos, 'z', record=True))
        self.assertIn((ypos, xpos), quote.stats.typos)
        self.assertTrue(quote.stats.typos[ypos, xpos])
        self.assertFalse(quote.istypo(ypos, xpos, 'x', record=True))
        self.assertIn((ypos, xpos), quote.stats.typos)
        self.assertFalse(quote.stats.typos[ypos, xpos])

    def test_eol(self):
        quote = speedpad.Quote([
                "foo bar",
                "",
                "xxx xx",
        ])
        self.assertEqual(quote.eol(-1), 0)
        self.assertEqual(quote.eol(0), 7)
        self.assertEqual(quote.eol(1), 0)
        self.assertEqual(quote.eol(2), 6)
        self.assertEqual(quote.eol(3), 0)

    def test_iseol(self):
        quote = speedpad.Quote([
                "foo bar",
                "",
                "xxx xx",
        ])
        self.assertTrue(quote.iseol(0, 7))
        self.assertTrue(quote.iseol(1, 1))
        self.assertTrue(quote.iseol(1, 0))
        self.assertTrue(quote.iseol(2, 20))
        self.assertFalse(quote.iseol(-1, -1))
        self.assertFalse(quote.iseol(0, 0))
        self.assertFalse(quote.iseol(2, 5))
        self.assertFalse(quote.iseol(3, 0))

    def test_iscomplete(self):
        quote = speedpad.Quote(["foo bar"])
        self.assertFalse(quote.iscomplete(-1, -1))
        self.assertFalse(quote.iscomplete(0, 0))
        self.assertFalse(quote.iscomplete(0, 6))
        self.assertTrue(quote.iscomplete(0, 7))
        self.assertTrue(quote.iscomplete(0, 9))
        self.assertTrue(quote.iscomplete(1, 0))
        self.assertTrue(quote.iscomplete(1, 9))

    def test_iscorrect(self):
        quote = speedpad.Quote(["foo bar"])
        self.assertTrue(quote.iscorrect())
        quote.istypo(0, 0, 'x', record=True)
        self.assertFalse(quote.iscorrect())
        quote.istypo(0, 0, 'f', record=True)
        self.assertTrue(quote.iscorrect())
        quote.istypo(0, 4, 'x', record=True)
        self.assertFalse(quote.iscorrect())
        quote.istypo(0, 4, 'b', record=True)
        self.assertTrue(quote.iscorrect())

    def test_typo_highscore(self):
        quote = speedpad.Quote([
                "foobar",
        ])
        quote.stats.typocounts['f']['a'] += 1
        quote.stats.typocounts['o']['b'] += 1
        quote.stats.typocounts['o']['c'] += 1
        quote.stats.typocounts['b']['d'] += 1
        quote.stats.typocounts['a']['e'] += 1
        quote.stats.typocounts['r']['f'] += 1
        self.assertEqual([
                ('o', [('b', 1), ('c', 1)]),
                ('a', [('e', 1)]),
                ('b', [('d', 1)]),
                ('f', [('a', 1)]),
                ('r', [('f', 1)]),
        ], quote.stats.typo_highscore)
        quote.stats.typocounts['f']['b'] += 2
        self.assertEqual([
                ('f', [('b', 2), ('a', 1)]),
                ('o', [('b', 1), ('c', 1)]),
                ('a', [('e', 1)]),
                ('b', [('d', 1)]),
                ('r', [('f', 1)]),
        ], quote.stats.typo_highscore)
        quote.stats.typocounts['b']['c'] += 1
        quote.stats.typocounts['o']['b'] += 2
        self.assertEqual([
                ('o', [('b', 3), ('c', 1)]),
                ('f', [('b', 2), ('a', 1)]),
                ('b', [('c', 1), ('d', 1)]),
                ('a', [('e', 1)]),
                ('r', [('f', 1)]),
        ], quote.stats.typo_highscore)
        quote.stats.typocounts['r']['f'] += 4
        self.assertEqual([
                ('r', [('f', 5)]),
                ('o', [('b', 3), ('c', 1)]),
                ('f', [('b', 2), ('a', 1)]),
                ('b', [('c', 1), ('d', 1)]),
                ('a', [('e', 1)]),
        ], quote.stats.typo_highscore)
        quote.stats.typocounts['f']['a'] += 2
        self.assertEqual([
                ('f', [('a', 3), ('b', 2)]),
                ('r', [('f', 5)]),
                ('o', [('b', 3), ('c', 1)]),
                ('b', [('c', 1), ('d', 1)]),
                ('a', [('e', 1)]),
        ], quote.stats.typo_highscore)


class TestQuoteGenerator(TestCase):

    def setUp(self):
        self.raw = "abcdefghijklmnopqrstuvwxyz"

    def factory(self, maxsize):
        while True:
            yield self.raw[:maxsize]

    def test_iterator(self):
        quotegen = speedpad.QuoteGenerator(self.factory, 2, 10)
        quote = quotegen.iterator.next()
        self.assertEqual(quote, self.raw[:20])

    def test_iteration(self):
        quotegen = speedpad.QuoteGenerator(self.factory, 2, 10)
        quote = quotegen.next()
        self.assertTrue(isinstance(quote, speedpad.Quote))
        self.assertEqual(quote.strlen, 20)
        self.assertEqual(quote.lines, [self.raw[:10], self.raw[10:20]])

    def test_clean(self):
        quotegen = speedpad.QuoteGenerator(self.factory, 2, 10)
        quote = quotegen.iterator.next()
        # input too long
        quotegen.wrapper.width = 20
        clean = quotegen.clean(quote)
        self.assertEqual(clean, [self.raw[:20]])
        # line too long
        quotegen.wrapper.width = 10
        clean = quotegen.clean(quote)
        self.assertEqual(clean, [self.raw[:10], self.raw[10:20]])
        # too many lines
        quotegen.wrapper.width = 5
        clean = quotegen.clean(quote)
        self.assertEqual(clean, [self.raw[:5], self.raw[5:10]])
        # strip
        quotegen = speedpad.QuoteGenerator(self.factory, 1, 50, strip=True)
        self.raw = " foo barbaz    qux "
        expect = [  "foo barbaz qux"     ]
        quote = quotegen.iterator.next()
        clean = quotegen.clean(quote)
        self.assertEqual(clean, expect)
        quotegen = speedpad.QuoteGenerator(self.factory, 1, 50, strip=False)
        self.raw = " foo barbaz    qux "
        expect = [ " foo barbaz    qux"  ]
        quote = quotegen.iterator.next()
        clean = quotegen.clean(quote)
        self.assertEqual(clean, expect)
        # tab expansion
        quotegen = speedpad.QuoteGenerator(self.factory, 1, 50,
                                           strip=False, tabsize=8)
        self.raw = " foo\tbarbaz    qux "
        expect = [ " foo    barbaz    qux"  ]
        quote = quotegen.iterator.next()
        clean = quotegen.clean(quote)
        self.assertEqual(clean, expect)
        quotegen = speedpad.QuoteGenerator(self.factory, 1, 50,
                                           strip=False, tabsize=5)
        self.raw = " foo\tbarbaz    qux "
        expect = [ " foo barbaz    qux"  ]
        quote = quotegen.iterator.next()
        clean = quotegen.clean(quote)
        self.assertEqual(clean, expect)
        # wrap
        quotegen = speedpad.QuoteGenerator(self.factory, 10, 50,
                                           strip=False, tabsize=4, wrap=10)
        self.raw = (
                " foo\tbarbaz    qux \n"
                "abcdefghijklmnopqrstuvwxyz\n"
                "\n"
                "xxx\tyyy zzz\n"
                "\n"
                " abc "
        )
        expect = [
                " foo",
                "barbaz",
                "qux",
                "abcdefghij",
                "klmnopqrst",
                "uvwxyz",
                "",
                "xxx yyy",
                "zzz",
                "",
        ]
        quote = quotegen.iterator.next()
        clean = quotegen.clean(quote)
        self.assertEqual(clean, expect)
        # same with wrap past last column
        quotegen = speedpad.QuoteGenerator(self.factory, 10, 10,
                                           strip=False, tabsize=4, wrap=20)
        quote = quotegen.iterator.next()
        clean = quotegen.clean(quote)
        self.assertEqual(clean, expect)
        # same with auto wrap
        quotegen = speedpad.QuoteGenerator(self.factory, 10, 10,
                                           strip=False, tabsize=4, wrap=0)
        quote = quotegen.iterator.next()
        clean = quotegen.clean(quote)
        self.assertEqual(clean, expect)
        # same with auto wrap and default width
        quotegen = speedpad.QuoteGenerator(self.factory, 10, 50,
                                           strip=False, tabsize=4,
                                           wrap=0, width=10)
        quote = quotegen.iterator.next()
        clean = quotegen.clean(quote)
        self.assertEqual(clean, expect)

    def test_resize(self):
        self.raw = (
                " foo\tbarbaz    qux \n"
                "abcdefghijklmnopqrstuvwxyz\n"
                "\n"
                "xxx\tyyy zzz\n"
                "\n"
                " abc "
        )
        expect = [
                " foo",
                "barbaz",
                "qux",
                "abcdefghij",
                "klmnopqrst",
                "uvwxyz",
                "",
                "xxx yyy",
                "zzz",
                "",
        ]
        quotegen = speedpad.QuoteGenerator(self.factory, 10, 50,
                                           strip=False, tabsize=4, wrap=0)
        quote = quotegen.iterator.next()
        clean = quotegen.clean(quote)
        self.assertNotEqual(clean, expect)
        quotegen.resize(0, -40)
        clean = quotegen.clean(quote)
        self.assertEqual(clean, expect)


class TestInputStats(TestCase):

    def test_addtypo(self):
        stats = speedpad.InputStats()
        self.assertFalse(stats.typos)
        stats.addtypo(0, 0, count=0)
        self.assertIn((0, 0), stats.typos)
        self.assertTrue(stats.typos[0, 0])
        self.assertEqual(stats.keystrokes_good, 0)
        self.assertEqual(stats.keystrokes_typo, 0)
        stats.addtypo(0, 0, count=1)
        self.assertIn((0, 0), stats.typos)
        self.assertTrue(stats.typos[0, 0])
        self.assertEqual(stats.keystrokes_good, 0)
        self.assertEqual(stats.keystrokes_typo, 1)

    def test_fixtypo(self):
        stats = speedpad.InputStats()
        self.assertFalse(stats.typos)
        stats.addtypo(0, 0, count=0)
        stats.fixtypo(0, 0, count=0)
        self.assertIn((0, 0), stats.typos)
        self.assertFalse(stats.typos[0, 0])
        self.assertEqual(stats.keystrokes_good, 0)
        self.assertEqual(stats.keystrokes_typo, 0)
        stats.fixtypo(0, 0, count=1)
        self.assertIn((0, 0), stats.typos)
        self.assertFalse(stats.typos[0, 0])
        self.assertEqual(stats.keystrokes_good, 1)
        self.assertEqual(stats.keystrokes_typo, 0)

    def test_speed(self):
        stats = speedpad.InputStats()
        stats.keystrokes_good = 100.0
        stats.timer.started = 100.0
        stats.timer.stopped = 100.9
        self.assertEqual(stats.speed, 0.0)
        stats.timer.stopped = 101.0
        self.assertEqual(stats.speed, 100.0)
        stats.timer.stopped = 150
        self.assertEqual(stats.speed, 2.0)
        stats.timer.stopped = 200
        self.assertEqual(stats.speed, 1.0)
        stats.timer.stopped = 300
        self.assertEqual(stats.speed, 0.5)

    def test_counters(self):
        stats = speedpad.InputStats()
        self.assertFalse(stats.typos)
        self.assertFalse(stats.typocounts)
        self.assertEqual(stats.keystrokes_typo, 0)
        self.assertEqual(stats.keystrokes_good, 0)
        self.assertEqual(stats.keystrokes_tab, 0)
        self.assertEqual(stats.keystrokes_space, 0)
        self.assertEqual(stats.keystrokes_enter, 0)
        stats.addtypo(0, 0, count=1)
        self.assertIn((0, 0), stats.typos)
        self.assertTrue(stats.typos[0, 0])
        self.assertEqual(stats.keystrokes_good, 0)
        self.assertEqual(stats.keystrokes_typo, 1)
        stats.fixtypo(0, 0, count=1)
        self.assertIn((0, 0), stats.typos)
        self.assertFalse(stats.typos[0, 0])
        self.assertEqual(stats.keystrokes_good, 1)
        self.assertEqual(stats.keystrokes_typo, 1)
        # auto increment is tested in TestSpeedPad.test_process

    def test_reset(self):
        stats = speedpad.InputStats()
        stats.addtypo(0, 0, count=1)
        stats.fixtypo(0, 0, count=1)
        stats.keystrokes_tab = 1
        stats.keystrokes_space = 2
        stats.keystrokes_enter = 3
        stats.typocounts['x']['y'] += 1
        stats.reset()
        self.assertFalse(stats.typos)
        self.assertFalse(stats.typocounts)
        self.assertEqual(stats.keystrokes_typo, 0)
        self.assertEqual(stats.keystrokes_good, 0)
        self.assertEqual(stats.keystrokes_tab, 0)
        self.assertEqual(stats.keystrokes_space, 0)
        self.assertEqual(stats.keystrokes_enter, 0)


class TestTimer(TestCase):

    def test_start(self):
        timer = speedpad.Timer()
        self.assertEqual(timer.started, 0)
        timer.start()
        self.assertGreater(timer.started, 0)
        self.assertRaises(RuntimeError, timer.start)

    def test_stop(self):
        timer = speedpad.Timer()
        self.assertEqual(timer.stopped, 0)
        self.assertRaises(RuntimeError, timer.stop)
        timer.start()
        timer.stop()
        self.assertGreater(timer.stopped, 0)
        self.assertRaises(RuntimeError, timer.stop)

    def test_elapsed(self):
        timer = speedpad.Timer()
        self.assertEqual(timer.elapsed, 0)
        timer.started = 100.0
        self.assertGreater(timer.elapsed, 0)
        timer.stopped = 100.0
        self.assertEqual(timer.elapsed, 0)
        timer.stopped = 105.5
        self.assertEqual(timer.elapsed, 5.5)
        timer.stopped = 0
        timer.stop()
        self.assertGreater(timer.elapsed, 0)

    def test_reset(self):
        timer = speedpad.Timer()
        timer.start()
        timer.stop()
        timer.reset()
        self.assertEqual(timer.started, 0)
        self.assertEqual(timer.stopped, 0)
        self.assertEqual(timer.elapsed, 0)


class TestProgressBar(CursesTestCase):

    @classmethod
    def setUpClass(cls):
        # set up 1 line x 50 col box (assumes termsize is large enough)
        cls.box = speedpad.Box(0, 0, 1, 50)

    def setUp(self):
        self.box.reset()
        self.bar = speedpad.ProgressBar(10)

    def tearDown(self):
        self.box.reset()

    def test_pos(self):
        self.assertEqual(self.bar.end, 0)
        self.assertEqual(self.bar.cur, 0)
        self.assertEqual(self.bar.pos, 0)
        self.bar.cur = 500
        self.assertEqual(self.bar.end, 0)
        self.assertEqual(self.bar.cur, 500)
        self.assertEqual(self.bar.pos, 0)
        self.bar.end = 1000
        self.assertEqual(self.bar.end, 1000)
        self.assertEqual(self.bar.cur, 500)
        self.assertEqual(self.bar.pos, 0.5)
        self.bar.cur = 1500
        self.assertEqual(self.bar.end, 1000)
        self.assertEqual(self.bar.cur, 1500)
        self.assertEqual(self.bar.pos, 1.0)
        self.bar.cur = -1
        self.assertEqual(self.bar.end, 1000)
        self.assertEqual(self.bar.cur, 0)
        self.assertEqual(self.bar.pos, 0)
        self.bar.cur = 800
        self.assertEqual(self.bar.end, 1000)
        self.assertEqual(self.bar.cur, 800)
        self.assertEqual(self.bar.pos, 0.8)
        self.bar.end = -1
        self.assertEqual(self.bar.end, 0)
        self.assertEqual(self.bar.cur, 0)
        self.assertEqual(self.bar.pos, 0)

    def test_reset(self):
        self.bar.end = 456
        self.bar.cur = 123
        self.bar.reset()
        self.assertEqual(self.bar.pos, 0)
        self.assertEqual(self.bar.cur, 0)
        self.assertEqual(self.bar.end, 0)

    def test_resize(self):
        self.assertEqual(self.bar.width, 10)
        self.bar.resize(0, -20)
        self.assertEqual(self.bar.width, 0)
        self.bar.resize(0, 15)
        self.assertEqual(self.bar.width, 15)

    def test_draw(self):
        win = self.box.box
        self.bar.end = 1000
        self.bar.cur = 750
        self.bar.draw(win, 0, 0)
        def eol(ypos):
            endpos = 0
            for xpos in xrange(50 - 1, -1, -1):
                if win.inch(ypos, xpos) != curses.ascii.SP:
                    endpos = xpos + 1
                    break
            return endpos
        self.assertEqual(eol(0), 7)
        self.box.reset()
        self.bar.width = 0
        self.bar.draw(win, 0, 0)
        self.assertEqual(eol(0), 0)
        self.box.reset()
        self.bar.width = 20
        self.bar.cur = 500
        self.bar.draw(win, 0, 0)
        self.assertEqual(eol(0), 10)
        self.box.reset()
        self.bar.cur = 1000
        self.bar.draw(win, 0, 0)
        self.assertEqual(eol(0), 20)


class TestInputBox(CursesTestCase):

    @classmethod
    def setUpClass(cls):
        # set up 10 line x 50 col box (assumes termsize is large enough)
        cls.box = speedpad.InputBox(1, 1, 10, 50, 10, 50, 0, 0)

    def setUp(self):
        self.box.reset()

    def tearDown(self):
        self.box.reset()

    def test_putch(self):
        ex = ord('x')
        # simple putch
        self.box.reset()
        self.box.putch(ex)
        ch = self.box.pad.inch(0, 0)
        self.assertEqual(ch, ex)
        # fill box
        self.box.reset()
        for pos in xrange(10 * 50):
            self.box.putch(ex)
        # lower right pos should stay empty
        for ypos in xrange(10):
            for xpos in xrange(50):
                ch = self.box.pad.inch(ypos, xpos)
                if ypos == 9 and xpos == 49:
                    self.assertEqual(ch, curses.ascii.SP)
                else:
                    self.assertEqual(ch, ex)
        # newline
        self.box.reset()
        self.box.putch(curses.ascii.NL)
        ypos, xpos = self.box.pad.getyx()
        self.assertEqual((ypos, xpos), (1, 0))
        # newline on last line does nothing
        self.box.reset()
        self.box.pad.move(9, 0)
        self.box.putch(curses.ascii.NL)
        ypos, xpos = self.box.pad.getyx()
        self.assertEqual((ypos, xpos), (9, 0))
        # backspace on upper left does nothing
        self.box.reset()
        self.box.putch(curses.ascii.BS)
        ypos, xpos = self.box.pad.getyx()
        self.assertEqual((ypos, xpos), (0, 0))
        # backspace after character
        self.box.reset()
        self.box.putch(ex)
        self.box.putch(curses.ascii.BS)
        ypos, xpos = self.box.pad.getyx()
        self.assertEqual((ypos, xpos), (0, 0))
        ch = self.box.pad.inch(ypos, xpos)
        self.assertEqual(ch, curses.ascii.SP)
        # backspace after sol wraps around
        self.box.reset()
        self.box.putch(ex)
        self.box.putch(curses.ascii.NL)
        self.box.putch(curses.ascii.BS)
        ypos, xpos = self.box.pad.getyx()
        self.assertEqual((ypos, xpos), (0, 1))

    def test_sol(self):
        ex = ord('x')
        # empty line
        self.box.reset()
        sol = self.box.sol(0)
        self.assertEqual(sol, 0)
        # no leading space
        self.box.reset()
        self.box.putch(ex)
        sol = self.box.sol(0)
        self.assertEqual(sol, 0)
        # leading space
        self.box.reset()
        self.box.putch(curses.ascii.SP)
        self.box.putch(ex)
        sol = self.box.sol(0)
        self.assertEqual(sol, 1)
        # skip and no leading space
        self.box.reset()
        self.box.putch(ex)
        self.box.putch(ex)
        sol = self.box.sol(0, skip=1)
        self.assertEqual(sol, 1)
        # skip and leading space
        self.box.reset()
        self.box.putch(curses.ascii.SP)
        self.box.putch(ex)
        self.box.putch(curses.ascii.SP)
        self.box.putch(ex)
        sol = self.box.sol(0, skip=2)
        self.assertEqual(sol, 3)

    def test_eol(self):
        ex = ord('x')
        # empty line
        self.box.reset()
        eol = self.box.eol(0)
        self.assertEqual(eol, 0)
        # no trailing space
        self.box.reset()
        self.box.putch(ex)
        self.box.putch(ex)
        eol = self.box.eol(0)
        self.assertEqual(eol, 2)
        # trailing space
        self.box.reset()
        self.box.putch(ex)
        self.box.putch(curses.ascii.SP)
        eol = self.box.eol(0)
        self.assertEqual(eol, 1)
        # at eol
        self.box.reset()
        for xpos in xrange(50):
            self.box.putch(ex)
        eol = self.box.eol(0)
        self.assertEqual(eol, 50)

    def test_continue_comment(self):
        s = "#"
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s), len(s))
        self.assertEqual(continuation, str2ord("#"))
        s = "# "
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s) - 1, len(s))
        self.assertEqual(continuation, str2ord("#"))
        s = "#x"
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s), len(s))
        self.assertEqual(continuation, str2ord("#"))
        # drop indent per default
        s = "# x"
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s), len(s))
        self.assertEqual(continuation, str2ord("#"))
        # keep indent if enabled
        s = "# x"
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s), len(s),
                                                 indent=True)
        self.assertEqual(continuation, str2ord("# "))
        s = "#  x"
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s), len(s),
                                                 indent=True)
        self.assertEqual(continuation, str2ord("#  "))
        # not enough space for indentation
        s = "#  x"
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s), len(s) - 1,
                                                 indent=True)
        self.assertEqual(continuation, str2ord("#"))
        # not enough space
        s = "# x"
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s), 0)
        self.assertFalse(continuation)

        s = "//"
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s), len(s))
        self.assertEqual(continuation, str2ord("//"))
        s = "// "
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s) - 1, len(s))
        self.assertEqual(continuation, str2ord("//"))
        s = "//x"
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s), len(s))
        self.assertEqual(continuation, str2ord("//"))
        # drop indent per default
        s = "// x"
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s), len(s))
        self.assertEqual(continuation, str2ord("//"))
        # keep indent if enabled
        s = "// x"
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s), len(s),
                                                 indent=True)
        self.assertEqual(continuation, str2ord("// "))
        s = "//  x"
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s), len(s),
                                                 indent=True)
        self.assertEqual(continuation, str2ord("//  "))
        # not enough space for indentation
        s = "//  x"
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s), len(s) - 1,
                                                 indent=True)
        self.assertEqual(continuation, str2ord("//"))
        # not enough space
        s = "// x"
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s), 0)
        self.assertFalse(continuation)

        s = "/*"
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s), len(s))
        self.assertEqual(continuation, str2ord(" *"))
        s = "/* "
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s) - 1, len(s))
        self.assertEqual(continuation, str2ord(" *"))
        s = "/*x"
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s), len(s))
        self.assertEqual(continuation, str2ord(" *"))
        # drop indent per default
        s = "/* x"
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s), len(s))
        self.assertEqual(continuation, str2ord(" *"))
        # keep indent if enabled
        s = "/* x"
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s), len(s),
                                                 indent=True)
        self.assertEqual(continuation, str2ord(" * "))
        s = "/*  x"
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s), len(s),
                                                 indent=True)
        self.assertEqual(continuation, str2ord(" *  "))
        # not enough space for indentation
        s = "/*  x"
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s), len(s) - 1,
                                                 indent=True)
        self.assertEqual(continuation, str2ord(" *"))
        # not enough space
        s = "/* x"
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s), 0)
        self.assertFalse(continuation)

        s = "*"
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s), len(s))
        self.assertEqual(continuation, str2ord("*"))
        s = "* "
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s) - 1, len(s))
        self.assertEqual(continuation, str2ord("*"))
        s = "*x"
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s), len(s))
        self.assertEqual(continuation, str2ord("*"))
        # drop indent per default
        s = "* x"
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s), len(s))
        self.assertEqual(continuation, str2ord("*"))
        # keep indent if enabled
        s = "* x"
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s), len(s),
                                                 indent=True)
        self.assertEqual(continuation, str2ord("* "))
        s = "*  x"
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s), len(s),
                                                 indent=True)
        self.assertEqual(continuation, str2ord("*  "))
        # not enough space for indentation
        s = "*  x"
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s), len(s) - 1,
                                                 indent=True)
        self.assertEqual(continuation, str2ord("*"))
        # not enough space
        s = "* x"
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s), 0)
        self.assertFalse(continuation)

        s = "/* foo bar */"
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s), len(s))
        self.assertFalse(continuation)
        s = "/*x foo bar x*/"
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s), len(s))
        self.assertFalse(continuation)
        s = "x/* foo bar */x"
        self.box.reset()
        self.putstr(s)
        continuation = self.box.continue_comment(0, 0, len(s), len(s))
        self.assertFalse(continuation)

    def putstr(self, s):
        # make sure we include the box.putch logic
        for ch in str2ord(s):
            self.box.putch(ch)


class TestSpeedPad(CursesTestCase):

    @classmethod
    def setUpClass(cls):
        cls.instance = speedpad.SpeedPad(
                player=speedpad.Player("test"),
                robot=speedpad.Robot("test", 0))
        cls.instance.initscreen()
        #cls.instance.speedbox = speedpad.SpeedBox(1, 1, 5, 50)
        #cls.instance.quotebox = speedpad.QuoteBox(5, 1, 10, 50, 5, 50, 0, 0)
        #cls.instance.inputbox = speedpad.InputBox(10, 1, 15, 50, 5, 50, 0, 0)
        cls.instance.initplayers()

    def setUp(self):
        self.instance.quotebox.reset()
        self.instance.inputbox.reset()
        self.quote = speedpad.Quote(["foo bar"])

    def tearDown(self):
        self.instance.quotebox.reset()
        self.instance.inputbox.reset()

    def test_update_player_speed(self):
        self.assertEqual(self.quote.stats.speed, 0)
        self.assertEqual(self.instance.player.speed, 0)
        self.quote.stats.timer.started = 100
        self.quote.stats.timer.stopped = 200
        self.quote.stats.keystrokes_good = 1000
        self.instance.update_player_speed(self.quote)
        self.assertEqual(self.instance.player.speed, 10.0)

    def test_update_robot_pos(self):
        self.quote.stats.timer.started = 100
        self.quote.stats.timer.stopped = 105
        self.instance.robot.pos = 0
        self.instance.robot.speed = 1.0
        self.instance.update_robot_pos(self.quote)
        self.assertEqual(self.instance.robot.pos, 5)

    def test_process(self):
        def process(ch, **kwargs):
            self.instance.process(self.quote, ch, [ch], **kwargs)
        def reset(quotelines):
            curses.flushinp()
            self.instance.queue.clear()
            self.quote = speedpad.Quote(quotelines)
            self.instance.speedbox.reset()
            self.instance.quotebox.reset()
            self.instance.inputbox.reset()
            self.instance.speedbox.load(self.quote)
            self.instance.quotebox.load(self.quote)
            self.instance.active = False
            self.instance.writable = True
        reset(["1"])
        self.assertFalse(self.instance.active)
        process(ord(' '))
        self.assertTrue(self.instance.active)
        self.assertEqual(self.instance.player.pos, 1)
        self.assertTrue(self.quote.stats.timer.started)
        self.assertTrue(self.quote.stats.typos)
        self.assertIn((0, 0), self.quote.stats.typos)
        self.assertTrue(self.quote.stats.typos[0, 0])
        self.assertTrue(self.quote.stats.typocounts)
        self.assertIn('1', self.quote.stats.typocounts)
        self.assertIn(' ', self.quote.stats.typocounts['1'])
        self.assertEqual(self.quote.stats.typocounts['1'][' '], 1)
        self.assertEqual(self.quote.stats.keystrokes_typo, 1)
        self.assertEqual(self.quote.stats.keystrokes_good, 0)
        self.assertEqual(self.quote.stats.keystrokes_tab, 0)
        self.assertEqual(self.quote.stats.keystrokes_space, 1)
        self.assertEqual(self.quote.stats.keystrokes_enter, 0)
        process(curses.ascii.BS)
        self.assertEqual(self.instance.player.pos, 0)
        self.assertTrue(self.quote.stats.typos)
        self.assertEqual(self.quote.stats.keystrokes_typo, 1)
        self.assertEqual(self.quote.stats.keystrokes_good, 0)
        process(ord('1'))
        self.assertEqual(self.instance.player.pos, 1)
        self.assertTrue(self.quote.stats.typos)
        self.assertIn((0, 0), self.quote.stats.typos)
        self.assertFalse(self.quote.stats.typos[0, 0])
        self.assertEqual(self.quote.stats.keystrokes_typo, 1)
        self.assertEqual(self.quote.stats.keystrokes_good, 1)
        self.assertTrue(self.instance.active)
        reset(["12"])
        self.assertFalse(self.instance.active)
        process(ord('1'))
        self.assertEqual(self.instance.player.pos, 1)
        self.assertFalse(self.quote.stats.typos)
        self.assertFalse(self.quote.stats.typocounts)
        self.assertEqual(self.quote.stats.keystrokes_typo, 0)
        self.assertEqual(self.quote.stats.keystrokes_good, 1)
        process(ord('2'))
        self.assertEqual(self.instance.player.pos, 2)
        self.assertFalse(self.quote.stats.typos)
        self.assertFalse(self.quote.stats.typocounts)
        self.assertEqual(self.quote.stats.keystrokes_typo, 0)
        self.assertEqual(self.quote.stats.keystrokes_good, 2)
        self.assertTrue(self.quote.iscomplete(0, 2))
        self.assertTrue(self.quote.iscorrect())
        self.assertTrue(self.instance.active)
        # auto eof after completion
        self.assertTrue(self.instance.queue)
        self.assertEqual(list(self.instance.queue), [curses.ascii.EOT])
        self.assertRaises(speedpad.QuoteStopSignal, process, curses.ascii.EOT)
        self.instance.active = False
        self.instance.writable = False
        self.assertTrue(self.quote.stats.timer.stopped)
        # no increment after completion
        process(curses.ascii.SP)
        process(curses.ascii.TAB)
        self.instance.active = True
        process(curses.ascii.NL)
        self.assertEqual(self.quote.stats.keystrokes_tab, 0)
        self.assertEqual(self.quote.stats.keystrokes_space, 0)
        self.assertEqual(self.quote.stats.keystrokes_enter, 0)
        self.instance.active = False
        self.assertRaises(speedpad.QuoteBreakSignal,
                          process, curses.ascii.NL)
        reset(["foo     bar",
               "baz"])
        for c in "foo": process(ord(c))
        self.assertEqual(self.instance.player.pos, 3)
        # tab expansion
        self.instance.tabsize = 2
        process(curses.ascii.TAB)
        self.assertEqual(self.quote.stats.keystrokes_tab, 1)
        self.assertEqual(self.quote.stats.keystrokes_space, 0)
        self.assertEqual(self.quote.stats.keystrokes_enter, 0)
        self.assertEqual(self.instance.player.pos, 3)
        self.assertTrue(self.instance.queue)
        self.assertEqual(list(self.instance.queue), str2ord(" "))
        self.instance.queue.clear()
        self.instance.tabsize = 8
        process(curses.ascii.TAB)
        self.assertEqual(self.quote.stats.keystrokes_tab, 2)
        self.assertEqual(self.instance.player.pos, 3)
        self.assertTrue(self.instance.queue)
        self.assertEqual(list(self.instance.queue), str2ord("     "))
        for sp in range(5): process(curses.ascii.SP, keyboard=False)
        self.assertEqual(self.instance.player.pos, 8)
        # backspace deletes trailing space
        process(curses.ascii.BS)
        self.assertEqual(self.instance.player.pos, 3)
        for sp in range(5): process(curses.ascii.SP, keyboard=False)
        self.assertEqual(self.instance.player.pos, 8)
        self.instance.queue.clear()
        for c in "bar": process(ord(c))
        self.assertEqual(self.instance.player.pos, 11)
        # manual newline on eol if strict
        self.instance.strict = True
        process(curses.ascii.SP)
        self.assertEqual(self.quote.stats.keystrokes_space, 0)
        self.assertEqual(self.instance.player.pos, 11)
        self.assertFalse(self.instance.queue)
        process(curses.ascii.TAB)
        self.assertEqual(self.instance.player.pos, 11)
        self.assertFalse(self.instance.queue)
        self.assertFalse(self.instance.queue)
        process(ord('x'))
        self.assertEqual(self.instance.player.pos, 11)
        self.assertFalse(self.instance.queue)
        # auto newline on eol
        self.instance.strict = False
        process(curses.ascii.SP)
        self.assertEqual(self.quote.stats.keystrokes_space, 0)
        self.assertEqual(self.instance.player.pos, 11)
        self.assertTrue(self.instance.queue)
        self.assertEqual(list(self.instance.queue), [curses.ascii.NL])
        self.instance.queue.clear()
        process(curses.ascii.TAB)
        self.assertEqual(self.instance.player.pos, 11)
        self.assertTrue(self.instance.queue)
        self.assertEqual(list(self.instance.queue), [curses.ascii.NL])
        self.instance.queue.clear()
        # next line
        process(curses.ascii.NL)
        self.assertEqual(self.quote.stats.keystrokes_enter, 1)
        self.assertEqual(self.instance.player.pos, 11)
        process(curses.ascii.SP)
        process(curses.ascii.SP)
        self.assertEqual(self.quote.stats.keystrokes_space, 2)
        process(curses.ascii.BS)
        # negative wrap around after backspace on first column
        process(curses.ascii.BS)
        self.assertEqual(self.instance.player.pos, 11)
        process(curses.ascii.NL)
        self.assertEqual(self.quote.stats.keystrokes_enter, 2)
        self.assertEqual(self.instance.player.pos, 11)
        for c in "bax": process(ord(c))
        self.assertEqual(self.instance.player.pos, 14)
        self.assertTrue(self.quote.stats.typos)
        self.assertIn((1, 2), self.quote.stats.typos)
        self.assertTrue(self.quote.stats.typos[1, 2])
        self.assertTrue(self.quote.stats.typocounts)
        self.assertIn('b', self.quote.stats.typocounts)
        self.assertIn('a', self.quote.stats.typocounts)
        self.assertIn('z', self.quote.stats.typocounts)
        self.assertIn(' ', self.quote.stats.typocounts['b'])
        self.assertIn(' ', self.quote.stats.typocounts['a'])
        self.assertIn('x', self.quote.stats.typocounts['z'])
        self.assertEqual(self.quote.stats.typocounts['b'][' '], 1)
        self.assertEqual(self.quote.stats.typocounts['a'][' '], 1)
        self.assertEqual(self.quote.stats.typocounts['z']['x'], 1)
        self.assertEqual(self.quote.stats.keystrokes_typo, 3)
        self.assertEqual(self.quote.stats.keystrokes_good, 8)
        # no-ops after completion, only backspace
        process(ord('x'))
        self.assertEqual(self.instance.player.pos, 14)
        process(curses.ascii.SP)
        self.assertEqual(self.instance.player.pos, 14)
        self.assertFalse(self.instance.queue)
        self.assertFalse(self.quote.stats.timer.stopped)
        self.assertFalse(self.quote.iscorrect())
        # delete over error
        process(curses.ascii.BS)
        self.assertEqual(self.instance.player.pos, 13)
        self.assertTrue(self.quote.stats.typos)
        self.assertIn((1, 2), self.quote.stats.typos)
        self.assertTrue(self.quote.stats.typos[1, 2])
        self.assertEqual(self.quote.stats.keystrokes_typo, 3)
        self.assertEqual(self.quote.stats.keystrokes_good, 8)
        # put x instead of z again
        process(ord('x'))
        self.assertEqual(self.instance.player.pos, 14)
        self.assertEqual(self.quote.stats.keystrokes_typo, 4)
        self.assertIn('x', self.quote.stats.typocounts['z'])
        self.assertEqual(self.quote.stats.typocounts['z']['x'], 2)
        process(curses.ascii.BS)
        # correct error
        process(ord('z'))
        self.assertEqual(self.instance.player.pos, 14)
        self.assertTrue(self.quote.stats.typos)
        self.assertIn((1, 2), self.quote.stats.typos)
        self.assertFalse(self.quote.stats.typos[1, 2])
        self.assertEqual(self.quote.stats.keystrokes_typo, 4)
        self.assertEqual(self.quote.stats.keystrokes_good, 9)
        self.assertTrue(self.quote.iscomplete(1, 3))
        self.assertTrue(self.quote.iscorrect())
        self.assertTrue(self.instance.queue)
        self.assertEqual(list(self.instance.queue), [curses.ascii.EOT])
        # auto indent
        reset(["  x",
               "  y"])
        for c in "  x": process(ord(c))
        self.assertEqual(self.instance.player.pos, 3)
        self.instance.indent = False
        process(curses.ascii.NL)
        self.assertEqual(self.instance.player.pos, 3)
        self.assertFalse(self.instance.queue)
        process(curses.ascii.BS)
        self.assertEqual(self.instance.player.pos, 3)
        self.instance.indent = True
        process(curses.ascii.NL)
        self.assertEqual(self.instance.player.pos, 3)
        self.assertTrue(self.instance.queue)
        self.assertEqual(list(self.instance.queue), str2ord("  "))
        # comment continuation
        reset(["#",
               "#"])
        process(ord('#'))
        self.assertEqual(self.instance.player.pos, 1)
        self.instance.syntax = False
        process(curses.ascii.NL)
        self.assertEqual(self.instance.player.pos, 1)
        self.assertFalse(self.instance.queue)
        process(curses.ascii.BS)
        self.assertEqual(self.instance.player.pos, 1)
        self.instance.syntax = True
        process(curses.ascii.NL)
        self.assertEqual(self.instance.player.pos, 1)
        self.assertTrue(self.instance.queue)
        self.assertEqual(list(self.instance.queue), [ord('#')])
        # comment continuation with leading space
        reset(["  #",
               "  #"])
        for c in "  #": process(ord(c))
        self.assertEqual(self.instance.player.pos, 3)
        self.instance.indent = False
        self.instance.syntax = False
        process(curses.ascii.NL)
        self.assertEqual(self.instance.player.pos, 3)
        self.assertFalse(self.instance.queue)
        process(curses.ascii.BS)
        self.assertEqual(self.instance.player.pos, 3)
        self.instance.indent = False
        self.instance.syntax = True
        process(curses.ascii.NL)
        self.assertEqual(self.instance.player.pos, 3)
        self.assertTrue(self.instance.queue)
        self.assertEqual(list(self.instance.queue), str2ord("#"))
        self.instance.queue.clear()
        process(curses.ascii.BS)
        self.assertEqual(self.instance.player.pos, 3)
        self.instance.indent = True
        self.instance.syntax = True
        process(curses.ascii.NL)
        self.assertEqual(self.instance.player.pos, 3)
        self.assertTrue(self.instance.queue)
        self.assertEqual(list(self.instance.queue), str2ord("  #"))
        # comment continuation with leading space and indent
        reset(["  #    x",
               "  #    x"])
        for c in "  #    x": process(ord(c))
        self.assertEqual(self.instance.player.pos, 8)
        self.instance.indent = False
        self.instance.syntax = True
        process(curses.ascii.NL)
        self.assertEqual(self.instance.player.pos, 8)
        self.assertTrue(self.instance.queue)
        self.assertEqual(list(self.instance.queue), str2ord("#"))
        self.instance.queue.clear()
        process(curses.ascii.BS)
        self.assertEqual(self.instance.player.pos, 8)
        self.instance.indent = True
        self.instance.syntax = True
        process(curses.ascii.NL)
        self.assertEqual(self.instance.player.pos, 8)
        self.assertTrue(self.instance.queue)
        self.assertEqual(list(self.instance.queue), str2ord("  #    "))
        # restart
        self.assertRaises(speedpad.QuoteResetSignal,
                          process, curses.ascii.CAN)
        # stop if active
        self.instance.active = True
        self.assertRaises(speedpad.QuoteStopSignal,
                          process, curses.ascii.EOT)
        # next if inactive
        self.instance.active = False
        self.assertRaises(speedpad.QuoteBreakSignal,
                          process, curses.ascii.EOT)


def str2ord(s):
    return map(ord, s)

def run_tests(**kwargs):
    module = __import__(__name__)
    results = []
    for loader, runner in (
            (TestLoader, TestRunner),
            (CursesTestLoader, CursesTestRunner),
    ):
        suite = loader().loadTestsFromModule(module)
        result = runner(**kwargs).run(suite)
        results.append(result)
    return results

if __name__ == '__main__':
    results = run_tests(verbosity=2)
    sys.exit(not all(result.wasSuccessful() for result in results))

# vim: et sw=4 sts=4 ts=4 tw=78 fen fdm=indent fdn=2 fdl=0
