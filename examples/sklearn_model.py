import typing as tp
import colt
import importlib

from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.base import BaseEstimator


@colt.register("sklearn-model", constructor="from_dict")
class SklearnModelWrapper:
    @classmethod
    def from_dict(cls, model_dict: tp.Dict[str, tp.Any]) -> BaseEstimator:
        model_path = model_dict.pop("@model")
        model_path = "sklearn." + model_path

        module_path, model_name = model_path.rsplit(".", 1)

        module = importlib.import_module(module_path)
        model_cls = getattr(module, model_name)

        if not issubclass(model_cls, BaseEstimator):
            raise ValueError(f"{model_path} is not an estimator")

        return model_cls(**model_dict)


if __name__ == "__main__":
    config = {
        "@type":
        "sklearn-model",
        "@model":
        "ensemble.VotingClassifier",
        "estimators": [
            ("rfc", {
                "@type": "sklearn-model",
                "@model": "ensemble.RandomForestClassifier",
                "n_estimators": 10
            }),
            ("svc", {
                "@type": "sklearn-model",
                "@model": "svm.SVC",
                "gamma": "scale"
            }),
        ]
    }

    X, y = load_iris(return_X_y=True)
    X_train, X_valid, y_train, y_valid = train_test_split(X, y)

    model = colt.build(config)
    model.fit(X_train, y_train)

    valid_accuracy = model.score(X_valid, y_valid)
    print(f"valid_accuracy: {valid_accuracy}")
