import colt

from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split

if __name__ == "__main__":
    config = {
        "@type":
        "sklearn.ensemble.VotingClassifier",
        "estimators": [
            ("rfc", {
                "@type": "sklearn.ensemble.RandomForestClassifier",
                "n_estimators": 10
            }),
            ("svc", {
                "@type": "sklearn.svm.SVC",
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
