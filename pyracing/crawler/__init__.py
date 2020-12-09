import abc

from typing import Dict


class Crawler(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_horses(self) -> Dict[str, str]:
        pass

    @abc.abstractmethod
    def get_games(self, game_date: str):
        pass


from .CrawlerHKJC import CrawlerHKJC
