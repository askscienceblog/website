import base64
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Annotated, Callable

from bs4 import BeautifulSoup
from jinja2 import Environment, FunctionLoader, StrictUndefined
from markupsafe import Markup
from pydantic import BaseModel, Field

from prng import pseudoRandom

CONFIG_JSON = re.compile(r"{#(?:\+|-)*\s*({.*?})\s*(?:\+|-)*#}", re.DOTALL)
RANDOM = pseudoRandom("ayrj.org")


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


def render_template(
    template_path: str,
    output_dir: str,
    post_processing: Callable[[str], str] = lambda x: x,
) -> None:
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
            file.write(post_processing(output))


def pandoc(
    value,
    arguments=["-f", "markdown", "-t", "html"],
):
    res = subprocess.run(
        ["pandoc"] + arguments,
        capture_output=True,
        text=True,
        encoding="utf-8",
        input=value,
    )
    print(res.stderr)
    return Markup(res.stdout)


env.filters["pandoc"] = pandoc


def censor_addresses(html: str) -> str:
    soup = BeautifulSoup(html, "html5lib")
    for address in soup.find_all("address"):
        inner_html = address.encode_contents(encoding="utf-8")
        scrambled = bytes(
            a ^ b for a, b in zip(RANDOM.randBytes(len(inner_html)), inner_html)
        )
        address.string = (
            "Contact information is protected. Please enable JavaScript to view."
        )
        address["enc-addr"] = base64.b64encode(scrambled).decode("utf-8")

    return soup.prettify()


if __name__ == "__main__":
    for entry in os.scandir("templates"):
        if entry.is_file():
            render_template(entry.path, "public", censor_addresses)
