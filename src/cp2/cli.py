import rich_click as click

from pathlib import Path
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table
from rich.box import HORIZONTALS

from .interactive import interactive
from .interactive_fzf import interactive_fzf
from .cp2_config import CP2Config

cp2_config = CP2Config()
console = Console()


@click.group()
def main():
    """CP2 - Easy to copy files or directories."""
    pass


@main.group()
def mark():
    """Manage mark bookmarks."""
    pass


@mark.command("add")
@click.argument("path")
@click.argument("name")
@click.argument("desc", required=False)
@click.option("-n", "--name", help="Name of the mark")
@click.option("-p", "--path", help="Path for the mark")
@click.option("-d", "--desc", help="Description for the mark")
def mark_add(path, name, desc, **options):
    """Add a new mark bookmark."""

    # Use option values if provided, otherwise use positional arguments
    final_path = options.get("path") or path
    final_name = options.get("name") or name
    final_desc = options.get("desc") or desc

    if cp2_config.has_mark(final_name):
        if not Confirm.ask(
            f"[yellow]Warning: Mark '{final_name}' already exists. Do you want to overwrite it?[/]"
        ):
            return

    # Validate the path
    resolve_path = Path(final_path).resolve()
    if not resolve_path.exists():
        console.print(f"[red]Error:[/] Path '{final_path}' does not exist.")
        return

    if not resolve_path.is_dir():
        console.print(f"[red]Error:[/] Path '{final_path}' is not a directory.")
        return

    # Add the mark to the configuration
    cp2_config.add_mark(final_name, str(resolve_path), final_desc)

    console.print(
        f"Adding mark '{final_name}' with path '{final_path}' and description '{final_desc}'"
    )


@mark.command("remove")
@click.argument("name")
def mark_remove(name):
    """Remove a mark bookmark by name."""

    console.print(f"Removing mark '{name}'")
    if not cp2_config.has_mark(name):
        console.print(f"[red]Error:[/] Mark '{name}' does not exist.")
        return
    cp2_config.remove_mark(name)
    console.print(f"[green]Successfully removed mark '{name}'[/green]")


@mark.command("list")
def mark_list():
    """List all mark bookmarks."""

    marks = cp2_config.list_marks()
    if not marks:
        console.print("[yellow]No marks found. 😥[/yellow]")
        return

    table = Table(box=HORIZONTALS, show_edge=False)
    table.add_column("Name", style="cyan", header_style="cyan", no_wrap=True)
    table.add_column("Path", style="magenta", header_style="magenta")
    table.add_column("Description", style="green", header_style="green", no_wrap=False)

    for name, info in marks.items():
        table.add_row(name, info["path"], info["description"])

    console.print(table)


@main.command()
def start():
    """Start CP2 interactive interface."""
    interactive(cp2_config, console)


@main.command()
def fzf():
    """Start CP2 interactive interface."""
    interactive_fzf(cp2_config, console)


if __name__ == "__main__":
    main()
