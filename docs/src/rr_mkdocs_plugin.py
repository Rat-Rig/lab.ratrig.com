import csv
from dataclasses import dataclass, field
import enum
from io import StringIO
from pprint import pprint
from pathlib import Path
from typing import List, Optional

from mkdocs.plugins import BasePlugin


class Plugin(BasePlugin):
    pass


@dataclass
class Item:
    name: str
    sku: str
    qty: int
    length: Optional[float]


@dataclass
class Product:
    name: str
    sku: str
    items: List[Item] = field(default_factory=list)

@dataclass
class CAD_Item:
    sku: str
    name: str
    filename: str
    image: str


def define_env(env):
    def generate_hardware_bom_tables(products):
        for index, product in enumerate(products):
            yield f""
            yield f"| SKU | Product name | QTY | Length (mm) |"
            yield f"| --- | ------------ | --- | ------ |"
            for item in product.items:
                length = item.length if item.length else ""
                sku = f"`{item.sku}`" if item.sku else ""
                yield f"| {sku} | {item.name} | {item.qty} | {length} |"

    @env.macro
    def hardware_bom(file_path: str):
        with open(Path(env.conf["docs_dir"]) / file_path, newline="") as csvfile:
            reader = csv.reader(csvfile, delimiter=",", quotechar='"')
            is_next_product = False
            is_next_item = False
            products = []
            for row in reader:
                if not any(row) or row[1].upper() == "B.O.M.":
                    continue
                elif row[4].upper() == "ITEM NAME":
                    is_next_item = True
                elif row[4].upper() == "PRODUCT NAME":
                    is_next_product = True
                    is_next_item = False
                    continue
                elif is_next_item:
                    item = Item(name=row[4], sku=row[1], qty=row[0], length=None)
                    if row[2]:
                        item.length = row[2]
                    products[-1].items.append(item)
                elif is_next_product:
                    products.append(Product(name=row[4], sku=row[1]))
                    is_next_product = False

        return "\n".join(generate_hardware_bom_tables(products))

    def get_filename(path):
        return path.strip('/').strip('\\').split('/')[-1].split('\\')[-1]

    def rr_cad_repo_generate_markdown(cad_db):
        yield f"| | | |"
        yield f"| :---: | :---: | :---: |"
        while cad_db:
            if len(cad_db) > 2:
                yield f"| [![](/cad/{cad_db[0].image})](/cad/{cad_db[0].filename})<br />**{cad_db[0].sku}**<br />{cad_db[0].name} | [![](/cad/{cad_db[1].image})](/cad/{cad_db[1].filename})<br />**{cad_db[1].sku}**<br />{cad_db[1].name} | [![](/cad/{cad_db[2].image})](/cad/{cad_db[2].filename})<br />**{cad_db[2].sku}**<br />{cad_db[2].name} |"
                cad_db = cad_db[3:]
            elif len(cad_db) > 1:
                yield f"| [![](/cad/{cad_db[0].image})](/cad/{cad_db[0].filename})<br />**{cad_db[0].sku}**<br />{cad_db[0].name} | [![](/cad/{cad_db[1].image})](/cad/{cad_db[1].filename})<br />**{cad_db[1].sku}**<br />{cad_db[1].name} | |"
                cad_db = cad_db[2:]
            elif len(cad_db) > 0:
                yield f"| [![](/cad/{cad_db[0].image})](/cad/{cad_db[0].filename})<br />**{cad_db[0].sku}**<br />{cad_db[0].name} | | |"
                cad_db = cad_db[1:]

    @env.macro
    def rr_cad_repo_build(subfolder: str, sortrepo=True):
        cad_files = Path(env.conf["docs_dir"] + "/cad/" + subfolder + "/").glob("*.step")
        cad_db = []

        for cad_file in cad_files:
            filename = get_filename(str(cad_file))
            t = filename.split("-", 1)
            sku = t[0]
            name = t[1].replace(".step","")
            filename = subfolder + "/" + filename
            cad_db.append(CAD_Item(sku, name, filename, filename.replace(".step", ".png")))
        if sortrepo:
            cad_db.sort(key=lambda x: x.name)
        return "\n".join(rr_cad_repo_generate_markdown(cad_db))

    @env.macro
    def printed_parts_bom_minimal(file_path: str):
        table = []
        table.append(f"| Name | QTY |")
        table.append(f"| ---- | --- |")
        with open(Path(env.conf["docs_dir"]) / file_path, newline="") as csvfile:
            reader = csv.reader(csvfile, delimiter=",", quotechar='"')
            for row in reader:
                table.append(
                    f"| {row[1]} | {row[2]} |"
                )

        return "\n".join(table)

    @env.macro
    def rr_build_project_entry(project: str, status: str, description: str):
        description = description.replace("\n","<br />")
        html = []
        html.append(f"<table>")
        html.append(f" <tr>")
        html.append(f"  <td width=\"520px\" rowspan=\"3\"><a href=\"/{project}/\"><img src=\"/assets/{project}/splash_thumb.png\"</a></td>")
        html.append(f"  <td><h3>Status:</h3></td>")
        html.append(f"  <td>{status}</td>")
        html.append(f" </tr>")
        html.append(f" <tr>")
        html.append(f"  <td><h3>Description:</h3></td>")
        html.append(f"  <td>{description}</td>")
        html.append(f" </tr>")
        html.append(f" <tr>")
        html.append(f"  <td><h3>Project&nbsp;Page:</h3></td>")
        html.append(f"  <td><a href=\"/{project}/\">Click here to view this project</a></td>")
        html.append(f" </tr>")
        html.append(f"</table>")
        return "\n".join(html)
