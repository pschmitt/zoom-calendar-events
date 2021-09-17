#!/usr/bin/env python

import argparse
import json
import os
from datetime import datetime, timedelta

from appdirs import user_config_dir
from gcsa.google_calendar import GoogleCalendar


def parse_args():
    parser = argparse.ArgumentParser()
    default_config_path = os.environ.get(
        "GCSA_CREDENTIALS",
        os.path.join(user_config_dir("gcsa"), "credentials.json"),
    )
    parser.add_argument(
        "-c",
        "--credentials_path",
        default=default_config_path,
        help="Path to file holding the gcal credentials (JSON)",
    )
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
    return parser.parse_args()


def get_current_zoom_meetings(
    credentials_path,
    cal_name_filter="work: ",
    hours_prior=1,
    hours_after=1,
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


def main():
    args = parse_args()
    get_current_zoom_meetings(
        credentials_path=args.credentials_path,
        cal_name_filter=args.calendar_filter,
        hours_prior=args.prior,
        hours_after=args.after,
        only_with_url=args.with_url,
    )


if __name__ == "__main__":
    main()
