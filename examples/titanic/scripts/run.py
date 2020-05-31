import argparse

import colt

from titanic.utils.jsonnet import load_jsonnet
from titanic.worker import Worker


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--module", action="append", default=[])
    parser.add_argument("--output")
    args = parser.parse_args()

    config = load_jsonnet(args.config)

    print(config)

    colt.import_modules(args.module)
    worker = colt.build(config, Worker)

    predictions = worker()

    if args.output:
        predictions.to_csv(args.output, index=False)


if __name__ == "__main__":
    main()
