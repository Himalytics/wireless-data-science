"""Build and execute the explanatory notebook against actual frozen study outputs."""
import sys
import os
import nbformat as n
from nbclient import NotebookClient
from source import ROOT

def main():
    nb=n.v4.new_notebook(); cells=[]
    def md(s): cells.append(n.v4.new_markdown_cell(s))
    def code(s): cells.append(n.v4.new_code_cell(s))
    md('# Project 05: Who responds because of assignment?\n\nThis notebook explains an executed study, not an unrun model sketch. Run `python run.py` to download the publisher data and fit all nine estimators first. Results are released Criteo advertising benchmark contrasts, not original campaign effects or wireless retention. Read DATA_CARD and protocol before interpreting numbers.')
    code("from pathlib import Path\nimport json, pandas as pd, numpy as np\nfrom IPython.display import display, Image\nR=Path('results')\ne=json.loads((R/'experiment.json').read_text())\ne")
    md('## Audit before inference\n\nAssignment is not exposure. Visit is the outcome. Anonymous baseline features are the only predictors. Nonuniform privacy selection prevents original-population effect recovery. We preserve profile groups across train/validation/test; source ordinals are not dates.')
    code("display(pd.read_csv(R/'audit.csv'))\ndisplay(pd.read_csv(R/'balance.csv'))\ns=pd.read_csv(R/'splits.csv.gz')\nassert s.groupby('profile').split.nunique().max()==1\nprint('No profile crosses a split boundary:', len(s), 'rows')")
    md('## Learn two response surfaces, then subtract\n\nThe T-learner fits treated and control visit models using only training observations. The difference is an uplift score. Four pairs are compared on validation policy contrast at 20% capacity. The test set never selects the model. Logistic treated-response ranking is a separate baseline; response probability does not equal incremental response.')
    code("display(pd.read_csv(R/'selection.csv'))\nprint('Frozen choice:',e['selected_model'])")
    md('## Policy evaluation from observed assignment and outcome\n\nFor propensity p, the IPW pseudo-outcome is TY/p − (1−T)Y/(1−p). Multiplying by a fixed allocation and averaging estimates the released-sample contrast under the working assignment assumptions. The primary scale is incremental visits per 1,000 **eligible**, not selected, users. Random-20% is its expected value without a simulated coin flip.')
    code("p=pd.read_csv(R/'predictions.csv.gz')\nw=p.treatment*p.visit/e['train_assignment_share']-(1-p.treatment)*p.visit/(1-e['train_assignment_share'])\nassert np.allclose(w,p.ipw)\ndisplay(pd.read_csv(R/'policies.csv'))\ndisplay(pd.read_csv(R/'paired_comparisons.csv'))")
    md('## Uncertainty is conditional\n\nPaired profile-cluster Poisson multiplier intervals keep the fitted policies fixed and cluster identical profiles. They omit fit/selection/propensity uncertainty and unknown advertiser dependence. Capacities and deciles are exploratory with pointwise intervals; no multiple-testing discovery is claimed.')
    code("display(Image(filename=str(R/'figures/03_policy.png')))\ndisplay(Image(filename=str(R/'figures/02_capacity.png')))")
    md('## Robustness and miscalibration\n\nCompare IPW to an augmented DR score, approximate published p=0.85 and covariate propensity. None repairs unknown publisher selection. Observed decile effects and predictions can disagree: good ranking is not calibrated individual effects.')
    code("display(pd.read_csv(R/'sensitivity.csv'))\ndisplay(pd.read_csv(R/'deciles.csv'))\ndisplay(Image(filename=str(R/'figures/04_deciles.png')))")
    md('## Recompute the decision, then challenge it\n\nA same-budget positive advantage can justify a follow-up experiment in the benchmark setting, not a carrier rollout. To transfer the method, collect randomized offer assignments, eligible pre-treatment features, actual costs and retention outcomes. Independently learn and evaluate a policy on those observations. No telecom effect is supplied by Criteo.')
    code("delta=((p.policy_uplift_20-.2)*p.ipw*1000).mean()\nprint(f'Frozen uplift-minus-random contrast: {delta:.3f} per 1,000 eligible')\nprint('Evidence limits: unknown selection, anonymous features, no dates, source-domain only.')")
    md('## Ownership experiment\n\nBefore a new evaluation, copy the study to a new local experiment directory and change one declared scientific choice (sample hash seed, capacity, propensity or model class). Preserve this study and all held-out results. Do not repeatedly tune against this test. Read BUILDERS_GUIDE for a two-hour path and seven substantive daily exercises.')
    nb.cells=cells;nb.metadata={'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}}
    if '--in-process' in sys.argv:
        # Execute real cells and capture actual rich outputs when kernel sockets are unavailable.
        from IPython.core.interactiveshell import InteractiveShell
        from IPython.utils.capture import capture_output
        shell=InteractiveShell.instance(); os.chdir(ROOT); count=0
        for cell in nb.cells:
            if cell.cell_type!='code': continue
            count+=1
            with capture_output() as captured:
                outcome=shell.run_cell(cell.source,store_history=False)
            if outcome.error_before_exec: raise outcome.error_before_exec
            if outcome.error_in_exec: raise outcome.error_in_exec
            outputs=[]
            if captured.stdout: outputs.append(n.v4.new_output('stream',name='stdout',text=captured.stdout))
            if captured.stderr: outputs.append(n.v4.new_output('stream',name='stderr',text=captured.stderr))
            for output in captured.outputs:
                outputs.append(n.v4.new_output('display_data',data=output.data,metadata=output.metadata))
            cell.execution_count=count;cell.outputs=outputs
        nb.metadata['execution_method']='Actual sequential in-process IPython execution; kernel sockets unavailable on recorded host'
    else:
        NotebookClient(nb,timeout=180,kernel_name='python3',resources={'metadata':{'path':str(ROOT)}}).execute()
        nb.metadata['execution_method']='Jupyter kernel via nbclient'
    n.write(nb,ROOT/'analysis.ipynb')
    print('Executed',sum(c.cell_type=='code' for c in cells),'notebook code cells')

if __name__=='__main__':main()
