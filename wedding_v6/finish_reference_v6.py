import make_reference_v6 as v
import sys,concurrent.futures,subprocess,json
m=v.m
(m.WORK/'concat.txt').write_text('\n'.join("file '"+(m.SEGS/f'{i:02}.mp4').as_posix()+"'" for i in range(len(m.T))),encoding='utf-8')
sys.argv.append('--force')
def repair(i):
    s=m.T[i];o=m.prepare(s);prev=m.T[i-1];po=m.prepare(prev)
    vf=m.video_last(prev) if prev['kind']=='video' else None
    old=m.scene_frame(po,prev['duration']-1/m.FPS,vf)
    return m.render(o,old)
if '--merge-only' not in sys.argv:
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for r in pool.map(repair,[29,30]):print('REFINED',r,flush=True)
(v.WORK/'timeline.json').write_text(json.dumps([dict(s,motion=v.TRANS.get(s['index'],'none'),hearts=v.HEARTS) for s in v.SCENES],ensure_ascii=False,indent=2),encoding='utf-8')
subprocess.run([m.FF,'-v','error','-y','-f','concat','-safe','0','-i',str(m.WORK/'concat.txt'),'-i',m.AUDIO,'-map','0:v:0','-map','1:a:0','-c:v','copy','-af','atrim=duration=247,asetpts=PTS-STARTPTS,afade=t=out:st=244:d=3','-c:a','aac','-b:a','320k','-ar','48000','-t','247','-movflags','+faststart',str(m.OUT)],check=True)
print('FINAL',m.OUT.stat().st_size,flush=True)
