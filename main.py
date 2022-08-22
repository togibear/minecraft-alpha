import math
import ctypes
import pyglet

pyglet.options["shadow_window"] = False
pyglet.options["debug_gl"] = False

import pyglet.gl as gl

import matrix
import shaders
import camera

import block_type
import texture_manager

class Window(pyglet.window.Window):
    def __init__(self, **args):
        super().__init__(**args)

        #blocks!
        self.texture_manager = texture_manager.Texture_manager(16, 16, 256)

        self.cobblestone = block_type.Block_type(self.texture_manager, "cobblestone", {"all": "cobblestone"})
        self.grass = block_type.Block_type(self.texture_manager, "grass", {"top": "grass_top", "bottom": "dirt", "sides": "grass_side"})
        self.dirt = block_type.Block_type(self.texture_manager, "dirt", {"all": "dirt"})
        self.stone = block_type.Block_type(self.texture_manager, "stone", {"all": "stone"})

        self.texture_manager.generate_mipmaps()

        #vertex array object
        self.vao = gl.GLuint(0)
        gl.glGenVertexArrays(1, ctypes.byref(self.vao))
        gl.glBindVertexArray(self.vao)

        #vertex position vbo
        self.vertex_position_vbo = gl.GLuint(0)
        gl.glGenBuffers(1, ctypes.byref(self.vertex_position_vbo))
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vertex_position_vbo)

        gl.glBufferData(gl.GL_ARRAY_BUFFER,
            ctypes.sizeof(gl.GLfloat * len(self.grass.vertex_positions)),
            (gl.GLfloat * len(self.grass.vertex_positions)) (*self.grass.vertex_positions),
            gl.GL_STATIC_DRAW)

        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, 0)
        gl.glEnableVertexAttribArray(0)

        #tex coord vbo

        self.tex_coord_vbo = gl.GLuint(0)
        gl.glGenBuffers(1, ctypes.byref(self.tex_coord_vbo))
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.tex_coord_vbo)

        gl.glBufferData(gl.GL_ARRAY_BUFFER,
            ctypes.sizeof(gl.GLfloat * len(self.grass.tex_coords)),
            (gl.GLfloat * len(self.grass.tex_coords)) (*self.grass.tex_coords),
            gl.GL_STATIC_DRAW)

        gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, 0)
        gl.glEnableVertexAttribArray(1)

        #shading vbo
        self.shading_vbo = gl.GLuint(0)
        gl.glGenBuffers(1, ctypes.byref(self.shading_vbo))
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.shading_vbo)

        gl.glBufferData(gl.GL_ARRAY_BUFFER,
            ctypes.sizeof(gl.GLfloat * len(self.grass.shading)),
            (gl.GLfloat * len(self.grass.shading)) (*self.grass.shading),
            gl.GL_STATIC_DRAW)

        gl.glVertexAttribPointer(2, 1, gl.GL_FLOAT, gl.GL_FALSE, 0, 0)
        gl.glEnableVertexAttribArray(2)

        #index buffer object
        self.ibo = gl.GLuint(0)
        gl.glGenBuffers(1, self.ibo)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.ibo)

        gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER,
            ctypes.sizeof(gl.GLuint * len(self.grass.indices)),
            (gl.GLuint * len(self.grass.indices)) (*self.grass.indices),
            gl.GL_STATIC_DRAW)

        #shader
        self.shader = shaders.Shader("vert.glsl", "frag.glsl")
        self.shader_sampler_location = self.shader.find_uniform(b"texture_array_sampler")
        self.shader.use()

        pyglet.clock.schedule_interval(self.update, 1.0 / 60)

        #mouse capture
        self.mouse_captured = False

        #camera
        self.camera = camera.Camera(self.shader, self.width, self.height)

    def update(self, delta_time):
        if not self.mouse_captured:
            self.camera.input = [0, 0, 0]
        
        self.camera.update_camera(delta_time)

    def on_draw(self):
        self.camera.update_matrices()
        
        #bind textures
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, self.texture_manager.texture_array)
        gl.glUniform1i(self.shader_sampler_location, 0)

        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        self.clear()

        gl.glDrawElements(gl.GL_TRIANGLES, len(self.grass.indices), gl.GL_UNSIGNED_INT, None)


    def on_resize(self, width, height):
        print(f"resize {width} * {height}")
        gl.glViewport(0, 0, width, height)

        self.camera.width = width
        self.camera.height =height

    def on_mouse_press(self, x, y, button, modifiers):
        self.mouse_captured = not self.mouse_captured
        self.set_exclusive_mouse(self.mouse_captured)

    def on_mouse_motion(self, x, y, delta_x, delta_y):
        if self.mouse_captured:
            sensitivity = 0.004

            self.camera.rotation[0] -= delta_x * sensitivity
            self.camera.rotation[1] += delta_y * sensitivity

            self.camera.rotation[1] = max(-math.tau / 4, min(math.tau / 4, self.camera.rotation[1]))

    def on_key_press(self, key, modifiers):
        if not self.mouse_captured:
            return
        
        if key == pyglet.window.key.D: self.camera.input[0] += 1
        elif key == pyglet.window.key.A: self.camera.input[0] -= 1
        elif key == pyglet.window.key.W: self.camera.input[2] += 1
        elif key == pyglet.window.key.S: self.camera.input[2] -= 1

        elif key == pyglet.window.key.SPACE: self.camera.input[1] += 1
        elif key == pyglet.window.key.LSHIFT: self.camera.input[1] -= 1

    def on_key_release(self, key, modifiers):
        if not self.mouse_captured:
            return
        
        if key == pyglet.window.key.D: self.camera.input[0] -= 1
        elif key == pyglet.window.key.A: self.camera.input[0] += 1
        elif key == pyglet.window.key.W: self.camera.input[2] -= 1
        elif key == pyglet.window.key.S: self.camera.input[2] += 1

        elif key == pyglet.window.key.SPACE: self.camera.input[1] -= 1
        elif key == pyglet.window.key.LSHIFT: self.camera.input[1] += 1




class Game:
    def __init__(self):
        self.config = gl.Config(double_buffer = True, major_version = 3, minor_version = 3, depth_size = 16)
        self.window = Window(config = self.config, width = 800, height = 600, caption = "minecraft clone", resizable = True, vsync = False)

    def run(self):
        pyglet.app.run()

if __name__ == "__main__":
    game = Game()
    game.run()