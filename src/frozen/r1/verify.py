"""Sequential second-implementation numerical checks, no experiment tuning."""
from analyses import ROOT,MAP,c,all_tapes,save
import numpy as np
import pandas as pd
import hashlib,json
checks=[]
def check(name,got,want,tol=1e-12):
    ok=bool(np.isclose(got,want,atol=tol,rtol=0,equal_nan=True))
    checks.append(dict(check=name,obtained=got,expected=want,pass_=ok))
def independently(a,sw,fb=None):
    y=a.y.to_numpy();f=a.pred.to_numpy();b=a.fallback.to_numpy() if fb is None else np.asarray(fb);s=a.scale.to_numpy();valid=np.isfinite(y);peak=valid&((y>a.peakcut.to_numpy()) if 'peakcut' in a else a.peak.to_numpy(bool))
    # Paired loss identity used as alternative to delivered-array subtraction.
    effect=np.zeros(len(a));effect[sw]=(np.abs(y[sw]-b[sw])-np.abs(y[sw]-f[sw]))/s[sw]
    return np.sum(effect[valid])/valid.sum(),np.sum(effect[peak])/peak.sum() if peak.any() else np.nan
def main():
    p=ROOT/'results';raw1=c.read(p/'E1_matched_rate/entity_results.csv',dtype={'entity':str});raw3=c.read(p/'E3_ccga_ablation/entity_results.csv',dtype={'entity':str});raw4=c.read(p/'E4_fallbacks/entity_results.csv',dtype={'entity':str});raw6=c.read(p/'E6_metrics_compute/entity_extended_metrics.csv',dtype={'entity':str});raw8=c.read(p/'E8_peak_alert/entity_alert_metrics.csv',dtype={'entity':str})
    keys=['dataset','entity','model','lag']
    indices=[d.set_index(keys).sort_index() for d in [raw1,raw3,raw4,raw6,raw8]]
    ids=c.read(p/'E1_matched_rate/selected_rows.csv.gz',usecols=keys+['policy','q','ordinal'],dtype={'entity':str});idgroups={k:set(g.ordinal) for k,g in ids.groupby(keys+['policy','q'])};del ids
    cache={(meta['dataset'],meta['entity'],meta['model'],meta['lag']):a for meta,a in all_tapes()}
    e2=c.read(p/'E2_gain_diagnostics/entity_metrics.csv',dtype={'entity':str}).set_index(keys)
    e7=c.read(p/'E7_month_stability/entity_month_results.csv',dtype={'entity':str}).set_index(keys).sort_index()
    for key,a0 in cache.items():
        ds,e,m,l=key;tag='/'.join(map(str,key));a=a0[a0.y.notna()];validord=np.flatnonzero(a0.y.notna())
        gain=(abs(a.y-a.pred)-abs(a.y-a.fallback))/a.scale;score=a.gain_score;pos=gain>0
        check(tag+'/E2_spearman',score.rank().corr(gain.rank()),e2.loc[key,'spearman'])
        npos=int(pos.sum());nneg=len(a)-npos
        auc=(score.rank()[pos].sum()-npos*(npos+1)/2)/(npos*nneg) if npos and nneg else np.nan
        check(tag+'/E2_AUC',auc,e2.loc[key,'auroc'])
        check(tag+'/E2_harm_count',((score>0)&(gain<0)).sum(),e2.loc[key,'harmful_positive_n'],0)
        for _,r in e7.loc[key].iterrows():
            z=a0[a0.index.month==r.month];sw=z['switch_'+r.policy].to_numpy(bool);avg,peak=independently(z,sw)
            check(tag+'/E7_average',avg,r.delta_avg);check(tag+'/E7_peak',peak,r.delta_peak)
        for _,r in indices[0].loc[key].iterrows():
            if pd.notna(r.q):
                score=a.risk if r.policy=='risk' else a.gain_score
                # Python stable sort, independent of production np.lexsort.
                order=sorted(range(len(a)),key=lambda i:(-float(score.iloc[i]),a.index[i],int(validord[i])))
                k=round(float(r.q)*len(a));sw=np.zeros(len(a),bool);sw[order[:k]]=True
                check(tag+'/E1_count',sw.sum(),r.switch_n,0);check(tag+'/E1_saved_ids',int(set(validord[sw])==idgroups[(*key,r.policy,r.q)]),1,0)
            else:sw=a['switch_'+r.policy].to_numpy(bool)
            avg,peak=independently(a,sw);check(tag+'/E1_avg',avg,r.delta_avg);check(tag+'/E1_peak',peak,r.delta_peak)
        for _,r in indices[1].loc[key].iterrows():
            sw=a0.gain_score.to_numpy()>r.threshold;avg,peak=independently(a0,sw);check(tag+'/E3_count',sw.sum(),r.switch_n,0);check(tag+'/E3_avg',avg,r.delta_avg);check(tag+'/E3_peak',peak,r.delta_peak)
        for _,r in indices[2].loc[key].iterrows():
            if r.delivered_fallback=='keep':fb=a0.pred
            elif r.delivered_fallback.startswith('learned_'):fb=cache[(ds,e,r.delivered_fallback[8:],l)].pred
            else:fb=cache[(ds,e,m,int(r.delivered_fallback[3:]))].fallback
            sw=a0['switch_'+r.policy].to_numpy(bool);avg,peak=independently(a0,sw,fb=fb);check(tag+'/E4_avg',avg,r.delta_avg);check(tag+'/E4_peak',peak,r.delta_peak);check(tag+'/E4_mask',int(hashlib.sha256(sw.tobytes()).hexdigest()==r.mask_sha256),1,0)
        for _,r in indices[3].loc[key].iterrows():
            z=a0[a0.y.notna()];sw=z['switch_'+r.policy].to_numpy(bool);g=z.pred.to_numpy().copy();g[sw]=z.fallback.to_numpy()[sw];err=z.y.to_numpy()-g
            check(tag+'/E6_RMSE',np.linalg.norm(err)/np.sqrt(len(err)),r.rmse_native)
        for _,r in indices[4].loc[key].iterrows():
            y=a.y.to_numpy();sw=np.zeros(len(a),bool) if r.policy=='keep' else a['switch_'+r.policy].to_numpy(bool);g=a.pred.to_numpy().copy();g[sw]=a.fallback.to_numpy()[sw];truth=y>r.train_q95;alert=g>r.train_q95
            for col,got in [('tp',sum(truth&alert)),('fp',sum(~truth&alert)),('fn',sum(truth&~alert)),('tn',sum(~truth&~alert))]:check(tag+'/E8_'+col,got,r[col],0)
    # Every produced summary regenerated from all entity rows; no favorable cell filter.
    for sub,rawname,summaryname,ks,cols in [
        ('E1_matched_rate','entity_results.csv','summary.csv',['dataset','model','lag','policy','q'],['delta_avg','delta_peak','switch_rate']),
        ('E3_ccga_ablation','entity_results.csv','summary.csv',['dataset','model','lag','variant'],['delta_avg','delta_peak','switch_rate']),
        ('E4_fallbacks','entity_results.csv','summary.csv',['dataset','model','lag','policy','delivered_fallback'],['delta_avg','delta_peak','switch_rate']),
        ('E7_month_stability','entity_month_results.csv','summary.csv',['dataset','model','lag','policy','month'],['delta_avg','delta_peak','switch_rate']),
        ('E8_peak_alert','entity_alert_metrics.csv','entity_macro.csv',['dataset','model','lag','policy'],['recall','precision','miss_rate','false_alarm_rate','f1'])]:
        raw=c.read(p/sub/rawname);summary=c.read(p/sub/summaryname)
        for i,r in summary.iterrows():
            subset=raw
            for k in ks:subset=subset[subset[k].isna()] if pd.isna(r[k]) else subset[subset[k]==r[k]]
            for col in cols:
                vals=subset[col].dropna().to_numpy();check(sub+f'/summary/{i}/{col}',sum(vals)/len(vals) if len(vals) else np.nan,r[col])
    # E3 selection from stored candidate evidence, including disabled cases.
    cand=c.read(p/'E3_ccga_ablation/candidate_decisions.csv',dtype={'entity':str})
    for key,g in cand.groupby(keys+['variant']):
        for _,v in g.iterrows():
            admitted=v.selected_hours>=v.min_hours and v.selected_days>=v.min_days and v[v.criterion]>0
            check('/'.join(map(str,key))+'/admission_rule',int(admitted),int(v.admitted),0)
        eligible=g[g.admitted];criterion=g.criterion.iloc[0];threshold=max(zip(eligible[criterion],eligible.threshold))[1] if len(eligible) else np.inf
        r=raw3
        for k,v in zip(keys+['variant'],key):r=r[r[k]==v]
        check('/'.join(map(str,key))+'/selected_threshold',threshold,r.threshold.iloc[0],0)
    report=save(checks,ROOT/'tests/independent_numeric_checks.csv');fail=report[~report.pass_];save(fail,ROOT/'tests/independent_numeric_failures.csv')
    (ROOT/'tests/verification.json').write_text(json.dumps(dict(checks=len(report),failed=len(fail),pass_=len(fail)==0,method='second arithmetic implementation and Python stable ranking; same sole executor, no independent human/agent reviewer'),indent=2))
    print('Independent checks',len(report),'failed',len(fail),flush=True);assert fail.empty
if __name__=='__main__':main()
