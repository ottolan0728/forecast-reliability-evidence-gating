"""Join exact frozen, label-free forecast components to separately verified observations."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd

def restore(root,dest,years):
    spec=json.loads((root/'configs/FROZEN_FORECAST_COMPONENTS.json').read_text());folder=root/'results/derived/frozen_forecast_components';counts={}
    for item in spec['components']:
        path=folder/item['file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256'],path.name
        a=pd.read_csv(path,float_precision='round_trip',dtype={'entity':str},parse_dates=['target_time'])
        assert list(a.columns)==item['columns'] and len(a)==item['rows']
        assert not set(a.columns)&{'y','fallback','p24','gain','residual','scoreable','covered','peak'}
        kind=item['file'].removesuffix('.csv.gz');schema=spec['original_schemas'][kind];out=[]
        keys=['entity','model'] if kind=='bdg2_evaluation' else ['entity','model','lag'] if kind=='ckw_evaluation' else ['dataset','entity','model','lag']
        for key,g in a.groupby(keys,sort=False):
            if kind=='bdg2_evaluation':ds='bdg2';e,m=key;lag=24
            elif kind=='ckw_evaluation':ds='ckw';e,m,lag=key
            else:label,e,m,lag=key;ds='bdg2' if label=='E1' else 'ckw'
            if ds not in years:continue
            y=years[ds][e];g=g.set_index('target_time').copy();g['y']=y.reindex(g.index);fb=y.shift(int(lag)).reindex(g.index)
            if kind=='bdg2_evaluation':
                g['p24']=fb;g['gain']=(abs(g.y-g.pred)-abs(g.y-g.p24))/g.scale;g['residual']=abs(g.y-g.pred);g['scoreable']=g.y.notna();g['covered']=((g.y>=g.lower)&(g.y<=g.upper)).where(g.y.notna());g['peak']=(g.y>y.loc[:'2016-06-30 23:00'].quantile(.95)).where(g.y.notna())
            else:g['fallback']=fb
            g=g.reset_index()[schema]
            if kind=='bdg2_evaluation':out.append(g)
            else:
                parent=dest/'evaluation/evidence_gating_ckw_c1/results/tapes' if kind=='ckw_evaluation' else dest/'calibration_scores';parent.mkdir(parents=True,exist_ok=True)
                name=f'{e}_{m}_lag{lag}.csv.gz' if kind=='ckw_evaluation' else f'{label}_{e}_{m}_lag{lag}.csv.gz'
                g.to_csv(parent/name,index=False,compression={'method':'gzip','mtime':0})
        if out:
            parent=dest/'evaluation/evidence_gating_external/results';parent.mkdir(parents=True,exist_ok=True);pd.concat(out,ignore_index=True).to_csv(parent/'issued_forecast_tape.csv.gz',index=False,compression={'method':'gzip','mtime':0})
        counts[kind]=len(a)
    (dest/'FORECAST_RESTORATION.json').write_text(json.dumps(dict(status='RESTORED_FROM_FROZEN_COMPONENTS_AND_HASH_VERIFIED_RAW_INPUTS',model_fits=0,inference=0,calibration_refits=0,component_rows=counts,scientific_settings_changed=False),indent=2))
