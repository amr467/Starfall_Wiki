import os, re, json

CONTENT_DIR = "content"
OUTPUT_FILE = os.path.join(CONTENT_DIR, "graph.html")

COLORS = {
    "Champion": "#c084fc",
    "Story": "#f9a8d4",
    "Pre-Starfall": "#fcd34d",
    "Post-Starfall Faction": "#6ee7b7",
    "Location": "#7dd3fc",
    "Meta": "#fb923c",
    "Mystery": "#f87171",
    "Figure": "#a78bfa",
    "Concept/Item": "#34d399",
    "Other": "#94a3b8",
}

def get_tags(text):
    m = re.search(r'tags:\s*\[([^\]]+)\]', text)
    if not m: return []
    return [t.strip().strip('"\'') for t in m.group(1).split(',')]

def get_group(tags):
    if 'Champion' in tags: return 'Champion'
    if 'Story' in tags or 'Chronicle' in tags: return 'Story'
    if 'Pre-Starfall' in tags or 'Civilization' in tags: return 'Pre-Starfall'
    if 'Post-Starfall' in tags or 'Faction' in tags: return 'Post-Starfall Faction'
    if 'Location' in tags or 'Ruins' in tags: return 'Location'
    if 'History' in tags or 'Anthology' in tags: return 'Meta'
    if 'Mystery' in tags: return 'Mystery'
    if 'Figure' in tags or 'Scholar' in tags: return 'Figure'
    if 'Concept' in tags or 'Magic' in tags or 'Item' in tags: return 'Concept/Item'
    return 'Other'

existing = set()
for f in os.listdir(CONTENT_DIR):
    if f.endswith('.md'):
        existing.add(f[:-3])

tags_map = {}
for f in os.listdir(CONTENT_DIR):
    if not f.endswith('.md'): continue
    text = open(os.path.join(CONTENT_DIR, f), encoding='utf-8').read()
    tags_map[f[:-3]] = get_tags(text)

edges = set()
for f in os.listdir(CONTENT_DIR):
    if not f.endswith('.md'): continue
    source = f[:-3]
    text = open(os.path.join(CONTENT_DIR, f), encoding='utf-8').read()
    for link in re.findall(r'\[\[([^\]|#]+)(?:\|[^\]]*)?\]\]', text):
        link = link.strip()
        if link in existing and link != source:
            edges.add(tuple(sorted([source, link])))

link_count = {}
for a, b in edges:
    link_count[a] = link_count.get(a, 0) + 1
    link_count[b] = link_count.get(b, 0) + 1

SKIP = {'champion_page'}
nodes = []
for name in sorted(existing):
    if name in SKIP: continue
    group = get_group(tags_map.get(name, []))
    nodes.append({
        "id": name,
        "color": COLORS.get(group, "#94a3b8"),
        "group": group,
        "links": link_count.get(name, 0)
    })

edges_list = [{"source": a, "target": b} for a, b in edges]

nodes_json = json.dumps(nodes)
edges_json = json.dumps(edges_list)

html = f"""---
title: Concept Map
---
<style>
#gw{{width:100%;height:640px;position:relative;}}
#gc{{width:100%;height:600px;border:0.5px solid #ccc;border-radius:8px;cursor:grab;display:block;}}
#tip{{position:absolute;display:none;background:#fff;border:0.5px solid #ccc;border-radius:6px;padding:5px 9px;font-size:12px;pointer-events:none;max-width:200px;z-index:10;}}
.ctrl{{display:flex;gap:8px;flex-wrap:wrap;padding:8px 0;align-items:center;}}
.leg{{display:flex;gap:10px;flex-wrap:wrap;padding:2px 0 8px;font-size:12px;}}
.dot{{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:3px;vertical-align:middle;}}
</style>
<div class="ctrl">
  <select id="fg"><option value="all">All categories</option><option value="Champion">Champions</option><option value="Story">Stories</option><option value="Pre-Starfall">Pre-Starfall</option><option value="Post-Starfall Faction">Post-Starfall factions</option><option value="Location">Locations</option><option value="Meta">Meta</option><option value="Mystery">Mystery</option><option value="Figure">Figures</option><option value="Concept/Item">Concepts &amp; items</option><option value="Other">Other</option></select>
  <input id="sq" type="text" placeholder="Search..." style="font-size:13px;width:140px;padding:4px 8px;border:1px solid #ccc;border-radius:4px;" />
  <button id="btn-rst" style="font-size:13px;padding:4px 10px;border:1px solid #ccc;border-radius:4px;background:#fff;cursor:pointer;">Reset</button>
  <span style="font-size:12px;color:#888;">Drag · scroll to zoom · click to highlight</span>
</div>
<div class="leg">
  <span><span class="dot" style="background:#c084fc"></span>Champion</span>
  <span><span class="dot" style="background:#f9a8d4"></span>Story</span>
  <span><span class="dot" style="background:#fcd34d"></span>Pre-Starfall</span>
  <span><span class="dot" style="background:#6ee7b7"></span>Post-Starfall</span>
  <span><span class="dot" style="background:#7dd3fc"></span>Location</span>
  <span><span class="dot" style="background:#fb923c"></span>Meta</span>
  <span><span class="dot" style="background:#f87171"></span>Mystery</span>
  <span><span class="dot" style="background:#a78bfa"></span>Figure</span>
  <span><span class="dot" style="background:#34d399"></span>Concept/Item</span>
  <span><span class="dot" style="background:#94a3b8"></span>Other</span>
</div>
<div id="gw"><canvas id="gc"></canvas><div id="tip"></div></div>
<script>
const NODES={nodes_json};
const EDGES={edges_json};
const canvas=document.getElementById('gc');
const DPR=window.devicePixelRatio||1;
const W=canvas.parentElement.offsetWidth||680,H=600;
canvas.width=W*DPR;canvas.height=H*DPR;
canvas.style.width=W+'px';canvas.style.height=H+'px';
const ctx=canvas.getContext('2d');ctx.scale(DPR,DPR);
const nm={{}};
const nodes=NODES.map(n=>{{const o={{...n,x:W/2+(Math.random()-.5)*400,y:H/2+(Math.random()-.5)*400,vx:0,vy:0}};nm[n.id]=o;return o;}});
let ag='all',st='',hl=null,tx=0,ty=0,tk=1,drag=null,doff={{x:0,y:0}},pan=false,ps={{x:0,y:0}},po={{x:0,y:0}},settled=false,iter=0,cs=null;
function nr(n){{return Math.max(4,Math.min(13,3+n.links*0.55));}}
function vis(){{return nodes.filter(n=>{{if(ag!=='all'&&n.group!==ag)return false;if(st&&!n.id.toLowerCase().includes(st.toLowerCase()))return false;return true;}});}}
function tick(){{if(settled)return;const vn=vis();const vs=new Set(vn.map(n=>n.id));const al=Math.max(0.01,0.6-iter*0.004);vn.forEach(a=>{{a.vx+=(W/2-a.x)*0.015*al;a.vy+=(H/2-a.y)*0.015*al;}});for(let i=0;i<vn.length;i++){{for(let j=i+1;j<vn.length;j++){{const a=vn[i],b=vn[j];let dx=a.x-b.x,dy=a.y-b.y,d2=dx*dx+dy*dy,d=Math.sqrt(d2)||0.1,rep=Math.min(800,120*120/d2);a.vx+=dx/d*rep*al;a.vy+=dy/d*rep*al;b.vx-=dx/d*rep*al;b.vy-=dy/d*rep*al;}}}}EDGES.forEach(e=>{{const a=nm[e.source],b=nm[e.target];if(!a||!b||!vs.has(e.source)||!vs.has(e.target))return;let dx=b.x-a.x,dy=b.y-a.y,d=Math.sqrt(dx*dx+dy*dy)||0.1,f=(d-70)*0.06*al;a.vx+=dx/d*f;a.vy+=dy/d*f;b.vx-=dx/d*f;b.vy-=dy/d*f;}});let mv=0;vn.forEach(n=>{{n.vx*=0.75;n.vy*=0.75;n.x+=n.vx;n.y+=n.vy;n.x=Math.max(20,Math.min(W-20,n.x));n.y=Math.max(20,Math.min(H-20,n.y));mv=Math.max(mv,Math.abs(n.vx)+Math.abs(n.vy));}});iter++;if(mv<0.3&&iter>60)settled=true;}}
function draw(){{ctx.clearRect(0,0,W,H);ctx.save();ctx.translate(tx,ty);ctx.scale(tk,tk);const vn=vis();const vs=new Set(vn.map(n=>n.id));const nb=new Set();if(hl){{EDGES.forEach(e=>{{if(e.source===hl)nb.add(e.target);if(e.target===hl)nb.add(e.source);}})}}ctx.lineWidth=0.7;EDGES.forEach(e=>{{const a=nm[e.source],b=nm[e.target];if(!a||!b||!vs.has(e.source)||!vs.has(e.target))return;ctx.globalAlpha=(!hl||(hl===e.source||hl===e.target))?0.2:0.03;ctx.strokeStyle='#94a3b8';ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke();}});vn.forEach(n=>{{const ih=hl===n.id,inn=nb.has(n.id);ctx.globalAlpha=!hl||ih||inn?1:0.12;ctx.beginPath();ctx.arc(n.x,n.y,nr(n),0,Math.PI*2);ctx.fillStyle=n.color;ctx.fill();if(ih){{ctx.strokeStyle='rgba(255,255,255,0.9)';ctx.lineWidth=2;ctx.stroke();ctx.lineWidth=0.7;}}}});ctx.globalAlpha=1;ctx.font=`${{Math.max(9,10/tk)}}px sans-serif`;ctx.fillStyle='rgba(30,30,30,0.85)';vn.forEach(n=>{{const ih=hl===n.id,inn=nb.has(n.id);if(!n.links>9&&!ih&&!inn)return;if(n.links<=9&&!ih&&!inn)return;ctx.globalAlpha=!hl||ih||inn?1:0.12;ctx.fillText(n.id,n.x+nr(n)+2,n.y+4);}});ctx.restore();}}
function loop(){{tick();draw();requestAnimationFrame(loop);}}loop();
function cxy(e){{const r=canvas.getBoundingClientRect();return{{x:e.clientX-r.left,y:e.clientY-r.top}};}}
function hit(cx,cy){{const wx=(cx-tx)/tk,wy=(cy-ty)/tk;const vn=vis();for(let i=vn.length-1;i>=0;i--){{const n=vn[i];if(Math.hypot(n.x-wx,n.y-wy)<nr(n)+5)return n;}}return null;}}
canvas.addEventListener('mousedown',e=>{{const{{x,y}}=cxy(e);cs={{x,y}};const n=hit(x,y);if(n){{drag=n;doff={{x:(x-tx)/tk-n.x,y:(y-ty)/tk-n.y}};canvas.style.cursor='grabbing';}}else{{pan=true;ps={{x,y}};po={{x:tx,y:ty}};canvas.style.cursor='grabbing';}}}});
canvas.addEventListener('mousemove',e=>{{const{{x,y}}=cxy(e);if(drag){{drag.x=(x-tx)/tk-doff.x;drag.y=(y-ty)/tk-doff.y;drag.vx=0;drag.vy=0;settled=false;}}else if(pan){{tx=po.x+(x-ps.x);ty=po.y+(y-ps.y);}}else{{const n=hit(x,y);const tip=document.getElementById('tip');if(n){{tip.style.display='block';tip.style.left=(x+12)+'px';tip.style.top=(y-10)+'px';tip.innerHTML=`<strong>${{n.id}}</strong><br><span style="color:#888">${{n.group}} · ${{n.links}} links</span>`;canvas.style.cursor='pointer';}}else{{tip.style.display='none';canvas.style.cursor='grab';}}}}}});
canvas.addEventListener('mouseup',e=>{{const{{x,y}}=cxy(e);if(drag&&cs&&Math.hypot(x-cs.x,y-cs.y)<5){{hl=hl===drag.id?null:drag.id;}}drag=null;pan=false;canvas.style.cursor='grab';document.getElementById('tip').style.display='none';}});
canvas.addEventListener('wheel',e=>{{e.preventDefault();const{{x,y}}=cxy(e);const f=e.deltaY<0?1.12:0.89;tx=x-(x-tx)*f;ty=y-(y-ty)*f;tk=Math.max(0.15,Math.min(6,tk*f));}},({{passive:false}}));
document.getElementById('btn-rst').onclick=()=>{{tx=0;ty=0;tk=1;hl=null;nodes.forEach(n=>{{n.x=W/2+(Math.random()-.5)*400;n.y=H/2+(Math.random()-.5)*400;n.vx=0;n.vy=0;}});settled=false;iter=0;}};
document.getElementById('fg').addEventListener('change',e=>{{ag=e.target.value;hl=null;settled=false;iter=0;}});
document.getElementById('sq').addEventListener('input',e=>{{st=e.target.value;hl=null;settled=false;iter=0;}});
</script>
"""

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Graph built: {len(nodes)} nodes, {len(edges_list)} edges -> {OUTPUT_FILE}")