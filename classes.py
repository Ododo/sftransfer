
class FileTransfer:

    _port = None

    @property
    def port(self):
        return self._port

    def initialization(self, *args, **kwargs):
        pass

    def serve_file(self, *args, **kwargs):
        pass

    def get_file(self, *args, **kwargs):
        pass


class RendezVous:

    def __init__(self, token):
        self._token = token

    def initialization(self, *args, **kwargs):
        pass

    def register(self, *args, **kwargs):
        pass

    def retreive(self, *args, **kwargs):
        pass


class Exchange:

    def __init__(self, rdv, transfer):
        self._rdv = rdv
        self._transfer = transfer

    def register(self, *args, **kwargs):
        return self._rdv.register(*args, **kwargs)

    def serve(self, *args, **kwargs):
        self._transfer.serve_file(*args, **kwargs)

    def retreive(self, *args, **kwargs):
        return self._rdv.retreive(*args, **kwargs)

    def get(self, *args, **kwargs):
        return self._transfer.get_file(*args, **kwargs)

    @property
    def port(self):
        return self._transfer.port


__all__ = [RendezVous, FileTransfer, Exchange]
