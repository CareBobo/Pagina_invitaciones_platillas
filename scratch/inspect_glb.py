import json
from pygltflib import GLTF2

def inspect_glb(filepath):
    try:
        gltf = GLTF2().load(filepath)
        
        print(f"--- Info for {filepath} ---")
        
        # Nodes
        print(f"Total Nodes: {len(gltf.nodes)}")
        node_names = [n.name for n in gltf.nodes if n.name]
        print(f"Node Names (sample): {node_names[:20]}")
        
        # Meshes
        print(f"\nTotal Meshes: {len(gltf.meshes)}")
        mesh_names = [m.name for m in gltf.meshes if m.name]
        print(f"Mesh Names: {mesh_names}")
        
        # Animations
        print(f"\nTotal Animations: {len(gltf.animations)}")
        for i, anim in enumerate(gltf.animations):
            print(f"  Animation {i}: {anim.name} (Channels: {len(anim.channels)})")
            
        # Materials
        print(f"\nTotal Materials: {len(gltf.materials)}")
        
    except Exception as e:
        print(f"Error reading GLB: {e}")

if __name__ == '__main__':
    inspect_glb(r'C:\Users\USER\Desktop\TODOS LOS PROYECTOS\Invitacion 1 boda\static\assets\libro3d.glb')
