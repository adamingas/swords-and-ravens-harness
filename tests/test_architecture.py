import ast

from raven_harness.config import PROJECT_ROOT


def test_server_and_harness_do_not_depend_on_evaluation_policy() -> None:
    production_paths = [
        PROJECT_ROOT / "src/raven_harness/app.py",
        PROJECT_ROOT / "src/raven_harness/manager.py",
        *sorted((PROJECT_ROOT / "src/raven_harness/harness").glob("*.py")),
    ]
    policy_names = {
        "PROMPT_CONFIGURATIONS",
        "house_rotation",
        "user_rotation",
        "summarize_results",
    }

    for path in production_paths:
        source = path.read_text()
        tree = ast.parse(source)
        imported_names = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        imported_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        defined_names = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        }

        assert not any(
            name == "evaluation" or name.endswith(".evaluation")
            for name in imported_names | imported_modules
        )
        assert not policy_names.intersection(imported_names | defined_names)
        assert "elo" not in source.casefold()


def test_evaluation_policy_stays_in_evaluation_modules() -> None:
    evaluator = (PROJECT_ROOT / "src/raven_harness/evaluation.py").read_text()

    for name in (
        "PROMPT_CONFIGURATIONS",
        "house_rotation",
        "user_rotation",
        "summarize_results",
    ):
        assert name in evaluator
