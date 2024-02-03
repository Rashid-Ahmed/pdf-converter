#!/usr/bin/ven python

from pathlib import Path
from pdf_converter.utils.process_eml import eml_to_pdf
from pdf_converter.utils.process_txt import txt_to_pdf
import logging
import typer

logger = logging.getLogger(__name__)
app = typer.Typer()


@app.command()
def eml2pdf(input_path: Path = typer.Argument(Path, help="Name and path of the eml file")
            , output_path: Path = typer.Argument(Path, help="Name and path of the output Pdf file")):
    input_bytes = open(input_path, "rb").read()
    parsed_bytes = eml_to_pdf(input_bytes)
    with open(output_path, "wb") as pdf_file:
        pdf_file.write(parsed_bytes)


@app.command()
def txt2pdf(input_path: Path = typer.Argument(Path, help="Name and path of the eml file")
            , output_path: Path = typer.Argument(Path, help="Name and path of the output Pdf file")):
    input_bytes = open(input_path, "rb").read()
    parsed_bytes = txt_to_pdf(input_bytes)
    with open(output_path, "wb") as pdf_file:
        pdf_file.write(parsed_bytes)


if __name__ == "__main__":
    app()
