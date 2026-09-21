import json, subprocess, re
t=json.load(open("transcript.json"))
raw=[(a.strip(),b,c) for s in t for a,b,c in s["words"]]
# merge "crane"+"signal" -> CraneSignal
words=[];i=0
while i<len(raw):
    w,b,c=raw[i]
    if w.lower().strip(",.")=="crane" and i+1<len(raw) and raw[i+1][0].lower().startswith("signal"):
        tail=re.sub(r"^signal","",raw[i+1][0],flags=re.I)
        words.append(("CraneSignal"+tail,b,raw[i+1][2])); i+=2
    else: words.append((w,b,c)); i+=1
json.dump(words,open("words.json","w"))

def ts(x):
    h=int(x//3600);m=int(x%3600//60);s=x%60
    return f"{h}:{m:02d}:{s:05.2f}"
def chunks(n):
    out=[];cur=[]
    for w in words:
        cur.append(w)
        if len(cur)>=n or w[0][-1] in ".?!,":
            out.append(cur);cur=[]
    if cur: out.append(cur)
    return out
HDR="""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
{style}

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
YEL="&H0000E6FF&"; WHITE="&H00FFFFFF&"; BLUE="&H00FF8A4A&"  # BGR
def build(name,style,n,fmt):
    ev=[]
    for ch in chunks(n):
        for k,(w,b,c) in enumerate(ch):
            end=ch[k+1][1] if k+1<len(ch) else c
            end=max(end,b+0.12)
            ev.append(f"Dialogue: 0,{ts(b)},{ts(end)},D,,0,0,0,,{fmt(ch,k)}")
    open(f"{name}.ass","w").write(HDR.format(style=style)+"\n".join(ev)+"\n")

def up(s): return s.upper()
# A: pop, 3 words, active yellow + bigger
def fa(ch,k):
    return " ".join((r"{\c"+YEL+r"\fscx118\fscy118}"+up(w)+r"{\c"+WHITE+r"\fscx100\fscy100}") if j==k else up(w) for j,(w,_,_) in enumerate(ch))
build("A","Style: D,Montserrat Black,88,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,9,3,2,60,60,400,1",3,fa)
# B: dark box, 4 words, active light blue
def fb(ch,k):
    return " ".join((r"{\c&H00FFB86B&}"+w+r"{\c"+WHITE+"}") if j==k else w for j,(w,_,_) in enumerate(ch))
build("B","Style: D,Inter ExtraBold,66,&H00FFFFFF,&H00FFFFFF,&HB4201008,&H00000000,0,0,0,0,100,100,0,0,3,22,0,2,60,60,360,1",4,fb)
# C: one word at a time, big
def fc(ch,k): return up(ch[k][0].rstrip(",.?!"))
build("C","Style: D,Montserrat Black,170,&H00FFFFFF,&H00FFFFFF,&H00E0561F,&H80000000,0,0,0,0,100,100,0,0,1,12,6,2,60,60,440,1",1,fc)
# D: two-line clean, 6 words, active yellow, soft shadow
def fd(ch,k):
    parts=[(r"{\c"+YEL+"}"+w+r"{\c"+WHITE+"}") if j==k else w for j,(w,_,_) in enumerate(ch)]
    if len(parts)>3: parts=parts[:3]+[r"\N"+parts[3]]+parts[4:]
    return " ".join(parts).replace(r" \N",r"\N")
build("D","Style: D,Inter ExtraBold,62,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,5,4,2,60,60,320,1",6,fd)

for n in "ABCD":
    for tag,tt in (("face",11.6),("screen",42.0)):
        subprocess.run(["ffmpeg","-y","-loglevel","error","-i","raw.mov","-vf",f"scale=1080:1920:flags=lanczos,ass={n}.ass:fontsdir=/home/drewp/.fonts","-ss",str(tt),"-frames:v","1",f"{n}_{tag}.png"],check=True)
# montage
subprocess.run("ffmpeg -y -loglevel error "+" ".join(f"-i {n}_{t}.png" for t in ("face","screen") for n in "ABCD")+" -filter_complex \""+"".join(f"[{i}:v]scale=405:720[s{i}];" for i in range(8))+"".join(f"[s{i}]" for i in range(8))+"xstack=inputs=8:layout=0_0|405_0|810_0|1215_0|0_720|405_720|810_720|1215_720\" -frames:v 1 styles.png",shell=True,check=True)
