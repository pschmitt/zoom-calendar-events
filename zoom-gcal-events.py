#!/usr/bin/env python

import argparse
import json
import os
import sys
from datetime import datetime, timedelta

from appdirs import user_config_dir
from gcsa.google_calendar import GoogleCalendar
from exchangelib import Credentials, Account, EWSDate, EWSDateTime
from exchangelib.folders import Calendar


def parse_args():
    parser = argparse.ArgumentParser()
    # parser.set_defaults(backend="gcal")
    parser.add_argument(
        "--calendar-filter", "-f", default="work: ", help="Calendar name filter"
    )
    parser.add_argument(
        "--prior",
        "-p",
        type=int,
        default=1,
        help="Include meetings that started X hours ago",
    )
    parser.add_argument(
        "--after",
        "-a",
        type=int,
        default=8,
        help="Include meetings that start in X hours in the future",
    )
    parser.add_argument(
        "--with-url",
        "-w",
        action="store_true",
        default=False,
        help="Only return meetings that have a zoom link set as the location",
    )

    subparsers = parser.add_subparsers(
        help="Backend: google or exchange", dest="backend", required=True
    )

    gcal_parser = subparsers.add_parser("gcal", help="Google Calendar backend")
    default_config_path = os.environ.get(
        "GCSA_CREDENTIALS",
        os.path.join(user_config_dir("gcsa"), "credentials.json"),
    )
    gcal_parser.add_argument(
        "-c",
        "--credentials_path",
        default=default_config_path,
        help="Path to file holding the gcal credentials (JSON)",
    )

    exchange_parser = subparsers.add_parser(
        "exchange", help="Microsoft Exchange backend"
    )
    exchange_parser.add_argument("-e", "--email", required=False, help="Email")
    exchange_parser.add_argument("-u", "--username", required=True, help="Username")
    exchange_parser.add_argument("-p", "--password", required=True, help="Password")

    return parser.parse_args()


def gcal_get_current_zoom_meetings(
    credentials_path,
    cal_name_filter="work: ",
    hours_prior=1,
    hours_after=8,
    only_with_url=True,
):
    calendar = GoogleCalendar(credentials_path=credentials_path)

    cals = calendar.service.calendarList().list().execute()

    # Find all work calendar and store them in work_cals
    work_cals = []

    for c in cals.get("items"):
        name = c.get("summaryOverride")
        if name and name.lower().startswith(cal_name_filter):
            work_cals.append(c.get("id"))

    # Search for zoom events
    events = []
    now = datetime.now()
    start_date = now - timedelta(hours=hours_prior)
    end_date = now + timedelta(hours=hours_after)

    location_filter = "zoom.us" if only_with_url else "zoom"
    for cal_id in work_cals:
        work_calendar = GoogleCalendar(
            calendar=cal_id, credentials_path=credentials_path
        )
        current_events = work_calendar.get_events(
            time_min=start_date, time_max=end_date
        )
        for ev in current_events:
            loc = ev.location
            if loc and location_filter in loc.lower():
                events.append(ev)

    data = []
    for ev in events:
        e = {
            "summary": ev.summary,
            "start": str(ev.start),
            "end": str(ev.end),
            "location": ev.location,
        }
        data.append(e)
    print(json.dumps(data))


def exchange_get_current_zoom_meetings(
    username,
    password,
    email=None,
    cal_name_filter="work: ",
    hours_prior=1,
    hours_after=8,
    only_with_url=True,
):
    # email defaults to the value of username
    email = email if email else username
    credentials = Credentials(username, password)
    account = Account(email, credentials=credentials, autodiscover=True)
    calendars = [x for x in account.calendar.children] + [account.calendar]

    now = datetime.now(tz=account.default_timezone)
    start_date = now - timedelta(hours=hours_prior)
    end_date = now + timedelta(hours=hours_after)

    today = datetime.today()
    tomorrow = today + timedelta(days=1)
    midnight_today = datetime.combine(
        today, datetime.min.time(), tzinfo=account.default_timezone
    )
    midnight_tomorrow = datetime.combine(
        tomorrow, datetime.min.time(), tzinfo=account.default_timezone
    )

    current_events = []

    location_filter = "zoom.us" if only_with_url else "zoom"
    for cal in calendars:
        # print(f"Processing calendar {cal}")
        for ev in cal.all().filter(start__range=(start_date, end_date)):
            loc = ev.location
            if not loc or location_filter not in loc.lower():
                continue

            current_events.append(ev)

    data = []
    for ev in current_events:
        if isinstance(ev.start, EWSDate):
            start = midnight_today
            end = midnight_tomorrow
        else:
            start = datetime.fromtimestamp(int(ev.start.timestamp()))
            end = datetime.fromtimestamp(int(ev.end.timestamp()))
        ev_data = {
            "summary": ev.subject,
            "start": str(ev.start),
            "end": str(ev.end),
            "location": ev.location,
        }
        data.append(ev_data)

    print(json.dumps(data))


def main():
    args = parse_args()
    if args.backend == "gcal":
        gcal_get_current_zoom_meetings(
            credentials_path=args.credentials_path,
            cal_name_filter=args.calendar_filter,
            hours_prior=args.prior,
            hours_after=args.after,
            only_with_url=args.with_url,
        )
    elif args.backend == "exchange":
        exchange_get_current_zoom_meetings(
            email=args.email,
            username=args.username,
            password=args.password,
            cal_name_filter=args.calendar_filter,
            hours_prior=args.prior,
            hours_after=args.after,
            only_with_url=args.with_url,
        )
    else:
        print(f"Unsupported backend: {args.backend}", file=sys.stderr)


if __name__ == "__main__":
    main()
