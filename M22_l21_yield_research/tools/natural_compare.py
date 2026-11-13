# Natural full-match comparison: standard OFF (I17 audit runs) vs J19, same 6 conditions.
# Separates decision counts from physical crowding and from defensive results.
# usage: python3 -I natural_compare.py <stdRunsDir> <j19RunsDir>
import json,glob,os,sys,gzip
def rows(pat):
  out=[]
  for d in sorted(glob.glob(pat)):
    f=os.path.join(d,'analysis.json')
    if not os.path.exists(f): continue
    a=json.load(open(f));out.append((os.path.basename(d),a))
  return out
def agg(R):
  S={'matches':len(R),'runs':[n for n,_ in R]}
  t=lambda f:sum(f(a) for _,a in R)
  def cc(a,ctx,pref=''):
    out={}
    for T in 'AB':
      for k,v in a['summary']['concentration'][T].items():
        if k.startswith(pref+ctx+':'): out[k.split(':')[1]]=out.get(k.split(':')[1],0)+v
    return out
  def share(ctx,pref,keys):
    num=t(lambda a:sum(v for k,v in cc(a,ctx,pref).items() if k in keys));den=t(lambda a:sum(cc(a,ctx,pref).values()));return round(100*num/den,1)
  S['decision_ge3BallDirected_oppCarry_%']=share('opp_carry','',{'3','4'})
  S['decision_eq2_oppCarry_%']=share('opp_carry','',{'2'})
  S['decision_le1_oppCarry_%']=share('opp_carry','',{'0','1'})
  S['physical_ge3Within5m_oppCarry_%']=share('opp_carry','near5_',{'3','4'})
  S['physical_0Within5m_oppCarry_%']=share('opp_carry','near5_',{'0'})
  S['sameTarget_ge3_oppCarry_%']=share('opp_carry','sameTarget2m_',{'3','4'})
  D=lambda k:t(lambda a:sum(a['summary']['defence'][T].get(k,0) for T in 'AB'))
  S['carrierFree5m_%ofCarry']=round(100*D('carrierFree5')/D('carryTicks'),1);S['carrierFree5mInDanger_%ofDanger']=round(100*D('carrierFree5Danger')/D('danger'),1)
  S['centralEmptyEpisodes']=t(lambda a:a['summary']['centralEmptyEpisodes']);S['centralEmptyEpisodesShot']=t(lambda a:a['summary']['centralEmptyEpisodesShot'])
  S['concEpisodes']=t(lambda a:a['summary']['concEpisodes']);S['concWin3s']=t(lambda a:sum(1 for e in a['concEpisodes'] if e['ownWin3s'] is not None));S['concConceded10m']=t(lambda a:sum(1 for e in a['concEpisodes'] if e['ballGain3s']>=10))
  S['jointPressEpisodes']=t(lambda a:a['summary']['jointPressEpisodes']);S['jointWin3s']=t(lambda a:sum(1 for e in a['jointPress'] if e['ownWin3s'] is not None))
  S['goals']=t(lambda a:len(a['summary']['goals']));S['shots']=t(lambda a:a['summary']['counts']['shots']);S['turnovers']=t(lambda a:a['summary']['counts']['turnovers'])
  S['playMin']=round(t(lambda a:a['summary']['playSeconds'])/60,1)
  S['transitions_shot10s']=t(lambda a:sum(1 for x in a['transitions'] if x['winnerShot10s']))
  S['loserRegain2s']=t(lambda a:sum(1 for x in a['transitions'] if x['loserRegainTick'] and x['loserRegainTick']-x['tick']<=40))
  S['bodyContactEpisodesSameTeam']=t(lambda a:a['summary']['counts']['bodyContactEpisodesSameTeam'])
  S['violations']=t(lambda a:a['summary']['violations'] or 0)
  return S
A=agg(rows(os.path.join(sys.argv[1],'std_off_*')));B=agg(rows(os.path.join(sys.argv[2],'m22_*')))
print(json.dumps({'standard_off':A,'m22':B},ensure_ascii=False,indent=1))
