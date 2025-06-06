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
player.height=1.8
player.cursor.color = color.white

stone_texture = "textures/stone.png"
diamond_ore_texture = "textures/diamond_ore.png"
gold_ore_texture = "textures/gold_ore.png"
iron_ore_texture = "textures/iron_ore.png"

player_money = 0
highlight_opacity = .75

mining_target = None
mining_start_time = 0 
mining_duration = 1.0 
is_mining = False 
original_color = None

depth = 16
width = 16
height = 8

stone_texture = load_texture(stone_texture)
diamond_ore_texture = load_texture(diamond_ore_texture)
gold_ore_texture = load_texture(gold_ore_texture)
iron_ore_texture = load_texture(iron_ore_texture)

border_left = Entity(model="cube", collider="box", visible = False, position = Vec3(-1,-height, depth/2), scale = (-1, height*5, depth*2))
border_right = Entity(model="cube", collider="box", visible = False, position = Vec3(width,-height, depth/2), scale = (1, height*5, depth*2))
border_near = Entity(model="cube", collider="box", visible = False, position = Vec3(width/2,-height, -1), scale = (width*2, height*5, 1))
border_far = Entity(model="cube", collider="box", visible = False, position = Vec3(width/2,-height, depth), scale = (width*2, height*5, 1))
border_bottom = Entity(model="cube", collider="box", visible = False, position = Vec3(width/2,-height-.5, depth/2), scale = (width*2, -1, depth*2))

mining_bar_bg = Entity(model='quad', scale=(0.3, 0.03), position=(0, -0.4, 0), 
    color=color.gray.tint(-.4), parent=camera.ui, enabled=False)
mining_bar = Entity(model='quad', scale=(0.0, 0.02), position=(-0.148, -0.4, -0.01), 
    origin=(-0.5, 0), color=color.orange, parent=camera.ui, enabled=False)

mining_text = Text(
    text = "0%",
    position = (0,-0.3925,-0.2),
    scale = .75,
    parent = camera.ui,
    enabled = False
    )

money_text = Text(
    text= f"${player_money}", 
    position = (-0.75, .45, -0.01),
    scale= 2,
    parent= camera.ui,
    color=rgb(0,255,0)
    )

money_bg = Entity(model="quad", scale=(0.5,0.2), position=(-0.85,.455, 0), color = color.gray.tint(-.4), parent = camera.ui)


pickaxe_level = 1
upgrade_base_cost = 20
pickaxe_speed_multiplier = 1.0
show_upgrade_menu = False

upgrade_menu_bg = Entity(model='quad', scale=(0.7, 0.7), position=(0, 0, 1), 
    color=color.gray.tint(-.4), parent=camera.ui, enabled=False)

upgrade_button = Button(text="Upgrade", scale=(0.2, 0.08),  position=(0, -0.15, -0.01), 
                        color=color.azure, highlight_color=color.azure.tint(-.2), parent=camera.ui, enabled=False)

upgrade_close_button = Button(text="Close", scale=(0.2, 0.08),  position=(0, -0.25, -0.01), 
                        color=color.red, highlight_color=color.red.tint(-.2), parent=camera.ui, enabled=False)

pickaxe_level_text = Text(text=f"Current Level: {pickaxe_level}", position=(-0.13, 0.2, -0.01), 
                            scale=1.5, parent=camera.ui, enabled=False)

upgrade_cost_text = Text(text=f"Upgrade Cost: ${upgrade_base_cost * pickaxe_level}", 
                            position=(-0.16, 0.1, -0.01), scale=1.5, parent=camera.ui, enabled=False)

pickaxe_speed_text = Text(text=f"Mining Speed: {pickaxe_speed_multiplier:.1f}x", 
                            position=(-0.16, 0, -0.01), scale=1.5, parent=camera.ui, enabled=False)

def toggle_upgrade_menu():
    global show_upgrade_menu
    show_upgrade_menu = not show_upgrade_menu

    pickaxe_level_text.text = f"Current Level: {pickaxe_level}"
    upgrade_cost_text.text = f"Upgrade Cost: ${upgrade_base_cost * pickaxe_level}"
    pickaxe_speed_text.text = f"Mining Speed: {pickaxe_speed_multiplier:.1f}x"

    upgrade_menu_bg.enabled = show_upgrade_menu
    upgrade_button.enabled = show_upgrade_menu
    upgrade_close_button.enabled = show_upgrade_menu
    pickaxe_level_text.enabled = show_upgrade_menu
    upgrade_cost_text.enabled = show_upgrade_menu
    pickaxe_speed_text.enabled = show_upgrade_menu

    if show_upgrade_menu:
        update_upgrade_button_appearance()
    
    player.cursor.enabled = not show_upgrade_menu
    mouse.locked = not show_upgrade_menu
    player.enabled = not show_upgrade_menu

def update_upgrade_button_appearance():
    cost = upgrade_base_cost * pickaxe_level
    if player_money >= cost:
        upgrade_button.color = color.azure
        upgrade_button.highlight_color = color.azure.tint(-.2)
    else:
        upgrade_button.color = color.gray.tint(-.3)
        upgrade_button.highlight_color = color.gray.tint(-.3)

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

for z in range(depth):
    for x in range(width):
        for y in range(height):
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
    if not show_upgrade_menu:
        if key == 'left mouse down':
            hit_info = raycast(camera.world_position, camera.forward, distance=8)
            if hit_info.hit and hasattr(hit_info.entity, 'value'):
                mining_target = hit_info.entity
                original_color = mining_target.color
                mining_start_time = time.time()
                is_mining = True
                mining_bar_bg.enabled = True
                mining_bar.enabled = True
                mining_text.enabled = True
        

        if key == 'left mouse up':
            if mining_target:
                mining_target.color = original_color
            is_mining = False
            mining_target = None
            mining_bar_bg.enabled = False
            mining_bar.enabled = False
            mining_text.enabled = False
            mining_bar.scale_x = 0
        
        if key == "e":
            toggle_upgrade_menu()

def upgrade_pickaxe():
    global player_money, pickaxe_level, pickaxe_speed_multiplier
    
    cost = upgrade_base_cost * pickaxe_level
    
    if player_money >= cost:
        player_money -= cost
        pickaxe_level += 1
        pickaxe_speed_multiplier = 1.0 + (pickaxe_level - 1) * 0.25
        
        money_text.text = f"${player_money}"
        pickaxe_level_text.text = f"Current Level: {pickaxe_level}"
        upgrade_cost_text.text = f"Upgrade Cost: ${upgrade_base_cost * pickaxe_level}"
        pickaxe_speed_text.text = f"Mining Speed: {pickaxe_speed_multiplier:.1f}x"

        update_upgrade_button_appearance()

upgrade_close_button.on_click = toggle_upgrade_menu
upgrade_button.on_click = upgrade_pickaxe

def update():
    global mining_target, mining_start_time, is_mining, player_money
    
    if is_mining and mining_target:
        hit_info = raycast(camera.world_position, camera.forward, distance=8, debug=True)
        
        if hit_info.hit and hit_info.entity == mining_target:
            elapsed = time.time() - mining_start_time
            mining_progress = min(elapsed * pickaxe_speed_multiplier / mining_target.mining_time, 1.0)
            mining_text.text = f"{round(mining_progress*100)}%"
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
                if show_upgrade_menu:
                    update_upgrade_button_appearance()
                destroy(mining_target)
                mining_target = None
                is_mining = False
                mining_bar_bg.enabled = False
                mining_bar.enabled = False
                mining_text.enabled = False
                mining_bar.scale_x = 0
        else:
            if mining_target:
                mining_target.color = original_color
            is_mining = False
            mining_target = None
            mining_bar_bg.enabled = False
            mining_bar.enabled = False
            mining_text.enabled = False
            mining_bar.scale_x = 0

    head_pos = Vec3(
        player.position.x,
        player.position.y + 1.5,
        player.position.z
    )
    
    hit_info = raycast(head_pos, player.up, distance=1)
    if hit_info.hit:
        hit_pos = hit_info.world_point
        horizontal_distance = ((hit_pos.x - head_pos.x)**2 + 
            (hit_pos.z - head_pos.z)**2)**0.5
        
        if horizontal_distance < 0.5:
            player.jump_height = 0
        else:
            player.jump_height = 2
    else:
        player.jump_height = 1


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