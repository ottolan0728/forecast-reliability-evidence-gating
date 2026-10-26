"""Hash-locked raw-input preprocessing only; no model fitting or policy selection."""
from pathlib import Path
import argparse,hashlib,json,io,sys,urllib.request
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from reconstruction_features import features

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return h.hexdigest()

def validate_files(contract,base,datasets):
    rows=[]
    for ds in datasets:
        for r in contract[ds]['inputs']:
            p=base/r['relative_path']
            if not p.is_file():raise ValueError('Missing separately obtained source: '+r['relative_path'])
            if p.stat().st_size!=r['bytes'] or digest(p)!=r['sha256']:raise ValueError('Frozen source identity mismatch: '+r['relative_path']+'; no newer source substitution allowed')
            rows.append(dict(dataset=ds,relative_path=r['relative_path'],sha256=r['sha256'],pass_=True))
    return rows

def bdg2(contract,base):
    cfg=contract['bdg2'];reg=pd.read_csv(ROOT/cfg['registry'],dtype={'building_id':str},float_precision='round_trip')
    assert len(reg)==20 and reg.eligible.all()
    p=base/cfg['inputs'][0]['relative_path'];header=pd.read_csv(p,nrows=0).columns[0]
    raw=pd.read_csv(p,usecols=[header]+reg.building_id.tolist(),nrows=8784,index_col=0,parse_dates=True)
    assert raw.index.equals(pd.date_range('2016-01-01','2016-12-31 23:00',freq='h'))
    out={}
    for _,r in reg.iterrows():
        y=raw[r.building_id].astype(float);dst=y.index.tz_localize(r.timezone,ambiguous='NaT',nonexistent='NaT').isna()
        out[r.building_id]=y.where(np.isfinite(y)&(y>=0)&~dst)
    return pd.DataFrame(out),reg

def ckw(contract,base):
    cfg=contract['ckw'];reg=pd.read_csv(ROOT/cfg['registry'],dtype={'entity':str},float_precision='round_trip')
    assert len(reg)==116 and reg.eligible.all()
    def load(items):
        parts=[]
        for r in items:
            d=pd.read_csv(base/r['relative_path'],dtype={'area_code':str})
            assert list(d.columns)==['area_code','timestamp','num_meter','value_kwh']
            d['timestamp']=pd.to_datetime(d.timestamp,utc=True,errors='raise')
            for c in ['num_meter','value_kwh']:d[c]=pd.to_numeric(d[c],errors='raise')
            parts.append(d)
        d=pd.concat(parts,ignore_index=True)
        assert not d.duplicated(['area_code','timestamp']).any() and d.area_code.notna().all()
        assert (d.timestamp.dt.minute.mod(15).eq(0)&d.timestamp.dt.second.eq(0)&d.timestamp.dt.microsecond.eq(0)).all()
        bad=(~np.isfinite(d.value_kwh))|(d.value_kwh<0)|(~np.isfinite(d.num_meter))|(d.num_meter<=0)|(d.num_meter.mod(1)!=0)
        d['valid_energy']=d.value_kwh.where(~bad)
        return d
    # Keep the frozen development-file boundary; September cannot fill August holes.
    dev=load(cfg['inputs'][:8]);ix=pd.date_range('2025-01-01','2025-09-01',freq='h',inclusive='left',tz='UTC');hourly=[]
    assert set(dev.area_code)==set(reg.entity)
    for e,g in dev.groupby('area_code',sort=True):
        g=g.sort_values('timestamp').set_index('timestamp');h=g.valid_energy.resample('h').sum(min_count=4).reindex(ix)
        counts=g.valid_energy.resample('h').count().reindex(ix,fill_value=0);h=h.where(counts.eq(4))
        hourly.append(pd.DataFrame(dict(timestamp=ix,area_code=e,value_kwh=h.values)))
    # The frozen C0->C1 interface was CSV serialization then default pandas read.
    d=pd.read_csv(io.StringIO(pd.concat(hourly).to_csv(index=False)),dtype={'area_code':str})
    d.timestamp=pd.to_datetime(d.timestamp,utc=True).dt.tz_localize(None)
    dev=d.pivot(index='timestamp',columns='area_code',values='value_kwh')
    tail=load(cfg['inputs'][8:]);tail.timestamp=tail.timestamp.dt.tz_localize(None)
    assert tail.timestamp.min()>=pd.Timestamp('2025-08-31')
    out=dev.reindex(pd.date_range('2025-01-01','2025-12-31 23:00',freq='h'))
    for e,g in tail.groupby('area_code'):
        if e not in out:continue
        h=g.set_index('timestamp').valid_energy.resample('h').sum(min_count=4)
        h=h[(h.index>='2025-09-01')&(h.index<'2026-01-01')];out.loc[h.index,e]=h
    assert np.array_equal(out.loc[dev.index].to_numpy(),dev.to_numpy(),equal_nan=True)
    return out,reg

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input-root',required=True);ap.add_argument('--dataset',choices=['bdg2','ckw','both'],default='both');ap.add_argument('--output');ap.add_argument('--dry-run',action='store_true');ap.add_argument('--validate-only',action='store_true');ap.add_argument('--download',action='store_true');args=ap.parse_args()
    contract=json.loads((ROOT/'configs/RAW_INPUT_CONTRACT.json').read_text());base=Path(args.input_root).resolve();datasets=['bdg2','ckw'] if args.dataset=='both' else [args.dataset]
    assert digest(ROOT/'src/reconstruction_features.py')==contract['feature_source_sha256'],'Frozen feature extraction changed'
    for ds in datasets:assert digest(ROOT/contract[ds]['registry'])==contract[ds]['registry_sha256'],'Frozen cohort registry changed'
    if args.download:
        for ds in datasets:
            for r in contract[ds]['inputs']:
                p=base/r['relative_path']
                if p.exists():continue
                if r.get('download_blocked'):raise ValueError('Frozen CKW source unavailable at current URL: '+r['relative_path']+'; obtain the exact hash-locked historical version separately')
                p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.partial')
                if tmp.exists():raise ValueError('Partial download already exists; inspect before retry')
                with urllib.request.urlopen(r['url'],timeout=120) as response,tmp.open('xb') as f:
                    while True:
                        b=response.read(2**20)
                        if not b:break
                        f.write(b)
                if tmp.stat().st_size!=r['bytes'] or digest(tmp)!=r['sha256']:raise ValueError('Downloaded version is not frozen source; retained .partial for inspection')
                tmp.rename(p)
    inputs=validate_files(contract,base,datasets)
    if args.dry_run:print(json.dumps(dict(mode='hash-only dry run',inputs=inputs,pass_=True),indent=2));return
    dest=Path(args.output).resolve() if args.output else None
    if not args.validate_only:
        if dest is None or dest.exists() or dest==ROOT or ROOT in dest.parents:raise ValueError('A new --output directory outside repository is required; reconstructed observations are not public assets')
        dest.mkdir(parents=True)
    summary=[];years={}
    for ds in datasets:
        year,registry=(bdg2 if ds=='bdg2' else ckw)(contract,base)
        years[ds]=year
        for e in year:
            y=year[e];x=features(y);yr=y.index[0].year;tr=y.index<pd.Timestamp(f'{yr}-07-01');ju=(y.index>=pd.Timestamp(f'{yr}-07-01'))&(y.index<pd.Timestamp(f'{yr}-08-01'));au=(y.index>=pd.Timestamp(f'{yr}-08-01'))&(y.index<pd.Timestamp(f'{yr}-09-01'));ev=y.index>=pd.Timestamp(f'{yr}-10-01')
            feature_ok=x.notna().all(1);labeled_ok=feature_ok&y.notna();q99=y[tr].quantile(.99);q95=y[tr].quantile(.95)
            ref=registry[registry['building_id' if ds=='bdg2' else 'entity']==e].iloc[0]
            names=['train_n','july_n','august_n'] if ds=='bdg2' else ['train_rows','july_rows','august_rows']
            counts=[int(labeled_ok[m].sum()) for m in [tr,ju,au]]
            assert counts==[int(ref[k]) for k in names],(ds,e,'frozen support mismatch')
            assert abs(q99-ref['train_q99' if ds=='bdg2' else 'scale'])<=1e-10,(ds,e,'normalizer mismatch')
            if ds=='ckw':assert abs(q95-ref.peakcut)<=1e-10,(ds,e,'peak mismatch')
            # Target/future masking at one fixed issue time must leave its features unchanged.
            t=pd.Timestamp(f'{yr}-10-15');changed=y.copy();changed.loc[t:]=np.nan
            assert np.array_equal(x.loc[t].to_numpy(),features(changed).loc[t].to_numpy(),equal_nan=True)
            summary.append(dict(dataset=ds,entity=e,calendar_rows=len(y),train_rows=counts[0],july_rows=counts[1],august_rows=counts[2],evaluation_issued=int((feature_ok&ev).sum()),evaluation_scoreable=int((labeled_ok&ev).sum()),train_q99=q99,train_q95=q95))
            if dest:
                folder=dest/ds;folder.mkdir(exist_ok=True)
                frame=x.copy();frame.insert(0,'y',y);frame['normalizer_q99']=q99;frame['peakcut_q95']=q95;frame['y_normalized']=y/q99;frame['issueable']=feature_ok;frame['scoreable']=labeled_ok;frame['temporal_role']=np.select([tr,ju,au,y.index<pd.Timestamp(f'{yr}-10-01')],['point_train','auxiliary_train','calibration','update_history'],default='evaluation')
                frame.to_csv(folder/(e+'.csv.gz'),index_label='timestamp')
        if dest:year.to_csv(dest/ds/'hourly.csv.gz',index_label='timestamp')
    result=dict(mode='validation-only' if args.validate_only else 'preprocessing reconstruction',pass_=True,entities=len(summary),inputs=len(inputs),fits=0,optimization=0,cohort_changed=False,stop_boundary='hourly observations, frozen causal features and temporal masks; before any model fitting/inference or policy recalibration')
    if dest:
        pd.DataFrame(summary).to_csv(dest/'support_and_scale_checks.csv',index=False);(dest/'RECONSTRUCTION_REPORT.json').write_text(json.dumps(result,indent=2));pd.DataFrame(inputs).to_csv(dest/'VALIDATED_INPUTS.csv',index=False)
        from restore_forecasts import restore
        restore(ROOT,dest,years)
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
