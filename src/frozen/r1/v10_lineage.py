"""Connect printed V10 primary/secondary cells to replayed numerical sources."""
from analyses import *
import re
def main():
    hand=Path(MAP['handoff'])/'context/submission_v10';main=(hand/'main_V10.tex').read_text(encoding='utf-8');supp=(hand/'supplementary_V10.tex').read_text(encoding='utf-8');rows=[]
    def check(label,printed,value,digits):
        got=f'{value:.{digits}f}';expected=printed.strip().replace('+','');ok=got==expected
        rows.append(dict(claim=label,printed=expected,source_value=value,source_rounded=got,display_digits=digits,pass_=ok))
    ec=c.read(ROOT/'reproduction/r9_replay/reproduction/E1_site_contrasts.csv');cc=c.read(ROOT/'reproduction/r9_replay/reproduction/C1_primary_contrasts.csv');su=c.read(c.E/'results/summary.csv')
    for line in main.splitlines():
        if re.match(r'^(Ridge|HGB)\s+&',line):
            fields=[z.strip().removesuffix('\\\\').strip() for z in line.split('&')]
            if len(fields)==8:
                model,metric=fields[:2];col='system_nmae' if metric=='Average' else 'peak_nmae';er=ec[(ec.model==model)&(ec.metric==col)].iloc[0]
                for j,pol in [(2,'keep_model'),(3,'gain_calibrated')]:check(f'E1 {model}/{metric}/{pol}',fields[j],su[(su.model==model)&(su.policy==pol)].iloc[0][col],6)
                check(f'E1 {model}/{metric}/site_delta',fields[4],er.site_mean_delta,6)
                lo,hi=re.findall(r'[-+]?\d+\.\d+',fields[5]);check('E1 CI lower',lo,er.ci_low,6);check('E1 CI upper',hi,er.ci_high,6);check('E1 p_raw',fields[6],er.p_raw,4);check('E1 p_holm',fields[7],er.p_holm,3)
            elif len(fields)==6:
                model,lag,metric=fields[:3];cr=cc[(cc.model==model)&(cc.lag==int(lag[4:]))&(cc.metric==metric.lower())].iloc[0]
                check(f'C1 {model}/{lag}/{metric}',fields[3],cr.delta,7);lo,hi=re.findall(r'[-+]?\d+\.\d+',fields[4]);check('C1 adjusted CI lower',lo,cr.family_lower,7);check('C1 adjusted CI upper',hi,cr.family_upper,7);check('C1 harmed entities',fields[5],cr.harm_entities,0)
    a5=c.read(ROOT/'reproduction/r9_replay/results/A5_peak_block_robustness.csv')
    for line in supp.splitlines():
        if re.match(r'^(Ridge|HGB)\s+& q',line):
            f=[z.strip().removesuffix('\\\\').strip() for z in line.split('&')];r=a5[(a5.dataset=='E1')&(a5.model==f[0])&(a5['quantile']==int(f[1][1:]))&(a5.metric=='peak')].iloc[0]
            for j,col,digits in [(2,'entities',0),(3,'entity_macro_delta',6),(4,'site_mean_delta',6),(5,'p_holm',4)]:check('V10 S5 '+f[0]+'/'+f[1]+'/'+col,f[j],r[col],digits)
    a1=c.read(ROOT/'reproduction/r9_replay/results/A1_common_budget_summary.csv');z=a1.pivot(index=['dataset','model','lag','target_budget'],columns='policy',values=['delta_avg','delta_peak']);rows.append(dict(claim='V10 S4 A1 all24cells',pass_=bool(((z[('delta_avg','comparative_gain')]<z[('delta_avg','residual_risk')]).sum()==24)&((z[('delta_peak','comparative_gain')]<z[('delta_peak','residual_risk')]).sum()==24))))
    save(rows,ROOT/'reproduction/V10_display_lineage.csv');assert all(r['pass_'] for r in rows),[r for r in rows if not r['pass_']];print('V10 display lineage',len(rows),'PASS',flush=True)
if __name__=='__main__':main()

