"""Full wedding film: editorial panels, kinetic type, light leaks; no doodles."""
import pathlib,sys,json,math,subprocess,concurrent.futures,threading
BASE=pathlib.Path(__file__).parent.resolve();sys.path.insert(0,str(BASE/'.video_tools'))
from PIL import Image,ImageOps,ImageDraw,ImageFont,ImageFilter
import numpy as np,pillow_heif,imageio_ffmpeg
pillow_heif.register_heif_opener()
W,H,FPS=1920,1080,30;Y='#f5c62e';INK='#252525';WHITE='#fafaf8'
WORK=BASE/'video_work_v4';WORK.mkdir(exist_ok=True)
SEGS=WORK/'segments';SEGS.mkdir(exist_ok=True)
PREV=WORK/'previews';PREV.mkdir(exist_ok=True)
OUT=BASE/'완성영상'/'WEDDING_DAY_에디토리얼_v4_4분07초.mp4'
FF=imageio_ffmpeg.get_ffmpeg_exe();AUDIO=str(BASE/'media/bgm.mp3')
T=json.loads((BASE/'video_work_v6/timeline.json').read_text(encoding='utf-8'))
M={x['id']:x for x in json.loads((BASE/'video_work/media.json').read_text(encoding='utf-8'))}
for item in M.values():item['path']=str(BASE/item['path'])
FONTS={};PHOTOS={}
def font(n,kind='ko'):
    key=(n,kind)
    if key not in FONTS:FONTS[key]=ImageFont.truetype(str(BASE/'fonts')+'/'+{'ko':'batang.ttc','en':'georgiai.ttf','sans':'arial.ttf'}[kind],n)
    return FONTS[key]
def ease(v):return 1-(1-max(0,min(1,v)))**3
def photo(mid):
    if mid not in PHOTOS:
        p=ImageOps.exif_transpose(Image.open(M[mid]['path'])).convert('RGB');p.thumbnail((2400,2400));PHOTOS[mid]=p
    return PHOTOS[mid]
FOCAL={4:(.5,1),29:(.5,1),34:(.5,.75),35:(.5,.40),37:(.5,.2),38:(.5,1),39:(.5,1),40:(.5,1),41:(.5,1)}
def fit(p,size,mid=None):return ImageOps.fit(p,size,Image.Resampling.BICUBIC,centering=FOCAL.get(mid,(.5,.5)))
def blank():return Image.new('RGB',(W,H),WHITE)
def label(layer,s,xy,size=42,fill=INK,kind='ko',center=False,highlight=False):
    d=ImageDraw.Draw(layer);f=font(size,kind);x,y=xy
    if center:x-=(f.getlength(s))/2
    if highlight:
        for word in ['함께','우리','시간','이야기']:
            if word in s:
                a=s.index(word);x1=x+f.getlength(s[:a]);ww=f.getlength(word)
                d.rectangle((x1-4,y+size*.32,x1+ww+4,y+size*1.06),fill='#f7df89');break
    d.text((x,y),s,font=f,fill=fill)
def caption(layer,s,box,size=58,fill=INK,highlight=True):
    x,y,w,h=box;ls=s.split('\n');f=font(size)
    while max(f.getlength(line) for line in ls)>w-30:size-=1;f=font(size)
    lh=round(size*1.6);top=y+(h-len(ls)*lh)/2
    for j,line in enumerate(ls):label(layer,line,(x+w/2,top+j*lh),size,fill,center=True,highlight=highlight)
def animated_paste(im,layer,pos=(0,0),opacity=1):
    if opacity<=0:return
    if opacity<.999:
        layer=layer.copy();layer.putalpha(layer.getchannel('A').point(lambda a:round(a*opacity)))
    im.paste(layer,(round(pos[0]),round(pos[1])),layer)
def border_card(p,box,angle=0):
    bw,bh=box;p=ImageOps.contain(p,(bw-30,bh-30),Image.Resampling.LANCZOS)
    c=Image.new('RGBA',(p.width+24,p.height+24),'white');c.paste(p,(12,12))
    if angle:c=c.rotate(angle,Image.Resampling.BICUBIC,expand=True)
    pad=Image.new('RGBA',(c.width+60,c.height+60));sh=Image.new('RGBA',pad.size)
    sh.paste((0,0,0,37),(28,34,28+c.width,34+c.height),c.getchannel('A'))
    pad.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)));pad.alpha_composite(c,(23,22));return pad
def enlarge(bg,z):
    if z<=1.0001:return bg.copy()
    nw,nh=round(W*z),round(H*z);p=bg.resize((nw,nh),Image.Resampling.BICUBIC)
    return p.crop(((nw-W)//2,(nh-H)//2,(nw-W)//2+W,(nh-H)//2+H))
def header(layer,index):
    chapter='OUR STORY' if index<11 else ('DAYS TOGETHER' if index<35 else 'COLLECTED MOMENTS')
    label(layer,chapter,(80,48),22,'#777777','sans');ImageDraw.Draw(layer).line((80,89,320,89),fill=Y,width=3)
def prepare(s):
    i=s['index'];k=s['kind'];obj={'s':s,'kind':k,'bg':blank(),'text':Image.new('RGBA',(W,H)),'items':[]}
    tx=obj['text']
    if k in ['full','hero','end']:
        obj['bg']=Image.open(BASE/'video_work_v3/cards'/f'{i:02d}_bg.png').convert('RGB')
        if k=='hero':
            label(tx,'Our Wedding Day',(W/2,155),145,Y,'en',True)
            label(tx,'백민규  ·  박지해',(W/2,875),44,'white',center=True)
            label(tx,'DECEMBER 12, 2026',(W/2,965),26,'white','sans',True)
        elif k=='end':
            caption(tx,'함께해 주셔서\n감사합니다.',(200,110,1520,270),75,'white',False)
            label(tx,'백민규  ·  박지해',(W/2,435),48,'white',center=True)
            label(tx,'2026.12.12',(W/2,930),36,Y,'sans',True)
        elif s['caption']:
            caption(tx,s['caption'],(120,875,1680,160),52,'white',False)
    elif k=='quote':
        right=s.get('side','right')=='right';cx=1420 if right else 500
        c=border_card(photo(s['ids'][0]),(870,950))
        obj['items']=[(c,(cx-c.width/2,(H-c.height)/2+15),0,'right' if right else 'left')]
        caption(tx,s['caption'],(65 if right else 1040,260,810,550),60)
        header(tx,i)
    elif k=='pair':
        for j,mid in enumerate(s['ids']):
            c=border_card(photo(mid),(860,880),0 if i in [24,25,41] else (.7 if j==0 else -.7))
            obj['items'].append((c,(480+j*960-c.width/2,105+(880-c.height)/2),j*.22,'left' if j==0 else 'right'))
        if s['caption']:caption(tx,s['caption'],(100,965,1720,100),45)
        if i in [24,25,41]:
            c,(cx,cy),_,_=obj['items'][-1]
            obj['expand']={'mid':s['ids'][-1],'from':(cx+35,cy+34,c.width-84,c.height-84)}
    elif k in ['grid','booth']:
        hascap=bool(s['caption']);width=1320 if hascap else 1840;cw=(width-18)//2;ch=490
        if k=='booth':
            p=photo(45);ims=[p.crop((round(.02*p.width),round(a*p.height),round(.98*p.width),round(b*p.height))) for a,b in [(.012,.222),(.231,.442),(.45,.662),(.67,.88)]]
        else:ims=[photo(mid) for mid in s['ids']]
        for j,p in enumerate(ims):
            mid=s['ids'][j] if k=='grid' else None
            tile=fit(p,(cw,ch),mid).convert('RGBA')
            obj['items'].append((tile,(40+j%2*(cw+18),40+j//2*(ch+18)),j*.15,'scale'))
        if hascap:caption(tx,s['caption'],(1420,220,430,650),53)
        if i==48:obj['expand']={'mid':12,'from':(40,40,cw,ch)}
    elif k.startswith('video'):
        obj['bg']=Image.open(BASE/'video_work_v3/cards'/f'{i:02d}_bg.png').convert('RGB')
        if k=='video':caption(tx,s['caption'],(120,895,1680,140),52,'white',False)
        else:
            caption(tx,s['caption'],(80,240,790,620),60);header(tx,i)
            d=ImageDraw.Draw(obj['bg']);x,y,vw,vh=s['vx'],s['vy'],s['vw'],s['vh'];d.rectangle((x-10,y-10,x+vw+10,y+vh+10),fill='white',outline='#dfdfdc',width=2)
    if i==32:
        obj['kind']='player';obj['bg']=blank();tx=Image.new('RGBA',(W,H));obj['text']=tx
        c=border_card(photo(44),(1010,800));obj['items']=[(c,(90,170),0,'left')]
        label(tx,'NOW PLAYING',(1190,230),28,'#777777','sans')
        caption(tx,'우리가\n노래하는 이유',(1170,320,660,260),63)
        label(tx,'백민규  ·  박지해',(1490,640),36,INK,center=True)
        label(tx,'OUR WEDDING SOUNDTRACK',(1490,885),20,'#777777','sans',True)
        obj['bg']=blank()
    return obj
def scene_frame(o,t,vframe=None):
    s=o['s'];i=s['index'];dur=s['duration'];k=o['kind']
    im=enlarge(o['bg'],1.012+.024*min(t/dur,1)) if k=='full' else (enlarge(o['bg'],1.04-.03*ease(t/dur)) if k=='hero' else o['bg'].copy())
    if vframe is not None:im.paste(vframe,(s['vx'],s['vy']))
    for item,(x,y),delay,mode in o['items']:
        u=ease((t-delay)/.6)
        if u>=.999:im.paste(item,(round(x),round(y)),item)
        elif u>0:
            if mode=='scale':
                scale=.88+.12*u;ww,hh=round(item.width*scale),round(item.height*scale);p=item.resize((ww,hh),Image.Resampling.BICUBIC)
                animated_paste(im,p,(x+(item.width-ww)/2,y+(item.height-hh)/2),u)
            else:animated_paste(im,item,(x+(1-u)*(100 if mode=='right' else -100),y+(1-u)*24),u)
    u=ease((t-.15)/.55);animated_paste(im,o['text'],(0,(1-u)*36),u)
    if k=='hero':
        # A geometric rule, not an illustrated underline.
        q=ease((t-.6)/.7);d=ImageDraw.Draw(im);d.rectangle((720,345,720+480*q,349),fill=Y)
    if k=='player':
        q=min((s['start']+t)/247,1);d=ImageDraw.Draw(im);d.rounded_rectangle((1190,765,1790,771),3,fill='#deded9');d.rounded_rectangle((1190,765,1190+max(6,600*q),771),3,fill=Y)
        d.ellipse((1183+600*q,759,1197+600*q,773),fill=INK)
        now=round(s['start']+t);label(im,f'{now//60:02}:{now%60:02}',(1190,800),23,'#777777','sans');label(im,'04:07',(1725,800),23,'#777777','sans')
    if 'expand' in o and t>dur-.72:
        q=ease((t-(dur-.72))/.66);a=o['expand'];x,y,ww,hh=a['from'];x=round(x*(1-q));y=round(y*(1-q));ww=round(ww+(W-ww)*q);hh=round(hh+(H-hh)*q)
        im.paste(fit(photo(a['mid']),(ww,hh),a['mid']),(x,y))
    return im
TRANS={1:'window',5:'slide',7:'window',11:'zoom',17:'slide',21:'dissolve',22:'window',26:'slide',30:'window',31:'burn',33:'dissolve',35:'window',38:'slide',40:'dissolve',42:'burn',44:'window',46:'dissolve',49:'zoom',51:'slide',55:'dissolve',58:'burn',59:'dissolve'}
def transition(im,old,t,kind):
    span=.55 if kind=='burn' else .40
    if t>=span:return im
    q=ease(t/span)
    if kind=='dissolve':return Image.blend(old,im,q)
    if kind=='window':
        base=old.copy();ww=max(2,round(W*q));hh=max(2,round(H*(.58+.42*q)));x=(W-ww)//2;y=(H-hh)//2;base.paste(im.crop((x,y,x+ww,y+hh)),(x,y));return base
    if kind=='slide':
        shift=round(W*q);base=blank();base.paste(old,(-shift,0));base.paste(im,(W-shift,0))
        # Soft motion blur is confined to the short transition.
        radius=2.2*math.sin(math.pi*min(1,t/span))
        return base.filter(ImageFilter.GaussianBlur(radius)) if radius>.2 else base
    if kind=='zoom':return Image.blend(enlarge(old,1+.16*q),enlarge(im,1+.12*(1-q)),q)
    if kind=='burn':
        base=Image.blend(old,im,q);p=t/span
        yy,xx=np.mgrid[0:90,0:160];cx=-35+230*p
        glow=np.exp(-((xx-cx)/37)**2-((yy-35)/95)**2);strength=math.sin(math.pi*p)
        ar=np.zeros((90,160,4),dtype=np.uint8);ar[:,:,0]=255;ar[:,:,1]=np.clip(170+85*glow,0,255).astype('uint8');ar[:,:,2]=np.clip(75+180*glow,0,255).astype('uint8');ar[:,:,3]=(glow*245*strength).astype('uint8')
        lay=Image.fromarray(ar).resize((W,H),Image.Resampling.BILINEAR);base.paste(lay,(0,0),lay);return base
    return im
def video_last(s):
    f=WORK/f"lastvideo_{s['index']:02}.png"
    subprocess.run([FF,'-v','error','-y','-ss',str(s.get('src',0)+s['duration']-.08),'-i',M[s['ids'][0]]['path'],'-frames:v','1','-vf',s['video_filter'],str(f)],check=True)
    return Image.open(f).convert('RGB')
def render(o,old):
    s=o['s'];i=s['index'];dest=SEGS/f'{i:02}.mp4'
    if dest.exists() and dest.stat().st_size>10000 and '--force' not in sys.argv:return i,'cached'
    dec=None
    if s['kind'].startswith('video'):
        dec=subprocess.Popen([FF,'-v','error','-threads','1','-ss',str(s.get('src',0)),'-i',M[s['ids'][0]]['path'],'-vf',s['video_filter']+',fps=30','-frames:v',str(s['frames']),'-pix_fmt','rgb24','-f','rawvideo','pipe:1'],stdout=subprocess.PIPE,stderr=(WORK/f'decode_{i}.log').open('wb'))
    log=(WORK/f'render_{i}.log').open('wb')
    proc=subprocess.Popen([FF,'-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','30','-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','18','-threads','2','-pix_fmt','yuv420p','-video_track_timescale','15360',str(dest)],stdin=subprocess.PIPE,stderr=log)
    last=None
    try:
        for f in range(s['frames']):
            t=f/FPS;vf=None
            if dec:
                n=s['vw']*s['vh']*3;data=dec.stdout.read(n)
                if len(data)==n:last=Image.frombytes('RGB',(s['vw'],s['vh']),data)
                assert last is not None,f'No decoded video {i}'
                vf=last
            im=scene_frame(o,t,vf)
            if old is not None and i in TRANS:im=transition(im,old,t,TRANS[i])
            if i==0 and t<.25:im=Image.blend(blank(),im,ease(t/.25))
            if i==len(T)-1 and t>s['duration']-.7:im=Image.blend(im,Image.new('RGB',(W,H)),min(1,(t-s['duration']+.7)/.67))
            proc.stdin.write(im.tobytes())
            if f in [7,min(s['frames']-1,round(FPS*1.1)),s['frames']-2]:im.save(PREV/f'{i:02}_{f:03}.jpg',quality=90)
        proc.stdin.close();rc=proc.wait();assert rc==0,(WORK/f'render_{i}.log').read_text()
    finally:
        if dec:dec.stdout.close();dec.wait()
        log.close()
    return i,'done'
def main():
    assert sum(s['frames'] for s in T)==7410
    assert {n for s in T for n in s['ids']}==set(range(1,47))
    objs=[];lasts=[]
    for s in T:
        o=prepare(s);objs.append(o);vf=video_last(s) if s['kind'].startswith('video') else None
        last=scene_frame(o,s['duration']-1/FPS,vf);lasts.append(last)
        last.save(WORK/f"card_{s['index']:02}.jpg",quality=90)
    timeline=[dict(s,transition_v4=TRANS.get(s['index'],'cut'),design_v4=objs[s['index']]['kind'],expands='expand' in objs[s['index']]) for s in T]
    (WORK/'timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Prepared 60 scenes / 247 seconds / no doodles',flush=True)
    only=next((v.split('=')[1] for v in sys.argv if v.startswith('--only=')),None)
    todo=objs if only is None else [objs[int(n)] for n in only.split(',')]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        fs=[pool.submit(render,o,lasts[o['s']['index']-1] if o['s']['index'] else None) for o in todo]
        for fut in concurrent.futures.as_completed(fs):i,state=fut.result();print(f'{i+1}/60 {state}',flush=True)
    if only is not None:return
    concat=WORK/'concat.txt';concat.write_text('\n'.join("file '"+(SEGS/f'{i:02}.mp4').as_posix()+"'" for i in range(60)),encoding='utf-8')
    subprocess.run([FF,'-v','error','-y','-f','concat','-safe','0','-i',str(concat),'-i',AUDIO,'-map','0:v:0','-map','1:a:0','-c:v','copy','-af','atrim=duration=247,asetpts=PTS-STARTPTS,afade=t=out:st=244:d=3','-c:a','aac','-b:a','320k','-ar','48000','-t','247','-movflags','+faststart',str(OUT)],check=True)
    print('FINAL',OUT,OUT.stat().st_size,flush=True)
if __name__=='__main__':main()
