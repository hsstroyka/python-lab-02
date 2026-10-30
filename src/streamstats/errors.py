class StreamStatsError(Exception):
    pass


class UnsupportedFormatError(StreamStatsError):
    pass


class InvalidEventError(StreamStatsError):
    pass


class InvalidTimestampError(InvalidEventError):
    pass


class CLIConfigError(StreamStatsError):
    pass