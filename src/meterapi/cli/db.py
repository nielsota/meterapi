import typer
from sqlalchemy import text

from meterapi.db import get_engine_for_cli

app = typer.Typer(help="Database utilities")


@app.command()
def ping() -> None:
    """Open a connection and run SELECT 1."""
    engine = get_engine_for_cli()
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar_one()
    except Exception as exc:
        typer.secho(f"connection failed: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    url = engine.url
    typer.secho(
        f"ok — {url.username}@{url.host}:{url.port}/{url.database} (SELECT 1 -> {result})",
        fg=typer.colors.GREEN,
    )
