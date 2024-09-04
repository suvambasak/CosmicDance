import pandas as pd

from cosmic_dance.io import fetch_from_url, read_CSV


class DST:
    '''Data attributes for Dst index'''

    TIMESTAMP = "TIMESTAMP"
    NANOTESLA = "nT"

    STARTTIME = "STARTTIME"
    ENDTIME = "ENDTIME"

    DURATION_HOURS = "DURATION_HOURS"


def get_Dst_in_range(df: pd.DataFrame, dfrom: pd.Timestamp, dto: pd.Timestamp) -> pd.DataFrame:
    '''Query the Dst index within given time range from the time series

    Params
    ------
    df: pd.DataFrame
        DataFrame of Dst indices
    dfrom: pd.Timestamp
        Start timestamp
    dto: pd.Timestamp
        End timestamp

    Returns
    -------
    DataFrame of Dst indices in given time window
    '''

    return df[df[DST.TIMESTAMP].between(dfrom, dto)]


def read_timespan_CSV(filename: str) -> pd.DataFrame:
    '''Reading the time window of Dst indices and window duration
    Generated by:
    - extract_timespan_above_nT_intensity
    - extract_timespan_between_nT_intensity

    Params
    ------
    filename: str
        CSV file of time window of Dst indices

    Returns
    -------
    DataFrame of time window and duration (hours)
    '''

    df = read_CSV(filename)

    df[DST.STARTTIME] = pd.to_datetime(df[DST.STARTTIME])
    df[DST.ENDTIME] = pd.to_datetime(df[DST.ENDTIME])

    # Window duration in hours
    return add_window_duration(df)


def merge_window(df: pd.DataFrame, days: int) -> pd.DataFrame:
    '''Merge two window closer then given days

    Params
    ------
    df: pd.DataFrame
        DataFrame of duration window
    days: int
        Time difference to merge two window

    Returns
    -------
    DataFrame of new time windows after merging
    '''

    del df[DST.DURATION_HOURS]
    events = df.to_dict(orient='records')

    # for event_id in range(len(events)-1):
    #     time_diff = (events[event_id+1].get("STARTTIME") -
    #                  events[event_id].get("ENDTIME"))/pd.Timedelta(days=1)
    #     if time_diff < 10:
    #         print(time_diff, events[event_id], events[event_id+1])

    merge_events = []

    # Traverse through the events
    for event in events:

        if len(merge_events) == 0:
            merge_events.append(event)

        # Time difference between two consecutive events
        time_diff = (
            event[DST.STARTTIME] - merge_events[-1][DST.ENDTIME]
        )/pd.Timedelta(days=1)

        # Update the previous event end time to next event end time (merge two event time)
        if time_diff < days:
            merge_events[-1][DST.ENDTIME] = event[DST.ENDTIME]

        else:
            merge_events.append(event)

    # Convert to DataFrame and add duration of new windows
    df = pd.DataFrame.from_dict(merge_events)
    return add_window_duration(df)


def add_window_duration(df: pd.DataFrame) -> pd.DataFrame:
    '''Adding the time window duration (in hours) column

    Params
    ------
    df: pd.DataFrame
        DataFrame of time window of Dst indices

    Returns
    -------
    DataFrame of time window with duration (hours)
    '''

    df[DST.DURATION_HOURS] = (
        df[DST.ENDTIME] - df[DST.STARTTIME]
    ) / pd.Timedelta(hours=1)

    return df


def extract_timespan_above_nT_intensity(df: pd.DataFrame, THRESHOLD: float) -> pd.DataFrame:
    '''Extract the above THRESHOLD intensity window from the Dst index time series

    Params
    ------
    df: pd.DataFrame
        Dst index time series
    THRESHOLD: float
        Intensity value (absolute)

    Returns
    -------
    DataFrame of time windows
    '''

    active_time_records = []
    stime = None
    etime = None

    # Traverse the time series and record the time window
    for timestamp, nT in zip(df[DST.TIMESTAMP], df[DST.NANOTESLA]):

        # Start widnow timestamp
        if (nT > THRESHOLD) and (stime is None):
            stime = timestamp
            # print(timestamp, nT, '\t START')

        # End window timestamp
        elif (nT < THRESHOLD) and (stime is not None) and (etime is None):
            etime = timestamp
            # print(timestamp, nT, '\t END')
        # else:
        #     print(timestamp, nT)

        # Recording one window and reset
        if (stime is not None) and (etime is not None):
            active_time_records.append({
                DST.STARTTIME: stime,
                DST.ENDTIME: etime
            })
            # print('RECORDED')

            stime, etime = None, None

    return pd.DataFrame.from_dict(active_time_records)


def extract_timespan_below_nT_intensity(df: pd.DataFrame, THRESHOLD: float) -> pd.DataFrame:
    '''Extract the below THRESHOLD intensity window from the Dst index time series

    Params
    ------
    df: pd.DataFrame
        Dst index time series
    THRESHOLD: float
        Intensity value (absolute)

    Returns
    -------
    DataFrame of time windows
    '''

    active_time_records = []
    stime = None
    etime = None

    # Traverse the time series and record the time window
    for timestamp, nT in zip(df[DST.TIMESTAMP], df[DST.NANOTESLA]):

        # Start widnow timestamp
        if (nT < THRESHOLD) and (stime is None):
            stime = timestamp
            # print(timestamp, nT, '\t START')

        # End window timestamp
        elif (nT > THRESHOLD) and (stime is not None) and (etime is None):
            etime = timestamp
            # print(timestamp, nT, '\t END')
        # else:
        #     print(timestamp, nT)

        # Recording one window and reset
        if (stime is not None) and (etime is not None):
            active_time_records.append({
                DST.STARTTIME: stime,
                DST.ENDTIME: etime
            })
            # print('RECORDED')

            stime, etime = None, None

    return pd.DataFrame.from_dict(active_time_records)


def extract_timespan_between_nT_intensity(df: pd.DataFrame, lb: int, ub: int) -> pd.DataFrame:
    '''Extract the given intensity window from the Dst index time series


    Params
    ------
    df: pd.DataFrame
        Dst index time series
    lb: int
        Lower bound of intensity (absolute)
    ub: int
        Upper bound of intensity (absolute)

    Returns
    -------
    DataFrame of time windows
    '''

    def in_range(v):
        'Is the given value within bound'

        if lb <= v and v <= ub:
            return True
        else:
            return False

    stime = None
    etime = None
    active_time_records = []

    # Traverse the time series and record the time window
    for timestamp, nT in zip(df[DST.TIMESTAMP], df[DST.NANOTESLA]):

        # Start widnow timestamp
        if in_range(nT) and (stime is None):
            stime = timestamp

        # End window timestamp
        elif not in_range(nT) and (stime is not None) and (etime is None):
            # etime = timestamp
            etime = _timestamp

        # Recording one window and reset
        if (stime is not None) and (etime is not None):
            active_time_records.append({
                DST.STARTTIME: stime,
                DST.ENDTIME: etime
            })

            stime, etime = None, None

        _timestamp = timestamp

    return pd.DataFrame.from_dict(active_time_records)


def read_dst_index_CSV(filename: str, abs_value: bool = True) -> pd.DataFrame:
    '''Read Dst indices from the CSV to a DataFrame

    Params
    ------
    filename: str
        Dst index CSV file
    abs_value: bool, optional
        Convert intensity to absolute values (Default absolute)

    Returns
    -------
    DataFrame of Dst index
    '''

    df = read_CSV(filename)
    df[DST.TIMESTAMP] = pd.to_datetime(df[DST.TIMESTAMP])

    if abs_value:
        df[DST.NANOTESLA] = df[DST.NANOTESLA].abs()

    return df


def parse_dst_index(urls: list[str]) -> pd.DataFrame:
    '''Request content from the given URLs in given order and generates a Dataframe with timestamp and intensity (nT)

    Params
    -------
    urls: list[str]
        List of URLs, in order (month wise)

    Returns
    -------
    pd.DataFrame: Dataframe of Dst index
    '''

    dst_index_records = []

    for id, url in enumerate(urls):
        print(f"|- ({id+1}/{len(urls)}): {url}")

        # Fetch and parse the content
        content = fetch_from_url(url)
        content = content.split('\n')[:-3]

        for line in content:

            # Extract Year, Month, Date
            yy = line[3:5]
            mm = line[5:7]
            dd = line[8:10]

            # Extract hourly value with timestamp
            h = 0
            for index in range(20, 116, 4):
                date = pd.to_datetime(
                    f"20{yy}-{mm}-{dd} {str(h).rjust(2, '0')}:00:00"
                )
                nT = int(line[index:index+4].strip())

                h += 1

                # Store the records
                dst_index_records.append({
                    DST.TIMESTAMP: date,
                    DST.NANOTESLA: nT
                })

    # create Dataframe
    return pd.DataFrame.from_dict(dst_index_records)
