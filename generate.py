import json
import os
from pathlib import Path

from jinja2 import Environment, FunctionLoader, StrictUndefined


def load_from_path(path: str) -> str:
    with open(path, "r") as file:
        return file.read()


env = Environment(
    loader=FunctionLoader(load_from_path), autoescape=True, undefined=StrictUndefined
)


def generate_templates(search_dir: Path, output_dir: Path, variables: Path) -> None:
    if variables.is_file():
        with variables.open() as file:
            data = json.load(file)
    else:
        data = {}

    index_path = search_dir / "index.html.j2"
    if index_path.is_file():
        output = env.get_template(str(index_path)).render(**data)
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_dir / "index.html", "w") as file:
            file.write(output)

    for path in os.listdir(search_dir):
        next_dir = search_dir / path
        if next_dir.is_dir():
            generate_templates(next_dir, output_dir / path, variables)


if __name__ == "__main__":
    root = Path("templates")
    output = Path("public")
    var = Path("vars.json")
    generate_templates(root, output, var)

    if var.is_file():
        with var.open() as file:
            data = json.load(file)
    else:
        data = {}

    if (root / "404.html.j2").is_file():
        outputs = env.get_template(str(root / "404.html.j2")).render(**data)
        with open(output / "404.html", "w") as file:
            file.write(outputs)
