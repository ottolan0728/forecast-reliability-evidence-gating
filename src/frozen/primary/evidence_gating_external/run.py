import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'
from pathlib import Path
import sys,json,itertools,importlib.metadata as im
from datetime import datetime,timezone
import pandas as pd
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
import joblib
ROOT=Path(__file__).resolve().parent
os.environ['MPLCONFIGDIR']=str(ROOT/'mpl-cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0,str(ROOT.parent/'evidence_gating_pilot'));import pilot
from prepare import clean
OUT=ROOT/'results';SEED=20260920
CONFIG=dict(max_iter=150,learning_rate=.05,max_leaf_nodes=15,min_samples_leaf=30,l2_regularization=1,early_stopping=False,random_state=SEED)
def finite_mean(a):
    a=np.asarray(a,float);a=a[np.isfinite(a)]
    return a.mean() if len(a) else np.nan
def md(d):return '| '+' | '.join(d.columns)+' |\n| '+' | '.join(['---']*len(d.columns))+' |\n'+'\n'.join('| '+' | '.join(map(str,row))+' |' for row in d.itertuples(index=False,name=None))
def main():
    assert not OUT.exists();OUT.mkdir();(OUT/'models').mkdir();(OUT/'figures').mkdir()
    sm=json.loads((ROOT/'selection_manifest.json').read_text());assert pilot.digest(ROOT/'selected_registry.csv')==sm['registry_sha256']
    assert pilot.digest(ROOT/'DESIGN_E1.md')==sm['design_sha256']
    assert pilot.digest(ROOT/'prepare.py')==sm['code_sha256']
    assert pilot.digest(Path(pilot.__file__))==sm['helper_sha256']
    assert pilot.digest(ROOT.parent/'evidence_gating_audit/reserved_entity_exposure.csv')==sm['exposure_inventory_sha256']
    pm=json.loads((ROOT.parent/'evidence_gating_p1/run_p1_v3/manifest.json').read_text())
    assert pilot.digest(Path(pilot.__file__))==pm['inputs'][str(Path(pilot.__file__))]
    assert (ROOT/'AUDIT_CLOSURE.md').exists(),'Audit closure required before test read'
    reg=pd.read_csv(ROOT/'selected_registry.csv').set_index('building_id')
    src=pilot.SRC/'data_raw/bdg2_electricity_raw.csv';assert pilot.digest(src)==sm['raw_sha256']
    dependencies=[Path(__file__),ROOT/'prepare.py',ROOT/'DESIGN_E1.md',ROOT/'selected_registry.csv',ROOT/'AUDIT_CLOSURE.md',ROOT.parent/'evidence_gating_pilot/pilot.py']
    record={'started_utc':datetime.now(timezone.utc).isoformat(),'selection':sm,'input_hashes':{str(p):pilot.digest(p) for p in dependencies},'environment':{d.metadata['Name']:d.version for d in im.distributions()},'config':CONFIG}
    (OUT/'manifest.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    header=pd.read_csv(src,nrows=0).columns[0]
    raw=pd.read_csv(src,usecols=[header]+reg.index.tolist(),nrows=8784,index_col=0,parse_dates=True)
    assert raw.index.equals(pd.date_range('2016-01-01','2016-12-31 23:00',freq='h'))
    metrics=[];tapes=[];candidates=[];admissions=[];counts=[];weeks=[]
    checks={'registry_frozen_before_testread':True,'calendar_2016_only':True,'no_truth_filter_for_issuing':True,'causal_features':True,'cost_decomposition':True,'weekly_mature_labels':True,'rolling_mature_labels':True}
    for j,e in enumerate(reg.index):
        y=clean(raw[e].astype(float),reg.loc[e,'timezone']);x=pilot.features(y)
        train=(y.index<'2016-07-01')&y.notna()&x.notna().all(axis=1)
        scale=y.loc[:'2016-06-30 23:00'].quantile(.99);peakcut=y.loc[:'2016-06-30 23:00'].quantile(.95)
        assert np.isclose(scale,reg.loc[e,'train_q99'])
        issue_mask=x.notna().all(axis=1)&(y.index>='2016-07-01');ix=y.index[issue_mask]
        changed=y.copy();changed.loc['2016-10-15':]=1e9
        assert np.allclose(x.loc[pd.Timestamp('2016-10-15')],pilot.features(changed).loc[pd.Timestamp('2016-10-15')],equal_nan=True)
        missing_current=y.copy();missing_current.loc[pd.Timestamp('2016-10-15')]=np.nan
        assert np.allclose(x.loc[pd.Timestamp('2016-10-15')],pilot.features(missing_current).loc[pd.Timestamp('2016-10-15')],equal_nan=True)
        mu=x.loc[train].mean();sd=x.loc[train].std().replace(0,1);z=(x-mu)/sd
        X=np.column_stack([np.ones(train.sum()),z.loc[train]]);pen=np.eye(X.shape[1]);pen[0,0]=0
        beta=np.linalg.solve(X.T@X+pen,X.T@(y[train].to_numpy()/scale));ridge=np.maximum(0,np.column_stack([np.ones(len(ix)),z.loc[ix]])@beta*scale)
        np.savez(OUT/'models'/f'{e}_Ridge.npz',beta=beta,mu=mu.to_numpy(),sd=sd.to_numpy(),features=np.array(x.columns),scale=scale)
        hgb=HistGradientBoostingRegressor(**CONFIG)
        with threadpool_limits(limits=1):hgb.fit(x.loc[train],y[train]/scale);hpred=np.maximum(0,hgb.predict(x.loc[ix])*scale)
        joblib.dump(hgb,OUT/'models'/f'{e}_HGB.joblib')
        for model,pred in [('Ridge',ridge),('HGB',hpred)]:
            a=pd.DataFrame({'y':y.loc[ix].values,'pred':pred,'p24':y.shift(24).loc[ix].values},index=ix)
            a['label_available_at']=a.index+pd.Timedelta(hours=1);a['gain']=(abs(a.y-a.pred)-abs(a.y-a.p24))/scale;a['residual']=abs(a.y-a.pred)
            july=(a.index<'2016-08-01')&a.y.notna();aug=(a.index>='2016-08-01')&(a.index<'2016-09-01')&a.y.notna()
            assert july.sum()>336 and aug.sum()>=336
            risk=HistGradientBoostingRegressor(**{**CONFIG,'max_iter':100})
            gx=x.loc[ix].copy();gx['point']=pred/scale;gx['fallback']=a.p24/scale;gx['disagreement']=gx.point-gx.fallback;gx['abs_disagreement']=abs(gx.disagreement)
            gainmodel=HistGradientBoostingRegressor(**{**CONFIG,'max_iter':100})
            with threadpool_limits(limits=1):
                risk.fit(x.loc[ix[july]],np.log(np.maximum(a.loc[july,'residual']/scale,1e-4)));a['risk']=np.exp(risk.predict(x.loc[ix]))
                gainmodel.fit(gx.loc[july],a.loc[july,'gain']);a['gain_score']=gainmodel.predict(gx)
            joblib.dump(risk,OUT/'models'/f'{e}_{model}_risk.joblib');joblib.dump(gainmodel,OUT/'models'/f'{e}_{model}_gain.joblib')
            cal=a.loc[aug];riskcut=cal.risk.quantile(.8);fixed=pilot.quantile90(cal.residual);accepted=[]
            for th in [0,.001,.005,.01,.02]:
                sw=cal.gain_score>th;nd=sw[sw].index.normalize().nunique();daily=(cal.gain*sw).resample('D').mean().reindex(pd.date_range('2016-08-01','2016-08-31'))
                lo,hi=pilot.bounds(daily,SEED);admit=sw.sum()>=48 and nd>=14 and lo>0
                candidates.append({'entity':e,'model':model,'threshold':th,'rows':int(sw.sum()),'days':nd,'mean_daily_gain':daily.mean(),'lower':lo,'upper':hi,'admitted':bool(admit)})
                if admit:accepted.append((lo,th))
            threshold=max(accepted)[1] if accepted else np.inf;admissions.append({'entity':e,'model':model,'enabled':bool(accepted),'threshold':threshold})
            radii=[]
            for day in pd.date_range('2016-09-01','2016-12-31'):
                hist=a[(a.index>=day-pd.Timedelta(days=28))&(a.label_available_at<day)&a.y.notna()]
                assert (hist.label_available_at<day).all()
                radii.append({'day':day,'radius':pilot.quantile90(hist.residual) if len(hist)>=336 else fixed})
            radii=pd.DataFrame(radii).set_index('day')
            week=[]
            for day in pd.date_range('2016-10-01','2016-12-31',freq='7D'):
                h=a[(a.index>=day-pd.Timedelta(days=28))&(a.label_available_at<day)&a.y.notna()];assert (h.label_available_at<day).all()
                daily=h.resample('D').agg(gain=('gain','mean'),n=('gain','size')).reindex(pd.date_range(day-pd.Timedelta(days=28),day-pd.Timedelta(days=1)))
                valid=daily.n>=18;lo=pilot.bounds(daily.gain.where(valid),SEED)[0] if valid.sum()>=14 else np.nan
                week.append({'update':day,'switch':bool(lo>0),'lower':lo,'days':int(valid.sum()),'entity':e,'model':model})
            w=pd.DataFrame(week).set_index('update');weeks.append(w.reset_index())
            t=a[a.index>='2016-10-01'].copy();assert t.index.equals(y.index[x.notna().all(axis=1)&(y.index>='2016-10-01')])
            q=radii.radius.reindex(t.index.normalize()).to_numpy();t['lower']=np.maximum(0,t.pred-q);t['upper']=t.pred+q
            score=t.y.notna().to_numpy();t['scoreable']=score;t['covered']=((t.y>=t.lower)&(t.y<=t.upper)).where(t.y.notna())
            assert np.array_equal(score,np.isfinite(t.y.to_numpy())&(t.y.to_numpy()>=0))
            t['peak']=(t.y>peakcut).where(t.y.notna());peak=(t.y.to_numpy()>peakcut)&score
            policies={'keep_model':np.zeros(len(t),bool),'uncertainty_scale20':t.risk.to_numpy()>riskcut,'gain_naive':t.gain_score.to_numpy()>0,'gain_calibrated':t.gain_score.to_numpy()>threshold,'static_relative':np.full(len(t),cal.gain.mean()>0),'weekly_relative':w['switch'].reindex(t.index,method='ffill').to_numpy(bool)}
            counts.append({'entity':e,'model':model,'calendar_hours':2208,'issueable_hours':len(t),'scoreable_hours':int(score.sum()),'issued_but_truth_missing':int((~score).sum())})
            em=abs(t.y.to_numpy()-t.pred.to_numpy())/scale;ef=abs(t.y.to_numpy()-t.p24.to_numpy())/scale
            for name,sw in policies.items():
                assert len(sw)==len(t) and len(score)==len(t)
                err=np.where(sw,ef,em);delta=sw*(ef-em)
                if score.any():
                    assert np.isclose(finite_mean(err)-finite_mean(em),finite_mean(delta))
                    assert finite_mean(np.minimum(em,ef))<=finite_mean(err)+1e-12
                retain=(~sw)&score
                metrics.append({'entity':e,'site':reg.loc[e,'site_id'],'model':model,'policy':name,'calendar_hours':2208,'issueable_n':len(t),'scoreable_n':int(score.sum()),'issue_rate':len(t)/2208,'score_rate':score.mean() if len(t) else np.nan,'switch_rate_issued':finite_mean(sw),'system_nmae':finite_mean(err),'peak_n':int(peak.sum()),'peak_nmae':np.mean(err[peak]) if peak.any() else np.nan,'cost_vs_keep':finite_mean(delta),'zero_switch':int(not sw.any()),'support_status':'SCOREABLE' if score.any() else 'NO_SCOREABLE_OUTCOMES','retained_interval_coverage':t.covered.to_numpy()[retain].astype(float).mean() if retain.any() else np.nan,'retained_width':((t.upper-t.lower).to_numpy()[retain]/scale).mean() if retain.any() else np.nan,'retained_n':int(retain.sum())})
                t['switch_'+name]=sw
            t['entity']=e;t['model']=model;t['scale']=scale;tapes.append(t.rename_axis('target_time').reset_index())
        print(f'{j+1}/{len(reg)} {e}',flush=True)
    r=pd.DataFrame(metrics);r.to_csv(OUT/'entity_metrics.csv',index=False)
    pd.DataFrame(counts).to_csv(OUT/'availability_counts.csv',index=False)
    pd.DataFrame(candidates).to_csv(OUT/'threshold_candidates.csv',index=False);pd.DataFrame(admissions).to_csv(OUT/'admissions.csv',index=False)
    pd.concat(weeks).to_csv(OUT/'weekly_evidence.csv',index=False);pd.concat(tapes).to_csv(OUT/'issued_forecast_tape.csv.gz',index=False,compression='gzip')
    summary=r.groupby(['model','policy']).mean(numeric_only=True);summary.to_csv(OUT/'summary.csv')
    sites=r.groupby(['model','policy','site']).mean(numeric_only=True);sites.to_csv(OUT/'site_metrics.csv')
    contrasts=[]
    for model in ['Ridge','HGB']:
        for metric in ['system_nmae','peak_nmae']:
            sub=r[r.model==model];p=sub.pivot(index=['entity','site'],columns='policy',values=metric);diff=(p.gain_calibrated-p.keep_model).dropna();d=diff.groupby('site').mean().values
            lo=hi=pv=np.nan
            if len(d)>=2:
                rng=np.random.default_rng(SEED);bs=d[rng.integers(0,len(d),(5000,len(d)))].mean(axis=1);lo,hi=np.quantile(bs,[.025,.975]);signs=np.array(list(itertools.product([-1,1],repeat=len(d))));pv=np.mean(abs((signs*d).mean(axis=1))>=abs(d.mean())-1e-14)
            contrasts.append({'model':model,'metric':metric,'entities':len(diff),'sites':len(d),'site_mean_delta':finite_mean(d),'ci_low':lo,'ci_high':hi,'p_raw':pv,'support_status':'DESCRIPTIVE_INFERENCE' if len(d)>=2 else 'INSUFFICIENT_SITES','better':int((diff< -1e-12).sum()),'worse':int((diff>1e-12).sum()),'ties':int((abs(diff)<=1e-12).sum())})
    c=pd.DataFrame(contrasts);order=c.p_raw.dropna().sort_values().index.to_numpy();adjusted=np.maximum.accumulate([(4-i)*c.p_raw.iloc[j] for i,j in enumerate(order)]) if len(order) else [];c['p_holm']=np.nan
    for j,pv in zip(order,adjusted):c.loc[j,'p_holm']=min(1,pv)
    c.to_csv(OUT/'primary_contrasts.csv',index=False)
    fig,axes=plt.subplots(1,2,figsize=(12,5),layout='constrained')
    for ax,model in zip(axes,['Ridge','HGB']):
        z=sites.loc[(model,'gain_calibrated')];b=sites.loc[(model,'keep_model')]
        ax.scatter(np.arange(len(z)),z.system_nmae-b.system_nmae,label='Average');ax.scatter(np.arange(len(z))+.12,z.peak_nmae-b.peak_nmae,label='Peak')
        ax.axhline(0,color='black',lw=1);ax.set(title=model,xticks=np.arange(len(z)),xticklabels=z.index,ylabel='Gain-admitted minus keep NMAE');ax.tick_params(axis='x',rotation=35)
    axes[1].legend();fig.suptitle('Reserved sites: positive difference = worse; local model fitting')
    for ext in ['png','pdf']:fig.savefig(OUT/'figures'/f'site-average-peak.{ext}',dpi=170,bbox_inches='tight')
    plt.close(fig)
    pretty=c.copy()
    for col in ['site_mean_delta','ci_low','ci_high','p_raw','p_holm']:pretty[col]=pretty[col].map(lambda v:f'{v:.6f}')
    rows=[]
    for (model,policy),z in summary.iterrows():rows.append({'model':model,'policy':policy,'NMAE':f'{z.system_nmae:.5f}','peak NMAE':f'{z.peak_nmae:.5f}','switch':f'{z.switch_rate_issued:.2%}','issue/calendar':f'{z.issue_rate:.2%}'})
    report=f'''# EG-E1：保留site的策略驗證

## 範圍

本流程保留的{reg.site_id.nunique()}sites／{len(reg)}建築，同BDG2家族；模型在各建築Jan–June訓練，July/August學習與admission，Oct–Dec評估。**是策略配方的跨site驗證，不是模型zero-shot transfer或獨立資料家族驗證。**原研究組未暴露狀態仍未知；採用方法前已有開發結果，因此須依完整策略凍結解讀。

## 完整結果

{md(pd.DataFrame(rows))}

上表entity-macro，peak排除沒有peak真值之建築。issue/calendar明確包含因pastfeature缺失而無法預測的時段；另有availability_counts.csv區分issued和scoreable，不把事後完整樣本當100%實際服务。

## 凍結的四個對比

{md(pretty)}

負值較好，site-macro與上表entity-macro不同。5000sitebootstrap、exactsignflip、Holm4；site少且非隨機，CI與p皆探索性，不以不顯著宣告非劣。average與peak均需支持才能提出双重效益，margin0僅是嚴格比較，不是物理安全標準。

## 稽核邊界

當下feature有效即發出prediction，不用當下y作issue篩選；真值後續不可評估只影響scoring。候選及排除規則見eligibility_registry；selectedregistry在讀Sep–Dec前留hash。No threshold retuning／no entity replacement aftertest。各模型輸出相同候選policy，後驗不存在最有利策略挑選。

Gain admission仍是August五候選搜索的啟發式，daily平均bootstrap與hourly評分權重不同，不能稱風險保證。Rolling區間只用過去成熟殘差，切換後不宣稱原區間有效。每日資料缺失、長零段／異常、timezone語義仍限制推廣；無節能或控制效果。

本輪不更改P0–P1c產物；完整lineage、environment、模型及issuedtape保存在manifest及models。未做不同seed重複或跨國驗證。
'''
    (OUT/'REPORT.md').write_text(report,encoding='utf-8')
    (OUT/'verification.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    record['completed_utc']=datetime.now(timezone.utc).isoformat();record['outputs']={str(f.relative_to(OUT)):pilot.digest(f) for f in OUT.rglob('*') if f.is_file() and f.name!='manifest.json'}
    (OUT/'manifest.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(pd.DataFrame(rows).to_string(index=False));print(c.to_string(index=False))
if __name__=='__main__':main()
