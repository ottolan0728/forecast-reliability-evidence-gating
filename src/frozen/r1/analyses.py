"""Locked R1 diagnostics. Run stages sequentially; never fit scientific point models."""
from pathlib import Path
import os,sys,json,hashlib,gzip,shutil
ROOT=Path(__file__).resolve().parents[1]; PROJECT=ROOT.parents[1]
MAP=json.loads((ROOT/'manifests/path_mapping.json').read_text())
MAP={k:str((ROOT/v).resolve()) if isinstance(v,str) and not Path(v).is_absolute() else v for k,v in MAP.items()}
os.environ['R9_SOURCE_OUTPUTS']=MAP['original_outputs']
os.environ['MPLCONFIGDIR']=str(ROOT/'environment/mplcache')
sys.path.insert(0,str(ROOT/'reproduction/r9_replay/scripts'))
import common as c
import numpy as np
import pandas as pd
from scipy.stats import spearmanr,kendalltau
from sklearn.metrics import roc_auc_score,average_precision_score,balanced_accuracy_score
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
STATUS='R1_REVIEWER_TRIGGERED_SECONDARY'
assert json.loads((ROOT/'reproduction/G0.json').read_text())['passed']
assert hashlib.sha256((ROOT/'PLAN_LOCK.md').read_bytes()).hexdigest()=='547a8285b97c6bc7d92072f23b0f7985e456f92caa410e17b4c5392becb89afb'
def folder(stage):
    p=ROOT/'results'/stage;p.mkdir(exist_ok=True);return p
def save(rows,p):
    df=rows if isinstance(rows,pd.DataFrame) else pd.DataFrame(rows)
    df.to_csv(p,index=False);return df
def all_tapes():
    for ds in ['E1','C1']:
        for e,m,l,s,a in c.tapes(ds):
            yield dict(dataset=ds,entity=e,model=m,lag=l,site=s,status=STATUS),a
def macro(df,keys):
    cols=[x for x in ['delta_avg','delta_peak','nmae','peak_nmae','switch_rate'] if x in df]
    out=df.groupby(keys,dropna=False)[cols].mean().reset_index()
    out['status']=STATUS;return out
def figsave(fig,name):
    fig.tight_layout();fig.savefig(ROOT/'figures'/f'{name}.pdf');fig.savefig(ROOT/'figures'/f'{name}.png',dpi=160);plt.close(fig)
def e0():
    p=folder('E0X');old=Path(MAP['original_outputs'])
    sources=[old/'evidence_gating_audit/reserved_entity_exposure.csv',old/'evidence_gating_audit/exposure_manifest.json',old/'evidence_gating_pilot/run_p0/entity_registry.csv',old/'evidence_gating_external/selected_registry.csv',old/'peak_mtl/r139/frozen_exposure_spec.json',old/'peak_mtl/r139/exposure_registry.csv']
    sm=[]
    for x in sources:
        sm.append(dict(path=str(x),size=x.stat().st_size,role='E0X exposure provenance',sha256=c.sha(x)))
        shutil.copyfile(x,p/(x.parent.name+'_'+x.name))
    save(sm,ROOT/'manifests/E0X_additional_inputs.csv')
    columns=pd.read_csv(PROJECT/'work/r9_recovered_inputs/bdg2_electricity_raw.csv',nrows=0).columns[1:]
    reserved=c.read(sources[0]).set_index('building_id');pilot=c.read(sources[2]);selected=c.read(sources[3])
    inventory=[]
    for e in columns:
        r=dict(entity=e,site=e.split('_')[0],used_E1=e in set(selected.building_id),used_pilot=e in set(pilot.building_id),untouched_proven=False)
        r['reason']='prior E1/pilot use' if r['used_E1'] or r['used_pilot'] else 'global exposure history not certified; absence from selected rosters does not establish untouched outcomes'
        if e in reserved.index:r['historical_no_other_exposure_verified']=bool(reserved.loc[e,'no_other_exposure_verified'])
        inventory.append(r)
    d=save(inventory,p/'cohort_inventory.csv')
    (ROOT/'E0X_NOT_FEASIBLE.md').write_text(f'# E0X not feasible\n\nHeader-only inventory: {len(d)} electricity entities, {d.site.nunique()} sites. Prior E1 {d.used_E1.sum()}, pilot {d.used_pilot.sum()}. No untouched cohort certified. The historical reserved registry explicitly has no_other_exposure_verified=False; the later MTL exposure specification documents extensive additional screening (1578 support-screen entities, 48 noneligibility-artifact-exposed entities, 23 unclassified entities). It does not certify the remaining entities as never outcome-inspected through R1. No new outcome values were read for cohort selection. Unknown exposure is not an independent cohort. See results/E0X/cohort_inventory.csv and hashed provenance copies. New cohort execution stopped; opened-cohort diagnostics continue.\n',encoding='utf-8')
    print('E0X inventory',len(d),flush=True)
def e1():
    p=folder('E1_matched_rate');rows=[];days={};selected=p/'selected_rows.csv.gz'
    with gzip.open(selected,'wt',encoding='utf-8',newline='') as stream:
        first=True
        for meta,a0 in all_tapes():
            a=a0[a0.y.notna()].copy();a['ordinal']=np.flatnonzero(a0.y.notna());n=len(a)
            for policy,col in [('risk','risk'),('gain','gain_score')]:
                assert np.isfinite(a[col]).all()
                order=np.lexsort((a.ordinal.to_numpy(),a.index.asi8,-a[col].to_numpy()))
                for q in [.05,.1,.2,.3,.4]:
                    k=round(q*n);sw=np.zeros(n,bool);sw[order[:k]]=True
                    v,dr=c.metrics(a,sw);rows.append(dict(**meta,policy=policy,q=q,k=k,mask_sha256=hashlib.sha256(sw.tobytes()).hexdigest(),**v))
                    ids=a.iloc[order[:k]][['ordinal']].reset_index().rename(columns={'index':'target_time'}).assign(**meta,policy=policy,q=q)
                    ids.to_csv(stream,index=False,header=first);first=False
                    if meta['dataset']=='C1':
                        for metric,mask in [('average',np.ones(n,bool)),('peak',c.peakmask(a))]:
                            key=(meta['model'],meta['lag'],policy,q,metric)
                            days.setdefault(key,[]).append(c.daily(a,dr,mask))
            for policy in ['gain_naive','gain_calibrated']:
                sw=a['switch_'+policy].to_numpy(bool);v,_=c.metrics(a,sw)
                rows.append(dict(**meta,policy=policy,q=np.nan,k=int(sw.sum()),mask_sha256=hashlib.sha256(sw.tobytes()).hexdigest(),**v))
    df=save(rows,p/'entity_results.csv');summ=macro(df,['dataset','model','lag','policy','q']);save(summ,p/'summary.csv')
    infer=[]
    for (m,l,pol,q,metric),vals in days.items():
        v=c.block_stats(np.column_stack([d.total for d in vals]),np.column_stack([d['count'] for d in vals]))
        v.pop('family_lower');v.pop('family_upper');infer.append(dict(dataset='C1',model=m,lag=l,policy=pol,q=q,metric=metric,**v))
    for (m,l,pol,q),g in df[(df.dataset=='E1')&df.q.notna()].groupby(['model','lag','policy','q']):
        for metric,col in [('average','delta_avg'),('peak','delta_peak')]:infer.append(dict(dataset='E1',model=m,lag=l,policy=pol,q=q,metric=metric,**c.site_stats(g,col)))
    inf=save(infer,p/'inference.csv');inf['scope']='ordinary exploratory 95% intervals; no global multiplicity claim';save(inf,p/'inference.csv')
    for metric in ['avg','peak']:
        fig,axes=plt.subplots(4,2,figsize=(11,14))
        for ax,((ds,m,l),g) in zip(axes.flat,summ.groupby(['dataset','model','lag'])):
            for pol in ['risk','gain']:
                z=g[g.policy==pol];ax.plot(z.switch_rate,z['delta_'+metric],'-o',label=pol)
            for pol,mk in [('gain_naive','x'),('gain_calibrated','s')]:
                z=g[g.policy==pol];ax.scatter(z.switch_rate,z['delta_'+metric],marker=mk,label=pol)
            ax.axhline(0,color='grey',lw=.7);ax.set(title=f'{ds} {m} lag{l}',xlabel='Scoreable replacement share',ylabel='Delivered minus original NMAE');ax.legend(fontsize=7)
        figsave(fig,'E1_'+metric+'_matched_rate')
    print('E1 complete',len(df),flush=True)
def diagnostics(x,y,loss,switch):
    positive=y>0;pred=x>0;harm=y<0;n=len(x)
    def rate(v,m):return float(v[m].mean()) if m.any() else np.nan
    varied=len(np.unique(positive))==2
    return dict(n=n,spearman=spearmanr(x,y).statistic if len(np.unique(x))>1 and len(np.unique(y))>1 else np.nan,kendall=kendalltau(x,y).statistic if len(np.unique(x))>1 else np.nan,auroc=roc_auc_score(positive,x) if varied else np.nan,auprc=average_precision_score(positive,x) if positive.any() else np.nan,sign_accuracy=float((positive==pred).mean()),balanced_accuracy=balanced_accuracy_score(positive,pred) if varied else np.nan,ppv=rate(positive,pred),harmful_positive_rate=rate(harm,pred),harmful_positive_all_fraction=float((pred&harm).mean()),harmful_positive_n=int((pred&harm).sum()),predicted_positive_n=int(pred.sum()),mean_harmful_case_loss=rate(loss,pred&harm),mean_harmful_gain_magnitude=rate(-y,pred&harm),frozen_switch_n=int(switch.sum()),frozen_switch_harm_rate=rate(harm,switch))
def e2():
    p=folder('E2_gain_diagnostics');rows=[];pools={};bins=[]
    for meta,a in all_tapes():
        a=a[a.y.notna()];x=a.gain_score.to_numpy();loss=abs(a.y-a.fallback).to_numpy()/a.scale.to_numpy();y=(abs(a.y-a.pred)-abs(a.y-a.fallback)).to_numpy()/a.scale.to_numpy()
        sw=a.switch_gain_calibrated.to_numpy(bool)
        v=diagnostics(x,y,loss,sw);rows.append(dict(**meta,**v))
        pools.setdefault((meta['dataset'],meta['model'],meta['lag']),[]).append(pd.DataFrame(dict(predicted=x,realized=y,fallback_loss=loss,switch=sw)))
    df=save(rows,p/'entity_metrics.csv');out=[]
    for key,ls in pools.items():
        a=pd.concat(ls,ignore_index=True);meta=dict(zip(['dataset','model','lag'],key));v=diagnostics(a.predicted.to_numpy(),a.realized.to_numpy(),a.fallback_loss.to_numpy(),a.switch.to_numpy(bool))
        if a.predicted.nunique()>1:slope,intercept=np.polyfit(a.predicted,a.realized,1)
        else:slope=intercept=np.nan
        out.append(dict(**meta,aggregation='pooled_descriptive',calibration_slope=slope,calibration_intercept=intercept,**v))
        q=pd.qcut(a.predicted,10,duplicates='drop');a['bin']=q
        for j,(_,g) in enumerate(a.groupby('bin',observed=True)):
            bins.append(dict(**meta,bin=j+1,actual_bins=q.cat.categories.size,n=len(g),predicted_mean=g.predicted.mean(),realized_mean=g.realized.mean(),positive_fraction=(g.realized>0).mean()))
        e=df[(df.dataset==key[0])&(df.model==key[1])&(df.lag==key[2])]
        out.append(dict(**meta,aggregation='entity_macro',**{col:e[col].mean() for col in v},entities=len(e)))
    save(out,p/'configuration_metrics.csv');b=save(bins,p/'calibration_bins.csv')
    for kind in ['calibration','positive_fraction']:
        fig,axes=plt.subplots(4,2,figsize=(11,14))
        for ax,(key,g) in zip(axes.flat,b.groupby(['dataset','model','lag'])):
            if kind=='calibration':
                ax.plot(g.predicted_mean,g.realized_mean,'o-');limits=[min(g.predicted_mean.min(),g.realized_mean.min()),max(g.predicted_mean.max(),g.realized_mean.max())];ax.plot(limits,limits,'--',color='gray');ax.set(xlabel='Mean predicted gain',ylabel='Mean realized gain')
            else:ax.plot(g.bin,g.positive_fraction,'o-');ax.set(xlabel='Predicted-gain bin',ylabel='Realized positive fraction',ylim=(0,1))
            ax.set_title(f'{key[0]} {key[1]} lag{int(key[2])}')
        figsave(fig,'E2_'+kind)
    print('E2 complete',len(df),flush=True)
def candidates(cal,scale,days):
    cal=cal[cal.index.day<=days];gain=(abs(cal.y-cal.pred)-abs(cal.y-cal.fallback))/scale
    out=[]
    for th in [0,.001,.005,.01,.02]:
        sw=cal.gain_score>th;d=(gain*sw).resample('D').mean().reindex(pd.date_range(f'{cal.index[0].year}-08-01',periods=days))
        rng=np.random.default_rng(20260920);ix=((rng.integers(0,days,(1000,int(np.ceil(days/7))))[:,:,None]+np.arange(7))%days).reshape(1000,-1)[:,:days]
        lo,hi=np.nanquantile(np.nanmean(d.to_numpy()[ix],axis=1),[.05,.95])
        out.append(dict(threshold=th,selected_hours=int(sw.sum()),selected_days=cal.index[sw].normalize().nunique(),mean_daily_gain=d.mean(),lower=lo,upper=hi,calibration_rows=len(cal),window_days=days))
    return out
def e3():
    p=folder('E3_ccga_ablation');rows=[];dec=[];checks=[]
    for meta,a in all_tapes():
        ds,e,m,l=meta['dataset'],meta['entity'],meta['model'],meta['lag']
        cal=c.read(ROOT/'reproduction/r9_replay/results/calibration_scores'/f'{ds}_{e}_{m}_lag{l}.csv.gz',parse_dates=['target_time']).set_index('target_time')
        variants=[('baseline',31,48,14,'lower',False),('A_fixed0',31,48,14,'lower',True),('B_mean',31,48,14,'mean_daily_gain',False),('C_support24_7',31,24,7,'lower',False),('D_support96_21',31,96,21,'lower',False),('E_first14',14,48,14,'lower',False),('E_first21',21,48,14,'lower',False),('E_full31',31,48,14,'lower',False)]
        cache={n:candidates(cal,a.scale.iloc[0],n) for n in [14,21,31]}
        for variant,n,h,d,criterion,fixed in variants:
            cc=cache[n][:1] if fixed else cache[n];accepted=[]
            for v in cc:
                support=v['selected_hours']>=h and v['selected_days']>=d;admit=support and v[criterion]>0
                dec.append(dict(**meta,variant=variant,min_hours=h,min_days=d,criterion=criterion,support_qualified=support,admitted=admit,**v))
                if admit:accepted.append((v[criterion],v['threshold']))
            th=max(accepted)[1] if accepted else np.inf;sw=a.gain_score.to_numpy()>th
            if variant=='baseline':
                same=np.array_equal(sw,a.switch_gain_calibrated.to_numpy(bool));checks.append(dict(**meta,pass_=same));assert same,(meta,'baseline admission mismatch')
            v,_=c.metrics(a,sw);rows.append(dict(**meta,variant=variant,threshold=th,enabled=bool(accepted),**v))
    df=save(rows,p/'entity_results.csv');save(dec,p/'candidate_decisions.csv');save(checks,p/'baseline_mask_checks.csv');save(macro(df,['dataset','model','lag','variant']),p/'summary.csv')
    (p/'A3_EXISTING_EVIDENCE.md').write_text('Pre-submission full fixed-threshold grid and naive/frozen operating points are replayed in reproduction/r9_replay/results/A3_admission_stage_raw.csv, A3_admission_stage_summary.csv, A3_inference.csv. Unequal action rates limit mechanism attribution. No best test threshold selected.\n')
    print('E3 complete',len(df),flush=True)
def e4():
    p=folder('E4_fallbacks');rows=[];audit=[]
    # Group all aligned backbones/fallbacks for each entity, no outcome selection.
    groups={}
    for meta,a in all_tapes():groups.setdefault((meta['dataset'],meta['entity']),{})[(meta['model'],meta['lag'])]=(meta,a)
    for (ds,e),group in groups.items():
        for (m,l),(meta,a) in group.items():
            other='Ridge' if m=='HGB' else 'HGB';b=group[(other,l)][1]
            assert a.index.equals(b.index);assert np.allclose(a.y,b.y,equal_nan=True)
            fallbacks={'keep':a.pred,'learned_'+other:b.pred}
            for ll in ([24] if ds=='E1' else [1,24,168]):fallbacks['lag'+str(ll)]=group[(m,ll)][1].fallback
            common=a.y.notna().to_numpy()
            for f in fallbacks.values():assert np.isfinite(f).all()
            audit.append(dict(**meta,original_scoreable=int(common.sum()),common_scoreable=int(common.sum()),lost_rows=0))
            for pol in ['gain_naive','gain_calibrated','uncertainty_scale20']:
                sw=a['switch_'+pol].to_numpy(bool);mh=hashlib.sha256(sw.tobytes()).hexdigest()
                for fb,f in fallbacks.items():
                    v,_=c.metrics(a,sw,fallback=f);rows.append(dict(**meta,policy=pol,delivered_fallback=fb,mask_sha256=mh,**v))
    df=save(rows,p/'entity_results.csv');save(audit,p/'alignment_audit.csv');su=macro(df,['dataset','model','lag','policy','delivered_fallback']);save(su,p/'summary.csv')
    fig,axes=plt.subplots(4,2,figsize=(12,15))
    for ax,(key,g) in zip(axes.flat,su.groupby(['dataset','model','lag'])):
        for pol,z in g.groupby('policy'):ax.plot(z.delivered_fallback,z.delta_avg,'o-',label=pol)
        ax.axhline(0,color='gray',lw=.7);ax.set(title=f'{key[0]} {key[1]} lag{int(key[2])}',ylabel='Average delivered minus original NMAE');ax.legend(fontsize=7)
    figsave(fig,'E4_fixed_mask_fallback');print('E4 complete',len(df),flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
