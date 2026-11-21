"""Reconstruction of observed reference layouts and motions with the couple's media."""
import make_editorial_v4 as m
import pathlib,sys,json,math,random,subprocess,concurrent.futures
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps,ImageFilter
BASE=m.BASE;W,H,FPS=1920,1080,30
WORK=BASE/'video_work_v6';WORK.mkdir(exist_ok=True)
AS=WORK/'assets';AS.mkdir(exist_ok=True)
m.WORK=WORK;m.SEGS=WORK/'segments';m.SEGS.mkdir(exist_ok=True)
m.PREV=WORK/'previews';m.PREV.mkdir(exist_ok=True)
(BASE/'완성영상').mkdir(exist_ok=True)
m.OUT=BASE/'완성영상'/'WEDDING_DAY_레퍼런스모션_v6_4분07초.mp4'
RED='#9e292e';BLUE='#345a79';PINK='#d48d9d';INK='#333337';HEARTS='--no-hearts' not in sys.argv
FONT={};TEXTURES={};CUTS={};VIDEO_SPECS={s['ids'][0]:s for s in m.T if s['kind'].startswith('video')}
def font(n,kind='hand'):
    key=(n,kind)
    if key not in FONT:FONT[key]=ImageFont.truetype(str(BASE/'fonts')+'/'+{'hand':'HMFMPYUN.TTF','bold':'malgunbd.ttf','serif':'BOD_R.TTF','italic':'georgiai.ttf','script':'KUNSTLER.TTF','sans':'arial.ttf'}[kind],round(n*(1.28 if kind=='script' else 1.07 if kind=='serif' else 1)))
    return FONT[key]
def txt(im,s,xy,size=50,color=INK,kind='hand',anchor=None):
    ImageDraw.Draw(im).text(xy,s,font=font(size,kind),fill=color,anchor=anchor)
def textimage(s,size=50,color=INK,kind='hand'):
    f=font(size,kind);b=f.getbbox(s);p=Image.new('RGBA',(b[2]-b[0]+30,b[3]-b[1]+28));ImageDraw.Draw(p).text((15-b[0],14-b[1]),s,font=f,fill=color);return p
def texture(color='ivory',size=(W,H),seed=19):
    key=(color,size,seed)
    if key not in TEXTURES:
        w,h=size;rgb={'ivory':(242,240,233),'pink':(231,207,211),'blue':(213,222,232),'white':(250,248,241),'red':(155,44,40),'graph':(247,246,237)}[color]
        rng=np.random.default_rng(seed);grain=rng.normal(0,1.9,(h,w,1))
        coarse=Image.fromarray(rng.integers(60,190,(30,45),dtype=np.uint8)).resize((w,h),Image.Resampling.BICUBIC)
        ar=np.clip(np.array(rgb)+grain+(np.asarray(coarse)[:,:,None].astype(float)-125)*.08,0,255).astype('uint8')
        p=Image.fromarray(ar);d=ImageDraw.Draw(p)
        for j in range(w*h//1500):
            x=int(rng.integers(w));y=int(rng.integers(h));d.line((x,y,x+2,y+1),fill=tuple(max(0,v-21) for v in rgb),width=1)
        folds=Image.new('RGBA',(w,h));fd=ImageDraw.Draw(folds)
        for j in range(10):
            x=rng.integers(-w,w*2);y=rng.integers(-h,h*2);x2=rng.integers(-w,w*2);y2=rng.integers(-h,h*2)
            fd.line((x,y,x2,y2),fill=(255,255,255,30),width=3);fd.line((x+4,y+4,x2+4,y2+4),fill=(50,40,30,9),width=3)
        p=p.convert('RGBA');p.alpha_composite(folds.filter(ImageFilter.GaussianBlur(4)))
        if color=='graph':
            d=ImageDraw.Draw(p)
            for x in range(0,w,38):d.line((x,0,x,h),fill='#dfdfd7',width=1)
            for y in range(0,h,38):d.line((0,y,w,y),fill='#dfdfd7',width=1)
        TEXTURES[key]=p.convert('RGB')
    return TEXTURES[key].copy()
def torn(w,h,color='white',seed=0,stamp=False):
    p=texture(color,(w,h),seed).convert('RGBA');mask=Image.new('L',(w,h));d=ImageDraw.Draw(mask);r=random.Random(seed)
    if stamp:
        d.rectangle((0,0,w,h),fill=255)
        for x in range(0,w,25):d.ellipse((x-5,-6,x+7,7),fill=0);d.ellipse((x-5,h-7,x+7,h+6),fill=0)
        for y in range(0,h,25):d.ellipse((-6,y-5,7,y+7),fill=0);d.ellipse((w-7,y-5,w+6,y+7),fill=0)
    else:
        pts=[(x,r.randrange(2,13)) for x in range(0,w,10)]+[(w-1,y) for y in range(0,h,10)]+[(x,h-1-r.randrange(2,13)) for x in range(w-1,-1,-10)]+[(r.randrange(2,10),y) for y in range(h-1,-1,-10)]
        d.polygon(pts,fill=255)
    p.putalpha(mask);return p
def shadow(p,pad=22):
    out=Image.new('RGBA',(p.width+pad*2,p.height+pad*2));sh=Image.new('RGBA',out.size)
    sh.paste((40,33,29),(pad+3,pad+8),p.getchannel('A').point(lambda a:int(a*.24)))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)));out.alpha_composite(p,(pad,pad));return out
def card(mid,box,style='polaroid',angle=0):
    p=m.photo(mid) if isinstance(mid,int) else mid;bw,bh=box
    p=ImageOps.contain(p,(bw-45,bh-(105 if style=='polaroid' else 45)),Image.Resampling.LANCZOS)
    cw,ch=p.width+40,p.height+(100 if style=='polaroid' else 40)
    c=torn(cw,ch,'white',int(mid) if isinstance(mid,int) else 55,style=='stamp') if style=='stamp' else texture('white',(cw,ch),31).convert('RGBA')
    c.paste(p,(20,20))
    if style=='film':
        d=ImageDraw.Draw(c);d.rectangle((0,0,cw-1,ch-1),outline='#242121',width=18)
        txt(c,'RDP III   16    OUR MEMORIES',(24,0),12,'#ddc574','sans')
    if style=='marker':
        ImageDraw.Draw(c).line([(12,15),(cw-12,20),(cw-15,ch-12),(10,ch-17),(12,15)],fill=RED,width=6,joint='curve')
    if angle:c=c.rotate(angle,Image.Resampling.BICUBIC,expand=True)
    return shadow(c)
def cut(who,height):
    key=(who,height)
    if key not in CUTS:
        path=BASE/'video_work_v2/assets'/f'{who}.png' if who in ['groom','bride'] else AS/f'{who}.png'
        p=Image.open(path).convert('RGBA');z=min(1500/p.width,height/p.height);p=p.resize((round(p.width*z),round(p.height*z)),Image.Resampling.LANCZOS);CUTS[key]=p
    return CUTS[key]
def create_cutouts():
    jobs=[('couple44',44),('couple17',17)]
    if all((AS/f'{name}.png').exists() for name,_ in jobs):return
    import onnxruntime as ort
    opt=ort.SessionOptions();opt.intra_op_num_threads=2;sess=ort.InferenceSession(str(BASE/'video_work_v2/u2netp.onnx'),sess_options=opt,providers=['CPUExecutionProvider'])
    for name,mid in jobs:
        p=m.photo(mid).copy();p.thumbnail((1400,1300));ar=np.asarray(p.resize((320,320)),dtype=np.float32)/255
        ar=(ar-np.array([.485,.456,.406],dtype=np.float32))/np.array([.229,.224,.225],dtype=np.float32)
        pred=sess.run(None,{sess.get_inputs()[0].name:ar.transpose(2,0,1)[None]})[0][0,0];pred=(pred-pred.min())/(pred.max()-pred.min()+1e-8)
        mask=Image.fromarray((np.clip((pred-.16)/.70,0,1)*255).astype('uint8')).resize(p.size,Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(.7))
        p=p.convert('RGBA');p.putalpha(mask);box=mask.getbbox();p=p.crop(box)
        a=Image.new('L',(p.width+40,p.height+40));a.paste(p.getchannel('A'),(20,20));out=Image.new('RGBA',a.size);out.paste('#fffdf7',mask=a.filter(ImageFilter.MaxFilter(21)));out.alpha_composite(p,(20,20));shadow(out).save(AS/f'{name}.png')

def bez(points,n=80):
    p=np.array(points);return [tuple(sum(math.comb(3,k)*(1-t)**(3-k)*t**k*p[k] for k in range(4))) for t in np.linspace(0,1,n)]
def deco(kind,size=220,color=RED):
    p=Image.new('RGBA',(size,size));d=ImageDraw.Draw(p);s=size/220
    def line(pts,w=4):d.line([(round(x*s),round(y*s)) for x,y in pts],fill=color,width=max(2,round(w*s)),joint='curve')
    if kind=='bow':
        for pts in [[(110,92),(5,-5),(16,145),(110,92)],[(110,92),(210,-5),(210,150),(110,92)],[(105,94),(56,128),(120,164),(66,214)],[(115,95),(168,128),(105,176),(174,205)]]:line(bez(pts))
    elif kind=='spark':
        for x,y,z in [(55,65,31),(145,135,23),(165,36,13)]:line([(x,y-z),(x+z*.28,y-z*.25),(x+z,y),(x+z*.28,y+z*.25),(x,y+z),(x-z*.28,y+z*.25),(x-z,y),(x-z*.28,y-z*.25),(x,y-z)],3)
    elif kind=='ring':
        d.ellipse((45*s,75*s,170*s,200*s),outline=color,width=max(2,round(4*s)));d.ellipse((55*s,85*s,160*s,190*s),outline=color,width=max(2,round(2*s)))
        line([(76,68),(94,42),(129,42),(149,68),(111,102),(76,68)]);line([(77,68),(149,68)]);line([(94,42),(111,102),(129,42)],2)
    elif kind=='camera':
        d.rounded_rectangle((15*s,55*s,205*s,180*s),18*s,fill='#4a4a4d',outline='#f9f8f2',width=max(3,round(8*s)))
        d.ellipse((66*s,72*s,160*s,165*s),fill='#b5b6b7');d.ellipse((78*s,84*s,148*s,154*s),fill='#263946');d.ellipse((92*s,94*s,118*s,120*s),fill='#8dabb4')
        d.rectangle((35*s,38*s,90*s,60*s),fill='#747679');d.rectangle((165*s,74*s,186*s,90*s),fill='#e2c872')
    elif kind=='plane':
        line([(17,119),(95,102),(143,22),(162,18),(139,104),(202,145),(196,164),(128,140),(94,193),(76,192),(90,129),(17,119)],4)
    elif kind=='heart':
        pts=[(110+78*math.sin(t)**3,109-(63*math.cos(t)-24*math.cos(2*t)-10*math.cos(3*t)-5*math.cos(4*t))) for t in np.linspace(0,2*math.pi,150)];line(pts,4)
    else:
        line(bez([(25,40),(5,185),(185,192),(185,107)]));line([(164,125),(185,106),(199,128)])
    return p
def layer(o,im,x,y,delay=0,mode='pop',span=.7,spin=0,hold=True):
    o['layers'].append(dict(im=im,x=x,y=y,delay=delay,mode=mode,span=span,spin=spin,hold=hold))
def word(o,s,x,y,size=50,color=INK,kind='hand',delay=0,mode='write',center=False):
    p=textimage(s,size,color,kind);layer(o,p,x-p.width/2 if center else x,y,delay,mode,.8)
def label(o,ko,en='',x=1450,y=70,delay=.05):
    w=max(300,int(font(47).getlength(ko))+60);p=torn(w,100,'red',len(ko));txt(p,ko,(w/2,50),47,'#fffaf2',anchor='mm');p=shadow(p,12)
    layer(o,p,min(x,W-p.width-35),y,delay,'drop',.65,spin=-3)
    if en:
        tx=textimage(en,32,PINK,'sans');q=Image.new('RGBA',(tx.width+14,tx.height+4),'#fffdf6');q.alpha_composite(tx,(7,0));q=shadow(q,10)
        layer(o,q,min(x+40,W-q.width-35),y+112,delay+.22,'pop',.65,spin=2)
def subtitle(o,s,delay=.5):
    if not s:return
    p=texture('white',(1610,106),29).convert('RGBA');p.putalpha(235);layer(o,p,235,948,delay,'up',.5)
    size=50
    while font(size).getlength(s)>1540:size-=1
    word(o,s,1040,960,size,delay=delay+.12,mode='write',center=True)
def speaker(o,who,delay=.1):
    p=cut(who,325);layer(o,p,40,713,delay,'pop',.65)
    word(o,'신랑' if who=='groom' else '신부',265,760,48,BLUE if who=='groom' else RED,delay=delay+.25,mode='pop')
    layer(o,deco('arrow',110,BLUE if who=='groom' else RED),235,805,delay+.3,'draw',1)
def tape(o,x,y,color='pink',delay=.8):
    p=torn(170,53,color,17);p.putalpha(p.getchannel('A').point(lambda a:int(a*.82)));layer(o,p,x,y,delay,'pop',.4,spin=7)
def empty(s,color='ivory'):
    return {'s':s,'kind':s['kind'],'bg':texture(color),'layers':[],'paths':[],'sparkles':False}
def path(o,pts,color=RED,width=5,delay=.5,span=1,behind=False):o['paths'].append(dict(pts=pts,color=color,width=width,delay=delay,span=span,behind=behind))
def heart_contour(cx,cy,w,h,seed=21,rough=0):
    # Asymmetric ink contour: separate hand-shaped cubic lobes, uneven point and retraced edge.
    segments=[[(.50,.23),(.36,-.055),(.065,.045),(.045,.285)],[(.045,.285),(-.035,.54),(.26,.79),(.485,.98)],[(.485,.98),(.63,.81),(1.045,.54),(.96,.285)],[(.96,.285),(.945,.025),(.64,-.045),(.50,.23)]]
    pts=[];rng=random.Random(seed)
    for seg in segments:
        for n,(x,y) in enumerate(bez(seg,100)):
            dx=rough*(math.sin(n*.77)+rng.uniform(-.7,.7));dy=rough*(math.sin(n*.53+1)+rng.uniform(-.7,.7))
            pts.append((cx+(x-.5)*w+dx,cy+(y-.5)*h+dy))
    return pts
def inkheart(o,cx,cy,w,h,color,delay=.5,double=False,behind=False):
    pts=heart_contour(cx,cy,w,h,rough=max(.5,w/500));path(o,pts,color,max(3,round(w/160)),delay,1.55,behind)
    if double:
        pts=heart_contour(cx+3,cy-3,w*.968,h*.964,38,rough=max(.7,w/550));path(o,pts,color,max(2,round(w/220)),delay+.2,1.65,behind)
def ribbon(o,cx,cy,size=210,color=RED,delay=.8,behind=False):
    # Two unequal folded loops, their inner seams, and long curling ribbon tails.
    segs=[[(0,0),(-.85,-.12),(-.66,-.58),(-.08,-.10)],[(0,0),(-.10,-1.07),(.73,-1.00),(.14,-.12)],[(.10,-.04),(.40,-.10),(.15,.18),(-.02,.10)],
          [(-.08,-.08),(-.55,-.18),(-.62,-.44),(-.14,-.15)],[(.11,-.13),(.52,-.76),(.08,-.94),(.08,-.20)],
          [(-.02,.08),(-.51,.25),(-.52,.72),(-.35,.94)],[(-.35,.94),(-.10,1.17),(-.71,1.32),(-.53,1.64)],
          [(.12,.06),(.69,.34),(.09,.80),(.68,1.06)],[(.68,1.06),(.90,1.12),(.91,1.41),(.73,1.53)]]
    for j,seg in enumerate(segs):
        pts=[(cx+x*size,cy+y*size) for x,y in bez(seg,60)];path(o,pts,color,3 if size<180 else 5,delay+j*.08,.8,behind)

SCENES=[]
def add(kind,dur,ids,caption='',**kw):SCENES.append(dict(kind=kind,requested=dur,ids=ids,caption=caption,**kw))
add('opening_a',7,[44,11])
add('opening_b',7,[37])
add('duo',8,[32,33])
add('profile_groom',8,[16,7])
add('profile_bride',8,[10,18])
add('chat',8,[9,3],'처음 마주 앉은 한 식탁에서 우리의 이야기가 시작됐습니다.')
add('bubble',7,[5,6],'평범한 하루에도 함께한 기억이 쌓였습니다.')
add('activity',8,[1,2,20],'함께 움직이는 날도 좋았습니다.',chapter='함께 즐기는 것은?',en='Days in motion',who='groom')
add('pair',7,[15,16],'각자의 걸음으로 올라, 같은 풍경을 바라봅니다.',chapter='함께 즐기는 것은?',en='Days in motion',who='bride')
add('filmstrip',7,[17,38,39,40],'우리의 페이스로',chapter='함께한 소중한 순간')
add('video',3.6,[21],'함께 움직이는 날들',src=0,who='groom')
add('video',8,[22],'함께하면 즐거운 순간',src=7,who='bride')
add('portrait',7,[13,14],'둘이서 채워 온 장면들',chapter='우리다운 모습은?',en='Just the two of us',who='groom')
add('filmphoto',7,[18,10],'기념하고 싶은 날에도 함께',chapter='우리다운 모습은?',en='Just the two of us',who='bride')
add('pair',7,[23,24],'서로를 담아 주고',chapter='함께 떠난 여행',en='Places we have been',who='groom')
add('activity',7,[32,33],'낯선 곳도 함께 걷고',chapter='함께 떠난 여행',en='Places we have been',who='bride')
add('pair',7,[34,35,36],'마음껏 들뜨는 날도',chapter='함께 떠난 여행',en='Places we have been',who='groom')
add('pair',7,[7,8,41],'푸른 계절을 지나',chapter='함께 떠난 여행',en='Places we have been',who='bride')
add('forever',8,[19,11],'나란히 쉬는 날도 좋았습니다.')
add('pinkphoto',7,[27,28],'천천히 머물고, 같은 그늘 아래',who='groom')
add('pinkphoto',7,[29,30],'걷다가, 쉬어 가다가',who='bride')
add('pinkphoto',7,[31,26],'하루의 끝에도 함께',who='groom')
add('memories',7,[37,44],'우리다운 순간들')
add('filmstrip',8,[32,33,36],'함께 떠난 여행',chapter='함께한 소중한 순간')
add('pair',7,[23,24,43],'둘이서 남긴 작은 장면들',chapter='함께한 소중한 순간',en='Our special moments',who='bride')
add('seasons',9,[12,38,4,20],'함께 쌓아 온 봄, 여름, 가을, 겨울')
add('keepsakes',8,[3,6,45],'차곡차곡 쌓인 우리의 시간')
add('video',8.5,[25],'함께한 하루의 한 장면',src=.3,who='bride')
add('pair',7,[42,43],'새로운 장면 속에서도 함께',chapter='함께한 소중한 순간',en='Our special moments',who='groom')
add('video',8.5,[46],'우리다운 표정으로, 앞으로도',src=1,who='bride')
add('booth',4,[45],'앞으로도, 우리답게.')
add('window_end',8,[11])
add('window_end',7,[12])
add('film_end',8,[11,37,44])
add('film_end',7,[4,12,41])
add('thanks',7,[11],'소중한 분들과 함께\n새로운 날을 시작합니다.')
add('thanks',7,[44],'행복한 시작을\n함께해 주셔서 감사합니다.')
fixed=sum(round(s['requested']*FPS) for s in SCENES if s['kind']=='video');wanted=sum(s['requested'] for s in SCENES if s['kind']!='video')
for i,s in enumerate(SCENES):s.update(index=i,frames=round(s['requested']*FPS) if s['kind']=='video' else round(s['requested']/wanted*(7410-fixed)))
SCENES[-1]['frames']+=7410-sum(s['frames'] for s in SCENES)
at=0
for s in SCENES:
    s.update(start=at/FPS,duration=s['frames']/FPS,end=(at+s['frames'])/FPS);at+=s['frames']
    if s['kind']=='video':
        mid=s['ids'][0];old=VIDEO_SPECS[mid];vw,vh=(1180,664) if mid==22 else ((450,790) if mid!=46 else (292,875))
        s.update(vx=(W-vw)//2,vy=135 if mid==46 else 160,vw=vw,vh=vh)
        crop='crop=iw/3:ih:iw/3:0,' if mid==46 else ''
        s['video_filter']=crop+f'scale={vw}:{vh}:force_original_aspect_ratio=increase,crop={vw}:{vh},setsar=1'
m.T=SCENES

def prepare(s):
    i=s['index'];k=s['kind'];ids=s['ids'];dur=s['duration']
    color='pink' if k in ['duo','profile_bride','forever','pinkphoto'] else ('blue' if k=='profile_groom' else 'ivory')
    o=empty(s,color)
    if k=='opening_a':
        p=cut('couple44',990);layer(o,p,W-p.width+80,115,.15,'up',1.1)
        word(o,'Our',135,430,180,'#d58c3a','script',.55)
        word(o,'Forever',120,610,185,'#c77c2b','serif',.85)
        word(o,'Mingyu + Jihae',460,940,35,'#be843b','italic',1.3,center=True)
        path(o,[(460+340*math.cos(t),970+29*math.sin(t)) for t in np.linspace(0,2*math.pi,100)],'#c39350',3,1.8,1)
        path(o,bez([(0,260),(240,420),(440,170),(720,485)]),'#dfbc69',6,.3,1.8,True)
        if HEARTS:inkheart(o,720,260,520,470,'#dfbc69',.6,False,True)
        path(o,bez([(720,485),(890,360),(1000,450),(1450,300)]),'#dfbc69',5,1.4,1.5,True)
        ribbon(o,1740,135,60,BLUE,1.3)
    elif k=='opening_b':
        p=shadow(torn(1040,1040,'white',72));layer(o,p,-65,25,0,'left',.7)
        p=cut('couple17',1020);layer(o,p,80,130,.25,'up',.8)
        word(o,'Our story begins here',1340,240,34,INK,'sans',.5,center=True)
        for j,(word_,fs,kind) in enumerate([('Happily',175,'serif'),('ever',145,'script'),('After',185,'serif')]):word(o,word_,1350,300+j*177,fs,RED,kind,.7+j*.25,center=True)
        word(o,'Mingyu + Jihae',1360,925,32,RED,'italic',1.5,center=True)
        path(o,[(1350+380*math.cos(t),950+31*math.sin(t)) for t in np.linspace(0,2*math.pi,100)],RED,3,1.7,1)
        if HEARTS:inkheart(o,1300,350,780,600,'#d7b7b6',.2,False,True)
        ribbon(o,1750,140,65,PINK,1)
    elif k=='duo':
        g=cut('groom',830);b=cut('bride',830);layer(o,g,70,220,.25,'left',1.1,spin=-7);layer(o,b,1360,220,.45,'right',1.1,spin=7)
        if HEARTS:
            inkheart(o,960,550,1010,835,RED,.1,True,True)
        else:
            pts=[(960+440*math.cos(t)*(1+.025*math.sin(10*t)),555+405*math.sin(t)*(1+.025*math.sin(10*t))) for t in np.linspace(0,2*math.pi,240)];path(o,pts,RED,5,.2,1.5)
            path(o,[(x+14,y+9) for x,y in pts],RED,3,.35,1.5)
        ribbon(o,615,200,175,RED,.65,True)
        word(o,'all things about',960,355,57,RED,'italic',.7,center=True)
        word(o,'U S',960,490,100,RED,'serif',1,center=True)
        word(o,'love story',960,660,103,RED,'script',1.4,center=True)
        for x in [35,1650]:layer(o,deco('spark',160,RED),x,240,1.6,'draw',1)
    elif k.startswith('profile'):
        groom=k=='profile_groom';who='groom' if groom else 'bride';c=BLUE if groom else RED
        p=cut(who,1030);layer(o,p,-40 if groom else 1220,110,.1,'left' if groom else 'right',1,spin=-4 if groom else 4)
        sheet=shadow(torn(1130,540,'graph' if groom else 'white',42));layer(o,sheet,730 if groom else 40,490,.5,'up',.8,spin=-3 if groom else 3)
        cx=1070 if groom else 835
        word(o,'Groom' if groom else 'Bride',cx,105,58,c,'serif',.3,center=True)
        path(o,[(cx+195*math.cos(t),145+46*math.sin(t)) for t in np.linspace(0,2*math.pi,90)],c,3,.6,.75)
        word(o,'백민규' if groom else '박지해',cx,235,135,c,'bold',.6,mode='pop',center=True)
        phrases=['함께 걷는 여행','새로운 도전','나란히 쉬는 시간'] if groom else ['기억하고 싶은 순간','둘이 채운 이야기','앞으로도 함께']
        for j,p in enumerate(phrases):word(o,'# '+p,820 if groom else 120,570+j*115,75,c if j==0 else INK,delay=1+j*.45)
        c1=card(ids[0],(240,285),'stamp',-7);c2=card(ids[1],(230,265),'stamp',8)
        layer(o,c1,1590 if groom else 50,190,1.6,'pop',.8);layer(o,c2,1670 if groom else 245,340,1.9,'pop',.8)
    elif k=='chat':
        p=card(9,(650,590),'stamp',-2);layer(o,p,210,80,.3,'pop',.8,spin=-5)
        p=card(3,(390,420),'stamp',3);layer(o,p,1410,390,1.2,'pop',.8,spin=5)
        bubble=Image.new('RGBA',(760,125));d=ImageDraw.Draw(bubble);d.rounded_rectangle((0,0,759,124),50,fill='#fffefa');d.polygon([(680,90),(745,150),(735,80)],fill='#fffefa')
        layer(o,shadow(bubble),240,675,.8,'pop',.7);word(o,'처음 마주 앉은 한 식탁에서',640,703,48,delay=1,center=True)
        layer(o,shadow(bubble.resize((620,125))),1000,810,1.7,'pop',.7);word(o,'우리의 이야기가 시작됐습니다',1330,842,44,delay=1.9,center=True)
        label(o,'우리의 첫 만남','How we first met',65,810,.2)
        subtitle(o,s['caption'],2.4)
        layer(o,deco('bow',125,PINK),50,590,1.6,'draw',1)
    elif k=='bubble':
        p=card(ids[0],(830,840),'polaroid',-5);layer(o,p,975,75,.3,'right',1,spin=7)
        bubble=shadow(torn(760,250,'white',82));layer(o,bubble,140,350,.4,'pop',.8)
        word(o,'함께한 평범한 하루',520,450,65,delay=.9,center=True)
        p=card(ids[1],(360,410),'stamp',5);layer(o,p,715,570,2,'pop',.8,spin=-5)
        label(o,'우리의 이야기','Our first pages',65,790,.1);subtitle(o,s['caption'],1)
        layer(o,deco('bow',150,PINK),65,130,1.2,'draw',1)
    elif k in ['activity','pair']:
        who=s.get('who','groom');speaker(o,who);label(o,s['chapter'],s['en'])
        if k=='activity':
            p=card(ids[0],(650,790),'polaroid',13);layer(o,p,260,130,.35,'pop',1,spin=-14)
            p=card(ids[1],(560,710),'polaroid',-4);layer(o,p,710,150,1.0,'pop',.9,spin=12)
            if len(ids)>2:p=card(ids[2],(650,670),'stamp',3)
            else:p=cut(who,710)
            layer(o,p,1235,260,1.75,'up',.85,spin=-5)
            tape(o,490,133,'blue',1.25);tape(o,910,145,'pink',1.7)
            layer(o,deco('camera',130),1160,760,2.4,'pop',.65,spin=12)
        else:
            p=card(ids[0],(780,810),'polaroid',5);layer(o,p,320,125,.3,'pop',.85,spin=-10)
            p=card(ids[1],(710,735),'polaroid',-8);layer(o,p,1030,215,1.0,'pop',.85,spin=9)
            if len(ids)>2:
                p=card(ids[2],(350,365),'stamp',4);layer(o,p,1435,620,2,'pop',.8,spin=8)
            layer(o,deco('plane',145,BLUE),120,250,1.8,'draw',1.2)
        subtitle(o,s['caption'],.8)
    elif k in ['portrait','filmphoto']:
        speaker(o,s['who']);label(o,s['chapter'],s['en'])
        style='film' if k=='filmphoto' else 'polaroid'
        for j,mid in enumerate(ids):
            source=m.fit(m.photo(mid),(810,700),mid) if k=='filmphoto' else mid
            p=card(source,(900,830),style,-4 if k=='filmphoto' else 1)
            layer(o,p,(W-p.width)//2,95,j*(dur*.50)+.3,'fade' if j else 'pop',.65,spin=8 if j==0 else 0)
            if j==0:o['layers'][-1]['exit_at']=dur*.5+.3
        layer(o,deco('ring',130,PINK),1640,580,1.3,'draw',1.1)
        layer(o,deco('bow',180,PINK),140,290,1.3,'draw',1)
        if HEARTS:
            inkheart(o,1535,455,125,142,PINK,1.8,True)
            inkheart(o,1620,530,64,76,PINK,2.1)
        subtitle(o,s['caption'],.7)
    elif k=='forever':
        panel=shadow(torn(1250,745,'white',42,True));layer(o,panel,660,80,.1,'right',1,spin=2);tape(o,1540,60,'pink',1)
        p=cut('couple44',850);layer(o,p,-80,260,.35,'left',.9,spin=3)
        word(o,'Why we chose',1270,260,125,RED,'script',.8,center=True);word(o,'Forever',1390,465,155,RED,'script',1.3,center=True)
        # Round photo pin, like the reference chapter card.
        p=m.fit(ImageOps.grayscale(m.photo(19)).convert('RGB'),(350,350)).convert('RGBA');mask=Image.new('L',p.size);ImageDraw.Draw(mask).ellipse((0,0,349,349),fill=255);p.putalpha(mask)
        pin=Image.new('RGBA',(400,460));d=ImageDraw.Draw(pin);d.ellipse((0,0,399,399),fill='white');d.polygon([(80,310),(200,460),(320,310)],fill='white');pin.alpha_composite(p,(25,25));layer(o,shadow(pin),55,585,1.2,'pop',.8)
        layer(o,deco('ring',125,'#fffdf7'),1670,850,1.7,'draw',1.1);o['sparkles']=True
    elif k=='pinkphoto':
        speaker(o,s['who']);o['sparkles']=True
        for j,mid in enumerate(ids):
            p=card(mid,(1120,770),'plain',0);layer(o,p,(W-p.width)//2,135,.35+j*dur*.49,'fade' if j else 'pop',.7)
            if j==0:o['layers'][-1]['exit_at']=dur*.49+.35
        tape(o,460,135,'pink',1)
        for kind,x,y in [('bow',140,240),('ring',130,530),('arrow',1625,370)]:layer(o,deco(kind,165,'#fffdf8'),x,y,1.2,'draw',1.1)
        if HEARTS:inkheart(o,1790,515,120,155,'#fffdf8',1.5,True)
        subtitle(o,s['caption'],.7)
    elif k=='memories':
        p=card(ImageOps.grayscale(m.photo(ids[0])).convert('RGB'),(910,800),'stamp',5);layer(o,p,100,100,.2,'pop',1,spin=-9)
        p=cut('couple44',870);layer(o,p,880,230,.65,'right',.85,spin=3)
        word(o,'Our Special',510,825,103,INK,'script',.8,center=True);word(o,'Moments',630,945,98,INK,'script',1.15,center=True)
        path(o,bez([(760,930),(960,950),(1030,840),(950,810)]),INK,5,1.7,1)
        label(o,'함께한 소중한 순간','',1390,45,.1);o['sparkles']=True
    elif k=='filmstrip':
        film=Image.new('RGBA',(1810,620),'#2e2827');d=ImageDraw.Draw(film)
        for j,mid in enumerate(ids[:3]):
            p=m.fit(m.photo(mid),(570,540),mid);film.paste(p,(25+j*595,40));txt(film,f'FRAME {j+1:02d}     OUR MEMORIES',(30+j*595,10),15,'#d6c2a1','sans')
        film=shadow(film.rotate(2,Image.Resampling.BICUBIC,expand=True));layer(o,film,25,200,.3,'left',1.1,spin=-4)
        if len(ids)>3:
            p=card(ids[3],(360,365),'stamp',-7);layer(o,p,1460,640,2.2,'pop',.8)
        label(o,s['chapter'],'',1390,50,.1);label(o,s['caption'],'',630,880,1.1)
        layer(o,deco('camera',135),100,870,1.3,'pop',.8,spin=-5)
    elif k=='seasons':
        label(o,'함께한 소중한 순간','',1380,45,.1)
        for j,mid in enumerate(ids):
            style='marker' if j in [0,3] else 'polaroid';source=m.fit(m.photo(mid),(430,490),mid) if mid==4 else mid
            p=card(source,(510,660),style,[8,5,-8,-6][j]);x=10+j*462;y=min([200,115,250,175][j],850-p.height)
            layer(o,p,x,y,.3+j*.5,'pop',.85,spin=[-9,10,-9,9][j])
            word(o,['봄','여름','가을','겨울'][j],x+220,y+p.height+5,49,delay=1+j*.5,center=True)
        label(o,s['caption'],'',280,925,1.2)
    elif k=='keepsakes':
        p=cut('groom',920);layer(o,p,-70,155,.2,'left',.9,spin=-4)
        p=card(ids[0],(780,800),'plain',0);layer(o,p,580,120,.7,'pop',.9)
        p=card(ids[1],(510,620),'polaroid',-8);layer(o,p,1310,410,1.4,'pop',.8,spin=12)
        p=card(ids[2],(220,690),'stamp',6);layer(o,p,1625,180,1.9,'pop',.8,spin=-8)
        label(o,'함께한 소중한 순간','',1390,45,.1);label(o,'우리의 작은 기록들','',1120,195,.7)
        subtitle(o,s['caption'],1.2)
        path(o,bez([(990,910),(1060,900),(1050,865),(1010,850)]),INK,4,1.4,1)
    elif k=='video':
        speaker(o,s['who']);label(o,'함께한 소중한 순간','Our moving memories',1390,55)
        x,y,vw,vh=s['vx'],s['vy'],s['vw'],s['vh'];p=texture('white',(vw+44,vh+70),12).convert('RGBA');p=shadow(p);layer(o,p,x-42,y-42,0,'fade',.3)
        o['video_insert_after']=len(o['layers']);tape(o,x+vw//2-85,y-20,'blue' if s['who']=='groom' else 'pink',.65)
        layer(o,deco('camera',150),1480,650,1,'pop',.7,spin=10);subtitle(o,s['caption'],.65)
    elif k=='booth':
        p=m.photo(45)
        for j,(a,b) in enumerate([(.012,.222),(.231,.442),(.45,.662),(.67,.88)]):
            pp=p.crop((round(.02*p.width),round(a*p.height),round(.98*p.width),round(b*p.height)));pp=card(pp,(500,610),'polaroid',[4,-5,5,-4][j]);layer(o,pp,20+j*465,180+(j%2)*135,j*.35,'pop',.75,spin=(-1)**j*9)
        label(o,'우리다운 표정으로','',1380,45);subtitle(o,s['caption'],1.4)
    elif k=='window_end':
        # A scalloped pink paper window; previous no-heart preference selects an oval.
        ww,hh=1480,950;panel=torn(ww,hh,'pink',33,True);mask=Image.new('L',(ww,hh));d=ImageDraw.Draw(mask)
        if HEARTS:
            pts=heart_contour(ww/2,hh*.49,ww*.89,hh*.95,85,rough=3.6);d.polygon(pts,fill=255)
        else:d.rounded_rectangle((65,50,ww-65,hh-50),radius=240,fill=255)
        for j,mid in enumerate(ids):
            p=m.fit(m.photo(mid),(ww,hh),mid)
            p=p.convert('RGBA');p.putalpha(mask)
            out=panel.copy();out.alpha_composite(p);out=shadow(out);layer(o,out,(W-out.width)/2,40,.2+j*dur*.5,'fade',.8)
        for x,y in [(20,700),(1720,140)]:layer(o,deco('bow',170,PINK),x,y,1,'draw',1.4)
        layer(o,deco('spark',140,PINK),20,270,1,'draw',1.4)
    elif k=='film_end':
        # Film roll is a moving strip, including adjacent frames and sprocket holes.
        roll=Image.new('RGB',(W*3,H),'#151315');d=ImageDraw.Draw(roll)
        for j,mid in enumerate(ids):
            p=ImageOps.grayscale(m.fit(m.photo(mid),(1500,920),mid)).convert('RGB');roll.paste(p,(j*W+210,80))
            for x in range(j*W,j*W+W,135):
                d.rounded_rectangle((x+30,10,x+83,65),8,fill='#c6bfc5');d.rounded_rectangle((x+30,H-65,x+83,H-10),8,fill='#c6bfc5')
        o['roll']=roll;o['sparkles']=True
    elif k=='thanks':
        p=ImageOps.grayscale(ImageOps.contain(m.photo(ids[0]),(1160,H),Image.Resampling.LANCZOS)).convert('RGB');p=Image.blend(p,Image.new('RGB',p.size,'#545454'),.18);o['bg']=Image.new('RGB',(W,H),'#969694');o['bg'].paste(p,(0,(H-p.height)//2))
        veil=Image.new('RGBA',(W,H));d=ImageDraw.Draw(veil);d.polygon([(1000,0),(W,0),(W,H),(1260,H)],fill=(210,210,205,155));layer(o,veil,0,0,0,'fade',.2)
        for j,line in enumerate(s['caption'].split('\n')):word(o,line,1470,440+j*90,62,'#ffffff',delay=.7+j*.25,center=True)
        word(o,'백민규 · 박지해',1470,750,43,'white',delay=1.4,center=True)
        word(o,'2026.12.12',1470,838,31,'white','sans',1.7,center=True)
    return o

def ease(v):return 1-(1-max(0,min(1,v)))**3
def back(v):
    v=max(0,min(1,v))-1;return 1+2.70158*v**3+1.70158*v*v
def paste(im,p,x,y,alpha=1):
    if alpha<=0:return
    if alpha<.999:p=p.copy();p.putalpha(p.getchannel('A').point(lambda a:round(a*alpha)))
    im.paste(p,(round(x),round(y)),p)
def draw_layer(im,a,t):
    age=t-a['delay']
    if age<0 or ('exit_at' in a and t>=a['exit_at']+.65):return
    p=a['im'];x,y=a['x'],a['y'];u=min(1,age/a['span']);q=ease(u);mode=a['mode'];alpha=min(1,u*4)
    if u<1:
        if mode in ['pop','drop']:
            z=max(.04,back(u));nw,nh=max(1,round(p.width*z)),max(1,round(p.height*z));p=p.resize((nw,nh),Image.Resampling.BICUBIC);x+=(a['im'].width-nw)/2;y+=(a['im'].height-nh)/2
            if mode=='drop':y-=(1-q)*150
        elif mode in ['left','right']:x+=(1-q)*(-450 if mode=='left' else 450)
        elif mode=='up':y+=(1-q)*180
        elif mode=='fade':alpha=q
        elif mode in ['write','draw']:
            width=max(1,round(p.width*q));p=p.crop((0,0,width,p.height));alpha=1
        if a['spin']:
            before=p.size;p=p.rotate(a['spin']*(1-q),Image.Resampling.BICUBIC,expand=True);x+=(before[0]-p.width)/2;y+=(before[1]-p.height)/2
    if 'exit_at' in a and t>a['exit_at']:alpha*=1-ease((t-a['exit_at'])/.65)
    paste(im,p,x,y,alpha)

def scene_frame(o,t,vframe=None):
    s=o['s'];im=o['bg'].copy()
    if 'roll' in o:
        phase=t/max(.001,s['duration'])*3;shot=min(2,int(phase));f=phase-shot
        q=ease(min(1,f/.18));x=round(max(0,shot-1)*W+W*q) if shot>0 else round(40*t/s['duration'])
        x=min(o['roll'].width-W,x);im=o['roll'].crop((x,0,x+W,H))
    def paths(behind):
        for a in o['paths']:
            if a.get('behind',False)!=behind:continue
            u=max(0,min(1,(t-a['delay'])/a['span']));n=round(u*(len(a['pts'])-1))+1
            if n>=2:ImageDraw.Draw(im).line(a['pts'][:n],fill=a['color'],width=a['width'],joint='curve')
    paths(True)
    for j,a in enumerate(o['layers']):
        if vframe is not None and j==o.get('video_insert_after'):
            im.paste(vframe,(s['vx'],s['vy']))
        draw_layer(im,a,t)
    paths(False)
    if o['sparkles']:
        lay=Image.new('RGBA',(W,H));d=ImageDraw.Draw(lay);rng=random.Random(71)
        for j in range(150):
            x=rng.randrange(W);y=rng.randrange(H);phase=rng.random()*6.28;a=max(0,math.sin(t*1.6+phase));r=1 if j%4 else 2;d.ellipse((x-r,y-r,x+r,y+r),fill=(255,250,242,int(a*100)))
        im.paste(lay,(0,0),lay)
    return im

TRANS={i:('paper' if s['kind'] in ['opening_b','duo','profile_groom','profile_bride','chat','forever','memories','seasons','window_end'] else ('diagonal' if s['kind']=='thanks' else 'fade')) for i,s in enumerate(SCENES) if i}
TRANS[32]='fade'
def transition(im,old,t,kind):
    span=.85 if kind=='paper' else (.65 if kind=='diagonal' else .36)
    if t>=span:return im
    p=t/span;q=ease(p)
    if kind=='fade':return Image.blend(old,im,q)
    if kind=='diagonal':
        mask=Image.new('L',(W,H));x=-500+(W+1000)*q;ImageDraw.Draw(mask).polygon([(0,0),(x+450,0),(x,H),(0,H)],fill=255);return Image.composite(im,old,mask)
    # Multiple rough horizontal paper bands wipe across in alternating directions.
    mask=Image.new('L',(W,H));d=ImageDraw.Draw(mask);rng=random.Random(85)
    for j in range(6):
        v=ease((p-j*.055)/.69);edge=round((W+40)*v)-20;y=j*H//6
        pts=[(edge+rng.randrange(-20,20),yy) for yy in range(y,y+H//6+12,6)]
        poly=[(-30,y-4)]+pts+[(-30,y+H//6+12)] if j%2==0 else [(W+30,y-4)]+[(W-x,yy) for x,yy in pts]+[(W+30,y+H//6+12)]
        if v>0:d.polygon(poly,fill=255)
    paper=texture('ivory');covered=Image.composite(paper,old,mask)
    reveal=ease(max(0,(p-.32)/.68));return Image.blend(covered,im,reveal)
m.prepare=prepare;m.scene_frame=scene_frame;m.TRANS=TRANS;m.transition=transition

def main():
    create_cutouts();assert sum(s['frames'] for s in SCENES)==7410
    assert {n for s in SCENES for n in s['ids']}==set(range(1,47))
    if '--preview' in sys.argv:
        for pg in range(math.ceil(len(SCENES)/12)):
            sheet=Image.new('RGB',(1440,1176),'#d5d0c9');d=ImageDraw.Draw(sheet)
            for j,s in enumerate(SCENES[pg*12:(pg+1)*12]):
                o=prepare(s);vf=m.video_last(s) if s['kind']=='video' else None;p=scene_frame(o,min(3.8,s['duration']*.75),vf);p.save(WORK/f"layout_{s['index']:02}.jpg",quality=92)
                p.thumbnail((474,267));x=j%3*480;y=j//3*294;sheet.paste(p,(x,y));d.text((x+5,y+270),f"{s['index']:02} {s['kind']}",font=font(17,'sans'),fill='black')
            sheet.save(WORK/f'layout_sheet_{pg+1}.jpg',quality=92)
        print('PREVIEWS READY',flush=True);return
    objs=[];lasts=[]
    for s in SCENES:
        o=prepare(s);objs.append(o);vf=m.video_last(s) if s['kind']=='video' else None;last=scene_frame(o,s['duration']-1/FPS,vf);lasts.append(last)
    (WORK/'timeline.json').write_text(json.dumps([dict(s,motion=TRANS.get(s['index'],'none'),hearts=HEARTS) for s in SCENES],ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Prepared {len(SCENES)} scenes, 247s, hearts={HEARTS}',flush=True)
    only=next((a.split('=')[1] for a in sys.argv if a.startswith('--only=')),None)
    todo=objs if only is None else [objs[int(n)] for n in only.split(',')]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        fs=[pool.submit(m.render,o,lasts[o['s']['index']-1] if o['s']['index'] else None) for o in todo]
        for f in concurrent.futures.as_completed(fs):print('RENDERED',f.result(),flush=True)
    if only is not None:return
    concat=WORK/'concat.txt';concat.write_text('\n'.join("file '"+(m.SEGS/f'{i:02}.mp4').as_posix()+"'" for i in range(len(SCENES))),encoding='utf-8')
    subprocess.run([m.FF,'-v','error','-y','-f','concat','-safe','0','-i',str(concat),'-i',m.AUDIO,'-map','0:v:0','-map','1:a:0','-c:v','copy','-af','atrim=duration=247,asetpts=PTS-STARTPTS,afade=t=out:st=244:d=3','-c:a','aac','-b:a','320k','-ar','48000','-t','247','-movflags','+faststart',str(m.OUT)],check=True)
    print('FINAL',m.OUT,m.OUT.stat().st_size,flush=True)
if __name__=='__main__':main()
