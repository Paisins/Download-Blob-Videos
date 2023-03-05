from typing import Optional

from rich.progress import (
    Column,
    Text,
    Task,
    BarColumn,
    Progress,
    TextColumn,
    ProgressColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)


class FileCountColumn(ProgressColumn):
    """my file count column"""

    def __init__(self, table_column: Optional[Column] = None) -> None:
        super().__init__(table_column=table_column)

    def render(self, task: "Task") -> Text:
        """Calculate common unit for completed and total."""
        completed = int(task.completed)

        # unit_and_suffix_calculation_base = (
        #     int(task.total) if task.total is not None else completed
        # )
        unit, suffix = 1, "files"
        precision = 0 if unit == 1 else 1

        completed_ratio = completed / unit
        completed_str = f"{completed_ratio:,.{precision}f}"

        if task.total is not None:
            total = int(task.total)
            total_ratio = total / unit
            total_str = f"{total_ratio:,.{precision}f}"
        else:
            total_str = "?"

        download_status = f"{completed_str}/{total_str} {suffix}"
        download_text = Text(download_status, style="progress.download")
        return download_text


files_progress = Progress(
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    FileCountColumn(),
    TimeRemainingColumn(),
    TimeElapsedColumn(),
)
