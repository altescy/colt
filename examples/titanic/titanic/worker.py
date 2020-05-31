import typing as tp
import os
import random

import colt
import numpy as np
import pandas as pd
import pdpipe as pdp
from sklearn.base import BaseEstimator
from sklearn.model_selection._search import BaseSearchCV

from titanic.logger import create_logger
from titanic.pdp.stages import PdpStage
from titanic.validator import SklearnValidator

logger = create_logger(__name__)


class Worker(colt.Registrable):
    def __init__(self, train_path: str, test_path: str,
                 random_seed: int) -> None:
        self._train_path = train_path
        self._test_path = test_path
        self._random_seed = random_seed

        random.seed(self._random_seed)
        np.random.seed(self._random_seed)

    def __call__(self):
        predictions = self.run()
        prediction_df = self.make_prediction_df(predictions)
        return prediction_df

    def prepare_data(self) -> tp.Tuple[pd.DataFrame, pd.DataFrame]:
        train_df = pd.read_csv(self._train_path)
        test_df = pd.read_csv(self._test_path)

        logger.info("datasets:")
        logger.info("%s:\n%s", self._train_path, train_df.info())
        logger.info("%s:\n%s", self._test_path, test_df.info())

        return train_df, test_df

    def make_prediction_df(self, predictions: np.ndarray) -> pd.DataFrame:
        test_df = pd.read_csv(self._test_path)

        output_df = pd.DataFrame()
        output_df["PassengerId"] = test_df["PassengerId"]
        output_df["Survived"] = predictions.astype(int)

        return output_df

    def run(self) -> np.ndarray:
        raise NotImplementedError


@Worker.register("sklearn_worker")
class SklearnWorker(Worker):
    def __init__(self, pdpipeline: PdpStage, model: BaseEstimator,
                 validator: SklearnValidator, train_path: str, test_path: str,
                 random_seed: int) -> None:
        super().__init__(train_path, test_path, random_seed)

        self.pdpipeline = pdpipeline
        self.model = model
        self.validator = validator

    def run(self) -> np.ndarray:
        print("run")
        train_df, test_df = self.prepare_data()

        logger.info("build ndarray")

        self.pdpipeline.fit(train_df)
        y_train = train_df.pop("Survived").to_numpy(dtype=np.float)
        X_train = self.pdpipeline.transform(train_df).to_numpy(dtype=np.float)
        X_test = self.pdpipeline.transform(test_df).to_numpy(dtype=np.float)

        logger.info("build model")

        model = self.model

        if isinstance(self.model, BaseSearchCV):
            grid = model

            logger.info("[ Parameter Search ] start parameter search")

            grid.fit(X_train, y_train)

            logger.info("[ Parameter Search ] best params: %s",
                        repr(grid.best_params_))
            logger.info("[ Parameter Search ] best score: %s",
                        repr(grid.best_score_))

            model = grid.best_estimator_

        logger.info("start training model")
        model.fit(X_train, y_train)

        logger.info("start validation: %s", repr(self.validator))

        scores = self.validator(model, X_train, y_train)
        score_mean = {key: val.mean() for key, val in scores.items()}
        score_std = {key: val.std() for key, val in scores.items()}

        for key in scores:
            mean = score_mean[key]
            std = score_std[key]
            logger.info("[ Score ]  %s : %f +/- %f", key, mean, std)

        predictions = model.predict(X_test)
        return predictions
