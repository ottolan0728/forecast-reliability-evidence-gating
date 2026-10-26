"""Independent frozen-metric checks on restored tapes; no training or new policies."""
from pathlib import Path
import argparse,json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
def ap_manual(y,s):
    order=np.argsort(-s,kind='stable');s=s[order];y=y[order];last=np.r_[np.flatnonzero(s[:-1]!=s[1:]),len(s)-1];tp=np.cumsum(y,dtype=np.int64)[last]
    return float(np.sum(np.diff(np.r_[0,tp])*tp/(last+1))/y.sum()) if y.any() else 0.
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--reconstruction',required=True);args=parser.parse_args();base=Path(args.reconstruction)
    reference=pd.read_csv(ROOT/'results/derived/primary/entity_metrics_recomputed.csv',dtype={'entity':str},float_precision='round_trip').set_index(['dataset','entity','model','lag','policy'])
    expected=pd.read_csv(ROOT/'results/derived/E2_gain_diagnostics/configuration_metrics.csv',float_precision='round_trip')
    checks=[];pool={}
    def check(label,got,want,tol):
        passed=bool(np.isclose(got,want,rtol=0,atol=tol,equal_nan=True));checks.append(dict(check=label,obtained=got,expected=want,tolerance=tol,pass_=passed));assert passed,(label,got,want)
    def finite(x):x=np.asarray(x);return x[np.isfinite(x)].mean() if np.isfinite(x).any() else np.nan
    def tapes():
        t=pd.read_csv(base/'evaluation/evidence_gating_external/results/issued_forecast_tape.csv.gz',float_precision='round_trip')
        for (e,m),a in t.groupby(['entity','model']):a=a.copy();a['fallback']=a.p24;yield 'E1',e,m,24,a
        for p in sorted((base/'evaluation/evidence_gating_ckw_c1/results/tapes').glob('*.gz')):
            e,m,l=p.name.removesuffix('.csv.gz').split('_');yield 'C1',e,m,int(l[3:]),pd.read_csv(p,float_precision='round_trip')
    nconfigs=0
    for ds,e,m,l,a in tapes():
        nconfigs+=1;y=a.y.to_numpy();pred=a.pred.to_numpy();fb=a.fallback.to_numpy();scale=a.scale.to_numpy();ok=np.isfinite(y);peak=ok&((y>a.peakcut.to_numpy()) if 'peakcut' in a else a.peak.to_numpy(bool));gain=(abs(y-pred)-abs(y-fb))/scale
        pool.setdefault((ds,m,l),[]).append((gain[ok]>0,a.gain_score.to_numpy()[ok]))
        for column in a:
            if not column.startswith('switch_'):continue
            pol=column[7:];r=reference.loc[(ds,e,m,l,pol)];sw=a[column].to_numpy(bool);delivered=np.where(sw,fb,pred);loss=abs(y-delivered)/scale;delta=loss-abs(y-pred)/scale;ret=ok&~sw;prefix='/'.join(map(str,[ds,e,m,l,pol]))
            values=dict(issued=len(a),scored=int(ok.sum()),peak_n=int(peak.sum()),switch_n=int(sw.sum()),retained_n=int(ret.sum()),switch_rate=sw.mean(),nmae=finite(loss),peak_nmae=finite(loss[peak]),delta_avg=finite(delta),delta_peak=finite(delta[peak]),retained_coverage=finite(((y>=a.lower)&(y<=a.upper))[ret]),retained_width=finite(((a.upper-a.lower)/scale)[ret]))
            for col,val in values.items():check(prefix+'/'+col,val,r[col],0 if col in ['issued','scored','peak_n','switch_n','retained_n'] else 1e-12)
    auprc=[]
    for (ds,m,l),items in pool.items():
        y=np.concatenate([a[0] for a in items]);score=np.concatenate([a[1] for a in items]);value=ap_manual(y,score);r=expected[(expected.dataset==ds)&(expected.model==m)&(expected.lag==l)&(expected.aggregation=='pooled_descriptive')].iloc[0]
        check(f'{ds}/{m}/{l}/pooled_AP',value,r.auprc,1e-12);auprc.append(dict(dataset=ds,model=m,lag=l,scoreable_n=len(y),average_precision=value))
    pd.DataFrame(checks).to_csv(base/'RESTORED_EVIDENCE_CHECKS.csv',index=False);pd.DataFrame(auprc).to_csv(base/'RESTORED_AUPRC.csv',index=False)
    report=dict(pass_=True,configurations=nconfigs,checks=len(checks),model_fits=0,inference=0,calibration_refits=0,scope='All frozen policy metric rows and all eight pooled E2 AP values from reconstructed evaluation tapes; post-outcome diagnostic labels unchanged')
    (base/'RESTORED_EVIDENCE_REPORT.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
