"""Execute this Python-only walkthrough in-process; no kernel server or ports required."""
import os
import traceback
from pathlib import Path

import nbformat
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output

HERE = Path(__file__).resolve().parent

if __name__ == "__main__":
    os.chdir(HERE)
    path = HERE / "analysis.ipynb"
    notebook = nbformat.read(path, as_version=4)
    shell = InteractiveShell.instance()
    count = 0
    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        count += 1
        with capture_output(display=True) as captured:
            result = shell.run_cell(cell.source, store_history=False)
        cell.execution_count = count
        cell.outputs = []
        for name in ("stdout", "stderr"):
            value = getattr(captured, name)
            if value:
                cell.outputs.append(nbformat.v4.new_output("stream", name=name, text=value))
        for output in captured.outputs:
            cell.outputs.append(nbformat.v4.new_output("display_data", data=output.data, metadata=output.metadata))
        error = result.error_before_exec or result.error_in_exec
        if error:
            cell.outputs.append(nbformat.v4.new_output("error", ename=type(error).__name__, evalue=str(error),
                traceback=traceback.format_exception(type(error), error, error.__traceback__)))
            nbformat.write(notebook, path)
            raise error
    notebook.metadata["execution_method"] = "Python cells executed with an in-process IPython shell; rich displays captured"
    notebook.metadata.kernelspec = {"name": "python3", "display_name": "Python 3", "language": "python"}
    nbformat.validate(notebook)
    nbformat.write(notebook, path)
    print(f"Executed {count} Python cells:", path)
