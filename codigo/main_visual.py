"""
Visualización interactiva 3D de la construcción de la Triangulación de Delaunay.

Librerías (las de la captura): webbrowser, os, py3Dmol.
Genera un archivo HTML (3Dmol.js) y lo abre en el navegador. En la página puedes
reproducir la construcción PASO A PASO: cada inserción de punto, la división del
triángulo (1->3) y cada edge flip, y rotar/hacer zoom con el mouse.

Uso:  python main_visual.py [--n 60] [--seed 7] [--no-open]
"""
import argparse
import json
import os
import webbrowser

import py3Dmol

from delaunay import IncrementalDelaunay
from terrain import generate_synthetic_terrain

ANCHO_TERRENO = 20.0
ALTO_TERRENO = 20.0


def _snapshot(solver, nuevos):
    """Triángulos activos (sin súper-triángulo) como filas [x0,y0,z0,...,z2,flag]."""
    ids_nuevos = {id(t) for t in nuevos}
    filas = []
    for tri in solver.get_active_triangles(remove_super=True):
        fila = []
        for v in tri.vertices:
            fila += [round(float(v.x), 4), round(float(v.y), 4), round(float(v.z), 4)]
        fila.append(1 if id(tri) in ids_nuevos else 0)
        filas.append(fila)
    return filas


def grabar_construccion(puntos, seed):
    """Ejecuta RIC y guarda un cuadro por cada evento (inserción / flip)."""
    cuadros, insertados = [], []

    def on_event(kind, p, nuevos):
        if kind == 'split':
            insertados.append([round(float(p.x), 4), round(float(p.y), 4), round(float(p.z), 4)])
            nflip[0] = 0
            texto = f"Punto {len(insertados)}/{len(puntos)}: se ubica en el DAG y divide su triángulo en 3"
        else:
            nflip[0] += 1
            texto = (f"Punto {len(insertados)}/{len(puntos)}: arista ilegal → edge flip #{nflip[0]} "
                     f"(propiedad del círculo vacío)")
        cuadros.append({
            "texto": texto,
            "tris": _snapshot(solver, nuevos),
            "pts": [list(q) for q in insertados],
            "flips": solver.flips,
        })

    nflip = [0]
    solver = IncrementalDelaunay(puntos, use_dag=True, on_event=on_event)
    finales = solver.build(shuffle=True, seed=seed)

    # Cuadro final: súper-triángulo ya removido
    cuadros.append({
        "texto": f"Modelo final: {len(finales)} triángulos, súper-triángulo removido "
                 f"({solver.flips} flips en total)",
        "tris": _snapshot(solver, []),
        "pts": [list(q) for q in insertados],
        "flips": solver.flips,
    })
    return cuadros, solver


PANEL_HTML = """
<style>
 body{margin:0;font-family:system-ui,Segoe UI,sans-serif;background:#0f1722;color:#e8eef6}
 #panel{padding:10px 16px;display:flex;flex-wrap:wrap;gap:10px 18px;align-items:center;background:#16212f;border-bottom:1px solid #26364a}
 #panel button{background:#1f6f8b;color:#fff;border:0;border-radius:6px;padding:7px 13px;font-size:15px;cursor:pointer}
 #panel button:hover{background:#2a8cae}
 #panel label{font-size:13px;color:#aebfd1;display:flex;align-items:center;gap:6px}
 #texto{padding:8px 16px;font-size:15px;min-height:22px;background:#122030}
 #leyenda{padding:4px 16px 8px;font-size:12px;color:#8fa3b8;background:#122030}
 .sw{display:inline-block;width:11px;height:11px;border-radius:2px;margin:0 4px 0 12px;vertical-align:-1px}
 input[type=range]{accent-color:#2a8cae}
</style>
<div id="panel">
  <button id="bIni" title="Inicio">⏮</button>
  <button id="bAtr" title="Paso atrás">◀</button>
  <button id="bPlay" title="Reproducir / pausar">⏸ Pausa</button>
  <button id="bSig" title="Paso adelante">▶</button>
  <button id="bFin" title="Modelo final">⏭</button>
  <label>Paso <input id="sPaso" type="range" min="0" max="0" value="0" style="width:260px"> <span id="nPaso"></span></label>
  <label>Velocidad <input id="sVel" type="range" min="1" max="30" value="8"></label>
  <label>Altura Z ×<input id="sZ" type="range" min="0" max="4" step="0.1" value="1.5"> <span id="nZ"></span></label>
  <label><input id="cAr" type="checkbox" checked> Aristas</label>
  <label><input id="cPt" type="checkbox" checked> Puntos</label>
</div>
<div id="texto"></div>
<div id="leyenda">Altura Z = 0 equivale a la vista 2D de la triangulación. Arrastra para rotar · rueda para zoom.
 <span class="sw" style="background:#ff7a2f"></span>triángulos nuevos del paso
 <span class="sw" style="background:#ff2d2d"></span>punto recién insertado
 <span class="sw" style="background:#222"></span>puntos previos
 · Elevación <span style="display:inline-block;width:110px;height:10px;vertical-align:-1px;background:linear-gradient(90deg,#5a6eeb,#32aae1,#46d296,#c8e650,#ffc846)"></span> baja → alta</div>
"""

PLAYER_JS = """
<script>
(function(){
  var F = __FRAMES__, UID = "__UID__", ZMIN = __ZMIN__, ZMAX = __ZMAX__;
  var k = 0, playing = true, timer = null, firstZoom = true;
  var $ = function(id){return document.getElementById(id);};
  var V = null;

  // Colormap por elevación (azul → verde → amarillo), claro para que la luz no lo apague
  var STOPS = [[90,110,235],[50,170,225],[70,210,150],[200,230,80],[255,200,70]];
  function hex(t){
    t = Math.max(0,Math.min(1,t))*(STOPS.length-1);
    var i = Math.min(Math.floor(t),STOPS.length-2), f = t-i, a=STOPS[i], b=STOPS[i+1];
    var r=Math.round(a[0]+(b[0]-a[0])*f), g=Math.round(a[1]+(b[1]-a[1])*f), bl=Math.round(a[2]+(b[2]-a[2])*f);
    return (r<<16)|(g<<8)|bl;
  }
  function col(z){ return hex((z-ZMIN)/((ZMAX-ZMIN)||1)); }

  function draw(){
    if(!V) return;
    var fr = F[k], zs = parseFloat($('sZ').value);
    $('nZ').textContent = zs.toFixed(1);
    V.removeAllShapes();
    var NB = 12, B = [], i, j, allv=[], alln=[], allf=[], c=0;
    function newG(){ return {v:[],n:[],f:[],c:0,vb:[],nb:[],fb:[]}; }
    for(i=0;i<NB;i++) B.push(newG());
    var hl = newG();
    for(i=0;i<fr.tris.length;i++){
      var t = fr.tris[i], zm = (t[2]+t[5]+t[8])/3;
      // 3Dmol ignora colorArr: se agrupan los triángulos por rango de elevación
      var g = (t[9]===1) ? hl : B[Math.min(NB-1, Math.max(0, Math.floor((zm-ZMIN)/((ZMAX-ZMIN)||1)*NB)))];
      // normal real del triángulo (CCW en XY => apunta hacia arriba)
      var ax=t[3]-t[0], ay=t[4]-t[1], az=(t[5]-t[2])*zs, bx=t[6]-t[0], by=t[7]-t[1], bz=(t[8]-t[2])*zs;
      var nx=ay*bz-az*by, ny=az*bx-ax*bz, nz=ax*by-ay*bx, nl=Math.sqrt(nx*nx+ny*ny+nz*nz)||1;
      nx/=nl; ny/=nl; nz/=nl;
      for(j=0;j<3;j++){
        var q = {x:t[3*j], y:t[3*j+1], z:t[3*j+2]*zs};
        g.v.push(q); g.n.push({x:nx,y:ny,z:nz});
        // cara inferior: normal invertida, desplazada 0.03 contra la normal (se ve iluminada al mirar por debajo)
        g.vb.push({x:q.x-0.03*nx, y:q.y-0.03*ny, z:q.z-0.03*nz}); g.nb.push({x:-nx,y:-ny,z:-nz});
        allv.push(q); alln.push({x:nx,y:ny,z:nz});
      }
      g.f.push(g.c,g.c+1,g.c+2); g.fb.push(g.c,g.c+2,g.c+1); g.c+=3;
      allf.push(c,c+1,c+2); c+=3;
    }
    function shape(g, color){
      if(!g.v.length) return;
      V.addCustom({vertexArr:g.v,  normalArr:g.n,  faceArr:g.f,  color:color});   // cara superior
      V.addCustom({vertexArr:g.vb, normalArr:g.nb, faceArr:g.fb, color:color});   // cara inferior (iluminada al rotar)
    }
    for(i=0;i<NB;i++) shape(B[i], '#'+('000000'+col(ZMIN+(i+0.5)/NB*(ZMAX-ZMIN)).toString(16)).slice(-6));
    shape(hl, '#ff7a2f');
    if(allv.length && $('cAr').checked){
      V.addCustom({vertexArr:allv, normalArr:alln, faceArr:allf, color:'#0b1118', wireframe:true});
    }
    // aristas gruesas de los triángulos nuevos del paso (siempre visibles aunque la pendiente se vea de canto)
    for(i=0;i<fr.tris.length;i++){
      var tn = fr.tris[i]; if(tn[9]!==1) continue;
      for(j=0;j<3;j++){
        var k1=(j+1)%3;
        V.addCylinder({start:{x:tn[3*j],y:tn[3*j+1],z:tn[3*j+2]*zs}, end:{x:tn[3*k1],y:tn[3*k1+1],z:tn[3*k1+2]*zs},
                       radius:0.07, color:'#ff7a2f', fromCap:1, toCap:1});
      }
    }
    if($('cPt').checked){
      for(i=0;i<fr.pts.length;i++){
        var p = fr.pts[i], last = (i===fr.pts.length-1 && k<F.length-1);
        V.addSphere({center:{x:p[0],y:p[1],z:p[2]*zs}, radius:last?0.28:0.14, color:last?'#ff2d2d':'#222222'});
      }
    }
    if(firstZoom){ V.zoomTo(); V.rotate(-55,'x'); V.zoom(1.15); firstZoom=false; }
    V.render();
    $('texto').textContent = "[" + (k+1) + "/" + F.length + "]  " + fr.texto + "   ·   flips acumulados: " + fr.flips;
    $('sPaso').value = k; $('nPaso').textContent = (k+1)+"/"+F.length;
  }
  function go(n){ k = Math.max(0,Math.min(F.length-1,n)); draw(); }
  function loop(){
    clearTimeout(timer);
    if(playing){
      if(k>=F.length-1){ playing=false; $('bPlay').textContent='▶ Reproducir'; return; }
      go(k+1);
      timer = setTimeout(loop, 1000/parseFloat($('sVel').value));
    }
  }
  function setPlay(p){ playing=p; $('bPlay').textContent = p?'⏸ Pausa':'▶ Reproducir'; if(p){ if(k>=F.length-1) k=0; loop(); } else clearTimeout(timer); }

  $('sPaso').max = F.length-1;
  $('bIni').onclick = function(){ setPlay(false); go(0); };
  $('bFin').onclick = function(){ setPlay(false); go(F.length-1); };
  $('bAtr').onclick = function(){ setPlay(false); go(k-1); };
  $('bSig').onclick = function(){ setPlay(false); go(k+1); };
  $('bPlay').onclick = function(){ setPlay(!playing); };
  $('sPaso').oninput = function(){ setPlay(false); go(parseInt(this.value)); };
  $('sZ').oninput = draw; $('cAr').onchange = draw; $('cPt').onchange = draw;

  $3Dmolpromise.then(function(){
    V = window["viewer_"+UID];
    // Encuadre fijo sobre el modelo final para que la cámara no "salte"
    k = F.length-1; draw(); k = 0; draw();
    setTimeout(loop, 600);
  });
})();
</script>
"""


def construir_html(cuadros):
    zs = [p[2] for c in cuadros[-1:] for p in c["pts"]]
    vista = py3Dmol.view(width="100%", height="78vh")
    vista.setBackgroundColor("#0f1722")
    html_visor = vista.write_html()   # py3Dmol define el visor (y su id único)
    uid = vista.uniqueid

    js = (PLAYER_JS.replace("__FRAMES__", json.dumps(cuadros, separators=(",", ":")))
                   .replace("__UID__", uid)
                   .replace("__ZMIN__", str(min(zs)))
                   .replace("__ZMAX__", str(max(zs))))
    return ("<!DOCTYPE html><html><head><meta charset='utf-8'>"
            "<title>Triangulación de Delaunay - Terreno 3D</title></head><body>"
            + PANEL_HTML + html_visor + js + "</body></html>")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--salida", default="terreno_delaunay.html")
    ap.add_argument("--no-open", action="store_true")
    a = ap.parse_args()

    print(f"Generando {a.n} puntos...")
    puntos = generate_synthetic_terrain(a.n, ANCHO_TERRENO, ALTO_TERRENO, seed=a.seed)

    print("Construyendo la triangulación (RIC + DAG) y grabando cada paso...")
    cuadros, solver = grabar_construccion(puntos, a.seed)
    print(f"  {len(cuadros)} cuadros · {solver.flips} edge flips · "
          f"{solver.stats()['profundidad_busqueda']:.1f} saltos promedio en el DAG")

    ruta = os.path.abspath(a.salida)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(construir_html(cuadros))
    print(f"HTML generado: {ruta}")

    if not a.no_open:
        print("Abriendo modelo 3D en el navegador...")
        webbrowser.open("file://" + ruta)


if __name__ == "__main__":
    main()
