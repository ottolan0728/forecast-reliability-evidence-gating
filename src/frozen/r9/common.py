import os
os.environ['OMP_NUM_THREADS']='1'
os.environ['OPENBLAS_NUM_THREADS']='1'
from pathlib import Path
import json, hashlib, itertools
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
BASE=Path(os.environ.get('R9_SOURCE_OUTPUTS',str(ROOT/'frozen_inputs/outputs' if (ROOT/'frozen_inputs/outputs').exists() else ROOT.parent))).resolve()
E=BASE/'evidence_gating_external'
C=BASE/'evidence_gating_ckw_c1'
C0=BASE/'evidence_gating_ckw_c0'
HAND=Path(os.environ.get('R9_HANDOFF',str(ROOT/'frozen_inputs/handoff' if (ROOT/'frozen_inputs/handoff').exists() else BASE.parent/'work/r9_handoff_20260930/CODEX_R9_ABLATION_HANDOFF_20260930')))
BDG2_RAW=Path(os.environ.get('R9_BDG2_RAW','PRIVATE_SOURCE/bdg2_electricity_raw.csv'))
SEED=20260930
FROZEN_SEED=20260920
for name in ['environment','manifests','r9a_inventory','reproduction','results','reports','tests','figures/previews']:
    (ROOT/name).mkdir(parents=True,exist_ok=True)
def resolve_input(p):
    p=Path(p)
    if p.exists():return p
    m=ROOT/'manifests/bundled_input_map.json'
    if m.exists():
        d=json.loads(m.read_text(encoding='utf-8'));key=str(p).replace('\\','/')
        if key in d['inputs']:return ROOT/d['inputs'][key]
        old=d['original_run_root'].replace('\\','/')
        if key.startswith(old+'/'):return ROOT/key[len(old)+1:]
    return p
def sha(p):
    h=hashlib.sha256()
    with resolve_input(p).open('rb') as f:
        for chunk in iter(lambda:f.read(2**20),b''):h.update(chunk)
    return h.hexdigest()
def read(p,**kw):return pd.read_csv(resolve_input(p),float_precision='round_trip',**kw)
def save(d,p):d.to_csv(ROOT/p,index=False)
def js(p,d): (ROOT/p).write_text(json.dumps(d,indent=2,default=str),encoding='utf-8')
def mean(x):
    x=np.asarray(x,float);x=x[np.isfinite(x)]
    return x.mean() if len(x) else np.nan
def gate():
    result=json.loads((ROOT/'reproduction/baseline_reproduction_checks.json').read_text())
    assert result['pass'], 'R9-A must pass'
    assert sha(ROOT/'manifests/input_manifest.csv')==result['input_manifest_sha256'], 'PASS is bound to a different input inventory'
    for _,r in read(ROOT/'manifests/input_manifest.csv').iterrows():
        assert resolve_input(r.path).stat().st_size==r['size'] and sha(r.path)==r.sha256, 'Frozen input changed: '+r.path
    cm=ROOT/'results/calibration_score_manifest.csv'
    if cm.exists():
        for _,r in read(cm).iterrows():assert sha(r.path)==r.sha256,'Recovered score changed: '+r.path
def tapes(dataset):
    if dataset=='E1':
        t=read(E/'results/issued_forecast_tape.csv.gz',parse_dates=['target_time'])
        reg=read(E/'selected_registry.csv').set_index('building_id')
        for (entity,model),a in t.groupby(['entity','model']):
            a=a.set_index('target_time').sort_index();a['fallback']=a.p24
            yield entity,model,24,reg.loc[entity,'site_id'],a
    else:
        for p in sorted((C/'results/tapes').glob('*.csv.gz')):
            entity,model,lag=p.name.removesuffix('.csv.gz').split('_')
            yield entity,model,int(lag[3:]),'CKW',read(p,parse_dates=['target_time']).set_index('target_time')
def peakmask(a):
    return a.y.notna().to_numpy() & ((a.y>a.peakcut).to_numpy() if 'peakcut' in a else a.peak.eq(True).to_numpy(bool))
def metrics(a,sw,peak=None,fallback=None):
    sw=np.asarray(sw,bool);f=a.pred.to_numpy();b=a.fallback.to_numpy() if fallback is None else np.asarray(fallback)
    y=a.y.to_numpy();scale=a.scale.to_numpy();ok=np.isfinite(y)
    assert np.isfinite(f).all() and np.isfinite(b).all()
    g=np.where(sw,b,f);loss=abs(y-g)/scale;keep=abs(y-f)/scale;dg=keep-abs(y-b)/scale;dr=loss-keep
    assert np.allclose(g,(1-sw.astype(int))*f+sw.astype(int)*b,rtol=0,atol=1e-10)
    assert np.allclose(dr[ok],(-sw.astype(int)*dg)[ok],rtol=0,atol=1e-12)
    pk=peakmask(a) if peak is None else np.asarray(peak,bool)&ok
    retained=ok&~sw
    return dict(issued=len(a),scored=int(ok.sum()),peak_n=int(pk.sum()),switch_n=int(sw.sum()),switch_rate=float(sw.mean()),retained_n=int(retained.sum()),nmae=mean(loss),peak_nmae=mean(loss[pk]),delta_avg=mean(dr),delta_peak=mean(dr[pk]),retained_coverage=mean(((y>=a.lower)&(y<=a.upper))[retained]),retained_width=mean(((a.upper-a.lower)/scale)[retained])),dr
def daily(a,delta,mask):
    d=pd.DataFrame({'total':np.where(mask,delta,0.),'count':np.asarray(mask,int)},index=a.index).resample('D').sum()
    return d.reindex(pd.date_range(f'{a.index[0].year}-10-01',f'{a.index[0].year}-12-31'),fill_value=0)
def block_indices(n,block,seed=FROZEN_SEED,draws=2000):
    rng=np.random.default_rng(seed)
    return ((rng.integers(0,n,(draws,int(np.ceil(n/block))))[:,:,None]+np.arange(block))%n).reshape(draws,-1)[:,:n]
def block_stats(sums,counts,block=7):
    sums=np.asarray(sums);counts=np.asarray(counts)
    def ratio(s,n):return np.divide(s,n,out=np.full(s.shape,np.nan),where=n>0)
    effects=ratio(sums.sum(0),counts.sum(0));support=np.isfinite(effects)
    vals=[]
    for ix in block_indices(len(sums),block):
        e=ratio(sums[ix].sum(0),counts[ix].sum(0))[support]
        vals.append(e.mean() if len(e) and np.isfinite(e).all() else np.nan)
    finite=np.array(vals);finite=finite[np.isfinite(finite)]
    ci=np.quantile(finite,[.025,.975,.05/16,1-.05/16]) if len(finite)>=1900 else [np.nan]*4
    return dict(entities=int(support.sum()),delta=mean(effects),ci95_lower=ci[0],ci95_upper=ci[1],family_lower=ci[2],family_upper=ci[3],valid_bootstraps=len(finite),harm_entities=int((effects>1e-12).sum()))
def site_stats(frame,value):
    f=frame.dropna(subset=[value]);d=f.groupby('site')[value].mean().to_numpy();lo=hi=p=np.nan
    if len(d)>=2:
        rng=np.random.default_rng(FROZEN_SEED);bs=d[rng.integers(0,len(d),(5000,len(d)))].mean(1);lo,hi=np.quantile(bs,[.025,.975])
        signs=np.array(list(itertools.product([-1,1],repeat=len(d))))
        p=float(np.mean(abs((signs*d).mean(1))>=abs(d.mean())-1e-14))
    return dict(entities=len(f),sites=len(d),site_mean_delta=mean(d),ci_low=lo,ci_high=hi,p_raw=p,better=int((f[value]<-1e-12).sum()),worse=int((f[value]>1e-12).sum()),ties=int((abs(f[value])<=1e-12).sum()))
def holm(d):
    d=d.copy();order=d.p_raw.dropna().sort_values().index;d['p_holm']=np.nan
    vals=np.maximum.accumulate([(len(order)-i)*d.loc[j,'p_raw'] for i,j in enumerate(order)])
    for j,v in zip(order,vals):d.loc[j,'p_holm']=min(1,v)
    return d
