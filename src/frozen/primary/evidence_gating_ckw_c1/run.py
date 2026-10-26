import os
os.environ['OMP_NUM_THREADS']='1'
os.environ['OPENBLAS_NUM_THREADS']='1'
from pathlib import Path
import sys,json,hashlib,importlib.metadata as im
from datetime import datetime,timezone
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parent
C0=ROOT.parent/'evidence_gating_ckw_c0'
sys.path.insert(0,str(ROOT.parent/'evidence_gating_pilot'))
import pilot
SEED=20260920
CONFIG=dict(max_iter=150,learning_rate=.05,max_leaf_nodes=15,min_samples_leaf=30,l2_regularization=1,early_stopping=False,random_state=SEED)
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()
def loaddev():
    for name,h in json.loads((C0/'audit_manifest.json').read_text()).items(): assert digest(C0/name)==h,name
    d=pd.read_csv(C0/'hourly_development.csv.gz',dtype={'area_code':str})
    d['timestamp']=pd.to_datetime(d.timestamp,utc=True).dt.tz_localize(None)
    return d.pivot(index='timestamp',columns='area_code',values='value_kwh')
def selfcheck():
    y=pd.Series(np.arange(800,dtype=float),pd.date_range('2025-01-01',periods=800,freq='h'))
    x=pilot.features(y)
    for value in [np.nan,1e9]:
        z=y.copy();z.iloc[400:]=value
        assert np.allclose(x.iloc[:401],pilot.features(z).iloc[:401],equal_nan=True)
    assert np.isnan(mean([]))
    assert np.isnan(ratio(np.array([0.]),np.array([0.]))[0])
def mean(a):
    a=np.asarray(a,float);a=a[np.isfinite(a)]
    return float(a.mean()) if len(a) else np.nan
def ratio(s,n):
    return np.divide(s,n,out=np.full_like(s,np.nan,dtype=float),where=n>0)
def freeze():
    assert not (ROOT/'freeze.json').exists()
    selfcheck();dev=loaddev();rows=[]
    for e in dev:
        y=dev[e];x=pilot.features(y);valid=x.notna().all(axis=1)&y.notna()
        tr=y.index<'2025-07-01';ju=(y.index>='2025-07-01')&(y.index<'2025-08-01');au=y.index>='2025-08-01'
        scale=y[tr].quantile(.99)
        ok=y[tr].notna().mean()>=.9 and scale>0 and valid[tr].sum()>=3000 and valid[ju].sum()>336 and valid[au].sum()>=336
        rows.append(dict(entity=e,eligible=bool(ok),train_rows=int(valid[tr].sum()),july_rows=int(valid[ju].sum()),august_rows=int(valid[au].sum()),scale=scale,peakcut=y[tr].quantile(.95)))
    pd.DataFrame(rows).to_csv(ROOT/'registry.csv',index=False)
    files=[ROOT/'run.py',ROOT/'DESIGN.md',ROOT/'registry.csv',Path(pilot.__file__),C0/'audit_manifest.json',C0/'hourly_development.csv.gz']
    (ROOT/'freeze.json').write_text(json.dumps(dict(frozen_utc=now(),hashes={str(p):digest(p) for p in files},environment={d.metadata['Name']:d.version for d in im.distributions()},checks='causal_features_and_empty_support_pass'),indent=2),encoding='utf-8')
    print(pd.DataFrame(rows).eligible.value_counts().to_dict())
def loadyear(dev):
    m=json.loads((ROOT/'download_manifest.json').read_text(encoding='utf-8-sig'));assert len(m)==4
    allrows=[]
    for item in m:
        p=ROOT/'raw'/item['file'];assert digest(p).lower()==item['sha256'].lower()
        d=pd.read_csv(p,dtype={'area_code':str});d['timestamp']=pd.to_datetime(d.timestamp,utc=True).dt.tz_localize(None)
        assert d.timestamp.min()>=pd.Timestamp('2025-08-31')
        assert set(d.columns)=={'area_code','timestamp','num_meter','value_kwh'}
        d['value_kwh']=d.value_kwh.where(np.isfinite(d.value_kwh)&(d.value_kwh>=0)&np.isfinite(d.num_meter)&(d.num_meter>0)&d.num_meter.mod(1).eq(0))
        allrows.append(d)
    d=pd.concat(allrows);assert not d.duplicated(['area_code','timestamp']).any()
    assert (d.timestamp.dt.minute.mod(15).eq(0)&d.timestamp.dt.second.eq(0)&d.timestamp.dt.microsecond.eq(0)).all()
    out=dev.reindex(pd.date_range('2025-01-01','2025-12-31 23:00',freq='h'))
    for e,g in d.groupby('area_code'):
        if e not in out: continue
        h=g.set_index('timestamp').value_kwh.resample('h').sum(min_count=4)
        h=h[(h.index>='2025-09-01')&(h.index<'2026-01-01')]
        out.loc[h.index,e]=h
    assert np.allclose(out.loc[dev.index],dev,equal_nan=True)
    return out
def run():
    frozen=json.loads((ROOT/'freeze.json').read_text())
    for p,h in frozen['hashes'].items(): assert digest(Path(p))==h,p
    assert (ROOT/'AUDIT_CLOSURE.md').exists()
    selfcheck();dev=loaddev();raw=loadyear(dev)
    out=ROOT/'results';assert not out.exists();out.mkdir();(out/'models').mkdir();(out/'tapes').mkdir()
    (out/'start.json').write_text(json.dumps({'started_utc':now(),'freeze_sha256':digest(ROOT/'freeze.json'),'downloads_sha256':digest(ROOT/'download_manifest.json')},indent=2))
    reg=pd.read_csv(ROOT/'registry.csv',dtype={'entity':str});reg=reg[reg.eligible].set_index('entity')
    metrics=[];candidates=[];admissions=[];dayrows=[]
    for n,e in enumerate(reg.index):
        y=raw[e];x=pilot.features(y);train=(y.index<'2025-07-01')&y.notna()&x.notna().all(axis=1)
        scale=reg.loc[e,'scale'];peakcut=reg.loc[e,'peakcut'];ix=x.index[(x.index>='2025-07-01')&x.notna().all(axis=1)]
        mu=x[train].mean();sd=x[train].std().replace(0,1);z=(x-mu)/sd
        X=np.column_stack([np.ones(train.sum()),z[train]]);pen=np.eye(X.shape[1]);pen[0,0]=0
        beta=np.linalg.solve(X.T@X+pen,X.T@(y[train]/scale));ridge=np.maximum(0,np.column_stack([np.ones(len(ix)),z.loc[ix]])@beta*scale)
        np.savez(out/'models'/f'{e}_Ridge.npz',beta=beta,mu=mu.values,sd=sd.values,features=x.columns.to_numpy(dtype=str),scale=scale)
        model=HistGradientBoostingRegressor(**CONFIG)
        with threadpool_limits(limits=1):model.fit(x[train],y[train]/scale);hgb=np.maximum(0,model.predict(x.loc[ix])*scale)
        joblib.dump(model,out/'models'/f'{e}_HGB.joblib')
        for name,pred in [('Ridge',ridge),('HGB',hgb)]:
            a=pd.DataFrame({'y':y.loc[ix],'pred':pred},index=ix);a['residual']=abs(a.y-a.pred);a['available']=a.index+pd.Timedelta(hours=1)
            july=(ix<'2025-08-01')&a.y.notna();aug=(ix>='2025-08-01')&(ix<'2025-09-01')&a.y.notna()
            assert july.sum()>336 and aug.sum()>=336
            risk=HistGradientBoostingRegressor(**{**CONFIG,'max_iter':100})
            with threadpool_limits(limits=1):risk.fit(x.loc[ix[july]],np.log(np.maximum(a.loc[july,'residual']/scale,1e-4)));a['risk']=np.exp(risk.predict(x.loc[ix]))
            joblib.dump(risk,out/'models'/f'{e}_{name}_risk.joblib')
            riskcut=a.loc[aug,'risk'].quantile(.8);fixed=pilot.quantile90(a.loc[aug,'residual'])
            radii={}
            for day in pd.date_range('2025-10-01','2025-12-31'):
                hist=a[(a.index>=day-pd.Timedelta(days=28))&(a.available<day)&a.y.notna()]
                radii[day]=pilot.quantile90(hist.residual) if len(hist)>=336 else fixed
            test=ix>=pd.Timestamp('2025-10-01')
            for lag in [1,24,168]:
                fallback=y.shift(lag).loc[ix];gain=(a.residual-abs(a.y-fallback))/scale
                gx=x.loc[ix].copy();gx['point']=a.pred/scale;gx['fallback']=fallback/scale;gx['disagreement']=gx.point-gx.fallback;gx['abs_disagreement']=abs(gx.disagreement)
                gm=HistGradientBoostingRegressor(**{**CONFIG,'max_iter':100})
                with threadpool_limits(limits=1):gm.fit(gx.loc[july],gain[july]);gs=gm.predict(gx)
                joblib.dump(gm,out/'models'/f'{e}_{name}_lag{lag}_gain.joblib')
                accepted=[]
                for th in [0,.001,.005,.01,.02]:
                    sw=gs[aug]>th;cal=gain[aug];days=cal.index[sw].normalize().nunique();daily=(cal*sw).resample('D').mean().reindex(pd.date_range('2025-08-01','2025-08-31'))
                    lo,hi=pilot.bounds(daily,SEED);ok=sw.sum()>=48 and days>=14 and lo>0
                    candidates.append(dict(entity=e,model=name,lag=lag,threshold=th,n=int(sw.sum()),days=days,lower=lo,upper=hi,admit=bool(ok)))
                    if ok:accepted.append((lo,th))
                threshold=max(accepted)[1] if accepted else np.inf
                admissions.append(dict(entity=e,model=name,lag=lag,threshold=threshold,enabled=bool(accepted)))
                t=a.loc[test,['y','pred','risk']].copy();t['fallback']=fallback[test];t['gain_score']=gs[test];t['scale']=scale;t['peakcut']=peakcut
                q=pd.Series(radii).reindex(t.index.normalize()).to_numpy();t['lower']=np.maximum(0,t.pred-q);t['upper']=t.pred+q
                valid=t.y.notna();peak=valid&(t.y>peakcut);em=abs(t.y-t.pred)/scale;ef=abs(t.y-t.fallback)/scale
                policies={'keep':np.zeros(len(t),bool),'always_fallback':np.ones(len(t),bool),'uncertainty_scale20':t.risk.to_numpy()>riskcut,'gain_naive':t.gain_score.to_numpy()>0,'gain_calibrated':t.gain_score.to_numpy()>threshold}
                for policy,sw in policies.items():
                    t['switch_'+policy]=sw;err=pd.Series(np.where(sw,ef,em),index=t.index);delta=err-em
                    if valid.any():assert np.isclose(mean(delta),mean(err)-mean(em))
                    retain=valid&~sw
                    metrics.append(dict(entity=e,model=name,lag=lag,policy=policy,calendar=2208,issued=len(t),scored=int(valid.sum()),peak_n=int(peak.sum()),nmae=mean(err),peak_nmae=mean(err[peak]),switch_rate=mean(sw),retained_coverage=mean(((t.y>=t.lower)&(t.y<=t.upper))[retain]),retained_width=mean(((t.upper-t.lower)/scale)[retain])))
                    if policy=='gain_calibrated' and lag in [1,24]:
                        for metric,mask in [('average',valid),('peak',peak)]:
                            calendar=pd.date_range('2025-10-01','2025-12-31')
                            if len(t):
                                dd=pd.DataFrame({'delta':delta.where(mask),'n':mask.astype(int)},index=t.index).resample('D').agg(total=('delta','sum'),count=('n','sum')).reindex(calendar,fill_value=0)
                            else:
                                dd=pd.DataFrame({'total':0.,'count':0},index=calendar)
                            dd['entity']=e;dd['model']=name;dd['lag']=lag;dd['metric']=metric;dayrows.append(dd.rename_axis('day').reset_index())
                t.rename_axis('target_time').to_csv(out/'tapes'/f'{e}_{name}_lag{lag}.csv.gz')
        print(f'{n+1}/{len(reg)} {e}',flush=True)
    r=pd.DataFrame(metrics);r.to_csv(out/'entity_metrics.csv',index=False);r.groupby(['model','lag','policy']).mean(numeric_only=True).to_csv(out/'summary.csv')
    pd.DataFrame(candidates).to_csv(out/'threshold_candidates.csv',index=False);pd.DataFrame(admissions).to_csv(out/'admissions.csv',index=False)
    days=pd.concat(dayrows);days.to_csv(out/'paired_daily.csv.gz',index=False)
    contrasts=[]
    for (model,lag,metric),g in days.groupby(['model','lag','metric']):
        sums=g.pivot(index='day',columns='entity',values='total').to_numpy();counts=g.pivot(index='day',columns='entity',values='count').to_numpy()
        effects=ratio(sums.sum(axis=0),counts.sum(axis=0));support=np.isfinite(effects);observed=mean(effects)
        rng=np.random.default_rng(SEED);draws=[]
        for b in range(2000):
            ix=((rng.integers(0,len(sums),int(np.ceil(len(sums)/7)))[:,None]+np.arange(7))%len(sums)).ravel()[:len(sums)]
            effects_b=ratio(sums[ix].sum(axis=0),counts[ix].sum(axis=0))
            draws.append(mean(effects_b[support]) if support.any() and np.isfinite(effects_b[support]).all() else np.nan)
        finite=np.asarray(draws);finite=finite[np.isfinite(finite)]
        intervals=np.quantile(finite,[.025,.975,.05/16,1-.05/16]) if len(finite)>=1900 else np.full(4,np.nan)
        contrasts.append(dict(model=model,lag=lag,metric=metric,entities=int(support.sum()),delta=observed,ci95_lower=intervals[0],ci95_upper=intervals[1],family_lower=intervals[2],family_upper=intervals[3],valid_bootstraps=len(finite),harm_entities=int((effects>1e-12).sum())))
    c=pd.DataFrame(contrasts);c.to_csv(out/'primary_contrasts.csv',index=False)
    (out/'manifest.json').write_text(json.dumps(dict(completed_utc=now(),freeze_sha256=digest(ROOT/'freeze.json'),outputs={str(p.relative_to(out)):digest(p) for p in out.rglob('*') if p.is_file() and p.name!='manifest.json'}),indent=2))
    print(c.to_string(index=False))
if __name__=='__main__':
    if sys.argv[1]=='freeze': freeze()
    elif sys.argv[1]=='run': run()
    else: raise ValueError('mode must be freeze or run')
