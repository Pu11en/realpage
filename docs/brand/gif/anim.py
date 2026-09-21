import math, subprocess, sys
from playwright.sync_api import sync_playwright
BLUE="#1a3d8f"; Y="#f5b700"
def ease(x): x=max(0,min(1,x)); return x*x*(3-2*x)
def clamp(a,b,x): return ease((x-a)/(b-a))
STAYS='<path d="M13.5 3 5 10M13.5 3 38 10" stroke="#fff" stroke-width="1.6" fill="none"/>'
MAST='<path d="M11 10h5v26h-5z" fill="#fff"/><path d="M11 10l2.5-7 2.5 7z" fill="#fff"/>'
BASE='<path d="M5 36h17v4H5z" fill="#fff"/>'
JIB=f'<path d="M4 10h36v4H4z" fill="{Y}"/><path d="M5 14h5v4H5z" fill="#fff"/>'
def wrap(inner,extra=""):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 44 44"><rect width="44" height="44" fill="{BLUE}"/>{extra}<g transform="translate(22 22.5) scale(0.72) translate(-22 -21.5)">{inner}</g></svg>'

# A: crane builds a building floor by floor
def build(t):
    i=min(2,int(t*3)); u=t*3-i
    tx=31; floors=1+i
    x0,w=25.5,11
    fl=""
    extra_op=1.0
    if i==2 and u>0.7: extra_op=1-clamp(0.7,1,u)
    for k in range(floors+ (1 if u>=0.55 else 0)):
        top=36-4*(k+1)
        op=1 if k==0 else extra_op
        fl+=f'<rect x="{x0}" y="{top+0.4}" width="{w}" height="3.6" fill="#fff" opacity="{op:.2f}"/>'
        for wx in (x0+1.6,x0+4.6,x0+7.6):
            fl+=f'<rect x="{wx}" y="{top+1.5}" width="1.8" height="1.4" fill="{BLUE}" opacity="{op:.2f}"/>'
    target=36-4*(floors+1)
    if u<0.55:
        ly=16+(target-16)*clamp(0,0.55,u); load=f'<rect x="{x0}" y="{ly:.2f}" width="{w}" height="4" fill="{Y}"/>'; hook=ly
    else:
        ly=target+(16-target)*clamp(0.62,1,u); load=""; hook=ly
    cable=f'<path d="M{tx-0.4} 14h0.8v{hook-14:.2f}h-0.8z" fill="#fff"/><rect x="{tx-1.6}" y="13.2" width="3.2" height="1.8" fill="#fff"/>'
    return wrap(STAYS+MAST+BASE+JIB+fl+cable+load)

# B: logo assembles itself, holds, fades
def assemble(t):
    mast=clamp(0.0,0.18,t); jib=clamp(0.15,0.33,t); stay=clamp(0.3,0.42,t); cab=clamp(0.4,0.52,t); load=clamp(0.5,0.6,t)
    fade=1-clamp(0.88,1,t)
    s=f'<g opacity="{fade:.2f}">'+BASE
    s+=f'<g transform="translate(0 {36*(1-mast):.2f}) scale(1 {max(mast,0.001):.3f})">{MAST}</g>'
    s+=f'<clipPath id="c"><rect x="0" y="0" width="{4+36*jib:.2f}" height="44"/></clipPath><g clip-path="url(#c)">{JIB}</g>'
    s+=f'<g opacity="{stay:.2f}">{STAYS}</g>'
    cy=14+8*cab
    if cab>0: s+=f'<path d="M31 14h1.6v{cy-14:.2f}H31z" fill="#fff"/>'
    if load>0:
        sw=6*math.sin(t*28)*(1-clamp(0.6,0.85,t))
        s+=f'<g transform="rotate({sw:.2f} 31.8 14)"><rect x="27.8" y="22" width="8" height="7" fill="{Y}" opacity="{load:.2f}"/></g>'
    return wrap(s+'</g>')

# C: static logo, clean signal ping from the load
def ping(t):
    rings=""
    for k in range(2):
        p=(t+k*0.5)%1; r=4+22*ease(p); op=0.55*(1-p)
        rings+=f'<circle cx="31.8" cy="25.5" r="{r:.2f}" fill="none" stroke="{Y}" stroke-width="0.9" opacity="{op:.2f}"/>'
    logo=STAYS+MAST+BASE+JIB+'<path d="M31 14h1.6v8H31z" fill="#fff"/>'+f'<rect x="27.8" y="22" width="8" height="7" fill="{Y}"/>'
    return wrap(rings+logo)

name,N,fps=sys.argv[1],int(sys.argv[2]),int(sys.argv[3])
fn={"build":build,"assemble":assemble,"ping":ping}[name]
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={"width":512,"height":512})
    for i in range(N):
        pg.set_content('<body style="margin:0">'+fn(i/N)+'</body>')
        pg.screenshot(path=f"{name}{i:03d}.png",clip={"x":0,"y":0,"width":512,"height":512})
    b.close()
subprocess.run(f'ffmpeg -y -loglevel error -framerate {fps} -i {name}%03d.png -vf "scale=400:400:flags=lanczos,split[a][b];[a]palettegen=max_colors=48[p];[b][p]paletteuse=dither=none" -loop 0 ../cranesignal-logo-{name}.gif',shell=True,check=True)
subprocess.run(f'ffmpeg -y -loglevel error -i {name}%03d.png -vf "select=\'not(mod(n,{N//8}))\',format=rgba,geq=r=\'r(X,Y)\':g=\'g(X,Y)\':b=\'b(X,Y)\':a=\'if(lte(hypot(X-256,Y-256),256),255,0)\',scale=160:-1,tile=8x1" -frames:v 1 /tmp/strip-{name}.png',shell=True,check=True)
subprocess.run(f"rm {name}*.png",shell=True)
