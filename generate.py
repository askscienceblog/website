import json
import os
from pathlib import Path

from jinja2 import Environment, FunctionLoader


def load_from_path(path: str) -> str:
    with open(path, "r") as file:
        return file.read()


env = Environment(loader=FunctionLoader(load_from_path), autoescape=True)


def generate_templates(search_dir: Path, output_dir: Path) -> None:
    dir = search_dir / "variables.json"
    if dir.is_file():
        with dir.open() as file:
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
            generate_templates(next_dir, output_dir / path)


if __name__ == "__main__":
    generate_templates(Path("templates"), Path("public"))
