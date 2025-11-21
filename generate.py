from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from pathlib import Path
import json
import os

env = Environment(loader=FileSystemLoader(""), autoescape=True)



def generate_templates(search_dir: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    dir = search_dir / "variables.json"
    if dir.is_file():
        with dir.open() as file:
            data = json.load(file)
    else:
        data = {}

    index_path = search_dir / "index.html.j2"
    if index_path.is_file():
        output = env.get_template(str(index_path)).render(**data)
        with open(output_dir / "index.html", "w") as file:
            file.write(output)

    for path in os.listdir(search_dir):
        next_dir = search_dir / path
        if next_dir.is_dir():
            generate_templates(next_dir, output_dir / path)


if __name__ == "__main__":
    main()
