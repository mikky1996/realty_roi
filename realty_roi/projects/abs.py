import pandas as pd
from abc import ABC, abstractmethod


class Project(ABC):

    @abstractmethod
    def input_summary(self) -> str:
        """Returns a summary of the project. Used in the summary report"""
        raise NotImplementedError

    @abstractmethod
    def evaluate(self, years: int = 30) -> pd.DataFrame:
        """Show projects progress over time"""
        raise NotImplementedError
