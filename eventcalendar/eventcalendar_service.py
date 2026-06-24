import csv
from core.utility import csv_text

import codecs
import json
from datetime import datetime

from eventcalendar.models import EventCalendar
from core.models import Tenant


def import_event_calendar_csv_file(csv_file, tenant: Tenant):
    START_DATE_COL = 0
    END_DATE_COL = 1
    TYPE_COL = 2
    DESCROPTION_COL = 3

    created_count = 0
    option_reader = csv.reader(codecs.iterdecode(csv_file, 'utf-8'), delimiter=',')

    try:
        next(option_reader)  # Skip header row
    except StopIteration:
        return 0

    for row in option_reader:
        if any(field.strip() for field in row):
            # Parse CSV columns
            raw_start_date = row[START_DATE_COL].strip()
            raw_end_date = row[END_DATE_COL].strip()
            type = row[TYPE_COL].strip()
            description = row[DESCROPTION_COL].strip()

            if type == EventCalendar.PUBLIC_HOLIDAY:
                try:
                    clean_start_date = datetime.strptime(raw_start_date, '%Y-%m-%d').date()
                    clean_end_date = datetime.strptime(raw_end_date, '%Y-%m-%d').date()

                    obj, created = EventCalendar.objects.get_or_create(
                        start_date=clean_start_date,
                        end_date=clean_end_date,
                        type=type,
                        description=description,
                        tenant=tenant,
                        is_active=True,
                        create_by_id=1,
                        update_by_id=1
                    )

                    if created:
                        created_count += 1

                except (ValueError, IndexError):
                    continue

    return created_count