"""Console entrypoint for Local AI Hub."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable

from app.cli import main as base_main
from app.model_packages import install_package_file
from app.session.modelstate import set_model


def _create_package(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="local-ai create")
    parser.add_argument("-f", "--file", required=True, help="path to LocalModel.yaml")
    parser.add_argument("--force", action="store_true", help="overwrite an existing package")
    parser.add_argument("--activate", action="store_true", help="set the package as active")
    args = parser.parse_args(argv)
    package = install_package_file(args.file, overwrite=args.force)
    print("Created LocalModel package")
    print(f"Name: {package.name}")
    print(f"Base: {package.base}")
    print(f"Path: {package.path}")
    if args.activate:
        print(set_model(package.name).strip())
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    args = list(argv) if argv is not None else sys.argv[1:]
    if args and args[0] == "create":
        return _create_package(args[1:])
    return base_main(args)


if __name__ == "__main__":
    raise SystemExit(main())
