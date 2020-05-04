local pdpipeline = import 'pdpipeline.jsonnet';
{
  "@type": "sklearn_worker",
  "random_seed": 0,
  "train_path": "./data/train.csv",
  "test_path": "./data/test.csv",
  "pdpipeline": pdpipeline,
  "model": {
    "@type": "lightgbm.LGBMClassifier",
    "boosting_type": "gbdt",
    "colsample_bytree": 0.7,
    "learning_rate": 0.01,
    "max_bin": 256,
    "max_depth": 4,
    "min_child_samples": 10,
    "min_child_weight": 1,
    "min_split_gain": 0.5,
    "n_estimators": 100,
    "objective": "binary",
    "num_leaves": 16,
    "random_state": 100,
    "reg_alpha": 0.5,
    "reg_lambda": 0.5,
    "scale_pos_weight": 1,
    "subsample": 0.9,
    "subsample_for_bin": 200,
    "subsample_freq": 1,
  },
  "validator": {
    "@type": "sklearn_cross_validator",
    "cv": 5,
    "scoring": {
      "accuracy": "accuracy",
      "precision": "precision_macro",
      "recall": "recall_macro",
      "fscore": "f1_macro"
    },
    "return_train_score": true
  }
}
