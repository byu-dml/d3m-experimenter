class ExperimenterError(Exception):
    pass


class ServerError(ExperimenterError):
    pass


class InvalidStateError(ExperimenterError):
    pass
