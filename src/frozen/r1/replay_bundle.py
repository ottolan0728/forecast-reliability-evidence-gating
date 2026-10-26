"""Portable, non-destructive derived-tape replay. Invoke from unpacked bundle."""
from pathlib import Path
import argparse,hashlib,shutil,subprocess,sys,os,json
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--smoke',action='store_true');args=ap.parse_args();src=Path(__file__).resolve().parents[1];dst=Path(args.output).resolve()
    assert not dst.exists(),'New output directory required; never overwrite audit evidence'
    assert src not in dst.parents,'Place replay outside the bundle directory'
    for line in (src/'BUNDLE_SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        expected,name=line.split('  ',1);assert hashlib.sha256((src/name).read_bytes()).hexdigest()==expected,name
    shutil.copytree(src,dst);(dst/'results').rename(dst/'expected_results');(dst/'results').mkdir()
    stages=[('remaining.py','e8')] if args.smoke else [('analyses.py',x) for x in ['e1','e2','e3','e4']]+[('remaining.py',x) for x in ['e6_metrics','e7','e8']]
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
    for script,stage in stages:subprocess.run([sys.executable,'-X','utf8',str(dst/'scripts'/script),stage],env=env,check=True)
    import pandas as pd
    import numpy as np
    checks=[]
    for p in (dst/'results').rglob('*.csv'):
        expected=dst/'expected_results'/p.relative_to(dst/'results')
        if not expected.exists():continue
        a=pd.read_csv(expected,float_precision='round_trip');b=pd.read_csv(p,float_precision='round_trip');assert a.shape==b.shape,p
        for col in a.columns:
            if pd.api.types.is_numeric_dtype(a[col]) and not pd.api.types.is_bool_dtype(a[col]):ok=np.allclose(a[col],b[col],atol=1e-12,rtol=0,equal_nan=True)
            else:ok=a[col].fillna('<NA>').equals(b[col].fillna('<NA>'))
            checks.append(dict(file=str(p.relative_to(dst)),column=col,pass_=bool(ok)))
    pd.DataFrame(checks).to_csv(dst/'portable_comparison.csv',index=False);assert all(x['pass_'] for x in checks)
    (dst/'PORTABLE_REPLAY_PASS.json').write_text(json.dumps(dict(pass_=True,checks=len(checks),mode='E8 smoke' if args.smoke else 'all completed scientific diagnostics; excludes infeasible E0X/E5 and machine-specific engineering timings'),indent=2));print('PORTABLE PASS',len(checks),flush=True)
if __name__=='__main__':main()
