from pathlib import Path
import hashlib, json, sys, platform
from datetime import datetime, timezone
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
SRC = Path('PRIVATE_SOURCE/Project RS_DG')
OUT = ROOT / 'run_p0'
SEED = 20260920

def digest(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''): h.update(b)
    return h.hexdigest()

def key(s): return hashlib.sha256(('EG-P0:'+s).encode()).hexdigest()

def features(y):
    x = pd.DataFrame({f'lag{k}': y.shift(k) for k in [1,2,3,24,48,168]})
    x['mean24'] = y.shift(1).rolling(24).mean()
    x['std24'] = y.shift(1).rolling(24).std()
    for name, values, period in [('hour',y.index.hour,24),('week',y.index.dayofweek,7),('year',y.index.dayofyear,366)]:
        x[name+'sin'] = np.sin(2*np.pi*values/period)
        x[name+'cos'] = np.cos(2*np.pi*values/period)
    return x

def quantile90(a):
    a = np.sort(np.asarray(a))
    return a[min(len(a)-1, int(np.ceil((len(a)+1)*.9))-1)]

def bounds(a, seed):
    a = np.asarray(a, float)
    rng = np.random.default_rng(seed)
    starts = rng.integers(0,len(a),(1000,int(np.ceil(len(a)/7))))
    inds = ((starts[:,:,None] + np.arange(7)) % len(a)).reshape(1000,-1)[:,:len(a)]
    means = np.nanmean(a[inds],axis=1)
    return np.nanquantile(means,[.05,.95])

def evidence(tape, update, scale):
    # strict availability cutoff and fixed calendar evidence window
    hist = tape[(tape.label_available_at < update) & (tape.index >= update-pd.Timedelta(days=56))]
    daily = hist.assign(diff=(hist.err_model-hist.err_p24)/scale).resample('D').agg(diff=('diff','mean'),cov=('covered','mean'),n=('y','size'))
    daily = daily.reindex(pd.date_range(update-pd.Timedelta(days=56),update-pd.Timedelta(days=1),freq='D'))
    valid = daily.n >= 18
    r = {'update':update,'evidence_days':int(valid.sum()),'point':'UNKNOWN','interval':'UNKNOWN','point_lo':np.nan,'point_hi':np.nan,'cov_lo':np.nan,'cov_hi':np.nan}
    if valid.sum() < 28: return r
    lo,hi = bounds(daily['diff'].where(valid),SEED)
    cl,ch = bounds(daily['cov'].where(valid),SEED+1)
    r.update(point_lo=lo,point_hi=hi,cov_lo=cl,cov_hi=ch)
    r['point'] = 'PASS' if hi < 0 else ('FAIL' if lo > 0 else 'UNKNOWN')
    width_ok = ((hist.upper-hist.lower)/scale).mean() <= 1
    r['interval'] = 'PASS' if cl >= .87 and width_ok else ('FAIL' if ch < .87 or not width_ok else 'UNKNOWN')
    return r

def selftest():
    idx = pd.date_range('2016-01-01',periods=400,freq='h')
    y = pd.Series(np.arange(400,dtype=float),idx)
    x = features(y)
    yp = y.copy(); yp.iloc[300:] = 1e8
    assert np.allclose(x.iloc[300],features(yp).iloc[300])
    assert quantile90(np.arange(1,10)) == 9
    assert np.array_equal(bounds(np.arange(56),SEED),bounds(np.arange(56),SEED))
    t = pd.DataFrame({'y':1.,'err_model':0.,'err_p24':1.,'covered':True,'upper':1.,'lower':0.,'label_available_at':idx+pd.Timedelta(hours=1)},index=idx)
    assert evidence(t,idx[-1],1)['point'] == 'UNKNOWN'
    print('Integrity self-tests passed',flush=True)

def main():
    selftest()
    if OUT.exists(): raise RuntimeError('Output exists; preserve run and choose a new run ID before rerunning.')
    OUT.mkdir()
    files = [SRC/'data_raw/bdg2_electricity_raw.csv',SRC/'data_raw/bdg2_metadata.csv']
    manifest = {'started_utc':datetime.now(timezone.utc).isoformat(),'python':sys.version,'platform':platform.platform(),'numpy':np.__version__,'pandas':pd.__version__,'seed':SEED,'script_sha256':digest(Path(__file__)),'design_sha256':digest(ROOT/'DESIGN.md'),'inputs':{str(p):{'sha256':digest(p),'bytes':p.stat().st_size} for p in files}}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    meta = pd.read_csv(files[1]).set_index('building_id')
    header = pd.read_csv(files[0],nrows=0).columns
    entities = sorted(set(header[1:]) & set(meta.index))
    sites = sorted(meta.loc[entities,'site_id'].unique(),key=key)
    ndev = max(1,int(np.ceil(2*len(sites)/3)))
    devsites = sites[:ndev]
    pd.DataFrame({'site_id':sites,'role':['development' if s in devsites else 'reserved_this_pilot_only' for s in sites]}).to_csv(OUT/'site_registry.csv',index=False)
    cols = [e for e in entities if meta.loc[e,'site_id'] in devsites]
    # File is chronological hourly, verified below; load only first leap-year rows.
    raw = pd.read_csv(files[0],usecols=[header[0]]+cols,nrows=8784,index_col=0,parse_dates=True)
    assert raw.index.equals(pd.date_range('2016-01-01', '2016-12-31 23:00',freq='h')), 'Unexpected chronology; do not truncate silently'
    qc=[]; series={}; strata={}
    for e in cols:
        y = raw[e].astype(float)
        tz = meta.loc[e,'timezone']
        if pd.isna(tz):
            qc.append({'entity':e,'eligible':False,'reason':'missing_timezone'}); continue
        local = y.index.tz_localize(tz,ambiguous='NaT',nonexistent='NaT')
        bad_dst = local.isna()
        clean = y.where(np.isfinite(y)&(y>=0)&~bad_dst)
        train = clean[clean.index < '2016-07-01']
        scale = train.quantile(.99)
        ok = train.notna().mean()>=.9 and scale>0 and features(clean).loc[:'2016-06-30 23:00'].dropna().shape[0]>=3000
        qc.append({'entity':e,'site':meta.loc[e,'site_id'],'eligible':bool(ok),'train_valid_fraction':train.notna().mean(),'train_zero_fraction':(train==0).mean(),'train_q99':scale,'dst_masked_hours':int(bad_dst.sum())})
        if ok:
            series[e]=clean
            group=(meta.loc[e,'site_id'],meta.loc[e,'primaryspaceusage'])
            strata.setdefault(group,[]).append(e)
    pd.DataFrame(qc).to_csv(OUT/'eligibility_qc.csv',index=False)
    groups=sorted(strata,key=lambda x:key(str(x)))
    for g in groups: strata[g].sort(key=key)
    selected=[]
    while len(selected)<24 and any(strata.values()):
        for g in groups:
            if strata[g] and len(selected)<24: selected.append(strata[g].pop(0))
    exposed=set(); exposure_files=[]
    for p in (SRC/'artifacts').glob('*/split_registry.csv'):
        registry=pd.read_csv(p)
        if 'entity_id' in registry: exposed.update(registry.loc[registry.dataset_family=='BDG2','entity_id'])
        exposure_files.append({'path':str(p),'sha256':digest(p)})
    (OUT/'exposure_sources.json').write_text(json.dumps(exposure_files,indent=2),encoding='utf-8')
    registry=meta.loc[selected,['site_id','primaryspaceusage','timezone']].copy()
    registry['seen_in_prior_split_registry']=[e in exposed for e in selected]
    registry['external_unexposed_claim']=False
    registry.to_csv(OUT/'entity_registry.csv')
    all_tapes=[]; gates=[]; results=[]; counts=[]
    for i,e in enumerate(selected):
        y=series[e]; x=features(y); trainmask=(y.index<'2016-07-01')&y.notna()&x.notna().all(axis=1)
        scale=y.loc[:'2016-06-30 23:00'].quantile(.99)
        mu=x.loc[trainmask].mean(); sd=x.loc[trainmask].std().replace(0,1)
        z=(x-mu)/sd
        X=np.column_stack([np.ones(trainmask.sum()),z.loc[trainmask]])
        penalty=np.eye(X.shape[1]); penalty[0,0]=0
        beta=np.linalg.solve(X.T@X+penalty,X.T@(y.loc[trainmask].values/scale))
        pred=pd.Series(np.maximum(0,np.column_stack([np.ones(len(z)),z])@beta*scale),index=y.index)
        tape=pd.DataFrame({'y':y,'pred':pred,'p24':y.shift(24),'p168':y.shift(168),'volatility':x.std24}).dropna()
        tape=tape[tape.index>='2016-07-01'].copy()
        tape['issued_at']=tape.index
        tape['label_available_at']=tape.index+pd.Timedelta(hours=1)
        tape['err_model']=abs(tape.y-tape.pred); tape['err_p24']=abs(tape.y-tape.p24)
        cal=tape[tape.index<'2016-09-01']; assert len(cal)>500
        q=quantile90(cal.err_model)
        tape['lower']=np.maximum(0,tape.pred-q); tape['upper']=tape.pred+q
        tape['covered']=(tape.y>=tape.lower)&(tape.y<=tape.upper)
        tape['peak']=tape.y>y.loc[:'2016-06-30 23:00'].quantile(.95)
        updates=pd.date_range('2016-09-26','2016-12-31',freq='W-MON')
        ledger=pd.DataFrame([evidence(tape,u,scale) for u in updates]).set_index('update')
        state=ledger.reindex(tape.index,method='ffill')
        test=tape[tape.index>='2016-10-01'].copy(); st=state.loc[test.index]
        p=(st.point=='PASS').values; c=(st.interval=='PASS').values
        static=ledger.iloc[0]
        rng=np.random.default_rng(SEED+i)
        vol=(test.volatility<=cal.volatility.quantile(.8)).values
        rnd=rng.random(len(test))<.8
        policies={'always_model':(np.ones(len(test),bool),np.ones(len(test),bool)), 'always_p24':(np.zeros(len(test),bool),np.zeros(len(test),bool)), 'independent':(p,p&c),'joint':(p&c,p&c),'static_independent':(np.full(len(test),static.point=='PASS'),np.full(len(test),static.point=='PASS' and static.interval=='PASS')),'volatility_q80':(vol,vol),'random_q80':(rnd,rnd)}
        assert np.all(p >= (p&c))
        for name,(release,interval) in policies.items():
            err=np.where(release,test.err_model,test.err_p24)
            peaks=test.peak.values
            results.append({'entity':e,'site':meta.loc[e,'site_id'],'policy':name,'n':len(test),'peak_n':int(peaks.sum()),'point_availability':release.mean(),'interval_availability':interval.mean(),'system_nmae':err.mean()/scale,'released_nmae':test.err_model.values[release].mean()/scale if release.any() else np.nan,'released_coverage':test.covered.values[interval].mean() if interval.any() else np.nan,'peak_release_rate':release[peaks].mean() if peaks.any() else np.nan,'peak_system_nmae':err[peaks].mean()/scale if peaks.any() else np.nan,'interval_n':int(interval.sum()),'interval_covered_n':int(test.covered.values[interval].sum()),'q90_width_over_scale':2*q/scale})
        ledger['entity']=e; gates.append(ledger.reset_index())
        tape['entity']=e; tape['scale']=scale; tape['point_state']=state.point; tape['interval_state']=state.interval
        all_tapes.append(tape.rename_axis('target_time').reset_index())
        counts.append({'entity':e,'training_rows':int(trainmask.sum()),'calibration_rows':len(cal),'evaluation_rows':len(test),'evaluation_expected_hours':2208,'scale':scale,'q90':q})
        print(f'{i+1}/{len(selected)} {e}: {len(test)} evaluation rows',flush=True)
    pd.concat(all_tapes).to_csv(OUT/'forecast_tape.csv.gz',index=False,compression='gzip')
    ledger=pd.concat(gates); ledger.to_csv(OUT/'gate_ledger.csv',index=False)
    res=pd.DataFrame(results); res.to_csv(OUT/'policy_entity_metrics.csv',index=False)
    pd.DataFrame(counts).to_csv(OUT/'row_counts.csv',index=False)
    summary=res.groupby('policy').agg(entities=('entity','size'),point_availability=('point_availability','mean'),interval_availability=('interval_availability','mean'),system_nmae=('system_nmae','mean'),released_coverage_macro=('released_coverage','mean'),peak_release_rate=('peak_release_rate','mean'),peak_system_nmae=('peak_system_nmae','mean'),interval_n=('interval_n','sum'),interval_covered_n=('interval_covered_n','sum'))
    summary['released_coverage_micro']=summary.interval_covered_n/summary.interval_n.replace(0,np.nan)
    summary.to_csv(OUT/'policy_summary.csv')
    states=ledger.groupby(['point','interval']).size().rename('entity_updates').reset_index(); states.to_csv(OUT/'state_counts.csv',index=False)
    manifest['completed_utc']=datetime.now(timezone.utc).isoformat(); manifest['entities']=len(selected)
    manifest['outputs']={p.name:digest(p) for p in OUT.iterdir() if p.name!='manifest.json'}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(summary.to_string()); print(states.to_string(index=False))

if __name__=='__main__': main()
