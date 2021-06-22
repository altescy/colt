import re
import typing as tp

import numpy as np
import pdpipe as pdp
from titanic.pdp.stages import PdpStage

import colt


@PdpStage.register("add_family_size")
class AddFamilySize(pdp.ApplyToRows):
    @staticmethod
    def compute_family_size(row):
        return row["SibSp"] + row["Parch"] + 1

    def __init__(self, name: str = None):
        super().__init__(
            self.compute_family_size,
            name or "FamilySize",
        )


@PdpStage.register("add_is_alone")
class AddIsAlone(pdp.ApplyToRows):
    @staticmethod
    def compute_is_alone(row):
        return (row["SibSp"] + row["Parch"]) == 0

    def __init__(self, name: str = None):
        super().__init__(
            self.compute_is_alone,
            name or "IsAlone",
        )


@PdpStage.register("add_name_title")
class AddNameTitle(pdp.ApplyToRows):
    DEFAULT_TITILES = {
        "Capt": "Officer",
        "Col": "Officer",
        "Major": "Officer",
        "Jonkheer": "Sir",
        "Don": "Sir",
        "Sir": "Sir",
        "Dr": "Dr",
        "Rev": "Rev",
        "theCountess": "Lady",
        "Dona": "Lady",
        "Mme": "Mrs",
        "Mlle": "Miss",
        "Ms": "Mrs",
        "Mr": "Mr",
        "Mrs": "Mrs",
        "Miss": "Miss",
        "Master": "Master",
        "Lady": "Lady",
    }

    def __init__(self, name: str = None, titles: tp.Dict[str, str] = None):
        super().__init__(
            self.compute_nametitle,
            name or "NameTitle",
        )
        self._titles = titles or self.DEFAULT_TITILES

    def compute_nametitle(self, row):
        title = re.findall(r", (\w+)\.", row["Name"])
        title = "" if len(title) < 1 else title[0]
        return self._titles.get(title, "other")


@PdpStage.register("add_cabin_category")
class AddCabinCategory(pdp.ApplyToRows):
    @staticmethod
    def compute_cabin_category(row):
        cabin = row["Cabin"]
        category = cabin[0] if isinstance(cabin, str) else np.NaN
        return category

    def __init__(self, name: str = None):
        super().__init__(
            self.compute_cabin_category,
            name or "CabinCategory",
        )


@PdpStage.register("add_deck")
class AddDeck(pdp.ApplyToRows):
    @staticmethod
    def compute_deck(row):
        cabin = row["Cabin"]
        if isinstance(cabin, str):
            deck = cabin[0]
            if deck in "ABC":
                deck = "ABC"
            elif deck in "DE":
                deck = "DE"
            elif deck in "FG":
                deck = "FG"
        else:
            deck = np.NaN
        return deck

    def __init__(self, name: str = None):
        super().__init__(
            self.compute_deck,
            name or "Deck",
        )
