# Build the P25 replay page from cont/off_<seed>.json (original behaviour: stops) and cont/p25_<seed>.json (candidate).
# usage: python3 -I build_viewer_p25.py <contDir> <k20 viewer template> <out.html>
import json,sys
cont,tpl,outF=sys.argv[1:4]
KINDS=['none','press','intercept','receive','save','cover','support','advance_support','cover_exchange','restart_position','throw_position','scan','dribble','pass','gk_recover','gk_support','shoot','restart_kick','throw_in','other','corner_header','corner_clear','gk_punch','corner_cross']
NOTE={1847:'A08のCK。落下球が頭の届く高さに入ったtickに、攻撃側A02（球まで0.50m）とA10（0.39m）が同時にヘディング候補。元の枝はここで停止。候補：同じ抽選でA02が接触し、24tick後にAの得点。A10は空振り（待ち時間が付く）。',
 771:'A09のCK。守備側B07（0.62m）とB08（0.69m）が同時にクリア候補。球に最も近い攻撃側A10（0.26m）は直前にpressへ切り替えており、候補に入っていない。候補：B08がクリア。',
 8081:'A04のCK。守備側B06（0.17m）とB07（0.63m）が同時にクリア候補。候補：B07がクリアし、約6.6秒後にAのスローイン。',
 600613:'A09のCK。守備側B05（0.28m）とB08（0.57m）が同時にクリア候補。GKのB00（1.02m）は同じtickにパンチを決めたが、適用前で候補外。候補：B05がクリア。約3秒後にA10がシュート。'}
FOCUS={1847:['A02','A10'],771:['B07','B08','A10'],8081:['B06','B07'],600613:['B05','B08','B00']}
def clip(cid,title,P,seed,label,variant,pair):
  fr=P['frames'];ids=[p[0] for p in fr[0]['p']];frames=[]
  for f in fr:
    pos=[];[pos.extend([round(p[1]*50),round(p[2]*50)]) for p in f['p']];pos.extend([round(f['ball'][0]*50),round(f['ball'][1]*50),round(f['ball'][2]*50)])
    frames.append({'p':pos,'d':[KINDS.index(p[3]) if p[3] in KINDS else KINDS.index('other') for p in f['p']],'t':pos[:44],'ph':0 if f['ph']=='play' else 1})
  ev=[]
  for e in P['events']:
    if e['type']=='contact':continue
    if e['type']=='kick':ev.append({'t':e['t'],'s':f"{e['player']} KICK {e.get('kind')}"+(f" (同時候補 {e['simultaneous']}人)" if (e.get('simultaneous') or 1)>1 else '')})
    elif e['type']=='aerial_duel':ev.append({'t':e['t'],'s':f"aerial_duel {'+'.join(e['players'])} ({'同チーム' if len(set(e['teams']))==1 else '両チーム'}) → 接触 {e['winner']}"})
    elif e['type']=='goal':ev.append({'t':e['t'],'s':f"GOAL {e.get('team')}"})
    elif e['type'] in('restart_placement','restart_taken'):ev.append({'t':e['t'],'s':f"{e['type']} {e.get('kind') or ''} {e.get('team') or ''}"})
  if P.get('error'):ev.append({'t':P['endTick'],'s':'停止: '+P['error']})
  ev.sort(key=lambda x:x['t'])
  return {'id':cid,'title':title,'note':NOTE[seed],'run':label,'variant':variant,'profile':'baseline','seed':seed,'zonal':False,'from':fr[0]['t'],'to':fr[-1]['t'],'focus':FOCUS[seed],'scale':50,'ids':ids,'roles':ids,'dict':KINDS,'reasons':KINDS,'phaseCodes':['play','restart'],'frames':frames,'events':ev,'pair':pair}
clips=[]
for seed in (1847,771,8081,600613):
  A=json.load(open(f'{cont}/off_{seed}.json'));B=json.load(open(f'{cont}/p25_{seed}.json'))
  clips.append(clip(f'K-{seed}',f'seed {seed} tick {A["stopTick"]}：元のCK研究枝（停止）',A,seed,'CK研究枝と同じ動作（P25をOFFにした複製）','ck_research (P25 OFF)',f'K-{seed}b'))
  clips.append(clip(f'K-{seed}b',f'seed {seed}：P25候補（続行）',B,seed,'P25候補（隔離コピー・未採用）','p25_ck_mixed_resolution',f'K-{seed}'))
h=open(tpl).read()
h=h.replace('<title>K20 Possession Compare</title>','<title>P25 CK Stops</title>')
i=h.index('<header>');j=h.index('</header>')+9
h=h[:i]+'<header><h1>TACTICAL MOMENT P25 CK研究枝の停止4場面：同じ保存状態からの比較</h1><div class="sub">左＝元のCK研究枝の動作（同チーム2人が同じtickに空中の球へ届くと停止）。右＝P25候補（未採用）：既存の空中競合と同じ抽選で1人だけが接触。どちらも停止の80tick前から表示（zonalDefence=false）。太枠＝同時候補の選手。球の円が大きいほど高い。</div></header>'+h[j:]
h=h.replace("const COL={","const COL={corner_header:'#e5484d',corner_clear:'#3b82f6',gk_punch:'#8b5cf6',corner_cross:'#ff6bcb',shoot:'#ff6bcb',")
a=h.index("document.getElementById('legend').innerHTML=");b=h.index('\n',a)
h=h[:a]+"document.getElementById('legend').innerHTML=Object.entries({corner_header:'corner_header（攻撃のヘディング）',corner_clear:'corner_clear（守備のクリア）',gk_punch:'gk_punch',press:'press',receive:'receive',cover:'cover',support:'support',restart_position:'restart'}).map(([k,v])=>`<span><i style=\"background:${COL[k]}\"></i>${v}</span>`).join('')+'<span>A=丸・白枠 / B=四角・黒枠 / 太枠=同時候補</span>';"+h[b:]
h=h.replace("K:'4 CK・再開'","K:'CK研究枝の停止4場面（左：元の動作／右：P25候補）'")
h=h.replace("if(document.getElementById('tg').checked){","if(false){").replace('<label class="cfg"><input type="checkbox" id="tg" checked> 目標線</label>','<input type="checkbox" id="tg" hidden>')
h=h.replace("${c.phaseCodes[fr.ph]}`","${c.phaseCodes[fr.ph]}  球の高さ ${bz.toFixed(2)}m`").replace("x.fillRect(6,6,250,22)","x.fillRect(6,6,360,22)")
h=h.replace('const CLIPS=/*CLIPS*/[];','const CLIPS='+json.dumps(clips,ensure_ascii=False,separators=(',',':'))+';')
open(outF,'w').write(h);print('clips',len(clips),'bytes',len(h))
