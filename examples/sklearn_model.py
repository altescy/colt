import pob

from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import VotingClassifier
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC


pob.register("voting-classifier")(VotingClassifier)
pob.register("rfc")(RandomForestClassifier)
pob.register("svc")(SVC)


if __name__ == "__main__":
    config = {
        "@type": "voting-classifier",
        "estimators": [
            ("rfc", {"@type": "rfc", "n_estimators": 10}),
            ("svc", {"@type": "svc", "gamma": "scale"}),
        ]
    }

    iris = load_iris()
    X, y = iris.data, iris.target
    X_train, X_valid, y_train, y_valid = train_test_split(X, y)

    model = pob.build(config)
    model.fit(X_train, y_train)

    valid_accuracy = model.score(X_valid, y_valid)
    print(f"valid_accuracy: {valid_accuracy}")

