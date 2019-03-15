import sys
import time
from os import path
from functools import wraps
from contextlib import contextmanager
from traceback import format_exc

import click

from . import __version__
from .application import Mudkip
from .config import Config
from .errors import MudkipError


def print_version(ctx, _param, value):
    if not value or ctx.resilient_parsing:
        return
    click.secho(f"Mudkip v{__version__}", fg="blue")
    ctx.exit()


@click.group()
@click.option(
    "--version",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=print_version,
    help="Show the version and exit.",
)
def mudkip():
    """A friendly Sphinx wrapper."""


@contextmanager
def exception_handler(exit=False):
    try:
        yield
    except Exception as exc:
        error = exc.args[0] if isinstance(exc, MudkipError) else format_exc()
        click.secho(error, fg="red", bold=True)

        if exit:
            sys.exit(1)


def config_params(command):
    @click.option(
        "--source-dir",
        type=click.Path(file_okay=False),
        help="The source directory.",
        default=Config.default_source_dir,
    )
    @click.option(
        "--output-dir",
        type=click.Path(file_okay=False),
        help="The output directory.",
        default=Config.default_output_dir,
    )
    @click.option("--verbose", is_flag=True, help="Show Sphinx output.")
    @wraps(command)
    def wrapper(*args, **kwargs):
        return command(*args, **kwargs)

    return wrapper


@mudkip.add_command
@click.command()
@config_params
def build(source_dir, output_dir, verbose):
    """Build documentation."""
    padding = "\n" * verbose

    click.secho(f'Building "{source_dir}"...{padding}', fg="blue")

    application = Mudkip(Config(source_dir, output_dir, verbose))

    with exception_handler(exit=True):
        application.build()

    click.secho("\nDone.", fg="yellow")


@mudkip.add_command
@click.command()
@config_params
def develop(source_dir, output_dir, verbose):
    """Start development server."""
    padding = "\n" * verbose

    click.secho(f'Watching "{source_dir}"...{padding}', fg="blue")

    application = Mudkip(Config(source_dir, output_dir, verbose))

    with exception_handler():
        application.build()

    @contextmanager
    def build_manager(event_batch):
        now = time.strftime("%H:%M:%S")
        click.secho(f"{padding}{now}", fg="black", bold=True, nl=False)

        if len(event_batch) == 1:
            event = event_batch[0]
            filename = path.basename(event.src_path)
            click.echo(f" {event.event_type} {filename}{padding}")
        else:
            click.echo(f" {len(event_batch)} changes{padding}")

        with exception_handler():
            yield

    try:
        application.develop(build_manager)
    except KeyboardInterrupt:
        click.secho("\nExit.", fg="yellow")
