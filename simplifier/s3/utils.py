
import time

import pytz


HTTP_HEADER_DATE_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'

def datetime_to_header(dt):
    return time.strftime(
        HTTP_HEADER_DATE_FORMAT,
        dt.replace(tzinfo=pytz.UTC).timetuple(),
    )
