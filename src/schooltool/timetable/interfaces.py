#
# SchoolTool - common information systems platform for school administration
# Copyright (c) 2005 Shuttleworth Foundation
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
Schedule and timetabling interfaces
"""

import pytz

import zope.schema
from zope.interface import Interface, Attribute
from zope.container.constraints import contains
from zope.container.interfaces import IContainer, IOrderedContainer
from zope.container.interfaces import IContained

from schooltool.app.interfaces import ISchoolToolCalendarEvent
from schooltool.app.utils import vocabulary

from schooltool.common import SchoolToolMessage as _


#
#  Schedule
#

activity_types = vocabulary(
    [("lesson", _("Lesson")),
     ("homeroom", _("Homeroom")),
     ("free", _("Free")),
     ("lunch", _("Lunch")),
     ])


class IPeriod(IContained):
    """A period of activity."""

    title = zope.schema.TextLine(
        title=u"Title of the period.",
        required=False)

    activity_type = zope.schema.Choice(
        title=_("Activity type."),
        required=True,
        default="lesson",
        vocabulary=activity_types)


class IMeeting(Interface):
    """A meeting represents a lesson or other scheduled activity."""

    dtstart = zope.schema.Datetime(
        title=u"Time of the start of the event",
        required=True)

    duration = zope.schema.Timedelta(
        title=u"Timedelta of the duration of the event",
        required=True)

    period = zope.schema.Object(
        title=u"The period to schedule.",
        schema=IPeriod,
        required=False)

    meeting_id = zope.schema.TextLine(
        title=u"Unique identifier of a meeting (lesson)",
        description=u"""
        The meeting_id is an arbitrary identifier of a meeting (lesson),
        the intended use is to mark meetings that are scheduled over several
        periods.
        """,
        required=False)


class ISchedule(Interface):
    """A schedule of meetings."""

    title = zope.schema.TextLine(
        title=u"Title of the timetalbe.",
        required=True)

    first = zope.schema.Date(
        title=u"First scheduled day.",
        required=True)

    last = zope.schema.Date(
        title=u"Last scheduled day.",
        required=True)

    timezone = zope.schema.Choice(
        title=_("Time Zone"),
        description=_("Meetings time zone."),
        values=pytz.common_timezones)

    def iterMeetings(date, until_date):
        """Yields lists of meetings for the given date range."""


class ISelectedPeriodsSchedule(ISchedule):
    """Schedule composed of meetings from another schedule with
    selected periods only."""

    schedule = zope.schema.Object(
        title=u"Schedule to filter meetings from.",
        schema=ISchedule,
        required=False)

    periods = Attribute(
        """Iterate only over meetings for these periods.""")


class IScheduleContainer(IContainer, ISchedule):
    """A container of schedules.

    The container itself is as a big composite schedule.
    """
    contains(ISchedule)

#
#  Day templates
#

class IDayTemplate(IOrderedContainer):
    title = zope.schema.TextLine(
        title=u"Title of the day.",
        required=False)


class IDayTemplateContainer(IOrderedContainer):
    """Ordered container of day templates."""
    contains(IDayTemplate)

    factory = Attribute("The template factory.")


class IDayPeriodsTemplate(IDayTemplate):
    contains(IPeriod)


class IPeriodTemplateContainer(IDayTemplateContainer):
    contains(IDayPeriodsTemplate)


class ITimeSlot(IContained):
    """Time slot designated for an activity."""

    tstart = zope.schema.Time(
        title=u"Time of the start of the event",
        required=True)

    duration = zope.schema.Timedelta(
        title=u"Timedelta of the duration of the event",
        required=True)

    activity_type = zope.schema.Choice(
        title=_("Activity type"),
        required=True,
        default="lesson",
        vocabulary=activity_types)


class IDayTimeSlotsTemplate(IDayTemplate):
    contains(ITimeSlot)


class ITimeSlotTemplateContainer(IDayTemplateContainer):
    contains(IDayTimeSlotsTemplate)


class ITimePeriod(IPeriod, ITimeSlot):
    """A period with additional scheduling information."""


class IDayScheduleTemplate(IDayTemplate):
    contains(ITimePeriod)


class IDayScheduleTemplateContainer(IDayTemplateContainer):
    contains(IDayScheduleTemplate)


class IDayTemplateSchedule(IContained):
    """Day templates scheduled for some dates."""

    templates = zope.schema.Object(
        title=u"The template container.",
        schema=IDayTemplateContainer,
        required=True)

    def iterDates(dates):
        """Yield day templates for given dates."""


class ICalendarDayTemplates(IDayTemplateSchedule):
    """Day templates."""

    starting_index = zope.schema.Int(
        title=u"Starting date should start as Nth day",
        default=0,
        required=True)

    def getDay(schedule, date):
        """Get template for the given date."""


class IWeekDayTemplates(IDayTemplateSchedule):
    """Iterator of day templates."""

    def getWeekDayKey(weekday):
        """Get weekday template container key."""

    def getWeekDay(weekday):
        """Get weekday template."""


class ISchooldays(Interface):
    """XXX: should be moved to term, as schooldays are defined there."""

    def iterDates(dates):
        """Iterate dates that are schooldays."""

    def __iter__():
        """Yield all schoolday dates."""

    def __contains__(date):
        """Return whether the date is a schoolday."""


class ISchoolDayTemplates(IDayTemplateSchedule):
    """Iterator that rotates on schooldays (as opposed to rotating on
    calendar days)"""

    starting_index = zope.schema.Int(
        title=u"Starting date should start as Nth day",
        default=0,
        required=True)


#
#  Timetabling
#


class ITimetableSchedule(ISchedule):
    """The schedule of meetings built from day templates."""

    periods = zope.schema.Object(
        title=u"Periods.",
        schema=IDayTemplateSchedule,
        required=True)


class IWeeklyTimetableSchedule(ITimetableSchedule):
    """The schedule of a weekly timetable."""

    periods = zope.schema.Object(
        title=u"Periods.",
        schema=IWeekDayTemplates,
        required=True)


class IRotatingTimetableSchedule(ITimetableSchedule):
    """The schedule of a rotating timetable."""

    periods = zope.schema.Object(
        title=u"Periods.",
        schema=ISchoolDayTemplates,
        required=True)


#
#  Calendar
#


class IScheduledCalendarEvent(IMeeting, ISchoolToolCalendarEvent):
    """Calendar event that forms a schedule."""

    schedule = zope.schema.Object(
        title=u"Schedule that generated this event.",
        schema=ISchedule,
        required=False)
