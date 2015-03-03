# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "eMonitor",
    "author": "Eibriel",
    "version": (0, 2),
    "blender": (2, 73, 0),
    "location": "Image > Send to eMonitor",
    "description": "Monitor your render on the Web",
    "warning": "",
    "wiki_url": "https://github.com/Eibriel/scripts/wiki",
    "tracker_url": "https://github.com/Eibriel/eMonitor/issues",
    "category": "Eibriel"}

import os
import bpy
import json
import logging
import requests
from bpy.app.handlers import persistent
from bpy.props import IntProperty, BoolProperty, StringProperty

from requests.exceptions import ConnectionError, Timeout


class eMonitorOpen (bpy.types.Operator):
    """Open render on eMonitor """
    bl_idname = "emonitor.open"
    bl_label = "Open render on eMonitor"

    share = bpy.props.EnumProperty(
        items=[
            ('NONE', 'None', 'Open eMonitor'),
            ('TWITTER', 'Twitter', 'Send to Twitter'),
            ('DIASPORA', 'Diaspora', 'Send to Diaspora')],
        name="Share",
        default='NONE')

    @classmethod
    def poll(self, context):
        wm = bpy.context.window_manager
        return wm.emonitor_JobUUID != ""

    def execute(self, context):
        wm = bpy.context.window_manager
        juuid = wm.emonitor_JobUUID
        twitter = "https://twitter.com/intent/tweet"
        diaspora = "https://diaspora.com.ar/bookmarklet"
        eurl = "http://monitor.eibriel.com"
        if 'edev' in context.scene:
            eurl = "http://localhost:5000"
        title = "eMonitor"
        if self.share == 'TWITTER':
            url = "{0}?original_referer={1}/{2}&url={1}/{2}&text={3}".format(
                twitter, eurl, juuid, title)
        elif self.share == 'DIASPORA':
            url = "{0}?url={1}/{2}&title={3}".format(
                diaspora, eurl, juuid, title)
        else:
            url = "{0}/{1}".format(eurl, juuid)

        bpy.ops.wm.url_open(url=url)
        return {'FINISHED'}


class eMonitorUpdate (bpy.types.Operator):
    """eMonitor update"""
    bl_idname = "emonitor.update"
    bl_label = "eMonitor update"

    api_url = ""

    render_status = bpy.props.StringProperty(
        name="eMonitor Render Status", default="")

    @classmethod
    def poll(self, context):
        scn = context.scene
        do = True
        if self.render_status == "":
            do = False
        if bpy.app.background:
            do = False

        if scn.render.use_sequencer and scn.sequence_editor:
            if len(scn.sequence_editor.sequences.items()) > 0:
                do = False
        return do

    def get_data(self, context):
        scene = context.scene
        cycles = scene.cycles
        data = {}
        if scene.render.engine == 'CYCLES':
            data['use_square_samples'] = cycles.use_square_samples
            data['feature_set'] = cycles.feature_set
            data['shading_system'] = cycles.shading_system
            data['progressive'] = cycles.progressive
            if cycles.progressive == 'PATH':
                data['samples'] = cycles.samples
            else:
                data['aa_samples'] = cycles.aa_samples
                data['diffuse_samples'] = cycles.diffuse_samples
                data['glossy_samples'] = cycles.glossy_samples
                data['transmission_samples'] = cycles.transmission_samples
                data['ao_samples'] = cycles.ao_samples
                data['mesh_light_samples'] = cycles.mesh_light_samples
                data['subsurface_samples'] = cycles.subsurface_samples
                data['volume_samples'] = cycles.volume_samples
                data['sample_all_lights_direct'] = cycles.sample_all_lights_direct
                data['sample_all_lights_indirect'] = cycles.sample_all_lights_indirect
            data['volume_step_size'] = cycles.volume_step_size
            data['volume_max_steps'] = cycles.volume_max_steps
            data['transparent_max_bounces'] = cycles.transparent_max_bounces
            data['transparent_min_bounces'] = cycles.transparent_min_bounces
            data['max_bounces'] = cycles.max_bounces
            data['min_bounces'] = cycles.min_bounces
            data['diffuse_bounces'] = cycles.diffuse_bounces
            data['glossy_bounces'] = cycles.glossy_bounces
            data['transmission_bounces'] = cycles.transmission_bounces
            data['volume_bounces'] = cycles.volume_bounces
            data['use_transparent_shadows'] = cycles.use_transparent_shadows
            data['caustics_reflective'] = cycles.caustics_reflective
            data['caustics_refractive'] = cycles.caustics_refractive
            data['blur_glossy'] = cycles.blur_glossy
        elif scene.render.engine == 'BLENDER_RENDER':
            data['use_ambient_occlusion'] = scene.world.light_settings.use_ambient_occlusion

        return json.dumps(data)


    def execute(self, context):
        scene = context.scene
        D = bpy.data
        wm = bpy.context.window_manager

        if not wm.emonitor_enabled:
            return {'FINISHED'}

        if D.filepath == '':
            file = 'untitled'
        else:
            file = os.path.split(D.filepath)[1]

        if self.render_status in ["JOB_START"]:
            wm.emonitor_frameCount = 0

        name = "{0}_{1}".format(file, scene.name)
        emon_data = {}
        emon_data['name'] = name
        emon_data['token_simple'] = wm.emonitor_TokenSimple
        emon_data['engine'] = scene.render.engine
        emon_data['freestyle'] = scene.render.use_freestyle
        emon_data['compositor'] = scene.render.use_compositing
        emon_data['sequencer'] = scene.render.use_sequencer
        emon_data['frame_start'] = scene.frame_start
        emon_data['frame_end'] = scene.frame_end
        if self.render_status not in ["RENDER_COMPLETE", "JOB_CANCELLED"]:
            emon_data['frame_current'] = scene.frame_current
        emon_data['status'] = self.render_status
        emon_data['engine_data'] = self.get_data(context)

        if scene.frame_current < scene.frame_start or\
                scene.frame_current > scene.frame_end:
            emon_data['frame_start'] = scene.frame_current
            emon_data['frame_end'] = scene.frame_current
            emon_data['frame_current'] = scene.frame_current

        # Detects rendering a single frame
        if self.render_status in ["RENDER_COMPLETE"]:
            if wm.emonitor_frameCount == 1:
                emon_data['frame_start'] = wm.emonitor_lastFrame
                emon_data['frame_end'] = wm.emonitor_lastFrame
                emon_data['frame_current'] = wm.emonitor_lastFrame

        wm.emonitor_lastFrame = scene.frame_current

        # print (emon_data)
        if self.render_status == "RENDER_START":
            wm.emonitor_RenderingFrame = True
            wm.emonitor_frameCount += 1

        self.api_url = "http://monitor.eibriel.com"
        if 'edev' in context.scene:
            self.api_url = "http://localhost:5000"

        if self.render_status == "JOB_START":
            apiurl = "{0}/api/job".format(self.api_url)
            try:
                r = requests.post(apiurl, data=emon_data, timeout=20)
            except ConnectionError:
                print ("[eMonitor] Connection Error A")
                return {'FINISHED'}
            except Timeout:
                print ("[eMonitor] Timeout Error A")
                return {'FINISHED'}
            if r.status_code != 200:
                print("[eMonitor] Error ({0}A)".format(r.status_code))
                return {'FINISHED'}
            rlist = json.loads(r.text)
            jobuuid = rlist['uuid']
            token_simple = rlist['token_simple']
            wm.emonitor_RenderingJob = True
            wm.emonitor_JobUUID = jobuuid
            wm.emonitor_TokenSimple = token_simple
        elif self.render_status in ["RENDER_UPDATE",
                                    "RENDER_END",
                                    "JOB_CANCELLED"]:
            juuid = wm.emonitor_JobUUID
            tmpfolder = context.user_preferences.filepaths.temporary_directory
            filepath = os.path.join(
                tmpfolder, 'thumbnail_{0}.png'.format(juuid))
            bpy.data.images["Render Result"].save_render(filepath)
            render_file = [('images', ('thumbnail.png',
                                       open(filepath, 'rb'),
                                       'image/png'))]
            apiurl = "{0}/api/job/{1}".format(self.api_url, juuid)
            try:
                r = requests.patch(apiurl,
                                files=render_file,
                                data=emon_data,
                                timeout=20)
            except ConnectionError:
                print ("[eMonitor] Connection Error C")
                return {'FINISHED'}
            except Timeout:
                print ("[eMonitor] Timeout Error C")
                return {'FINISHED'}
            if r.status_code != 200:
                print("[eMonitor] Error ({0}B)".format(r.status_code))
                return {'FINISHED'}
            rlist = json.loads(r.text)
        else:
            juuid = wm.emonitor_JobUUID
            apiurl = "{0}/api/job/{1}".format(self.api_url, juuid)
            try:
                r = requests.patch(apiurl, data=emon_data, timeout=20)
            except ConnectionError:
                print ("[eMonitor] Connection Error C")
                return {'FINISHED'}
            except Timeout:
                print ("[eMonitor] Timeout Error C")
                return {'FINISHED'}

            if r.status_code != 200:
                print("[eMonitor] Error ({0}C)".format(r.status_code))
                return {'FINISHED'}
            rlist = json.loads(r.text)

        return {'FINISHED'}


@persistent
def render_init(scene):
    logging.debug("Start Job")
    if bpy.ops.emonitor.update.poll():
       bpy.ops.emonitor.update(render_status="JOB_START")


@persistent
def render_pre(scene):
    logging.debug("Start Render")
    if bpy.ops.emonitor.update.poll():
        bpy.ops.emonitor.update(render_status="RENDER_START")


@persistent
def render_post(scene):
    wm = bpy.context.window_manager
    logging.debug("End Render")
    wm.emonitor_RenderingFrame = False
    if bpy.ops.emonitor.update.poll():
        bpy.ops.emonitor.update(render_status="RENDER_END")


@persistent
def render_cancel(scene):
    wm = bpy.context.window_manager
    logging.debug("Job Cancelled")
    wm.emonitor_RenderingJob = False
    wm.emonitor_RenderingFrame = False
    if bpy.ops.emonitor.update.poll():
        bpy.ops.emonitor.update(render_status="JOB_CANCELLED")
        wm.emonitor_TokenSimple = -1
        wm.emonitor_enabled = False


@persistent
def render_complete(scene):
    wm = bpy.context.window_manager
    logging.debug("Job Completed")
    wm.emonitor_RenderingJob = False
    wm.emonitor_RenderingFrame = False
    if bpy.ops.emonitor.update.poll():
        bpy.ops.emonitor.update(render_status="RENDER_COMPLETE")
        wm.emonitor_TokenSimple = -1
        wm.emonitor_enabled = False


@persistent
def render_write(scene):
    logging.debug("Image Saved")


def buttons_emonitor(self, context):
    wm = bpy.context.window_manager
    self.layout.separator()
    prop = self.layout.operator("emonitor.open", "Open eMonitor")
    prop.share = 'NONE'
    #prop = self.layout.operator("emonitor.open", "Tweet")
    #prop.share = 'TWITTER'
    #prop = self.layout.operator("emonitor.open", "Diaspora")
    #prop.share = 'DIASPORA'
    self.layout.prop(wm, 'emonitor_enabled')


def register():
    wm = bpy.types.WindowManager
    bpy.types.INFO_MT_render.append(buttons_emonitor)
    wm.emonitor_StartTime = IntProperty(options={'HIDDEN', 'SKIP_SAVE'})
    wm.emonitor_RenderingFrame = BoolProperty(
        name="Rendering Frame", default=False, options={'HIDDEN', 'SKIP_SAVE'})
    wm.emonitor_RenderingJob = BoolProperty(
        name="Rendering Job", default=False, options={'HIDDEN', 'SKIP_SAVE'})
    wm.emonitor_JobUUID = StringProperty(
        name="Job UUID", default="", options={'HIDDEN', 'SKIP_SAVE'})
    wm.emonitor_TokenSimple = IntProperty(
        default=-1, options={'HIDDEN', 'SKIP_SAVE'})
    wm.emonitor_enabled = BoolProperty(
        name="Enable eMonitor", default=False, options={'HIDDEN', 'SKIP_SAVE'})
    wm.emonitor_lastFrame = IntProperty(
        default=-9999, options={'HIDDEN', 'SKIP_SAVE'})
    wm.emonitor_frameCount = IntProperty(
        default=0, options={'HIDDEN', 'SKIP_SAVE'})

    bpy.app.handlers.render_init.append(render_init)
    bpy.app.handlers.render_pre.append(render_pre)
    bpy.app.handlers.render_post.append(render_post)
    bpy.app.handlers.render_cancel.append(render_cancel)
    bpy.app.handlers.render_complete.append(render_complete)
    bpy.app.handlers.render_write.append(render_write)
    bpy.utils.register_module(__name__)


def unregister():
    bpy.types.INFO_MT_render.remove(buttons_emonitor)
    bpy.app.handlers.render_init.remove(render_init)
    bpy.app.handlers.render_pre.remove(render_pre)
    bpy.app.handlers.render_post.remove(render_post)
    bpy.app.handlers.render_cancel.remove(render_cancel)
    bpy.app.handlers.render_complete.remove(render_complete)
    bpy.app.handlers.render_write.remove(render_write)
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
