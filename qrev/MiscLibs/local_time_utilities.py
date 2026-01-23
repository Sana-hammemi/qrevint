from datetime import datetime, timezone

def local_time_from_iso(time_str, utc_offset):

    # Covert iso to datetime object
    utc = datetime.fromisoformat(time_str)
    # Add UTC timezone to make datetime timezone aware
    utc = utc.replace(tzinfo=timezone.utc)
    # Get time zone
    tz = utc_offset_to_tz(utc_offset)
    # Compute local time
    time_local = utc.astimezone(tz)
    return time_local

def utc_offset_to_tz(utc_time_offset):

    if utc_time_offset is None:
        utc_time_offset = "00:00:00"
    offset = utc_time_offset
    if utc_time_offset[0] != "+" and utc_time_offset[0] != "-":
        if len(utc_time_offset) == 8:
            offset = "+" + utc_time_offset
        else:
            # DSM 20250625 Not sure what this code was intended to trap
            if len(utc_time_offset) > 3:
                tz_strip = utc_time_offset[3:]
                if len(tz_strip) <= 2:
                    offset = tz_strip[0] + '0' + tz_strip[1] + '00'
                else:
                    offset = utc_time_offset[3:] + '00'
            else:
                offset = "+" + utc_time_offset
    tz = datetime.strptime(offset, "%z").tzinfo
    return tz

def tz_formatted_string(serial_time, utc_time_offset, fmt):
    tz = utc_offset_to_tz(utc_time_offset)
    formatted_string = datetime.fromtimestamp(serial_time, tz=tz).strftime(fmt)
    return formatted_string