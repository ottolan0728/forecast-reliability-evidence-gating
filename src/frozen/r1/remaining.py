from analyses import *
import time,platform,importlib.metadata
def e5_support():
    from architectures import data,P
    rows=[]
    for ds,e,site,y in data():
        yr=y.index[0].year;win=np.lib.stride_tricks.sliding_window_view(y.to_numpy(),169)[:,:168];ix=y.index[168:];ok=np.isfinite(win).all(1)&y.loc[ix].notna().to_numpy()
        july=int((ok&(ix>=pd.Timestamp(f'{yr}-07-01'))&(ix<pd.Timestamp(f'{yr}-08-01'))).sum());aug=int((ok&(ix>=pd.Timestamp(f'{yr}-08-01'))&(ix<pd.Timestamp(f'{yr}-09-01'))).sum())
        rows.append(dict(dataset=ds,entity=e,site=site,july_n=july,august_n=aug,support_pass=july>336 and aug>=336,classification='feasibility only; no evaluation loss read'))
    d=save(rows,P/'complete_cohort_support_inventory.csv')
    with (ROOT/'E5_FEASIBILITY_FAILURE.md').open('a',encoding='utf-8') as f:
        f.write(f'\nFull support inventory (all {len(d)} entities): {(~d.support_pass).sum()} fail the inherited July >336 / August >=336 rule after complete-window issueability. Six-entity smoke passed but did not establish whole-cohort feasibility. These support thresholds came from the original E1/C1 recipe and were retained by the locked frozen-style auxiliary/calibration design. No aggregate architecture-effect claims are reported. Completing the exact full-cohort stress test would require a prospectively authorized change to the missing-history/calibration specification; no such change was made. Partial trained checkpoints and logs remain available for audit only.\n')
    print('E5 support',len(d),'failed',int((~d.support_pass).sum()),flush=True)
def e6_metrics():
    p=folder('E6_metrics_compute');rows=[]
    for meta,a in all_tapes():
        y=a.y.to_numpy();ok=np.isfinite(y);pk=c.peakmask(a);scale=a.scale.to_numpy()
        for column in a.columns:
            if not column.startswith('switch_'):continue
            sw=a[column].to_numpy(bool);g=np.where(sw,a.fallback,a.pred);err=y-g
            rows.append(dict(**meta,policy=column[7:],n=int(ok.sum()),peak_n=int(pk.sum()),mae_native=c.mean(abs(err)),rmse_native=np.sqrt(c.mean(err**2)),nrmse=np.sqrt(c.mean((err/scale)**2)),peak_underprediction=c.mean(np.maximum(err[pk],0)/scale[pk]),max_peak_abs_normalized=np.max(abs(err[pk])/scale[pk]) if pk.any() else np.nan,peak_underpredicted_fraction=c.mean(err[pk]>0)))
    d=save(rows,p/'entity_extended_metrics.csv')
    cols=['nrmse','peak_underprediction','max_peak_abs_normalized','peak_underpredicted_fraction']
    save(d.groupby(['dataset','model','lag','policy'])[cols].mean().reset_index(),p/'normalized_entity_macro.csv')
    save(d.groupby(['dataset','model','lag','policy'])[cols].quantile([0,.25,.5,.75,1]).rename_axis(['dataset','model','lag','policy','quantile']).reset_index(),p/'normalized_entity_distributions.csv')
    print('E6 metrics',len(d),flush=True)
def e6_compute():
    from architectures import data,peakrss,pilot
    import joblib
    from sklearn.ensemble import HistGradientBoostingRegressor
    from threadpoolctl import threadpool_limits
    p=folder('E6_metrics_compute');series=data();reps=[next(z for z in series if z[0]==ds) for ds in ['E1','C1']];rows=[]
    config=dict(max_iter=150,learning_rate=.05,max_leaf_nodes=15,min_samples_leaf=30,l2_regularization=1,early_stopping=False,random_state=20260920)
    def bench(meta,phase,fn,n=1):
        fn() # exactly one warmup
        for repeat in range(3):
            start=time.perf_counter();result=fn();seconds=time.perf_counter()-start
            rows.append(dict(**meta,phase=phase,repeat=repeat+1,seconds=seconds,n_operations=n,amortized_seconds_per_operation=seconds/n,cpu_process_lifetime_peak_rss=peakrss(),gpu_peak_allocated_bytes=0,status='ENGINEERING_BENCHMARK'))
        return result
    for ds,e,site,y in reps:
        year=y.index[0].year;scale=y.loc[:f'{year}-06-30 23:00'].quantile(.99);x=pilot.features(y);train=(x.index<pd.Timestamp(f'{year}-07-01'))&x.notna().all(1)&y.notna();ix=x.index[(x.index>=pd.Timestamp(f'{year}-07-01'))&x.notna().all(1)]
        for model in ['Ridge','HGB']:
            meta=dict(dataset=ds,entity=e,model=model,lag=24)
            if model=='Ridge':
                mu=x[train].mean();sd=x[train].std().replace(0,1);X=np.column_stack([np.ones(train.sum()),((x[train]-mu)/sd)]);target=y[train].to_numpy()/scale;pen=np.eye(X.shape[1]);pen[0,0]=0
                beta=bench(meta,'one_time_point_fit',lambda:np.linalg.solve(X.T@X+pen,X.T@target));features=np.column_stack([np.ones(len(ix)),(x.loc[ix]-mu)/sd]);predict=lambda z:np.maximum(0,z@beta)*scale
            else:
                def fit():
                    h=HistGradientBoostingRegressor(**config)
                    with threadpool_limits(1):h.fit(x[train],y[train]/scale)
                    return h
                h=bench(meta,'one_time_point_fit',fit);features=x.loc[ix]
                def predict(z):
                    with threadpool_limits(1):return np.maximum(0,h.predict(z))*scale
            pred=bench(meta,'recurring_point_batch_inference',lambda:predict(features),len(ix));bench(meta,'recurring_point_single_row_inference',lambda:predict(features[-1:] if model=='Ridge' else features.iloc[-1:]))
            a=pd.DataFrame(dict(y=y.loc[ix],pred=pred,fallback=y.shift(24).loc[ix]),index=ix);july=(ix<pd.Timestamp(f'{year}-08-01'))&a.y.notna();aug=(ix>=pd.Timestamp(f'{year}-08-01'))&(ix<pd.Timestamp(f'{year}-09-01'))&a.y.notna();gain=(abs(a.y-a.pred)-abs(a.y-a.fallback))/scale
            gx=x.loc[ix].copy();gx['point']=a.pred/scale;gx['fallback']=a.fallback/scale;gx['disagreement']=gx.point-gx.fallback;gx['abs_disagreement']=abs(gx.disagreement)
            for kind,f,target in [('risk',x.loc[ix],np.log(np.maximum(abs(a.y-a.pred)/scale,1e-4))),('gain',gx,gain)]:
                def fitaux():
                    h=HistGradientBoostingRegressor(**{**config,'max_iter':100})
                    with threadpool_limits(1):h.fit(f.loc[july],target.loc[july])
                    return h
                haux=bench(meta,'one_time_'+kind+'_fit',fitaux)
                def score(z):
                    with threadpool_limits(1):return haux.predict(z)
                scores=bench(meta,'recurring_'+kind+'_batch_score',lambda:score(f),len(f));bench(meta,'recurring_'+kind+'_single_row_score',lambda:score(f.iloc[-1:]))
                if kind=='gain':a['gain_score']=scores
            a['gain']=gain
            def admit():
                cal=a.loc[aug];accepted=[]
                for th in [0,.001,.005,.01,.02]:
                    sw=cal.gain_score>th;d=(cal.gain*sw).resample('D').mean().reindex(pd.date_range(f'{year}-08-01',f'{year}-08-31'));lo,hi=pilot.bounds(d,20260920)
                    if sw.sum()>=48 and cal.index[sw].normalize().nunique()>=14 and lo>0:accepted.append((lo,th))
                return max(accepted)[1] if accepted else np.inf
            th=bench(meta,'one_time_august_admission_5thresholds',admit)
            bench(meta,'recurring_route_batch',lambda:np.where(a.gain_score.to_numpy()>th,a.fallback.to_numpy(),a.pred.to_numpy()),len(a))
            def interval():
                day=pd.Timestamp(f'{year}-10-01');hist=a[(a.index>=day-pd.Timedelta(days=28))&(a.index+pd.Timedelta(hours=1)<day)&a.y.notna()]
                return pilot.quantile90(abs(hist.y-hist.pred))
            bench(meta,'recurring_daily_interval_update',interval)
    save(rows,p/'compute_benchmark.csv')
    (p/'TIMING_HARNESS.md').write_text('Engineering-only representative reruns: lexicographically first entity per dataset, Ridge/HGB, lag24, one warmup then three measured repetitions; threadpool1. Batch times divided by row count are amortized throughput, not single-request latency; single-row inference measured separately. CPU peak RSS is process-lifetime Windows PeakWorkingSetSize, not incremental per-stage allocation. CPU-only GPU allocation=0. Neural complete-cohort timing unavailable because E5 support feasibility failed; partial20epoch fit timings are feasibility measurements, not three-repeat benchmarks. No engineered prediction replaces frozen scientific tapes. Hardware/environment in environment/.\n')
    print('E6 benchmark',len(rows),flush=True)
def e7():
    p=folder('E7_month_stability');rows=[]
    for meta,a in all_tapes():
        for month in [10,11,12]:
            z=a[a.index.month==month]
            for pol in ['gain_naive','gain_calibrated','uncertainty_scale20']:
                sw=z['switch_'+pol].to_numpy(bool);v,_=c.metrics(z,sw);valid=z.y.notna().to_numpy();gain=(abs(z.y-z.pred)-abs(z.y-z.fallback))/z.scale;sel=sw&valid
                rows.append(dict(**meta,month=month,policy=pol,scored_switch_n=int(sel.sum()),harmful_switch_n=int(((gain<0).to_numpy()&sel).sum()),harmful_switch_fraction=c.mean((gain<0).to_numpy()[sel]),**v))
    d=save(rows,p/'entity_month_results.csv');su=macro(d,['dataset','model','lag','policy','month']);harm=d.groupby(['dataset','model','lag','policy','month'])[['harmful_switch_n','scored_switch_n']].sum().reset_index();harm['pooled_harmful_switch_fraction']=harm.harmful_switch_n/harm.scored_switch_n;save(su.merge(harm),p/'summary.csv');print('E7',len(d),flush=True)
def alerts(y,g,cut):
    truth=y>cut;pred=g>cut;tp=int((truth&pred).sum());fp=int((~truth&pred).sum());fn=int((truth&~pred).sum());tn=int((~truth&~pred).sum())
    ratio=lambda a,b:a/b if b else np.nan
    return dict(tp=tp,fp=fp,fn=fn,tn=tn,recall=ratio(tp,tp+fn),precision=ratio(tp,tp+fp),miss_rate=ratio(fn,fn+tp),false_alarm_rate=ratio(fp,fp+tn),f1=ratio(2*tp,2*tp+fp+fn))
def e8():
    p=folder('E8_peak_alert');cuts=c.read(ROOT/'reproduction/r9_replay/results/train_peak_thresholds.csv',dtype={'entity':str}).set_index(['dataset','entity']);rows=[]
    for meta,a in all_tapes():
        a=a[a.y.notna()];cut=cuts.loc[(meta['dataset'],meta['entity']),'q95'];y=a.y.to_numpy();original=alerts(y,a.pred.to_numpy(),cut)
        for pol in ['keep','gain_naive','gain_calibrated','uncertainty_scale20']:
            sw=np.zeros(len(a),bool) if pol=='keep' else a['switch_'+pol].to_numpy(bool);g=np.where(sw,a.fallback,a.pred);v=alerts(y,g,cut)
            rows.append(dict(**meta,policy=pol,train_q95=cut,**v,**{'change_'+k:v[k]-original[k] for k in ['recall','precision','miss_rate','false_alarm_rate','f1']}))
    d=save(rows,p/'entity_alert_metrics.csv');cols=['recall','precision','miss_rate','false_alarm_rate','f1'];save(d.groupby(['dataset','model','lag','policy'])[cols+['change_'+x for x in cols]].mean().reset_index(),p/'entity_macro.csv');print('E8',len(d),flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
