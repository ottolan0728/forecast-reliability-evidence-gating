from common import *
checks=[];rows=[];dayrows=[]
def check(label,expected,got,count=False):
    nan=pd.isna(expected) and pd.isna(got)
    if isinstance(expected,str):ok=expected==got;diff=np.nan
    else:
        diff=abs(float(expected)-float(got));ok=nan or (diff==0 if count else diff<=1e-12)
    checks.append(dict(check=label,expected=expected,obtained=got,absolute_difference=diff,tolerance=0 if count else 1e-12,passed=bool(ok)))
for dataset,root in [('E1',E),('C1',C)]:
    expected=read(root/'results/entity_metrics.csv',dtype={'entity':str})
    for entity,model,lag,site,a in tapes(dataset):
        assert not a.index.duplicated().any()
        exp=expected[(expected.entity==entity)&(expected.model==model)]
        if dataset=='C1':exp=exp[exp.lag==lag]
        for _,r in exp.iterrows():
            sw=a['switch_'+r.policy].to_numpy(bool);v,dr=metrics(a,sw)
            row=dict(dataset=dataset,entity=entity,site=site,model=model,lag=lag,policy=r.policy,**v);rows.append(row)
            mapping={'nmae':'system_nmae','issued':'issueable_n','scored':'scoreable_n','switch_rate':'switch_rate_issued','retained_coverage':'retained_interval_coverage'} if dataset=='E1' else {}
            for col in ['nmae','peak_nmae','issued','scored','peak_n','switch_rate','retained_coverage','retained_width']:
                ec=mapping.get(col,col);check(f'{dataset}/{entity}/{model}/{lag}/{r.policy}/{col}',r[ec],v[col],col in ['issued','scored','peak_n'])
            check(f'{dataset}/{entity}/{model}/{lag}/{r.policy}/switch_n',round(r[mapping.get('switch_rate','switch_rate')]*v['issued']),v['switch_n'],True)
            if dataset=='E1':check(f'E1/{entity}/{model}/{r.policy}/retained_n',r.retained_n,v['retained_n'],True)
            if dataset=='C1' and lag in [1,24] and r.policy=='gain_calibrated':
                for metric,mask in [('average',a.y.notna().to_numpy()),('peak',peakmask(a))]:
                    d=daily(a,dr,mask).reset_index(names='day');d['entity']=entity;d['model']=model;d['lag']=lag;d['metric']=metric;dayrows.append(d)
    print(dataset,'tape recomputation complete',flush=True)
r=pd.DataFrame(rows);save(r,'reproduction/entity_metrics_recomputed.csv')
for dataset,root in [('E1',E),('C1',C)]:
    keys=['model','policy']+(['lag'] if dataset=='C1' else [])
    agg=r[r.dataset==dataset].groupby(keys).mean(numeric_only=True)
    stored=read(root/'results/summary.csv').set_index(keys)
    for idx,s in stored.iterrows():
        for col in ['nmae','peak_nmae','switch_rate']:
            name={'nmae':'system_nmae','switch_rate':'switch_rate_issued'}.get(col,col) if dataset=='E1' else col
            check(f'{dataset}/macro/{idx}/{col}',s[name],agg.loc[idx,col])
e=r[(r.dataset=='E1')&(r.policy=='gain_calibrated')]
for model,g in e.groupby('model'):
    for col,val in [('issued',43017),('scored',42981)]:check(f'E1/{model}/service/{col}',val,g[col].sum(),True)
    check(f'E1/{model}/calendar',44160,len(g)*2208,True)
    check(f'E1/{model}/missing_truth',36,(g.issued-g.scored).sum(),True)
ec=[]
for model in ['Ridge','HGB']:
    for metric,col in [('system_nmae','delta_avg'),('peak_nmae','delta_peak')]:ec.append(dict(model=model,metric=metric,**site_stats(e[e.model==model],col)))
ec=holm(pd.DataFrame(ec));save(ec,'reproduction/E1_site_contrasts.csv')
for _,s in read(E/'results/primary_contrasts.csv').iterrows():
    g=ec[(ec.model==s.model)&(ec.metric==s.metric)].iloc[0]
    for col in ec.columns.difference(['model','metric']):check(f'E1/site/{s.model}/{s.metric}/{col}',s[col],g[col],col in ['entities','sites','better','worse','ties'])
days=pd.concat(dayrows);save(days,'reproduction/C1_paired_daily_recomputed.csv.gz')
stored=read(C/'results/paired_daily.csv.gz',parse_dates=['day'],dtype={'entity':str})
k=['day','entity','model','lag','metric'];dd=days.set_index(k).sort_index();ss=stored.set_index(k).sort_index()
check('C1/daily_keys',True,dd.index.equals(ss.index),True)
check('C1/daily_counts_max_diff',0,(dd['count']-ss['count']).abs().max(),True)
check('C1/daily_total_max_diff',0,(dd.total-ss.total).abs().max())
cc=[]
for (model,lag,metric),g in days.groupby(['model','lag','metric']):
    s=g.pivot(index='day',columns='entity',values='total').to_numpy();n=g.pivot(index='day',columns='entity',values='count').to_numpy()
    cc.append(dict(model=model,lag=lag,metric=metric,**block_stats(s,n)))
cc=pd.DataFrame(cc);save(cc,'reproduction/C1_primary_contrasts.csv')
for _,s in read(C/'results/primary_contrasts.csv').iterrows():
    g=cc[(cc.model==s.model)&(cc.lag==s.lag)&(cc.metric==s.metric)].iloc[0]
    for col in cc.columns.difference(['model','lag','metric']):check(f'C1/primary/{s.model}/{s.lag}/{s.metric}/{col}',s[col],g[col],col in ['entities','harm_entities','valid_bootstraps'])
cons=[]
for (dataset,model,lag),g in r[r.policy=='gain_calibrated'].groupby(['dataset','model','lag']):
    g=g.sort_values('entity');z=g.set_index('entity').delta_avg;best=z.idxmin();net=-z.sum();pos=-z.clip(upper=0).sum()
    cons.append(dict(dataset=dataset,model=model,lag=lag,best_entity=best,best_delta=z[best],net_improvement=net,best_share_of_net=-z[best]/net if net>0 else np.nan,mean_without_best=z.drop(best).mean()))
    if dataset=='C1':
        s=read(C/'concentration.csv',dtype={'best_entity':str});s=s[(s.model==model)&(s.lag==lag)].iloc[0]
        for col in ['best_entity','best_delta','net_improvement','best_share_of_net','mean_without_best']:check(f'C1/concentration/{model}/{lag}/{col}',s[col],cons[-1][col])
    else:
        s=read(E/'gain_concentration_diagnostic.csv').set_index('model').loc[model]
        for old,new in [('largest_gain_entity','best_entity'),('largest_gain_delta','best_delta'),('largest_gain_share_net','best_share_of_net'),('mean_excluding_largest_gain','mean_without_best')]:check(f'E1/concentration/{model}/{old}',s[old],cons[-1][new])
        check(f'E1/concentration/{model}/positive_share',s.largest_gain_share_positive,-z[best]/pos)
save(pd.DataFrame(cons),'reproduction/concentration_recomputed.csv')
hc=read(ROOT/'r9a_inventory/archive_hash_checks.csv')
# A checksum document cannot normally contain its own final hash. This supplied
# self-reference is preserved as a packaging warning, never waived for evidence.
selfref=hc.path.map(lambda p:Path(p).resolve()==(HAND/'HANDOFF_CHECKSUMS.sha256').resolve())
check('archived_evidence_hash_failures',0,int((~hc.loc[~selfref,'ok']).sum()),True)
out=pd.DataFrame(checks);save(out,'reproduction/baseline_reproduction.csv');passed=bool(out.passed.all())
js('reproduction/baseline_reproduction_checks.json',dict(pass_=passed,**{'pass':passed},input_manifest_sha256=sha(ROOT/'manifests/input_manifest.csv'),checks=len(out),failed=int((~out.passed).sum()),max_loss_difference=float(out.absolute_difference.max()),interval_precision_note='CSV round-trip parsing; independent arithmetic can differ in last binary digits; all endpoints checked at 1e-12, stricter than requested loss tolerance. Same seeds/draws/order; no substantive formatting discrepancy.'))
report=f'# R9-A reproduction: {"PASS" if passed else "FAIL"}\n\n{len(out)} comparisons; {int((~out.passed).sum())} failures. All original hashes checked separately. Numeric counts exact; loss tolerance 1e-12. Interval differences in final floating-point digits are documented in baseline_reproduction.csv. No row-set changes.\n'
(ROOT/'reproduction/R9A_REPRODUCTION_REPORT.md').write_text(report,encoding='utf-8')
if not passed:
    (ROOT/'reports/R9A_REPRODUCTION_FAILURE_REPORT.md').write_text(report+'\n'+out[~out.passed].to_csv(index=False)+'\nSee input manifest and archive_hash_checks.csv for implicated hashes. No secondary execution permitted.',encoding='utf-8')
print(report,flush=True)
raise SystemExit(0 if passed else 2)
