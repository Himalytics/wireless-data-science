"""Create and execute the explanatory notebook using the current Python environment."""
from pathlib import Path

import nbformat
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output


def main():
    notebook = nbformat.v4.new_notebook()
    markdown = nbformat.v4.new_markdown_cell
    code = nbformat.v4.new_code_cell
    notebook.cells = [
        markdown("# When do 80% complaint intervals miss?\nProject 04. Run the full replay with `python run.py` first. This notebook inspects the saved outputs and recomputes observed coverage."),
        code("from pathlib import Path\nimport json, pandas as pd\nfrom IPython.display import display, Image\nr = Path('results')\nmanifest = json.loads(Path('data/source_manifest.json').read_text())\nprint({k: manifest[k] for k in ['counts', 'absent_calendar_days', 'retrieved_at_utc']})"),
        markdown("## Issue-time boundaries\nA Monday forecast can use counts through the prior Sunday under the zero-lag assumption. A four-week forecast targets the week starting three Mondays later. An error becomes eligible the Monday after the target week closes, with additional delay in the sensitivity replay."),
        code("p = pd.read_csv(r/'predictions.csv', parse_dates=['origin','target','latest_score_available','latest_feature_week'])\nassert (p.latest_score_available <= p.origin).all()\nassert (p.latest_feature_week < p.origin).all()\nprint(p[['origin','target','horizon','latest_score_available']].drop_duplicates().head())\ndisplay(pd.read_csv(r/'development.csv'))"),
        markdown("## Calibration and evaluation\nThe recent mean is constant across interval methods at each origin. The frozen and rolling references hold alpha at 0.2. The adaptive variant updates alpha after earlier intervals resolve and clips it to a finite range. The score adds width and a penalty for either tail miss. Smaller scores are better."),
        code("covered = p.actual.between(p.lower,p.upper)\nassert (covered == p.covered).all()\ndisplay(p.assign(checked=covered).groupby(['horizon','method']).checked.agg(['sum','count','mean']))\ndisplay(Image(filename=str(r/'coverage.png')))"),
        markdown("## Look past aggregate coverage\nInspect period and direction of misses. Moving-block draws pair methods on the same target weeks. The central 95% resampling ranges condition on this replay and do not establish coverage or statistical significance under arbitrary shift."),
        code("display(pd.read_csv(r/'periods.csv'))\ndisplay(pd.read_csv(r/'paired_blocks.csv'))\ndisplay(Image(filename=str(r/'timeline.png')))"),
        markdown("## Change the assumptions\nThe two-week lag delays both fresh features and score feedback. The issue-mix sensitivity removes reports with the exact Unwanted Calls label. Both reuse the development-selected gain."),
        code("display(pd.read_csv(r/'sensitivity.csv'))\ndisplay(pd.read_csv(r/'point_baselines.csv'))"),
        markdown("## Decision\nKeep a simple interval reference and instrument direction of misses by horizon and arrival vintage. The historical snapshot cannot establish what had actually been published on each forecast date. Review the report and run the builder exercises before reusing this workflow.")
    ]
    notebook.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
    shell = InteractiveShell.instance()
    count = 0
    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        count += 1
        with capture_output(display=True) as captured:
            outcome = shell.run_cell(cell.source)
        if outcome.error_before_exec or outcome.error_in_exec:
            raise outcome.error_before_exec or outcome.error_in_exec
        cell.execution_count = count
        if captured.stdout:
            cell.outputs.append(nbformat.v4.new_output("stream", name="stdout", text=captured.stdout))
        for output in captured.outputs:
            cell.outputs.append(nbformat.v4.new_output("display_data", data=output.data, metadata=output.metadata))
    nbformat.validate(notebook)
    nbformat.write(notebook, Path("analysis.ipynb"))
    print(f"Executed {count} notebook cells")


if __name__ == "__main__":
    main()
