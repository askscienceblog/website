import json
import os
import re

from jinja2 import Environment, FunctionLoader, StrictUndefined
from pydantic import BaseModel, Field

CONFIG_JSON = re.compile(r"{#(?:\+|-)*\s*({.*?})\s*(?:\+|-)*#}", re.DOTALL)


class TemplateOptions(BaseModel):
    copies: list[str] = []
    extension: str = Field(default="", pattern=r"^$|^\..*")


def load_from_path(path: str) -> str:
    with open(path, "r") as file:
        return file.read()


env = Environment(
    loader=FunctionLoader(load_from_path), autoescape=True, undefined=StrictUndefined
)


def generate_templates(search_dir: str, output_dir: str) -> None:
    for entry in os.scandir(search_dir):
        if entry.is_file() and os.path.splitext(entry)[1] == ".j2":
            with open(entry, "r") as file:
                text = file.read()
            mat = CONFIG_JSON.search(text)
            if mat is None:
                mat = r"{}"
            else:
                mat = mat.group(1)

            options = TemplateOptions.model_validate_json(mat)
            for copy in options.copies:
                with open(copy, "r") as file:
                    var = json.load(file)

                filename = os.path.splitext(os.path.basename(copy))[0]
                output = env.get_template(entry.path).render(**var)

                os.makedirs(output_dir, exist_ok=True)
                with open(
                    os.path.join(output_dir, filename + options.extension), "w"
                ) as file:
                    file.write(output)

        if entry.is_dir():
            generate_templates(entry.path, os.path.join(output_dir, entry.name))


if __name__ == "__main__":
    generate_templates("templates", "public")
