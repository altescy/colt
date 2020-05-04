kaggle Titanic Example
===

### 1. Prepare Dataset

```
$ make dataset
$ ls data
gender_submission.csv  test.csv  train.csv
```

### 2. Write Configurations

- Create features by using [pdpipe](https://pdpipe.github.io/pdpipe/): [`configs/pdpipeline.jsonnet`](https://github.com/altescy/colt/blob/master/examples/titanic/configs/pdpipeline.jsonnet)
- Configure [`SklearnWorker`](https://github.com/altescy/colt/blob/master/examples/titanic/titanic/worker.py#L56-L111): [`configs/lgbm.jsonnet`](https://github.com/altescy/colt/blob/master/examples/titanic/configs/lgbm.jsonnet)

### 3. Train Model and Make Predictions

```
$ make run
$ head submit.csv
PassengerId,Survived
892,0
893,1
894,0
895,0
896,1
897,0
898,1
899,0
900,1
```
