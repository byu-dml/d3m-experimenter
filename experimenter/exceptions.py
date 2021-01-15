class ExperimenterError(Exception):
    pass


class ServerError(ExperimenterError):
    pass


class InvalidStateError(ExperimenterError):
    pass


class NotImplementedError(ExperimenterError):
    pass


class InvalidArgumentValueError(ExperimenterError):
    pass
