"""Independent vertical plane competition selection from authored Lobby geometry.

Only projected interiors farther than radius+margin from edges are used; any
nearby non-horizontal authored triangle excludes a probe. The resulting cases
contain multiple distinct horizontal camera-enabled planes on one vertical ray.
This checks nearest native hit in the loaded terrain, not all actors/frames.
"""
import numpy as np

def projected_distance(point,vertices):
    """Unsigned point-to-projected-triangle distance and minimum edge distance."""
    v=vertices[:,(0,2)].astype(float);p=np.asarray(point,dtype=float)
    edges=np.roll(v,-1,axis=0)-v;rel=p-v
    denom=np.sum(edges*edges,axis=1)
    t=np.divide(np.sum(edges*rel,axis=1),denom,out=np.zeros(3),where=denom>0)
    delta=rel-np.clip(t,0,1)[:,None]*edges;edge_dist=float(np.sqrt(np.sum(delta*delta,axis=1)).min())
    cross=edges[:,0]*rel[:,1]-edges[:,1]*rel[:,0]
    a=v[1]-v[0];b=v[2]-v[0]
    inside=(np.all(cross>=-1e-9) or np.all(cross<=1e-9)) and abs(a[0]*b[1]-a[1]*b[0])>1e-8
    return (0. if inside else edge_dist),edge_dist,inside

def select_cases(mesh,ph,limit=16):
    tri=mesh['pos'][mesh['tri']];normal=np.cross(tri[:,1].astype(float)-tri[:,0],tri[:,2].astype(float)-tri[:,0]);area=np.linalg.norm(normal,axis=1)
    horizontal=np.divide(abs(normal[:,1]),area,out=np.zeros(len(tri)),where=area>0)>.9999999
    camera_enabled=np.array([bool(ph['filters'][int(tag)]&128) for tag in mesh['tag']])
    largest=sorted(np.flatnonzero(horizontal & camera_enabled & (area>10)),key=lambda i:-area[i]);out=[];seen=set()
    for original in largest:
        center=tri[original].mean(axis=0);xz=center[(0,2),]
        key=(float(xz[0]),float(xz[1]))
        if key in seen:continue
        seen.add(key);planes=[];unsafe=False
        for i,vertices in enumerate(tri):
            if not camera_enabled[i] or area[i]<=0:continue
            dist,margin,inside=projected_distance(xz,vertices)
            if not horizontal[i] and dist<.35:unsafe=True;break
            if horizontal[i] and inside:
                if margin<.35:unsafe=True;break
                planes.append({'triangle':int(i),'tag':int(mesh['tag'][i]),'key':int(mesh['key'][i]),'y':float(vertices[0,1]),'projected_edge_margin':margin})
        ys=sorted(set(r['y'] for r in planes))
        if unsafe or len(ys)<2 or ys[-1]-ys[0]<1:continue
        start=np.array([xz[0],np.float32(ys[-1])+np.float32(3),xz[1]],np.float32)
        end=np.array([xz[0],np.float32(ys[0])-np.float32(3),xz[1]],np.float32)
        out.append({'start':start.tolist(),'end':end.tolist(),'radius':float(np.float32(.3)),'plane_y':ys[-1],'competing_planes':planes,'distinct_y':ys})
        if len(out)==limit:break
    return out
