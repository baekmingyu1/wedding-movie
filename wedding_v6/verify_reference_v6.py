import pathlib,sys,subprocess,json,re
BASE=pathlib.Path(__file__).parent.resolve();sys.path.insert(0,str(BASE/'.video_tools'))
from PIL import Image,ImageDraw,ImageFont
import imageio_ffmpeg
FF=imageio_ffmpeg.get_ffmpeg_exe();WORK=BASE/'video_work_v6';FINAL=BASE/'완성영상'/'WEDDING_DAY_레퍼런스모션_v6_4분07초.mp4'
T=json.loads((WORK/'timeline.json').read_text(encoding='utf-8'))
assert sum(s['frames'] for s in T)==7410
assert {x for s in T for x in s['ids']}==set(range(1,47))
info=subprocess.run([FF,'-hide_banner','-i',str(FINAL)],capture_output=True,text=True,encoding='utf-8',errors='replace').stderr
assert '00:04:07.00' in info and '1920x1080' in info and 'Audio: aac' in info,info
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
for pg in range((len(T)+11)//12):
    sheet=Image.new('RGB',(1440,4*294),'#d8d2c8');dr=ImageDraw.Draw(sheet)
    for j,s in enumerate(T[pg*12:(pg+1)*12]):
        t=s['start']+min(3,s['duration']/2);p=WORK/f"qa_{s['index']:02d}.jpg"
        subprocess.run([FF,'-v','error','-y','-ss',str(t),'-i',str(FINAL),'-frames:v','1','-vf','scale=474:-1',str(p)],check=True)
        im=Image.open(p);x=j%3*480;y=j//3*294;sheet.paste(im,(x,y));dr.text((x+4,y+270),f"{s['index']:02d} / {t:.2f}s",font=font,fill='#332d28')
    sheet.save(WORK/f'final_qa_{pg+1}.jpg',quality=92)
dec=subprocess.run([FF,'-v','error','-i',str(FINAL),'-map','0:v:0','-map','0:a:0','-progress','pipe:1','-f','null','-'],capture_output=True,text=True,encoding='utf-8',errors='replace')
assert dec.returncode==0 and not dec.stderr.strip(),dec.stderr
frames=int(re.findall(r'frame=(\d+)',dec.stdout)[-1]);assert frames==7410,frames
report={'duration':247,'frames':frames,'resolution':'1920x1080','fps':30,'photos':42,'source_clips':4,'scenes':len(T),'audio':'AAC stereo, 320kbps','decode':'passed','size_bytes':FINAL.stat().st_size}
(WORK/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False),flush=True)


