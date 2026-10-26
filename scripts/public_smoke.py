"""Public-package verification and archived-table reconstruction; no model fits."""
from pathlib import Path
import argparse,ast,gzip,hashlib,json,os,re,subprocess,sys
import numpy as np
import pandas as pd

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--require-publication-ready',action='store_true');args=ap.parse_args()
    root=Path(__file__).resolve().parents[1];out=Path(args.output).resolve()
    if out.exists() or out==root or root in out.parents:raise ValueError('Use a new output directory outside the repository')
    out.mkdir(parents=True);checks=[]
    def ck(name,ok):
        checks.append(dict(check=name,pass_=bool(ok)))
        if not ok:raise AssertionError(name)
    def read(p):return pd.read_csv(root/'results/derived'/p,float_precision='round_trip')
    register=pd.read_csv(root/'docs/PUBLIC_FILE_REGISTER.csv',keep_default_na=False)
    files=[p for p in root.rglob('*') if p.is_file() and not any(x in p.parts for x in ['.git','__pycache__','.venv'])]
    included=register[register.decision!='EXCLUDE'];listed=set(included.destination_path)
    ck('every_public_file_registered',set(p.relative_to(root).as_posix() for p in files)==listed)
    for _,r in included.iterrows():
        p=root/r.destination_path;b=p.read_bytes()
        if r.destination_path!='docs/PUBLIC_FILE_REGISTER.csv':ck('sha256/'+r.destination_path,hashlib.sha256(b).hexdigest()==r.public_sha256)
        if p.suffix in ['.md','.json','.csv','.py','.txt','.tex','.cff']:
            t=b.decode('utf-8-sig')
            ck('secret_and_private_path_scan/'+r.destination_path,not re.search(r'(?:(?<![A-Za-z])[A-Za-z]:[/\\]|/[U]sers/|/[h]ome/|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY)',t))
        if p.name.endswith('.csv.gz'):
            payload=gzip.decompress(b);header=payload.splitlines()[0].decode().split(',')
            ck('no_observations_in_components/'+r.destination_path,not(set(header)&{'y','y_true','value_kwh','p24','p1','p168','actual','target_value','fallback','gain','residual'}))
            ck('compressed_payload_no_private_paths/'+r.destination_path,not re.search(rb'[A-Za-z]:[/\\]|github_pat_|-----BEGIN .*PRIVATE KEY',payload))
        if p.suffix=='.py':ast.parse(b);ck('syntax/'+r.destination_path,True)
        if p.suffix=='.csv' and r.destination_path.startswith('results/'):
            h=pd.read_csv(p,nrows=0).columns
            ck('no_hourly_observation_columns/'+r.destination_path,not(set(h)&{'y','y_true','value_kwh','p24','p1','p168','actual','target_value'}))
    # Reconstruct existing summaries from frozen entity tables. No tapes/labels loaded.
    for stage,entity,keys,cols in [
        ('E1_matched_rate','entity_results.csv',['dataset','model','lag','policy','q'],['delta_avg','delta_peak','nmae','peak_nmae','switch_rate']),
        ('E3_ccga_ablation','entity_results.csv',['dataset','model','lag','variant'],['delta_avg','delta_peak','nmae','peak_nmae','switch_rate']),
        ('E4_fallbacks','entity_results.csv',['dataset','model','lag','policy','delivered_fallback'],['delta_avg','delta_peak','nmae','peak_nmae','switch_rate']),
        ('E7_month_stability','entity_month_results.csv',['dataset','model','lag','policy','month'],['delta_avg','delta_peak','nmae','peak_nmae','switch_rate'])]:
        data=read(stage+'/'+entity);expected=read(stage+'/summary.csv');got=data.groupby(keys,dropna=False)[cols].mean().reset_index()
        merged=expected.merge(got,on=keys,validate='one_to_one',suffixes=('_expected','_got'));ck(stage+'/row_count',len(merged)==len(expected)==len(got))
        for col in cols:ck(stage+'/'+col,np.allclose(merged[col+'_expected'],merged[col+'_got'],atol=1e-12,rtol=0,equal_nan=True))
        got.to_csv(out/(stage+'_reconstructed.csv'),index=False)
    e=read('E1_matched_rate/summary.csv');z=e[e.policy.isin(['risk','gain'])].pivot(index=['dataset','model','lag','q'],columns='policy',values=['delta_avg','delta_peak'])
    ck('matched_average_40_of_40',int((z['delta_avg']['gain']<z['delta_avg']['risk']).sum())==40)
    ck('matched_peak_39_of_40',int((z['delta_peak']['gain']<z['delta_peak']['risk']).sum())==39)
    frozen=json.loads((root/'verification/frozen/verification.json').read_text());ck('historical_146964_checks',frozen['checks']==146964 and frozen['failed']==0)
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
    subprocess.run([sys.executable,str(root/'scripts/regenerate_frozen_figures.py'),'--output',str(out/'figures')],check=True,env=env)
    ck('seven_frozen_plot_blocks_execute',len(list((out/'figures').glob('*.pdf')))==7)
    printed=pd.read_csv(root/'verification/ACCEPTED_PRINTED_CELL_CHECKS.csv');unresolved=int((~printed.pass_).sum())
    candidate=pd.read_csv(root/'verification/resolution/PRODUCTION_CANDIDATE_PRINTED_CELL_CHECKS.csv');ck('corrected_candidate_all_printed_cells',candidate.pass_.all());ck('original_six_errors_preserved',unresolved==6)
    result=dict(corrected_candidate_printed_failures=0,public_ckw_historical_source_gate='BLOCKED',smoke_pass=True,checks=len(checks),scientific_experiments_executed=False,model_fits=0,raw_observations_loaded=False,manuscript_discrepancies=unresolved,publication_recommendation='REVISE' if unresolved else 'SEE_PUBLIC_RELEASE_AUDIT')
    pd.DataFrame(checks).to_csv(out/'checks.csv',index=False);(out/'SMOKE_TEST_REPORT.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
    if args.require_publication_ready and unresolved:sys.exit(2)
if __name__=='__main__':main()
