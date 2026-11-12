// Audit recorder (read-only use of I17 engine through research_guard). Writes to outdir only.
import fs from 'node:fs';import path from 'node:path';import zlib from 'node:zlib';
const [I17,variant,seedS,ticksS,profile,outdir,saveEveryS,extraS]=process.argv.slice(2);const extra=extraS?JSON.parse(extraS):{};
const {register,create,save}=await import(path.join(I17,'research_guard.mjs'));
const seed=Number(seedS),maxT=Number(ticksS),saveEvery=Number(saveEveryS||6000);
fs.mkdirSync(outdir,{recursive:true});
await register(variant);
const N=22, K=Math.ceil(maxT)+10;
const pos=new Int16Array(K*(N*2+3)); // x*50,y*50 ; ball x,y,z
const dec=new Uint8Array(K*N), tgt=new Int16Array(K*N*2), phase=new Uint8Array(K), restartK=new Uint8Array(K), lastTeam=new Uint8Array(K);
const dict=['none'],di=new Map([['none',0]]),code=s=>{if(!di.has(s)){di.set(s,dict.length);dict.push(s);}return di.get(s);};
const cur=Array.from({length:N},()=>({c:0,tx:0,ty:0}));let idx=null;
const out=fs.createWriteStream(path.join(outdir,'events.jsonl'));
const decOut=fs.createWriteStream(path.join(outdir,'decisions.jsonl'));
const lastDec=new Array(N).fill(null);
const skipEv=new Set(['offside_phase','offside_phase_cleared']);
const strip=o=>{const r={};for(const[k,v]of Object.entries(o)){if(k==='sample'||k==='candidates'||k==='observation'||k==='evidence')continue;r[k]=v;}return r;};
const counts={};
const sink=ev=>{const ch=ev.channel;counts[ch]=(counts[ch]||0)+1;
 if(ch==='decision'){const i=idx?.get(ev.player);if(i==null)return;const d=ev.decision||{};const k=(d.kind||'?')+'|'+(d.reason||'');const c=code(k);
   cur[i].c=c;cur[i].tx=d.target?.x??0;cur[i].ty=d.target?.y??0;
   const key=k+'|'+(d.targetId??'');if(lastDec[i]!==key){lastDec[i]=key;decOut.write(JSON.stringify({t:ev.tick,p:ev.player,k,tid:d.targetId??null,tg:d.target?[+d.target.x.toFixed(2),+d.target.y.toFixed(2)]:null,sc:d.score})+'\n');}
   return;}
 if(ch==='event'){if(skipEv.has(ev.type))return;out.write(JSON.stringify(strip(ev))+'\n');return;}
 if(ch==='body_contact'){out.write(JSON.stringify({channel:ch,tick:ev.tick,players:ev.players,impulse:+(ev.impulse||0).toFixed(3),sep:ev.separation})+'\n');return;}
 if(ch==='contact_solve'||ch==='official'||ch==='dead_ball_constraint'){out.write(JSON.stringify({channel:ch,tick:ev.tick,type:ev.type,kind:ev.kind,players:ev.players})+'\n');return;}
};
const e=create(variant,{seed,zonalDefence:profile==='soc-existing-on',...extra},sink);
const st0=e.exportState();idx=new Map(st0.players.map((p,i)=>[p.id,i]));
const ids=st0.players.map(p=>p.id);
const meta={variant,profile,seed,extraOptions:extra,activeConfig:st0.config,schema:st0.schema,engine:st0.engine,ids,roles:st0.players.map(p=>p.role),abilities:st0.players.map(p=>p.abilities),saves:[]};
const phaseCodes=['play','restart','finished','abandoned','halftime','kickoff'];const pc=s=>{let i=phaseCodes.indexOf(s);if(i<0){phaseCodes.push(s);i=phaseCodes.length-1;}return i;};
const rk=['none'];const rkc=s=>{s=s||'none';let i=rk.indexOf(s);if(i<0){rk.push(s);i=rk.length-1;}return i;};
const t0=Date.now();let t=0;
const W=N*2+3;
function snap(i){const p=e.physicalSnapshot();const o=i*W;for(let j=0;j<N;j++){const q=p.players[j];pos[o+2*j]=Math.round(q.x*50);pos[o+2*j+1]=Math.round(q.y*50);}
 pos[o+2*N]=Math.round(p.ball.x*50);pos[o+2*N+1]=Math.round(p.ball.y*50);pos[o+2*N+2]=Math.round(p.ball.z*50);phase[i]=pc(p.phase);lastTeam[i]=p.ball.lastTeam==='A'?1:p.ball.lastTeam==='B'?2:0;
 for(let j=0;j<N;j++){dec[i*N+j]=cur[j].c;tgt[(i*N+j)*2]=Math.round(cur[j].tx*50);tgt[(i*N+j)*2+1]=Math.round(cur[j].ty*50);}}
snap(0);
let restartKind=null;meta.crash=null;
for(t=0;t<maxT&&!e.finished;t++){
 if(saveEvery>0&&t>0&&t%saveEvery===0){const f=`save_${t}.json`;fs.writeFileSync(path.join(outdir,f),save(e,variant),{flag:'wx'});meta.saves.push({tick:t,file:f});}
 try{e.step();}catch(err){meta.crash={tickBeforeStep:t,engineTick:e.tick,message:String(err&&err.message||err),stack:String(err&&err.stack||'').split('\n').slice(0,6)};break;}
 snap(t+1);
}
let fin;try{fin=e.exportState();}catch(err){fin={tick:t,score:null,stats:null,result:null,violations:[],eventCount:null,eventDigest:null};meta.exportError=String(err.message);}
meta.finalTick=fin.tick;meta.score=fin.score;meta.stats=fin.stats;meta.result=fin.result;meta.violations=fin.violations;meta.blocked=e.blocked?.()??null;meta.phaseCodes=phaseCodes;meta.decisionDict=dict;meta.sinkCounts=counts;meta.wallMs=Date.now()-t0;meta.recordedTicks=t+1;meta.posScale=50;meta.posWidth=W;meta.eventCount=fin.eventCount;meta.eventDigest=fin.eventDigest;
const n=t+1;
const bin=(name,arr,len)=>fs.writeFileSync(path.join(outdir,name),zlib.gzipSync(Buffer.from(arr.buffer,0,len*arr.BYTES_PER_ELEMENT)));
bin('pos.i16.gz',pos,n*W);bin('dec.u8.gz',dec,n*N);bin('tgt.i16.gz',tgt,n*N*2);bin('phase.u8.gz',phase,n);bin('lastteam.u8.gz',lastTeam,n);
if(!meta.crash){try{fs.writeFileSync(path.join(outdir,'final_save.json'),save(e,variant));}catch(err){meta.saveError=String(err.message);}}
await new Promise(r=>out.end(r));await new Promise(r=>decOut.end(r));
fs.writeFileSync(path.join(outdir,'meta.json'),JSON.stringify(meta,null,1));
console.log(JSON.stringify({outdir,seed,profile,variant,finalTick:fin.tick,score:fin.score,wallMs:meta.wallMs,violations:fin.violations.length,crash:meta.crash?.message??null}));
