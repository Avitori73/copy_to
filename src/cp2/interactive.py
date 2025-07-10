from pathlib import Path
import shutil
import signal
import sys
from typing import List, Tuple
from .fuzzy_search import fuzzy_search_files
from .load_files import load_files_to_cache
from .cp2_config import CP2Config
from rich.console import Console
from rich.table import Table
from rich.box import HORIZONTALS
import questionary


def signal_handler(sig, frame):
    """处理 Ctrl+C 信号"""
    print("\n👋 Operation cancelled by user. Goodbye!")
    sys.exit(0)


def interactive(cp2_config: CP2Config, target_path: str, console: Console) -> None:
    """
    Start the interactive interface for CP2.

    Args:
        cp2_config (CP2Config): The configuration object for CP2.
        target_path (str): The path to start the interactive session in.
    """
    # 注册信号处理器以确保 Ctrl+C 能够正确处理
    signal.signal(signal.SIGINT, signal_handler)

    # search files
    console.print("[cyan]Initializing CP2...[/cyan]")
    marks = cp2_config.list_marks()
    marks = [mark for mark in marks.items() if mark[1]["path"] != target_path]
    if not marks:
        console.print("[yellow]No marks found. Please add some marks first.🤠[/yellow]")
        return

    console.print("[cyan]Loading files from directory...[/cyan]")
    cache = load_files_to_cache(cp2_config, target_path)
    console.print(f"[green]✅ Found {len(cache)} files[/green]")

    console.print("[cyan]Starting interactive file selection...[/cyan]")
    selected_files: List[Tuple[str, str, int]] = []
    while True:
        query = questionary.text(
            "Which file do you want to copy? (type at least 3 characters to search, or 'n' to next step)",
        ).ask()

        # 检查是否被中断（questionary 返回 None）
        if query is None:
            console.print("\n[yellow]👋 Operation cancelled by user. Goodbye![/yellow]")
            return

        if query == "n":
            break

        # Perform search in cache
        results = fuzzy_search_files(query, cache)
        if not results:
            console.print("[yellow]🧐 No files found matching your query.[/yellow]")
            continue

        choose_files = questionary.checkbox(
            "Search results:",
            choices=[questionary.Choice(title=file[0], value=file) for file in results],
        ).ask()

        # 检查选择是否被中断
        if choose_files is None:
            console.print("\n[yellow]👋 Selection cancelled. Goodbye![/yellow]")
            return

        if choose_files:
            selected_files.extend(choose_files)

    if not selected_files:
        console.print("[yellow]No files selected for copying. Exiting...👋[/yellow]")
        return

    # Double check selected files
    console.print("[green]Selected files for copying:[/green]")
    table = Table(box=HORIZONTALS, show_edge=False)
    table.add_column("File", style="cyan", header_style="cyan", no_wrap=True)
    table.add_column("Path", style="magenta", header_style="magenta")
    for file, path, score in selected_files:
        table.add_row(file, path)
    console.print(table)
    confirmed = questionary.confirm("Is that correct? (y/n)").ask()

    # 检查确认是否被中断
    if confirmed is None:
        console.print("\n[yellow]👋 Confirmation cancelled. Goodbye![/yellow]")
        return

    if not confirmed:
        console.print("[yellow]😵 Operation cancelled.[/yellow]")
        return

    while True:
        destinations = questionary.checkbox(
            "Where do you want to copy these files?",
            choices=[
                questionary.Choice(title=f"{name} {info['path']}", value=info["path"])
                for name, info in marks
            ],
        ).ask()

        # 检查目标选择是否被中断
        if destinations is None:
            console.print(
                "\n[yellow]👋 Destination selection cancelled. Goodbye![/yellow]"
            )
            return

        if destinations:
            break

        console.print(
            "[yellow]No destinations selected. Please select at least one destination.[/yellow]"
        )

    console.print("[cyan]Copying files to selected destinations...[/cyan]")

    root_path = Path(target_path)
    for dest in destinations:
        dest_path = Path(dest)

        for filename, filepath, score in selected_files:
            source_path = Path(filepath)
            relative_path = source_path.relative_to(root_path)
            target_file = dest_path / relative_path
            target_file.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy2(source_path, target_file)
        console.print(f"[green]✅ Copied files to {dest}[/green]")

    console.print("[green]🎉 All files copied successfully! 🎉[/green]")
