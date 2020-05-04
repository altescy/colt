import typing as tp

import colt
import numpy as np
from sklearn.base import BaseEstimator
from sklearn.model_selection import cross_validate
from sklearn.model_selection import train_test_split


class SklearnValidator:
    def __call__(self, model: BaseEstimator, X: np.ndarray, y: np.ndarray):
        return self._validate(model, X, y)

    def _validate(self, model: BaseEstimator, X: np.ndarray,
                  y: np.ndarray) -> tp.Dict[str, np.ndarray]:
        raise NotImplementedError


@colt.register("sklearn_split_validator")
class SklearnSplitValidator(SklearnValidator):
    def __init__(self, **options):
        self._options = options

    def _validate(self, model: BaseEstimator, X: np.ndarray, y: np.ndarray):
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, **self._options)

        train_score = np.array(model.score(X_train, y_train))
        test_score = np.array(model.score(X_test, y_test))

        return {"train": train_score, "test": test_score}


@colt.register("sklearn_cross_validator")
class SklearnCrossValidator(SklearnValidator):
    def __init__(self, **options):
        self._options = options

    def _validate(self, model: BaseEstimator, X: np.ndarray, y: np.ndarray):
        return cross_validate(model, X, y, **self._options)
