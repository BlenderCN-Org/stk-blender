import bpy

print('=======================================')

for img in bpy.data.images:
    print(img.name)
    is_alpha = False
    if 'compositing' in img:
        #print('    compositing = ', img['compositing'])
        
        if img['compositing'] == 'blend':
            img['shader'] = 'alphablend'
            is_alpha = True
        if img['compositing'] == 'test':
            img['shader'] = 'alphatest'
            is_alpha = True
        if img['compositing'] == 'additive':
            img['shader'] = 'additive'
            is_alpha = True
        if img['compositing'] == 'coverage':
            img['shader'] = 'alphatest'
            is_alpha = True
        
    if 'graphical_effect' in img:
        #print('    graphical_effect = ', img['graphical_effect'])
        
        if img['graphical_effect'] == 'bubble':
            img['shader'] = 'bubble'
        if img['graphical_effect'] == 'grass':
            img['shader'] = 'grass'
            is_alpha = True
        if img['graphical_effect'] == 'spheremap':
            img['shader'] = 'spheremap'
        if img['graphical_effect'] == 'splatting':
            img['shader'] = 'splatting'
        if img['graphical_effect'] == 'water_shader':
            img['shader'] = 'water_shader'
            
    if 'light' in img and img['light'] == 'false' and not is_alpha:
        img['shader'] = 'unlit'
        
        