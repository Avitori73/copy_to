import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
from typing import List, Set
from .cp2_config import CP2Config
from rich.console import Console
from rich.table import Table
from rich.box import HORIZONTALS
import questionary


def signal_handler(sig, frame):
    """处理 Ctrl+C 信号"""
    print("\n👋 Operation cancelled by user. Goodbye!")
    sys.exit(0)


def interactive_fzf(cp2_config: CP2Config, console: Console) -> None:
    """
    Start the interactive interface for CP2.

    Args:
        cp2_config (CP2Config): The configuration object for CP2.
        target_path (str): The path to start the interactive session in.
    """
    # 注册信号处理器以确保 Ctrl+C 能够正确处理
    signal.signal(signal.SIGINT, signal_handler)

    target_path = os.getcwd()

    # search files
    console.print("[cyan]Initializing CP2...[/cyan]")
    marks = cp2_config.list_marks()
    marks = [mark for mark in marks.items() if mark[1]["path"] != target_path]
    if not marks:
        console.print("[yellow]No marks found. Please add some marks first.🤠[/yellow]")
        return

    console.print("[cyan]Starting interactive file selection...[/cyan]")
    selected_files: Set[str] = set()

    while True:
        # select files by fd, fzf
        if not selected_files:
            fzf_result = select_files_by_fzf(console)
            if not fzf_result:
                console.print("[yellow]No files selected.😓[/yellow]")
                continue
            selected_files.update(fzf_result)
        else:
            preview_selected_file(console, selected_files)
            console.print("[yellow]─" * 50 + "[/yellow]")
            console.print("[yellow]Type: 'n' to proceed to the next step.[/yellow]")
            console.print("[yellow]Type: 'r' to re-select files.[/yellow]")
            console.print("[yellow]Type: 's' to select more files.[/yellow]")
            console.print("[red]Type: 'q' to quit.[/red]")
            query = questionary.text("Type your choice:").ask()

            if query is None:
                console.print(
                    "\n[yellow]👋 Operation cancelled by user. Goodbye![/yellow]"
                )
                return

            if query.lower() == "n":
                break
            elif query.lower() == "r":
                selected_files.clear()
                continue
            elif query.lower() == "s":
                fzf_result = select_files_by_fzf(console)
                if not fzf_result:
                    console.print("[yellow]No files selected.😓[/yellow]")
                    continue
                selected_files.update(fzf_result)
            elif query.lower() == "q":
                console.print(
                    "\n[yellow]👋 Operation cancelled by user. Goodbye![/yellow]"
                )
                return

    if not selected_files:
        console.print("[yellow]No files selected for copying. Exiting...👋[/yellow]")
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

    copy_files_to(target_path, console, selected_files, destinations)


def preview_selected_file(console: Console, selected_files: Set[str]) -> None:
    console.print("[green]Selected files for copying:[/green]")
    table = Table(box=HORIZONTALS, show_edge=False)
    table.add_column("#", style="yellow", header_style="yellow", width=3)
    table.add_column("File", style="cyan", header_style="cyan", no_wrap=True)
    table.add_column("Path", style="magenta", header_style="magenta")
    for idx, path in enumerate(selected_files, 1):
        file = Path(path).name
        table.add_row(str(idx), file, path)
    console.print(table)


def select_files_by_fzf(console: Console) -> List[str]:
    """
    Use fzf to select files interactively.
    command fd --type f | fzf --multi
    """
    try:
        fzf_cmd = "fd --type f | fzf --multi"
        fzf_result = subprocess.run(fzf_cmd, capture_output=True, text=True, shell=True)
        if fzf_result.returncode == 0:
            selected = [
                line.strip()
                for line in fzf_result.stdout.strip().split("\n")
                if line.strip()
            ]
            return selected
        else:
            console.print("[red]Error:[/] No files selected or fzf command failed.")
            return []
    except subprocess.CalledProcessError as e:
        raise SystemExit(f"Error running fzf: {e}")
    except FileNotFoundError:
        raise SystemExit(
            "fzf or fd command not found. Please install them to use this feature."
        )


def copy_files_to(target_path, console, selected_files, destinations):
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


def copy_file_to(target_path, console, file_path, destinations):
    root_path = Path(target_path)
    file_path = Path(file_path)
    for dest in destinations:
        dest_path = Path(dest)
        relative_path = file_path.relative_to(root_path)
        target_file = dest_path / relative_path
        target_file.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(file_path, target_file)
        console.print(f"[green]✅ Copied file to {dest}[/green]")


def copy_dir_to(target_path, console, dir_path, destinations):
    root_path = Path(target_path)
    dir_path = Path(dir_path)
    for dest in destinations:
        dest_path = Path(dest)
        source_path = Path(dir_path)
        relative_path = source_path.relative_to(root_path)
        target_dir = dest_path / relative_path
        target_dir.mkdir(parents=True, exist_ok=True)

        shutil.copytree(source_path, target_dir, dirs_exist_ok=True)
        console.print(f"[green]✅ Copied directory to {dest}[/green]")
