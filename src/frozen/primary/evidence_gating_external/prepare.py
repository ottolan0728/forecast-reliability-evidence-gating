from pathlib import Path
import sys,json,hashlib
from datetime import datetime,timezone
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'evidence_gating_pilot'));import pilot
def key(e):return hashlib.sha256(('EG-E1:'+e).encode()).hexdigest()
def clean(raw,tz):
    dst=raw.index.tz_localize(tz,ambiguous='NaT',nonexistent='NaT').isna()
    return raw.where(np.isfinite(raw)&(raw>=0)&~dst)
def main():
    assert not (ROOT/'selected_registry.csv').exists(),'Registry already frozen'
    metadata=pd.read_csv(ROOT.parent/'evidence_gating_audit/reserved_entity_exposure.csv')
    src=pilot.SRC/'data_raw/bdg2_electricity_raw.csv'
    header=pd.read_csv(src,nrows=0).columns[0]
    raw=pd.read_csv(src,usecols=[header]+metadata.building_id.tolist(),nrows=5856,index_col=0,parse_dates=True)
    assert raw.index.equals(pd.date_range('2016-01-01','2016-08-31 23:00',freq='h'))
    rows=[]
    for _,m in metadata.iterrows():
        reason=[]
        if pd.isna(m.timezone):
            rows.append({**m.to_dict(),'eligible':False,'reason':'timezone_missing'});continue
        y=clean(raw[m.building_id].astype(float),m.timezone);x=pilot.features(y)
        train=y.index<'2016-07-01';ok=x.notna().all(axis=1)&y.notna()
        scale=y[train].quantile(.99);ntrain=int((ok&train).sum());nj=int((ok&(y.index>='2016-07-01')&(y.index<'2016-08-01')).sum());na=int((ok&(y.index>='2016-08-01')).sum())
        if y[train].notna().mean()<.9:reason.append('training_valid_fraction')
        if not scale>0:reason.append('nonpositive_scale')
        if ntrain<3000:reason.append('training_features')
        if nj<=336:reason.append('july_evidence')
        if na<336:reason.append('august_evidence')
        rows.append({**m.to_dict(),'eligible':not reason,'reason':';'.join(reason),'train_n':ntrain,'july_n':nj,'august_n':na,'train_q99':scale,'selection_hash':key(m.building_id)})
    qc=pd.DataFrame(rows);qc.to_csv(ROOT/'eligibility_registry.csv',index=False)
    selected=qc[qc.eligible].sort_values('selection_hash').groupby('site_id',sort=True).head(4).sort_values(['site_id','selection_hash'])
    selected.to_csv(ROOT/'selected_registry.csv',index=False)
    summary=qc.groupby('site_id').agg(candidates=('building_id','size'),eligible=('eligible','sum'));summary['selected']=selected.groupby('site_id').size();summary=summary.fillna(0)
    summary.to_csv(ROOT/'readiness_by_site.csv')
    record={'frozen_utc':datetime.now(timezone.utc).isoformat(),'value_read_end':'2016-08-31 23:00:00','raw_sha256':pilot.digest(src),'registry_sha256':pilot.digest(ROOT/'selected_registry.csv'),'design_sha256':pilot.digest(ROOT/'DESIGN_E1.md'),'code_sha256':pilot.digest(Path(__file__)),'exposure_inventory_sha256':pilot.digest(ROOT.parent/'evidence_gating_audit/reserved_entity_exposure.csv'),'helper_sha256':pilot.digest(Path(pilot.__file__))}
    (ROOT/'selection_manifest.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(summary.to_string())
if __name__=='__main__':main()
