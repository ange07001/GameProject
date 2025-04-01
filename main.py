from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.shaders import lit_with_shadows_shader
import random
import time
import copy

app = Ursina(fullscreen=True)

Entity.default_shader = lit_with_shadows_shader

editor_camera = EditorCamera(enabled=False, ignore_paused=True)
player = FirstPersonController(enabled=True)
player.camera_pivot.y = 1.5

stone_texture = "textures\\stone.png"
diamond_ore_texture = "textures\\diamond_ore.png"
gold_ore_texture = "textures\\gold_ore.png"
iron_ore_texture = "textures\\iron_ore.png"

player_money = 0
highlight_opacity = .75

mining_target = None
mining_start_time = 0 
mining_duration = 1.0 
is_mining = False 
original_color = None

mining_bar_bg = Entity(model='quad', scale=(0.3, 0.03), position=(0, -0.4, 0), 
    color=color.gray.tint(-.4), parent=camera.ui, enabled=False)
mining_bar = Entity(model='quad', scale=(0.0, 0.02), position=(-0.148, -0.4, -0.01), 
    origin=(-0.5, 0), color=color.orange, parent=camera.ui, enabled=False)

money_text = Text(
    text= f"${player_money}", 
    position = (-0.8,.45),
    scale= 2,
    parent= camera.ui
    )

class Voxel(Button):
    def __init__(self, position=(0,0,0), texture=stone_texture):
        super().__init__(parent=scene,
            position=position,
            model='cube',
            origin_y=.5,
            texture=texture,
            color=color.hsv(0,0, random.uniform(0.9,1.0)),
            highlight_color=color.hsv(0,0,highlight_opacity),
        )
        if texture == diamond_ore_texture:
            self.value = 10
            self.mining_time = 3.0  
        elif texture == gold_ore_texture:
            self.value = 5
            self.mining_time = 2.0
        elif texture == iron_ore_texture:
            self.value = 2
            self.mining_time = 1.5
        else:
            self.value = 1
            self.mining_time = 1.0  

for z in range(16):
    for x in range(16):
        for y in range(8):
            rand_val = random.random()
            
            if rand_val < 0.005:
                block_texture = diamond_ore_texture
            elif rand_val < 0.05:
                block_texture = gold_ore_texture
            elif rand_val < 0.125:
                block_texture = iron_ore_texture
            else:
                block_texture = stone_texture
                
            voxel = Voxel(position=(x, -y, z), texture=block_texture)


def input(key):
    global player_money, mining_target, mining_start_time, is_mining, original_color
    if key == 'right mouse down':
        hit_info = raycast(camera.world_position, camera.forward, distance=8)
        if hit_info.hit and hasattr(hit_info.entity, 'value'):
            mining_target = hit_info.entity
            original_color = mining_target.color
            mining_start_time = time.time()
            is_mining = True
            mining_bar_bg.enabled = True
            mining_bar.enabled = True
    

    if key == 'right mouse up':
        if mining_target:
            mining_target.color = original_color
        is_mining = False
        mining_target = None
        mining_bar_bg.enabled = False
        mining_bar.enabled = False
        mining_bar.scale_x = 0

def update():
    global mining_target, mining_start_time, is_mining, player_money
    
    if is_mining and mining_target:
        hit_info = raycast(camera.world_position, camera.forward, distance=8)
        
        if hit_info.hit and hit_info.entity == mining_target:
            elapsed = time.time() - mining_start_time
            mining_progress = min(elapsed / mining_target.mining_time, 1.0)
            hit_info.entity.color
            
            mining_bar.scale_x = mining_progress * 0.3
            current_color = color.rgba(
                original_color.r, 
                original_color.g, 
                original_color.b, 
                1 - mining_progress
            )

            hit_info.entity.color = current_color

            if mining_progress >= 1.0:
                player_money += mining_target.value
                print(f"Money: ${player_money}")
                money_text.text = f"${player_money}"
                destroy(mining_target)
                mining_target = None
                is_mining = False
                mining_bar_bg.enabled = False
                mining_bar.enabled = False
                mining_bar.scale_x = 0
        else:
            if mining_target:
                mining_target.color = original_color
            is_mining = False
            mining_target = None
            mining_bar_bg.enabled = False
            mining_bar.enabled = False
            mining_bar.scale_x = 0
    if raycast(player.position, camera.up, distance=2).hit: # ToDo: get pos independent of head orientation
        player.jump_height = 0
    else:
        player.jump_height = 2


def pause_input(key):
    if key == 'tab':
        editor_camera.enabled = not editor_camera.enabled

        player.cursor.enabled = not editor_camera.enabled
        mouse.locked = not editor_camera.enabled
        editor_camera.position = player.position

pause_handler = Entity(ignore_paused=True, input=pause_input)

sun = DirectionalLight()
sun.look_at(Vec3(1,-1,-1))
Sky()

app.run()