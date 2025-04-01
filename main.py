from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.shaders import lit_with_shadows_shader

app = Ursina()

Entity.default_shader = lit_with_shadows_shader

editor_camera = EditorCamera(enabled=False, ignore_paused=True)
player = FirstPersonController(enabled=True)


class Voxel(Button):
    def __init__(self, position=(0,0,0)):
        super().__init__(parent=scene,
            position=position,
            model='cube',
            origin_y=.5,
            texture='minecraft-block-collection\\textures\\stone.png',
            color=color.hsv(0,0, random.uniform(0.9,1.0)),
            highlight_color=color.hsv(0,0,.75),
        )

for z in range(16):
    for x in range(16):
        voxel = Voxel(position=(x,0,z))


def input(key):
    if key == 'left mouse down':
        hit_info = raycast(camera.world_position, camera.forward, distance=8)
        if hit_info.hit:
            Voxel(position=hit_info.entity.position + hit_info.normal)
    if key == 'right mouse down' and mouse.hovered_entity:
        hit_info = raycast(camera.world_position, camera.forward, distance=8)
        if hit_info.hit:
            
            destroy(mouse.hovered_entity)

def pause_input(key):
    if key == 'tab':    # press tab to toggle edit/play mode
        editor_camera.enabled = not editor_camera.enabled

        player.cursor.enabled = not editor_camera.enabled
        mouse.locked = not editor_camera.enabled
        editor_camera.position = player.position

pause_handler = Entity(ignore_paused=True, input=pause_input)

sun = DirectionalLight()
sun.look_at(Vec3(1,-1,-1))
Sky()

player = FirstPersonController()
app.run()