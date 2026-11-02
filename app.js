/* Συγχώνευση των έργων ΕΣΠΑ (data-espa.js), αν υπάρχουν */
if(typeof P_ESPA!=="undefined")P.push(...P_ESPA);
const T={first:"Πρώτη επίσημη πράξη",contract:"Σύμβαση / ανάθεση",start:"Έναρξη εργασιών",open:"Λειτουργία / εγκαίνια",other:"Άλλο ορόσημο"};
const MON=["Ιαν","Φεβ","Μαρ","Απρ","Μαΐ","Ιουν","Ιουλ","Αυγ","Σεπ","Οκτ","Νοε","Δεκ"];
function range(d){const p=d.split("-").map(Number);
  if(p.length===3){const x=new Date(Date.UTC(p[0],p[1]-1,p[2]));return[x,x]}
  if(p.length===2)return[new Date(Date.UTC(p[0],p[1]-1,1)),new Date(Date.UTC(p[0],p[1],0))];
  return[new Date(Date.UTC(p[0],0,1)),new Date(Date.UTC(p[0],11,31))]}
function fmt(d){const p=d.split("-").map(Number);
  if(p.length===3)return p[2]+" "+MON[p[1]-1]+" "+p[0];if(p.length===2)return MON[p[1]-1]+" "+p[0];return String(p[0])}
const gd=s=>new Date(s+"T00:00:00Z");
const overlap=(d,list,f,t)=>{const[a,b]=range(d);return list.filter(x=>gd(x[f])<=b&&gd(x[t])>a)};
const govsFor=d=>overlap(d,GOV,"from","to");
function minsFor(p,d){const m=MIN[p.ministry];if(!m||!m.from)return{state:"none",m};
  const[a,b]=range(d);if(b<gd(m.from))return{state:"before",m};
  const L=m.list.map(r=>({name:r[0],from:r[1],to:r[2],title:r[3]||m.name})).filter(x=>gd(x.from)<=b&&gd(x.to)>a);
  return L.length?{state:"ok",m,L}:{state:"gap",m}}
function yr(dt){return dt.getUTCFullYear()+(dt-Date.UTC(dt.getUTCFullYear(),0,1))/31557600000}
function mid(d){const[a,b]=range(d);return new Date((+a + +b)/2)}
const esc=s=>String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

/* Timeline */
const Y0=1967,Y1=2027,VW=1000,PL=8,PR=8;
const X=y=>PL+(y-Y0)/(Y1-Y0)*(VW-PL-PR);
function marker(t,x,y){
  if(t==="first")return`<circle cx="${x}" cy="${y}" r="6" fill="var(--paper)" stroke="var(--mark)" stroke-width="2.2"/>`;
  if(t==="contract")return`<path d="M${x} ${y-7} L${x+7} ${y} L${x} ${y+7} L${x-7} ${y} Z" fill="var(--mark)"/>`;
  if(t==="start")return`<rect x="${x-5.5}" y="${y-5.5}" width="11" height="11" fill="var(--mark)"/>`;
  if(t==="open")return`<circle cx="${x}" cy="${y}" r="7" fill="var(--accent)" stroke="var(--paper)" stroke-width="1.5"/>`;
  return`<line x1="${x}" y1="${y-8}" x2="${x}" y2="${y+8}" stroke="var(--muted)" stroke-width="2.2"/>`}
function axis(p,hiGov){
  let s=`<svg viewBox="0 0 ${VW} 74" role="img" aria-label="Χρονολόγιο: ${esc(p.name)}">`;
  GOV.forEach((g,i)=>{const a=Math.max(yr(gd(g.from)),Y0),b=Math.min(yr(gd(g.to)),Y1);if(b<=a)return;
    const fill=hiGov===g.id?"var(--band-hi)":(i%2?"var(--band-a)":"var(--band-b)");
    s+=`<rect x="${X(a)}" y="6" width="${X(b)-X(a)}" height="44" fill="${fill}"><title>${esc(g.pm)} · ${esc(g.kind)} · ${fmt(g.from)} – ${g.to>"2090"?"σήμερα":fmt(g.to)}</title></rect>`});
  for(let y=1970;y<=2020;y+=10)s+=`<line x1="${X(y)}" y1="6" x2="${X(y)}" y2="54" stroke="var(--line)"/><text x="${X(y)}" y="68" text-anchor="middle">${y}</text>`;
  s+=`<text x="${X(Y0)}" y="68">1967</text><text x="${X(Y1)}" y="68" text-anchor="end">σήμερα</text>`;
  const xs=p.ms.map(m=>X(yr(mid(m.d))));
  if(xs.length>1)s+=`<line x1="${Math.min(...xs)}" y1="28" x2="${Math.max(...xs)}" y2="28" stroke="var(--mark)" stroke-width="1.5" stroke-dasharray="3 3"/>`;
  p.ms.forEach((m,i)=>{s+=`<g>${marker(m.t,xs[i],28)}<title>${esc(T[m.t])}: ${esc(m.l)} · ${fmt(m.d)}</title></g>`});
  return s+"</svg>"}

/* Table cells */
function govCell(m){const g=govsFor(m.d);
  if(g.length===1)return`${esc(g[0].pm)} <span class="na">(${esc(g[0].kind)})</span>`;
  return`<span class="flag">Στο διάστημα «${fmt(m.d)}» υπήρξαν ${g.length} κυβερνήσεις:</span> `+g.map(x=>esc(x.pm)).join(" · ")+`<br><span class="na">Χρειάζεται ακριβέστερη ημερομηνία.</span>`}
function minCell(p,m){const r=minsFor(p,m.d);const est=p.mv?"":`<br><span class="na">Υπουργείο: εκτίμηση βάσει κατηγορίας</span>`;
  if(r.state==="before")return`<span class="na">Δεν έχει καταγραφεί: το χρονολόγιο υπουργών ${esc(r.m.name)} ξεκινά το ${r.m.from.slice(0,4)}</span>`;
  if(r.state==="gap")return`<span class="na">Δεν έχει καταγραφεί υπουργός γι' αυτό το διάστημα</span>`;
  if(r.state==="none")return r.m?`<span class="na">Δεν έχει καταγραφεί ακόμη χρονολόγιο υπουργών ${esc(r.m.name)}</span>`:`<span class="na">Δεν αντιστοιχίζεται: το έργο υλοποιεί ο δικαιούχος φορέας</span>`;
  if(r.L.length===1)return`${esc(r.L[0].name)}<br><span class="na">${esc(r.L[0].title)}</span>${est}`;
  return`<span class="flag">Στο διάστημα «${fmt(m.d)}» υπήρξαν ${r.L.length} υπουργοί:</span> `+r.L.map(x=>esc(x.name)).join(" · ")+est}
function docCell(m){if(!m.doc)return'<span class="na">Αναζητείται</span>';
  return`<span class="okdoc">${esc(m.doc)}</span>`+(m.docu?`<br><a href="${m.docu}" target="_blank" rel="noopener">Κείμενο νόμου</a>`:"")}
const val=v=>v?esc(v):'<span class="na">Δεν έχει καταγραφεί</span>';
function phaseMatch(p,m,g,mn){return(!g||govsFor(m.d).some(x=>x.id===g))&&(!mn||(()=>{const r=minsFor(p,m.d);return r.state==="ok"&&r.L.some(x=>x.name===mn)})())}
function card(p,g,mn){
  const y=p.ms.map(m=>m.d.slice(0,4));const act=g||mn;
  const rows=p.ms.map(m=>`<tr${act&&phaseMatch(p,m,g,mn)?' class="hi"':''}><td>${esc(T[m.t])}</td><td>${esc(m.l)}${m.flag?`<br><span class="flag">${esc(m.flag)}</span>`:""}</td><td class="date">${fmt(m.d)}</td><td>${govCell(m)}</td><td>${minCell(p,m)}</td><td>${docCell(m)}</td><td><a href="${p.src[m.s][1]}" target="_blank" rel="noopener">[${m.s+1}]</a></td></tr>`).join("");
  const build=/κατασκευή|εξέλιξη/i.test(p.status);
  return`<article class="card" id="p-${p.id}">
  <div class="card-head"><h3>${esc(p.name)}</h3><div class="meta">${p.origin==="espa"?'<span class="chip src">ΕΣΠΑ · MIS '+p.mis+'</span>':""}<span class="chip cat">${esc(p.cat)}</span><span class="chip">${esc(p.region)}</span><span class="chip${build?" build":""}">${esc(p.status)}</span><span class="chip">${y[0]}${y.length>1?"–"+y[y.length-1]:""}</span></div></div>
  <div class="axis">${axis(p,g)}</div>
  <dl class="facts"><div><dt>Κόστος</dt><dd>${val(p.cost)}</dd></div><div><dt>Χρηματοδότηση</dt><dd>${val(p.funding)}</dd></div><div><dt>Ανάδοχος / φορέας</dt><dd>${val(p.contractor)}</dd></div>${p.ministry?`<div><dt>Εποπτεύον υπουργείο</dt><dd>${esc(MIN[p.ministry].name)}${p.mv?"":' <span class="na">(εκτίμηση)</span>'}</dd></div>`:""}</dl>
  ${p.note?`<p class="note">${esc(p.note)}</p>`:""}
  <details${act?" open":""}><summary>Φάσεις, κυβερνήσεις, υπουργοί και πηγές</summary>
   <div class="tbl"><table><thead><tr><th>Φάση</th><th>Πράξη</th><th>Ημερομηνία</th><th>Κυβέρνηση (πρωθυπουργός)</th><th>Αρμόδιος υπουργός</th><th>Πρωτογενές έγγραφο</th><th>Πηγή</th></tr></thead><tbody>${rows}</tbody></table></div>
   <div class="src">${p.src.map((s,i)=>`<span>[${i+1}] <a href="${s[1]}" target="_blank" rel="noopener">${esc(s[0])}</a></span>`).join("")}</div>
  </details></article>`}

/* Map: Natural Earth 1:50m outline of Greece, equirectangular projection centred on 38.5°N */
const KX=60*Math.cos(38.5*Math.PI/180),proj=([la,lo])=>[(lo-19.3)*KX,(41.85-la)*60];
let sel=null;
function drawMap(visible){
  const vis=new Set(visible.map(p=>p.id));
  let s=`<svg viewBox="0 0 440 425" role="img" aria-label="Χάρτης της Ελλάδας με τα έργα"><path class="land" d="${GR}"/>`;
  P.filter(p=>p.geo&&Array.isArray(p.geo[0])).forEach(p=>{const pts=p.geo.map(proj).map(q=>q.map(v=>v.toFixed(1)).join(",")).join(" ");
    s+=`<g class="pin${vis.has(p.id)?"":" dim"}" tabindex="0" role="button" data-ids="${p.id}" aria-label="${esc(p.name)}"><polyline points="${pts}"/><title>${esc(p.name)}</title></g>`});
  const pts=P.filter(p=>p.geo&&!Array.isArray(p.geo[0])).map(p=>({p,xy:proj(p.geo)}));const groups=[];
  pts.forEach(o=>{const g=groups.find(g=>Math.hypot(g.xy[0]-o.xy[0],g.xy[1]-o.xy[1])<10);if(g){g.items.push(o.p)}else groups.push({xy:o.xy,items:[o.p]})});
  groups.forEach(g=>{const n=g.items.length,on=g.items.some(p=>vis.has(p.id)),r=n>1?9:6;
    s+=`<g class="pin${on?"":" dim"}" tabindex="0" role="button" data-ids="${g.items.map(p=>p.id).join(",")}" aria-label="${esc(g.items.map(p=>p.name).join(", "))}"><circle cx="${g.xy[0].toFixed(1)}" cy="${g.xy[1].toFixed(1)}" r="${r}"/>${n>1?`<text x="${g.xy[0].toFixed(1)}" y="${(g.xy[1]+3.5).toFixed(1)}" text-anchor="middle">${n}</text>`:""}<title>${esc(g.items.map(p=>p.name).join("\n"))}</title></g>`});
  $("map").innerHTML=s+"</svg>";
  $("map").querySelectorAll(".pin").forEach(el=>{const go=()=>{sel=el.dataset.ids.split(",");render()};
    el.addEventListener("click",go);el.addEventListener("keydown",e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();go()}})})}

const $=id=>document.getElementById(id);
[...new Set(P.map(p=>p.cat))].sort().forEach(c=>$("cat").insertAdjacentHTML("beforeend",`<option>${esc(c)}</option>`));
GOV.forEach(g=>$("gov").insertAdjacentHTML("beforeend",`<option value="${g.id}">${esc(g.pm)} (${g.from.slice(0,4)}–${g.to>"2090"?"σήμερα":g.to.slice(0,4)})</option>`));
const minNames=new Set();P.forEach(p=>p.ms.forEach(m=>{const r=minsFor(p,m.d);if(r.state==="ok")r.L.forEach(x=>minNames.add(x.name))}));
[...minNames].sort((a,b)=>a.localeCompare(b,"el")).forEach(n=>$("min").insertAdjacentHTML("beforeend",`<option>${esc(n)}</option>`));
P.sort((a,b)=>range(a.ms[0].d)[0]-range(b.ms[0].d)[0]);
$("coverage").innerHTML=Object.values(MIN).filter(m=>m.from).map(m=>`<li>${esc(m.name)}: από ${fmt(m.from)} έως σήμερα · <a href="${m.src}" target="_blank" rel="noopener">πηγή</a></li>`).join("");
(()=>{const all=P.flatMap(p=>p.ms.map(m=>({p,m})));const docs=all.filter(x=>x.m.doc).length;const mins=all.filter(x=>minsFor(x.p,x.m.d).state==="ok").length;
  $("stats").innerHTML=`<span><b>${P.length}</b> έργα</span><span><b>${all.length}</b> φάσεις</span><span><b>${mins}</b> φάσεις με αρμόδιο υπουργό</span><span><b>${docs}</b> φάσεις με πρωτογενές έγγραφο</span>`})();
const norm=s=>s.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"").replace(/ς/g,"σ");
/* Αναζήτηση ανεξάρτητη από την κατάληξη: «Κρήτη», «Κρήτης», «Χανιά», «Χανίων» */
const stems=q=>q.split(/\s+/).filter(Boolean).map(t=>t.length>=5?t.slice(0,-2):t.length>=4?t.slice(0,-1):t);
const REGIONS=["Ανατολικής Μακεδονίας και Θράκης","Κεντρικής Μακεδονίας","Δυτικής Μακεδονίας","Ηπείρου","Θεσσαλίας","Ιονίων Νήσων","Δυτικής Ελλάδας","Στερεάς Ελλάδας","Αττικής","Πελοποννήσου","Βορείου Αιγαίου","Νοτίου Αιγαίου","Κρήτης"];
function fillRegions(){const r=$("reg").value;$("reg").innerHTML='<option value="">Όλη η χώρα</option>'+REGIONS.map(x=>{const n=P.filter(p=>(p.perif||[]).includes(x)).length;return`<option value="${esc(x)}"${x===r?" selected":""}>${esc(x)} (${n})</option>`}).join("");}
function fillPE(){const r=$("reg").value,cur=$("pe").value;const L=[...new Set(P.filter(p=>!r||(p.perif||[]).includes(r)).flatMap(p=>p.pe||[]))].sort((a,b)=>a.localeCompare(b,"el"));$("pe").innerHTML='<option value="">Όλες</option>'+L.map(x=>`<option value="${esc(x)}"${x===cur?" selected":""}>${esc(x)}</option>`).join("");$("pe").disabled=!L.length;}
fillRegions();fillPE();
const PAGE=40;let limit=PAGE;
function render(keep){if(!keep)limit=PAGE;
  const q=stems(norm($("q").value.trim())),c=$("cat").value,o=$("origin").value,rg=$("reg").value,pe=$("pe").value,g=$("gov").value,mn=$("min").value;
  const base=P.filter(p=>(!c||p.cat===c)&&(!o||(o==="espa")===(p.origin==="espa"))&&(!q.length||(t=>q.every(s=>t.includes(s)))(norm(p.name+" "+p.region+" "+p.cat+" "+(p.contractor||"")+" "+(p.perif||[]).join(" ")+" "+(p.pe||[]).join(" "))))&&(!rg||(p.perif||[]).includes(rg))&&(!pe||(p.pe||[]).includes(pe))&&((!g&&!mn)||p.ms.some(m=>phaseMatch(p,m,g,mn))));
  drawMap(base);
  const out=sel?base.filter(p=>sel.includes(p.id)):base;
  $("selbar").hidden=!sel;if(sel)$("seltext").textContent="Επιλογή από τον χάρτη: "+sel.length+(sel.length===1?" έργο":" έργα");
  $("count").textContent=out.length+(out.length===1?" έργο":" έργα")+((g||mn)?" με τουλάχιστον μία φάση που ταιριάζει. Οι σχετικές φάσεις επισημαίνονται.":", σε χρονολογική σειρά πρώτης φάσης.");
  const shown=out.slice(0,limit);$("list").innerHTML=out.length?shown.map(p=>card(p,g,mn)).join("")+(out.length>limit?`<button class="more" id="more" type="button">Εμφάνιση ${Math.min(PAGE,out.length-limit)} ακόμη (εμφανίζονται ${limit} από ${out.length})</button>`:""):'<div class="empty">Κανένα έργο δεν ταιριάζει στα φίλτρα. Δοκίμασε άλλη λέξη ή πάτησε «Εμφάνιση όλων».</div>'}
["q","cat","origin","gov","min","pe"].forEach(id=>$(id).addEventListener("input",()=>render()));
$("reg").addEventListener("input",()=>{$("pe").value="";fillPE();render()});
$("clearsel").addEventListener("click",()=>{sel=null;render()});
render();

document.addEventListener("click",e=>{if(e.target&&e.target.id==="more"){limit+=PAGE;render(true)}});
