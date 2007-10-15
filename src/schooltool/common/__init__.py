#
# SchoolTool - common information systems platform for school administration
# Copyright (c) 2003 Shuttleworth Foundation
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
"""
Things common to the SchoolTool server and clients.
"""

import re
import locale
import datetime
import urllib

from zope.schema import Date
from zope.interface import Interface, implements

__metaclass__ = type


def parse_date(value):
    """Parse a ISO-8601 YYYY-MM-DD date value.

    Examples:

        >>> parse_date('2003-09-01')
        datetime.date(2003, 9, 1)
        >>> parse_date('20030901')
        Traceback (most recent call last):
          ...
        ValueError: Invalid date: '20030901'
        >>> parse_date('2003-IX-01')
        Traceback (most recent call last):
          ...
        ValueError: Invalid date: '2003-IX-01'
        >>> parse_date('2003-09-31')
        Traceback (most recent call last):
          ...
        ValueError: Invalid date: '2003-09-31'
        >>> parse_date('2003-09-30-15-42')
        Traceback (most recent call last):
          ...
        ValueError: Invalid date: '2003-09-30-15-42'

    """
    try:
        y, m, d = map(int, value.split('-'))
        return datetime.date(y, m, d)
    except ValueError:
        raise ValueError("Invalid date: %r" % value)


def parse_time(value):
    """Parse a ISO 8601 HH:MM time value.

    Examples:

        >>> parse_time('01:25')
        datetime.time(1, 25)
        >>> parse_time('9:15')
        datetime.time(9, 15)
        >>> parse_time('12:1')
        datetime.time(12, 1)
        >>> parse_time('00:00')
        datetime.time(0, 0)
        >>> parse_time('23:59')
        datetime.time(23, 59)
        >>> parse_time('24:00')
        Traceback (most recent call last):
          ...
        ValueError: Invalid time: '24:00'
        >>> parse_time('06:30PM')
        Traceback (most recent call last):
          ...
        ValueError: Invalid time: '06:30PM'

    """
    try:
        h, m = map(int, value.split(':'))
        return datetime.time(h, m)
    except ValueError:
        raise ValueError("Invalid time: %r" % value)


def parse_datetime(s):
    """Parse a ISO 8601 date/time value.

    Only a small subset of ISO 8601 is accepted:

      YYYY-MM-DD HH:MM:SS
      YYYY-MM-DD HH:MM:SS.ssssss
      YYYY-MM-DDTHH:MM:SS
      YYYY-MM-DDTHH:MM:SS.ssssss

    Returns a datetime.datetime object without a time zone.

    Examples:

        >>> parse_datetime('2003-04-05 11:22:33.456789')
        datetime.datetime(2003, 4, 5, 11, 22, 33, 456789)

        >>> parse_datetime('2003-04-05 11:22:33.456')
        datetime.datetime(2003, 4, 5, 11, 22, 33, 456000)

        >>> parse_datetime('2003-04-05 11:22:33.45678999')
        datetime.datetime(2003, 4, 5, 11, 22, 33, 456789)

        >>> parse_datetime('01/02/03')
        Traceback (most recent call last):
          ...
        ValueError: Bad datetime: 01/02/03

    """
    m = re.match(r"(\d+)-(\d+)-(\d+)[ T](\d+):(\d+):(\d+)([.](\d+))?$", s)
    if not m:
        raise ValueError("Bad datetime: %s" % s)
    ssssss = m.groups()[7]
    if ssssss:
        ssssss = int((ssssss + "00000")[:6])
    else:
        ssssss = 0
    y, m, d, hh, mm, ss = map(int, m.groups()[:6])
    return datetime.datetime(y, m, d, hh, mm, ss, ssssss)


def dedent(text):
    r"""Remove leading indentation from triple-quoted strings.

    Example:

        >>> dedent('''
        ...     some text
        ...     is here
        ...        with maybe some indents
        ...     ''')
        ...
        'some text\nis here\n   with maybe some indents\n'

    Corner cases (mixing tabs and spaces, lines that are indented less than
    the first line) are not handled yet.
    """
    lines = text.splitlines()
    first, limit = 0, len(lines)
    while first < limit and not lines[first]:
        first += 1
    if first >= limit:
        return ''
    firstline = lines[first]
    indent, limit = 0, len(firstline)
    while indent < limit and firstline[indent] in (' ', '\t'):
        indent += 1
    return '\n'.join([line[indent:] for line in lines[first:]])


def to_unicode(s):
    r"""Convert a UTF-8 string to Unicode.

    Example:

        >>> to_unicode('\xc4\x84\xc5\xbeuol\xc5\xb3')
        u'\u0104\u017euol\u0173'

    For convenience, to_unicode accepts None as the argument value.  This makes
    it easier to use it with libxml2 functions such as nsProp, which return
    None for missing attribute values.

        >>> to_unicode(None) is None
        True

    """
    if s is None:
        return None
    else:
        return unicode(s, 'UTF-8')


locale_charset = locale.getpreferredencoding()


def to_locale(us):
    r"""Convert a Unicode string to the current locale encoding.

    Example:

        >>> from schooltool import common
        >>> old_locale_charset = common.locale_charset

        >>> common.locale_charset = 'UTF-8'
        >>> to_locale(u'\u263B')
        '\xe2\x98\xbb'

        >>> common.locale_charset = 'ASCII'
        >>> to_locale(u'Unrepresentable: \u263B')
        'Unrepresentable: ?'

        >>> locale_charset = old_locale_charset

    """
    return us.encode(locale_charset, 'replace')


def from_locale(s):
    r"""Convert an 8-bit string in locale encoding to Unicode.

    Example:

        >>> from schooltool import common
        >>> old_locale_charset = common.locale_charset

        >>> from_locale('xyzzy')
        u'xyzzy'

        >>> common.locale_charset = 'UTF-8'
        >>> from_locale('\xe2\x98\xbb')
        u'\u263b'

        >>> locale_charset = old_locale_charset

    """
    return unicode(s, locale_charset)


class StreamWrapper:
    r"""Unicode-friendly wrapper for writable file-like objects.

    Here the terms 'encoding' and 'charset' are used interchangeably.

    The main use case for StreamWrapper is wrapping sys.stdout and sys.stderr
    so that you can forget worrying about charsets of your data.

        >>> from StringIO import StringIO
        >>> from schooltool import common
        >>> old_locale_charset = common.locale_charset
        >>> common.locale_charset = 'UTF-8'

        >>> sw = StreamWrapper(StringIO())
        >>> print >> sw, u"Hello, world! \u00b7\u263b\u00b7"
        >>> sw.stm.getvalue()
        'Hello, world! \xc2\xb7\xe2\x98\xbb\xc2\xb7\n'

    By default printing Unicode strings to stdout/stderr will raise Unicode
    errors if the stream encoding does not include some characters you are
    printing.  StreamWrapper will replace unconvertable characters to question
    marks, therefore you should only use it for informative messages where such
    loss of information is acceptable.

        >>> common.locale_charset = 'US-ASCII'
        >>> sw = StreamWrapper(StringIO())
        >>> print >> sw, u"Hello, world! \u00b7\u263b\u00b7"
        >>> sw.stm.getvalue()
        'Hello, world! ???\n'

    StreamWrapper converts all unicode strings that are written to it to the
    encoding defined in the wrapped stream's 'encoding' attribute, or, if that
    is None, to the locale encoding.  Typically the stream's encoding attribute
    is set when the stream is connected to a console device, and None when the
    stream is connected to a file.  On Unix systems the console encoding
    matches the locale charset, but on Win32 systems they differ.

        >>> s = StringIO()
        >>> s.encoding = 'ISO-8859-1'
        >>> sw = StreamWrapper(s)
        >>> print >> sw, u"Hello, world! \u00b7\u263b\u00b7"
        >>> sw.stm.getvalue()
        'Hello, world! \xb7?\xb7\n'

    You can print other kinds of objects:

        >>> sw = StreamWrapper(StringIO())
        >>> print >> sw, 1, 2,
        >>> print >> sw, 3
        >>> sw.stm.getvalue()
        '1 2 3\n'

    but not 8-bit strings:

        >>> sw = StreamWrapper(StringIO())
        >>> print >> sw, "\xff"
        Traceback (most recent call last):
          ...
        UnicodeDecodeError: 'ascii' codec can't decode byte 0xff in position 0: ordinal not in range(128)

    In addition to 'write', StreamWrapper provides 'flush' and 'writelines'

        >>> sw = StreamWrapper(StringIO())
        >>> sw.write('xyzzy\n')
        >>> sw.flush()
        >>> sw.writelines(['a', 'b', 'c', 'd'])
        >>> sw.stm.getvalue()
        'xyzzy\nabcd'

    Clean up:

        >>> common.locale_charset = old_locale_charset

    """

    def __init__(self, stm):
        self.stm = stm
        self.encoding = getattr(stm, 'encoding', None)
        if self.encoding is None:
            self.encoding = locale_charset

    def write(self, obj):
        self.stm.write(obj.encode(self.encoding, 'replace'))

    def flush(self):
        self.stm.flush()

    def writelines(self, seq):
        for obj in seq:
            self.write(obj)


class UnicodeAwareException(Exception):
    r"""Unicode-friendly exception.

    Sadly, the standard Python exceptions deal badly with Unicode strings:

        >>> e = ValueError(u"\u2639")
        >>> unicode(e)
        Traceback (most recent call last):
            ...
        UnicodeEncodeError: 'ascii' codec can't encode character u'\u2639' in position 0: ordinal not in range(128)

    UnicodeAwareException fixes this problem, so please subclass it for custom
    SchoolTool exceptions that might be shown to the user and therefore need
    to be internationalized.

        >>> e1 = UnicodeAwareException(u"\u2639")
        >>> unicode(e1)
        u'\u2639'

        >>> e2 = UnicodeAwareException(u"\u2639", e1)
        >>> unicode(e2)
        u'\u2639 \u2639'

    See also
    http://sf.net/tracker/?func=detail&aid=1012952&group_id=5470&atid=355470
    """

    def __unicode__(self):
        return u" ".join(map(unicode, self.args))


def looks_like_a_uri(uri):
    r"""Check if the argument looks like a URI string.

    Refer to http://www.ietf.org/rfc/rfc2396.txt for details.
    We're only approximating to the spec.

    Some examples of valid URI strings:

        >>> looks_like_a_uri('http://foo/bar?baz#quux')
        True
        >>> looks_like_a_uri('HTTP://foo/bar?baz#quux')
        True
        >>> looks_like_a_uri('mailto:root')
        True

    These strings are all invalid URIs:

        >>> looks_like_a_uri('2HTTP://foo/bar?baz#quux')
        False
        >>> looks_like_a_uri('\nHTTP://foo/bar?baz#quux')
        False
        >>> looks_like_a_uri('mailto:postmaster ')
        False
        >>> looks_like_a_uri('mailto:postmaster text')
        False
        >>> looks_like_a_uri('nocolon')
        False
        >>> looks_like_a_uri(None)
        False

    """
    uri_re = re.compile(r"^[A-Za-z][A-Za-z0-9+-.]*:\S\S*$")
    return bool(uri and uri_re.match(uri) is not None)


def unquote_uri(uri):
    r"""Unquote a URI.

       >>> unquote_uri('/terms/%C5%BEiema')
       u'/terms/\u017eiema'

       >>> unquote_uri(u'/terms/%C5%BEiema')
       u'/terms/\u017eiema'

    """
    return urllib.unquote(str(uri)).decode('UTF-8')


def collect(fn):
    """Convert a generator to a function that returns a list of items.

        >>> @collect
        ... def something(x, y, z):
        ...     yield x
        ...     yield y + z

        >>> something(1, 2, 3)
        [1, 5]

    """
    def collector(*args, **kw):
        return list(fn(*args, **kw))
    collector.__name__ = fn.__name__
    collector.__doc__ = fn.__doc__
    return collector


class IDateRange(Interface):
    """A range of dates (inclusive).

    If r is an IDateRange, then the following invariant holds:
    r.first <= r.last

    Note that empty date ranges cannot be represented.
    """

    first = Date(
        title=u"The first day of the period of time covered.")

    last = Date(
        title=u"The last day of the period covered.")

    def __iter__():
        """Iterate over all dates in the range from the first to the last."""

    def __contains__(date):
        """Return True if the date is within the range, otherwise False.

        Raises a TypeError if date is not a datetime.date.
        """

    def __len__():
        """Return the number of dates covered by the range."""


class DateRange(object):
    """A date range implementation using the standard datetime module.

    Date ranges are low-level components that represent a date
    span. They are mainly used to implement the date handling in
    terms:

      >>> january = DateRange(datetime.date(2003, 1, 1), datetime.date(2003, 1, 31))
      >>> IDateRange.providedBy(january)
      True

    You can use date ranges to check whether a certain date is within
    the range:

      >>> datetime.date(2002, 12, 31) in january
      False
      >>> datetime.date(2003, 2, 1) in january
      False
      >>> datetime.date(2003, 1, 1) in january
      True
      >>> datetime.date(2003, 1, 12) in january
      True
      >>> datetime.date(2003, 1, 31) in january
      True

    You can ask the date range for the amount of dates it includes.

      >>> days = list(january)
      >>> len(days)
      31
      >>> len(january)
      31

    As you can see, the boundary dates are inclusive. You can also
    iterate through all the dates in the date range.

      >>> days = DateRange(
      ...     datetime.date(2003, 1, 1), datetime.date(2003, 1, 2))
      >>> list(days)
      [datetime.date(2003, 1, 1), datetime.date(2003, 1, 2)]

      >>> days = DateRange(
      ...     datetime.date(2003, 1, 1), datetime.date(2003, 1, 1))
      >>> list(days)
      [datetime.date(2003, 1, 1)]

    If the beginning of the of the date range is later than the end, a
    value error is raised:

      >>> DateRange(datetime.date(2003, 1, 2),
      ...           datetime.date(2003, 1, 1)) # doctest: +NORMALIZE_WHITESPACE
      Traceback (most recent call last):
      ...
      ValueError: Last date datetime.date(2003, 1, 1) less than
                  first date datetime.date(2003, 1, 2)

    """
    implements(IDateRange)

    def __init__(self, first, last):
        self.first = first
        self.last = last
        if last < first:
            raise ValueError("Last date %r less than first date %r" %
                             (last, first))

    def __iter__(self):
        date = self.first
        while date <= self.last:
            yield date
            date += datetime.date.resolution

    def __len__(self):
        return (self.last - self.first).days + 1

    def __contains__(self, date):
        return self.first <= date <= self.last


_version = None

def get_version():
    global _version
    if _version is not None:
        return _version
    import os
    directory = os.path.split(__file__)[0]
    f = open(os.path.join(directory, 'version.txt'), 'r')
    result = f.read()
    _version = result
    f.close()
    return result

from zope.i18nmessageid import MessageFactory
SchoolToolMessage = MessageFactory("schooltool")