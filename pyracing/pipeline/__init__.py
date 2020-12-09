import abc


class Pipeline(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def put(self):
        pass
