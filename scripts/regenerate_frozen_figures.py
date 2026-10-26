"""Exact plotting blocks extracted from frozen analyses.py/reports.py.
Only I/O bindings changed; uses archived summary CSVs, never observation tapes.
"""
from pathlib import Path
import argparse,os
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);args=ap.parse_args()
ROOT=Path(__file__).resolve().parents[1];DEST=Path(args.output).resolve()
DEST.mkdir(parents=True,exist_ok=False)
os.environ['MPLCONFIGDIR']=str(DEST/'mplcache')
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
class c:
    @staticmethod
    def read(p):return pd.read_csv(p,float_precision='round_trip')
def figsave(fig,name):
    fig.tight_layout();fig.savefig(DEST/(name+'.pdf'));plt.close(fig)
def frozen_plots():
    summ=c.read(ROOT/'results/derived/E1_matched_rate/summary.csv')
    for metric in ['avg','peak']:
        fig,axes=plt.subplots(4,2,figsize=(11,14))
        for ax,((ds,m,l),g) in zip(axes.flat,summ.groupby(['dataset','model','lag'])):
            for pol in ['risk','gain']:
                z=g[g.policy==pol];ax.plot(z.switch_rate,z['delta_'+metric],'-o',label=pol)
            for pol,mk in [('gain_naive','x'),('gain_calibrated','s')]:
                z=g[g.policy==pol];ax.scatter(z.switch_rate,z['delta_'+metric],marker=mk,label=pol)
            ax.axhline(0,color='grey',lw=.7);ax.set(title=f'{ds} {m} lag{l}',xlabel='Scoreable replacement share',ylabel='Delivered minus original NMAE');ax.legend(fontsize=7)
        figsave(fig,'E1_'+metric+'_matched_rate')
    fig,ax=plt.subplots(figsize=(11,5));d=c.read(ROOT/'results/derived/E2_gain_diagnostics/configuration_metrics.csv');d=d[d.aggregation=='pooled_descriptive'];labels=d.dataset+' '+d.model+' lag'+d.lag.astype(str);ax.bar(labels,d.harmful_positive_rate);ax.tick_params(axis='x',rotation=30);ax.set(ylabel='Harmful fraction among predicted-positive rows',ylim=(0,1));figsave(fig,'E2_harmful_positive')
    s=c.read(ROOT/'results/derived/E4_fallbacks/summary.csv')
    for metric,suffix in [('avg',''),('peak','_peak')]:
        fig,axes=plt.subplots(4,2,figsize=(12,15))
        for ax,(key,g) in zip(axes.flat,s.groupby(['dataset','model','lag'])):
            for pol,z in g.groupby('policy'):ax.plot(z.delivered_fallback,z['delta_'+metric],'o-',label=pol)
            ax.axhline(0,color='gray',lw=.7);ax.set(title=f'{key[0]} {key[1]} lag{int(key[2])}',ylabel=f'{metric} delivered minus original NMAE');ax.legend(fontsize=7)
        figsave(fig,'E4_fixed_mask_fallback'+suffix)
    b=c.read(ROOT/'results/derived/E2_gain_diagnostics/calibration_bins.csv')
    for kind in ['calibration','positive_fraction']:
        fig,axes=plt.subplots(4,2,figsize=(11,14))
        for ax,(key,g) in zip(axes.flat,b.groupby(['dataset','model','lag'])):
            if kind=='calibration':
                ax.plot(g.predicted_mean,g.realized_mean,'o-');limits=[min(g.predicted_mean.min(),g.realized_mean.min()),max(g.predicted_mean.max(),g.realized_mean.max())];ax.plot(limits,limits,'--',color='gray');ax.set(xlabel='Mean predicted gain',ylabel='Mean realized gain')
            else:ax.plot(g.bin,g.positive_fraction,'o-');ax.set(xlabel='Predicted-gain bin',ylabel='Realized positive fraction',ylim=(0,1))
            ax.set_title(f'{key[0]} {key[1]} lag{int(key[2])}')
        figsave(fig,'E2_'+kind)
frozen_plots()
