import typer

from meterapi.cli import db as db_cmd

app = typer.Typer(help="meterapi developer CLI")
app.add_typer(db_cmd.app, name="db", help="Database utilities")


if __name__ == "__main__":
    app()
