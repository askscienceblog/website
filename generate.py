import json
import os
import re
import subprocess
from pathlib import Path
from typing import Annotated

from jinja2 import Environment, FunctionLoader, StrictUndefined
from markupsafe import Markup
from pydantic import BaseModel, Field
from bs4 import BeautifulSoup

CONFIG_JSON = re.compile(r"{#(?:\+|-)*\s*({.*?})\s*(?:\+|-)*#}", re.DOTALL)


class RenderVariable(BaseModel):
    namespace: str
    path: Path


class TemplateOptions(BaseModel):
    read_from: Path | None = None
    write_to: list[Annotated[str, Field(pattern=r"[a-zA-Z0-9.\-_~]*")]] = []
    file_extension: str = Field(default="", pattern=r"^$|^\..*")
    variables: list[RenderVariable] = []


def load_from_path(path: str) -> str:
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


env = Environment(
    loader=FunctionLoader(load_from_path), autoescape=True, undefined=StrictUndefined
)


def render_template(template_path: str, output_dir: str) -> None:
    # load config
    with open(template_path, "r") as file:
        template = file.read()
    mat = CONFIG_JSON.search(template)
    if mat is None:
        mat = r"{}"
    else:
        mat = mat.group(1)

    options = TemplateOptions.model_validate_json(mat)
    if options.read_from is None:  # return if no need to render
        return

    var = {}
    for vars in options.variables:
        with vars.path.open("r", encoding="utf-8") as file:
            var[vars.namespace] = json.load(file)

    for entry in os.scandir(options.read_from):
        if not entry.is_file():
            continue

        with open(entry, "r", encoding="utf-8") as file:
            var.update(json.load(file))

        filename = os.path.splitext(os.path.basename(entry))[0] + options.file_extension
        output = env.get_template(template_path).render(**var)
        os.makedirs(os.path.join(output_dir, *options.write_to), exist_ok=True)
        with Path(output_dir, *options.write_to, filename).open(
            "w", encoding="utf-8"
        ) as file:
            file.write(output)


def pandoc(
    value,
    arguments=["-f", "markdown", "-t", "html"],
):
    return Markup(
        subprocess.run(
            ["pandoc"] + arguments,
            capture_output=True,
            text=True,
            encoding="utf-8",
            input=value,
        ).stdout
    )


def content_list(article_html):
    soup = BeautifulSoup(article_html, "html5lib")
    tag_level = 0
    output = ""
    for tag in soup.find_all(["h2", "h3", "h4", "h5", "h6"]):
        heading = int(tag.name[1]) - 1
        if heading > tag_level:
            output += "<li><ol>" * (heading - tag_level)
        elif heading < tag_level:
            output += "</ol></li>" * (tag_level - heading)

        output += f"<li>{tag.get_text()}</li>"
        tag_level = heading

    output += "</ol></li>" * (tag_level)

    return Markup(output[4:-5])


env.filters["pandoc"] = pandoc
env.filters["content_list"] = content_list

if __name__ == "__main__":
    for entry in os.scandir("templates"):
        if entry.is_file():
            render_template(entry.path, "public")
