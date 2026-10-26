"""R1 E5 fixed architecture stress test; no scientific outcome-based tuning."""
from analyses import ROOT,PROJECT,MAP,c,folder,save,macro,STATUS
import os,sys,json,time,hashlib,importlib.util,ctypes,platform,importlib.metadata
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
sys.path.append(str(Path(MAP['original_outputs'])/'peak_mtl/r143/.venv/Lib/site-packages'))
import torch
from torch import nn
torch.set_num_threads(1);torch.use_deterministic_algorithms(True)
P=folder('E5_architectures')
for s in ['models','tapes','logs']:(P/s).mkdir(exist_ok=True)
sys.path.insert(0,str(Path(MAP['original_outputs'])/'evidence_gating_pilot'))
import pilot
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
class Network(nn.Module):
    def __init__(self,kind):
        super().__init__();self.kind=kind
        if kind=='LSTM':self.rnn=nn.LSTM(1,32,batch_first=True);self.drop=nn.Dropout(.1)
        else:
            self.conv=nn.ModuleList([nn.Conv1d(a,b,3,dilation=d) for a,b,d in [(1,16,1),(16,32,2),(32,32,4)]])
            self.drop=nn.Dropout(.1)
        self.head=nn.Linear(36,1)
    def forward(self,x,calendar):
        if self.kind=='LSTM':z=self.drop(self.rnn(x.unsqueeze(-1))[0][:,-1,:])
        else:
            z=x.unsqueeze(1)
            for conv,d in zip(self.conv,[1,2,4]):z=self.drop(torch.relu(conv(nn.functional.pad(z,(2*d,0)))))
            z=z[:,:,-1]
        return self.head(torch.cat([z,calendar],1)).squeeze(1)
def peakrss():
    class PMC(ctypes.Structure):
        _fields_=[('cb',ctypes.c_ulong),('PageFaultCount',ctypes.c_ulong)]+[(n,ctypes.c_size_t) for n in ['PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage']]
    p=PMC();p.cb=ctypes.sizeof(p)
    ctypes.windll.kernel32.GetCurrentProcess.restype=ctypes.c_void_p
    ctypes.windll.psapi.GetProcessMemoryInfo.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_ulong]
    ok=ctypes.windll.psapi.GetProcessMemoryInfo(ctypes.windll.kernel32.GetCurrentProcess(),ctypes.byref(p),p.cb)
    if not ok:raise ctypes.WinError()
    return p.PeakWorkingSetSize
def data():
    old=Path(MAP['original_outputs']);reg=c.read(c.E/'selected_registry.csv').set_index('building_id')
    rawpath=PROJECT/'work/r9_recovered_inputs/bdg2_electricity_raw.csv';first=pd.read_csv(rawpath,nrows=0).columns[0]
    raw=pd.read_csv(rawpath,usecols=[first]+list(reg.index),nrows=8784,index_col=0,parse_dates=True)
    prepare=module('frozen_prepare',c.E/'prepare.py');out=[]
    for e in sorted(reg.index):out.append(('E1',e,reg.loc[e,'site_id'],prepare.clean(raw[e],reg.loc[e,'timezone'])))
    ck=module('frozen_ckw',c.C/'run.py');whole=ck.loadyear(ck.loaddev());r=c.read(c.C/'registry.csv',dtype={'entity':str});r=r[r.eligible]
    for e in sorted(r.entity):out.append(('C1',e,'CKW',whole[e]))
    return out
def fit(ds,e,site,y,kind):
    seed=20261012+int(hashlib.sha256(e.encode()).hexdigest()[:8],16)%1000000
    torch.manual_seed(seed);np.random.seed(seed)
    year=y.index[0].year;scale=y.loc[:f'{year}-06-30 23:00'].quantile(.99);cut=y.loc[:f'{year}-06-30 23:00'].quantile(.95)
    # Target t uses y[t-168:t], never current/future truth.
    windows=np.lib.stride_tricks.sliding_window_view(y.to_numpy(),169)[:,:168].copy()/scale
    ix=y.index[168:];valid=np.isfinite(windows).all(1);windows=windows[valid];ix=ix[valid]
    target=y.loc[ix].to_numpy()/scale
    cal=np.column_stack([np.sin(2*np.pi*ix.hour/24),np.cos(2*np.pi*ix.hour/24),np.sin(2*np.pi*ix.dayofweek/7),np.cos(2*np.pi*ix.dayofweek/7)])
    tr=(ix<pd.Timestamp(f'{year}-07-01'))&np.isfinite(target)
    assert tr.sum()>0,(ds,e,'no training windows')
    xx=torch.tensor(windows,dtype=torch.float32);cc=torch.tensor(cal,dtype=torch.float32);tt=torch.tensor(target,dtype=torch.float32)
    ids=np.flatnonzero(tr);model=Network(kind);opt=torch.optim.Adam(model.parameters(),lr=.001);lossfn=nn.MSELoss();logs=[];start=time.perf_counter()
    for epoch in range(20):
        model.train();order=ids[torch.randperm(len(ids)).numpy()];total=0
        for begin in range(0,len(order),64):
            batch=order[begin:begin+64];opt.zero_grad();loss=lossfn(model(xx[batch],cc[batch]),tt[batch]);loss.backward()
            if kind=='LSTM':nn.utils.clip_grad_norm_(model.parameters(),1.)
            opt.step();total+=loss.item()*len(batch)
        logs.append(dict(epoch=epoch+1,train_mse=total/len(ids),elapsed_seconds=time.perf_counter()-start,seed=seed,train_n=len(ids)))
    fitsecs=time.perf_counter()-start;model.eval();start=time.perf_counter()
    with torch.no_grad():pred=np.concatenate([model(xx[j:j+256],cc[j:j+256]).numpy() for j in range(0,len(xx),256)])
    infsecs=time.perf_counter()-start;pred=np.maximum(0,pred)*scale
    stem=f'{ds}_{e}_{kind}';save(logs,P/'logs'/f'{stem}.csv');torch.save(model.state_dict(),P/'models'/f'{stem}.pt')
    a=pd.DataFrame(dict(y=y.loc[ix],pred=pred,fallback=y.shift(24).loc[ix]),index=ix);a=a[a.index>=pd.Timestamp(f'{year}-07-01')].copy();fx=pilot.features(y).loc[a.index]
    assert fx.notna().all().all()
    july=(a.index<pd.Timestamp(f'{year}-08-01'))&a.y.notna();aug=(a.index>=pd.Timestamp(f'{year}-08-01'))&(a.index<pd.Timestamp(f'{year}-09-01'))&a.y.notna()
    service=dict(dataset=ds,entity=e,model=kind,site=site,seed=seed,train_n=int(tr.sum()),july_n=int(july.sum()),august_n=int(aug.sum()),scale=scale,peakcut=cut,fit_seconds=fitsecs,inference_seconds=infsecs,inference_n=len(xx),cpu_process_peak_rss=peakrss(),gpu_peak_allocated_bytes=0,status=STATUS)
    assert july.sum()>336 and aug.sum()>=336,(ds,e,'insufficient frozen-style auxiliary/calibration support',service)
    config=dict(max_iter=100,learning_rate=.05,max_leaf_nodes=15,min_samples_leaf=30,l2_regularization=1,early_stopping=False,random_state=20260920)
    risk=HistGradientBoostingRegressor(**config);gainmodel=HistGradientBoostingRegressor(**config);a['residual']=abs(a.y-a.pred);a['gain']=(a.residual-abs(a.y-a.fallback))/scale
    gx=fx.copy();gx['point']=a.pred/scale;gx['fallback']=a.fallback/scale;gx['disagreement']=gx.point-gx.fallback;gx['abs_disagreement']=abs(gx.disagreement)
    with threadpool_limits(limits=1):
        start=time.perf_counter();risk.fit(fx.loc[july],np.log(np.maximum(a.loc[july,'residual']/scale,1e-4)));service['risk_fit_seconds']=time.perf_counter()-start
        start=time.perf_counter();gainmodel.fit(gx.loc[july],a.loc[july,'gain']);service['gain_fit_seconds']=time.perf_counter()-start
        a['risk']=np.exp(risk.predict(fx));a['gain_score']=gainmodel.predict(gx)
    import joblib
    joblib.dump(risk,P/'models'/f'{stem}_risk.joblib');joblib.dump(gainmodel,P/'models'/f'{stem}_gain.joblib')
    caldata=a.loc[aug];accepted=[];candidates=[];start=time.perf_counter()
    for th in [0,.001,.005,.01,.02]:
        sw=caldata.gain_score>th;days=caldata.index[sw].normalize().nunique();daily=(caldata.gain*sw).resample('D').mean().reindex(pd.date_range(f'{year}-08-01',f'{year}-08-31'))
        lo,hi=pilot.bounds(daily,20260920);admit=sw.sum()>=48 and days>=14 and lo>0
        candidates.append(dict(threshold=th,n=int(sw.sum()),days=days,lower=lo,upper=hi,admit=bool(admit)))
        if admit:accepted.append((lo,th))
    threshold=max(accepted)[1] if accepted else np.inf;service['calibration_seconds']=time.perf_counter()-start
    radii={};fixed=pilot.quantile90(caldata.residual)
    for day in pd.date_range(f'{year}-10-01',f'{year}-12-31'):
        hist=a[(a.index>=day-pd.Timedelta(days=28))&(a.index+pd.Timedelta(hours=1)<day)&a.y.notna()]
        radii[day]=pilot.quantile90(hist.residual) if len(hist)>=336 else fixed
    t=a.loc[a.index>=pd.Timestamp(f'{year}-10-01')].copy();rr=pd.Series(radii).reindex(t.index.normalize()).to_numpy();t['scale']=scale;t['peakcut']=cut;t['lower']=np.maximum(0,t.pred-rr);t['upper']=t.pred+rr
    policies=dict(keep=np.zeros(len(t),bool),gain_naive=t.gain_score.to_numpy()>0,gain_calibrated=t.gain_score.to_numpy()>threshold,uncertainty_scale20=t.risk.to_numpy()>caldata.risk.quantile(.8))
    for pol,sw in policies.items():t['switch_'+pol]=sw
    # Save tapes but defer aggregate scientific evaluation until the six-entity smoke gate passes.
    t.rename_axis('target_time').to_csv(P/'tapes'/f'{stem}.csv.gz');save(candidates,P/'logs'/f'{stem}_candidates.csv')
    service.update(threshold=threshold,calendar_n=2208,issued_n=len(t),scoreable_n=int(t.y.notna().sum()),missing_issue_n=2208-len(t))
    (P/'logs'/f'{stem}_service.json').write_text(json.dumps(service,indent=2),encoding='utf-8')
    print(ds,e,kind,'fit_seconds',round(fitsecs,2),'issued',len(t),flush=True)
    return service
def main():
    config=dict(seed_base=20261012,lookback=168,lstm_hidden=32,lstm_layers=1,tcn_channels=[16,32,32],tcn_kernel=3,tcn_dilations=[1,2,4],dropout=.1,epochs=20,batch_size=64,lr=.001,device='cpu',torch=torch.__version__,plan_sha256=c.sha(ROOT/'PLAN_LOCK.md'))
    (P/'architecture_config.json').write_text(json.dumps(config,indent=2));series=data();smoke=[z for ds,n in [('E1',2),('C1',4)] for z in [q for q in series if q[0]==ds][:n]]
    order=smoke+[z for z in series if (z[0],z[1]) not in {(s[0],s[1]) for s in smoke}];services=[]
    try:
        for i,(ds,e,site,y) in enumerate(order):
            for kind in ['LSTM','TCN']:services.append(fit(ds,e,site,y,kind))
            if i==5:
                (P/'SMOKE_GATE.json').write_text(json.dumps(dict(pass_=True,entities=[(z[0],z[1]) for z in smoke],fits=len(services),max_fit_seconds=max(s['fit_seconds'] for s in services),scientific_aggregate_outcomes_accessed=False),indent=2))
        save(services,P/'service_denominators.csv');rows=[]
        for s in services:
            a=c.read(P/'tapes'/f"{s['dataset']}_{s['entity']}_{s['model']}.csv.gz",parse_dates=['target_time']).set_index('target_time')
            for pol in ['keep','gain_naive','gain_calibrated','uncertainty_scale20']:
                v,_=c.metrics(a,a['switch_'+pol]);rows.append(dict(dataset=s['dataset'],entity=s['entity'],site=s['site'],model=s['model'],lag=24,policy=pol,status=STATUS,**v))
        df=save(rows,P/'entity_results.csv');save(macro(df,['dataset','model','lag','policy']),P/'summary.csv')
    except Exception as exc:
        save(services,P/'partial_service_denominators.csv')
        (ROOT/'E5_FEASIBILITY_FAILURE.md').write_text('# E5 feasibility failure\n\n'+repr(exc)+'\n\nNo architecture substituted, no entity silently removed. Partial tapes/logs are engineering/feasibility artifacts only; no complete-cohort scientific architecture claim.\n',encoding='utf-8');raise
if __name__=='__main__':main()
