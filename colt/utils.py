import importlib
import pkgutil
import sys
import typing as tp


def import_submodules(package_name: str) -> None:
    """
    original code is here:
    https://github.com/allenai/allennlp/blob/v0.9.0/allennlp/common/util.py
    """
    importlib.invalidate_caches()

    sys.path.append(".")

    # Import at top level
    module = importlib.import_module(package_name)
    path = getattr(module, "__path__", [])
    path_string = "" if not path else path[0]

    for module_finder, name, _ in pkgutil.walk_packages(path):
        if path_string and getattr(module_finder, "path") != path_string:  # noqa: B009
            continue
        subpackage = f"{package_name}.{name}"
        import_submodules(subpackage)


def import_modules(module_names: tp.List[str]) -> None:
    """
    This method import modules recursively.
    You should call this method to register your classes
    if these classes are written on several files.
    """
    for module_name in module_names:
        import_submodules(module_name)


def indent(s: str, level: int = 1) -> str:
    tabs = "\t" * level
    return tabs + s.replace("\n", f"\n{tabs}")
