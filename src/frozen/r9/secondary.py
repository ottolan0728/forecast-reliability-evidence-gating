from common import *
def summary(rows,keys):
    df=pd.DataFrame(rows);out=[]
    for k,g in df.groupby(keys,dropna=False):
        k=k if isinstance(k,tuple) else (k,)
        d=dict(zip(keys,k));d.update(entities=len(g),peak_entities=int(g.delta_peak.notna().sum()),issued=int(g.issued.sum()),scored=int(g.scored.sum()),switch_n=int(g.switch_n.sum()),switch_rate_pooled=g.switch_n.sum()/g.issued.sum(),switch_rate_macro=g.switch_rate.mean(),retained_n=int(g.retained_n.sum()),delta_avg=g.delta_avg.mean(),delta_peak=g.delta_peak.mean(),harm_avg=int((g.delta_avg>1e-12).sum()),harm_peak=int((g.delta_peak>1e-12).sum()))
        for c in ['calibration_n','calibration_switch_n','calibration_days']:
            if c in g:d[c]=int(g[c].sum())
        if 'calibration_switch_rate' in g:d['calibration_switch_rate_macro']=g.calibration_switch_rate.mean()
        d['status']='secondary/opened-cohort diagnostic';out.append(d)
    return pd.DataFrame(out)
def source(dataset,entity,model,lag):
    p=E/'results/issued_forecast_tape.csv.gz' if dataset=='E1' else C/'results/tapes'/f'{entity}_{model}_lag{lag}.csv.gz'
    return dict(source_path=str(p),source_sha256=sha(p))
def a1():
    gate();rows=[]
    for dataset in ['E1','C1']:
        for entity,model,lag,site,a in tapes(dataset):
            path=ROOT/'results/calibration_scores'/f'{dataset}_{entity}_{model}_lag{lag}.csv.gz';cal=read(path)
            for budget in [.1,.2,.3]:
                for policy,col in [('residual_risk','risk'),('comparative_gain','gain_score')]:
                    threshold=cal[col].quantile(1-budget);sw=a[col].to_numpy()>threshold;cs=cal[col]>threshold
                    v,_=metrics(a,sw)
                    rows.append(dict(dataset=dataset,entity=entity,site=site,model=model,lag=lag,policy=policy,target_budget=budget,threshold=threshold,tie_rule='strict_greater_than_linear_quantile',calibration_n=len(cal),calibration_switch_n=int(cs.sum()),calibration_switch_rate=float(cs.mean()),calibration_source=str(path),calibration_sha256=sha(path),mask_sha256=hashlib.sha256(sw.tobytes()).hexdigest(),**v,**source(dataset,entity,model,lag)))
    save(pd.DataFrame(rows),'results/A1_common_budget_raw.csv');save(summary(rows,['dataset','model','lag','target_budget','policy']),'results/A1_common_budget_summary.csv')
    (ROOT/'reports/A1_RANDOM_COMPARATOR_STATUS.md').write_text('# Random comparator\n\nNo deployable August-defined random comparator exists in frozen code. None invented. Optional A1b was not executed; all mandatory common-budget risk/gain cells are reported. No random-policy inference is claimed.\n')
def a2():
    gate();rows=[];lost=[]
    # CKW tapes share complete predictor/fallback indices. All three source lags
    # and three frozen masks are retained, including secondary lag168 sources.
    for entity,model,lag,site,a in tapes('C1'):
        alt={l:read(C/'results/tapes'/f'{entity}_{model}_lag{l}.csv.gz',parse_dates=['target_time']).set_index('target_time') for l in [1,24,168]}
        for l,t in alt.items():
            assert a.index.equals(t.index)
            for col in ['y','pred','scale']:assert np.allclose(a[col],t[col],rtol=0,atol=0,equal_nan=True)
            assert np.isfinite(t.fallback).all()
        common=a.y.notna()
        for t in alt.values():common &= t.fallback.notna()
        lost.append(dict(entity=entity,model=model,source_lag=lag,original_scoreable=int(a.y.notna().sum()),common_scoreable=int(common.sum()),lost_n=int((a.y.notna()&~common).sum()),reason='none: all alternative fallbacks available'))
        assert np.array_equal(common,a.y.notna())
        for policy in ['gain_calibrated','gain_naive','uncertainty_scale20']:
            sw=a['switch_'+policy].to_numpy(bool);mh=hashlib.sha256(sw.tobytes()).hexdigest()
            for delivered in [0,1,24,168]:
                fb=a.pred if delivered==0 else alt[delivered].fallback
                v,_=metrics(a,sw,fallback=fb)
                rows.append(dict(dataset='C1',entity=entity,site=site,model=model,source_lag=lag,policy=policy,delivered_lag=delivered,mask_sha256=mh,**v,**source('C1',entity,model,lag)))
    save(pd.DataFrame(rows),'results/A2_same_mask_fallback_raw.csv');save(summary(rows,['dataset','model','source_lag','policy','delivered_lag']),'results/A2_same_mask_fallback_summary.csv');save(pd.DataFrame(lost),'results/A2_row_intersection_audit.csv')
def a3():
    gate();rows=[];daygroups={}
    for dataset,root in [('E1',E),('C1',C)]:
        candidates=read(root/'results/threshold_candidates.csv',dtype={'entity':str});admissions=read(root/'results/admissions.csv',dtype={'entity':str})
        for entity,model,lag,site,a in tapes(dataset):
            c=candidates[(candidates.entity==entity)&(candidates.model==model)]
            ad=admissions[(admissions.entity==entity)&(admissions.model==model)]
            if dataset=='C1':c=c[c.lag==lag];ad=ad[ad.lag==lag]
            threshold=ad.iloc[0].threshold
            cp=ROOT/'results/calibration_scores'/f'{dataset}_{entity}_{model}_lag{lag}.csv.gz';cal=read(cp,parse_dates=['target_time'])
            for variant,th in [('naive',0.),('fixed_0.001',.001),('fixed_0.005',.005),('fixed_0.01',.01),('fixed_0.02',.02),('frozen_admitted',threshold)]:
                sw=a.gain_score.to_numpy()>th;cs=cal.gain_score>th;v,dr=metrics(a,sw)
                record=c[c.threshold==th]
                lb=float(record.lower.iloc[0]) if len(record) else np.nan
                admitted=bool(record['admitted' if dataset=='E1' else 'admit'].iloc[0]) if len(record) else False
                if variant=='frozen_admitted':assert np.array_equal(sw,a.switch_gain_calibrated.to_numpy(bool))
                rows.append(dict(dataset=dataset,entity=entity,site=site,model=model,lag=lag,variant=variant,threshold=th,calibration_n=len(cal),calibration_switch_n=int(cs.sum()),calibration_days=int(cal.loc[cs,'target_time'].dt.normalize().nunique()),calibration_switch_rate=float(cs.mean()),august_lower_bound=lb,august_candidate_admitted=admitted,calibration_source=str(cp),calibration_sha256=sha(cp),**v,**source(dataset,entity,model,lag)))
                if dataset=='C1':
                    for metric,mask in [('average',a.y.notna().to_numpy()),('peak',peakmask(a))]:
                        daygroups.setdefault((model,lag,variant,metric),[]).append((entity,daily(a,dr,mask)))
    df=pd.DataFrame(rows);save(df,'results/A3_admission_stage_raw.csv');save(summary(rows,['dataset','model','lag','variant']),'results/A3_admission_stage_summary.csv')
    infer=[]
    for (model,lag,variant,metric),values in daygroups.items():
        values.sort(key=lambda v:v[0]);s=np.column_stack([v.total for _,v in values]);n=np.column_stack([v['count'] for _,v in values]);bs=block_stats(s,n)
        bs.pop('family_lower');bs.pop('family_upper')
        infer.append(dict(dataset='C1',model=model,lag=lag,variant=variant,metric=metric,block_days=7,inference_status='exploratory ordinary intervals; no global secondary multiplicity adjustment',**bs))
    for variant,g in df[df.dataset=='E1'].groupby('variant'):
        rr=[]
        for model,h in g.groupby('model'):
            for metric,col in [('average','delta_avg'),('peak','delta_peak')]:rr.append(dict(dataset='E1',model=model,lag=24,variant=variant,metric=metric,**site_stats(h,col)))
        z=holm(pd.DataFrame(rr));z['inference_status']='Holm four contrasts within variant only; not across variants';infer.extend(z.to_dict('records'))
    save(pd.DataFrame(infer),'results/A3_inference.csv')
def a5():
    gate();cuts=read(ROOT/'results/train_peak_thresholds.csv',dtype={'entity':str}).set_index(['dataset','entity']);rows=[];daygroups={}
    for dataset in ['E1','C1']:
        for entity,model,lag,site,a in tapes(dataset):
            if dataset=='C1' and lag not in [1,24]:continue
            for quantile in [90,95,99]:
                cut=cuts.loc[(dataset,entity),f'q{quantile}'];mask=(a.y>cut).to_numpy()
                if quantile==95:assert np.array_equal(mask,peakmask(a))
                v,dr=metrics(a,a.switch_gain_calibrated,peak=mask)
                rows.append(dict(dataset=dataset,entity=entity,site=site,model=model,lag=lag,quantile=quantile,train_threshold=cut,**v))
                if dataset=='C1':
                    for metric,m in [('average',a.y.notna().to_numpy()),('peak',mask)]:daygroups.setdefault((model,lag,quantile,metric),[]).append((entity,daily(a,dr,m)))
    df=pd.DataFrame(rows);save(df,'results/A5_peak_entity_raw.csv');out=[]
    for (model,lag,q,metric),values in daygroups.items():
        values.sort(key=lambda v:v[0]);s=np.column_stack([v.total for _,v in values]);n=np.column_stack([v['count'] for _,v in values])
        for block in [7,14,28]:out.append(dict(dataset='C1',model=model,lag=lag,quantile=q,metric=metric,block_days=block,primary_setting=(q==95 and block==7),interval_scope='eight contrasts within cell only; not whole robustness grid',**block_stats(s,n,block)))
    for q,g in df[df.dataset=='E1'].groupby('quantile'):
        rr=[]
        for model,h in g.groupby('model'):
            for metric,col in [('average','delta_avg'),('peak','delta_peak')]:rr.append(dict(dataset='E1',model=model,lag=24,quantile=q,metric=metric,block_days=np.nan,primary_setting=q==95,entity_macro_delta=h[col].mean(),**site_stats(h,col)))
        out.extend(holm(pd.DataFrame(rr)).to_dict('records'))
    result=pd.DataFrame(out);save(result,'results/A5_peak_block_robustness.csv')
    stable=[]
    for _,v in result[result.dataset=='C1'].iterrows():
        p=result[(result.dataset=='C1')&(result.model==v.model)&(result.lag==v.lag)&(result.metric==v.metric)&result.primary_setting].iloc[0]
        def conclusion(x):return 'supported_negative' if x.family_upper<0 else ('supported_positive' if x.family_lower>0 else 'interval_crosses_zero_or_unavailable')
        base=conclusion(p);now=conclusion(v)
        stable.append(dict(dataset='C1',model=v.model,lag=v.lag,metric=v.metric,quantile=v['quantile'],block_days=v.block_days,entities=v.entities,primary_conclusion=base,cell_conclusion=now,stability='unchanged' if base==now else ('weakened' if now=='interval_crosses_zero_or_unavailable' else 'changed'),point_sign_changed=np.sign(v.delta)!=np.sign(p.delta)))
    for _,v in result[result.dataset=='E1'].iterrows():
        p=result[(result.dataset=='E1')&(result.model==v.model)&(result.metric==v.metric)&result.primary_setting].iloc[0]
        def e_conclusion(x):return ('supported_negative' if x.site_mean_delta<0 else 'supported_positive') if x.p_holm<.05 else 'not_supported_by_Holm'
        base=e_conclusion(p);now=e_conclusion(v)
        stable.append(dict(dataset='E1',model=v.model,lag=v.lag,metric=v.metric,quantile=v['quantile'],block_days=np.nan,entities=v.entities,sites=v.sites,primary_conclusion=base,cell_conclusion=now,stability='unchanged' if base==now else 'changed',point_sign_changed=np.sign(v.site_mean_delta)!=np.sign(p.site_mean_delta)))
    save(pd.DataFrame(stable),'results/A5_stability.csv')
def r9r():
    gate();r=read(ROOT/'reproduction/entity_metrics_recomputed.csv',dtype={'entity':str});rows=[]
    # The decision note identifies Ridge/uncertainty_scale20, but does not name
    # one fallback. Preserve all three exact configurations, not closest row.
    for lag in [1,24,168]:
        z=r[(r.dataset=='C1')&(r.model=='Ridge')&(r.lag==lag)];keep=z[z.policy=='keep'];g=z[z.policy=='uncertainty_scale20']
        rows.append(dict(dataset='C1',model='Ridge',fallback=f'lag-{lag}',policy='uncertainty_scale20',nominal_coverage=.9,retained_coverage=g.retained_coverage.mean(),coverage_aggregation='equal-area macro of scored retained coverage',keep_coverage=keep.retained_coverage.mean(),retained_n=int(g.retained_n.sum()),switch_n=int(g.switch_n.sum()),switch_rate=g.switch_rate.mean(),mean_width=g.retained_width.mean(),keep_avg_nmae=keep.nmae.mean(),delivered_avg_nmae=g.nmae.mean(),delta_avg=g.nmae.mean()-keep.nmae.mean(),keep_peak_nmae=keep.peak_nmae.mean(),delivered_peak_nmae=g.peak_nmae.mean(),delta_peak=g.peak_nmae.mean()-keep.peak_nmae.mean(),artifact_path=str(C/'results/summary.csv'),artifact_sha256=sha(C/'results/summary.csv'),tape_provenance='manifests/input_manifest.csv',status='VERIFIED exact frozen configuration; decision note fallback unspecified'))
    save(pd.DataFrame(rows),'results/R9R_retained_reliability_bridge.csv')
    (ROOT/'reports/R9R_RECOVERY_REPORT.md').write_text('# R9-R recovery\n\nFrozen decision note names Ridge / uncertainty_scale20 but does not specify a lag. All three frozen fallback configurations are returned with exact tape-recomputed numbers. lag-24 provides a verified instance of the stated contrast; it is not claimed to be the unique configuration intended by the note. Coverage and normalized width are equal-area macros; retained/switch counts are pooled counts over 116 areas. Issued switches include unscoreable targets; retained_n counts scoreable retained rows. Full source hashes are in input_manifest.csv.\n')
if __name__=='__main__':
    import sys
    globals()[sys.argv[1]]()
    print(sys.argv[1],'complete',flush=True)
