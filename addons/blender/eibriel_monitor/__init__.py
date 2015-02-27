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
    "version": (0, 1),
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

from eibriel_monitor.emonitor_data import emonitor_data


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
        twitter="https://twitter.com/intent/tweet"
        diaspora="https://diaspora.com.ar/bookmarklet"
        eurl = "http://monitor.eibriel.com"
        title = "eMonitor"
        if self.share == 'TWITTER':
            url="{0}?original_referer={1}/{2}&url={1}/{2}&text={3}".format(
                    twitter, eurl, juuid, title)
        elif self.share == 'DIASPORA':
            url="{0}?url={1}/{2}&title={3}".format(
                diaspora, eurl, juuid, title)
        else:
            url="{0}/{1}".format(eurl, juuid)

        bpy.ops.wm.url_open(url=url)
        return {'FINISHED'}


class eMonitorUpdate (bpy.types.Operator):
    """eMonitor update"""
    bl_idname = "emonitor.update"
    bl_label = "eMonitor update"

    api_url = bpy.props.StringProperty(
        name="eMonitor API URL", default="")
    render_status = bpy.props.StringProperty(
        name="eMonitor Render Status", default="")

    @classmethod
    def poll(self, context):
        return self.api_url != "" or self.render_status != ""

    def get_data(self):
        # scene = context.scene
        return

    def execute(self, context):
        scene = context.scene
        D = bpy.data
        wm = bpy.context.window_manager

        if D.filepath == '':
            file = 'untitled'
        else:
            file = os.path.split(D.filepath)[1]

        name = "{0}_{1}".format(file, scene.name)
        emon_data = emonitor_data()
        emon_data.name = name
        emon_data.engine = scene.render.engine
        emon_data.freestyle = scene.render.use_freestyle
        emon_data.compositor = scene.render.use_compositing
        emon_data.sequencer = scene.render.use_sequencer
        emon_data.frame_start = scene.frame_start
        emon_data.frame_end = scene.frame_end
        if self.render_status not in ["RENDER_COMPLETE", "JOB_CANCELLED"]:
            emon_data.frame_current = scene.frame_current
        emon_data.status = self.render_status
        emon_data.data = self.get_data()

        #print (emon_data.array())
        if self.render_status == "RENDER_START":
            wm.emonitor_RenderingFrame = True

        self.api_url = "http://localhost:5000"
        self.api_url = "http://monitor.eibriel.com"

        if self.render_status == "JOB_START":
            apiurl = "{0}/api/job".format(self.api_url)
            r = requests.post(apiurl, data = emon_data.array())
            if r.status_code != 200:
                logging.error("Error")
                return {'FINISHED'}
            rlist = json.loads(r.text)
            jobuuid = rlist['uuid']
            wm.emonitor_RenderingJob = True
            wm.emonitor_JobUUID = jobuuid
        elif self.render_status in ["RENDER_UPDATE", "RENDER_END", "JOB_CANCELLED"]:
            juuid = wm.emonitor_JobUUID
            tmpfolder = context.user_preferences.filepaths.temporary_directory
            filepath = os.path.join(
                tmpfolder, 'thumbnail_{0}.png'.format(juuid))
            bpy.data.images["Render Result"].save_render(filepath)
            render_file = [('images', ('thumbnail.png', open(filepath, 'rb'), 'image/png'))]
            apiurl = "{0}/api/job/{1}".format(self.api_url, juuid)
            r = requests.patch(apiurl, files = render_file , data = emon_data.array())
            if r.status_code != 200:
                logging.error("Error")
                return {'FINISHED'}
            rlist = json.loads(r.text)
        else:
            juuid = wm.emonitor_JobUUID
            apiurl = "{0}/api/job/{1}".format(self.api_url, juuid)
            r = requests.patch(apiurl, data = emon_data.array())
            if r.status_code != 200:
                logging.error("Error: {0}".format(r.status_code))
                return {'FINISHED'}
            rlist = json.loads(r.text)

        return {'FINISHED'}

@persistent
def render_init(scene):
    logging.debug("Start Job")
    url="http://team.eibriel.com"
    bpy.ops.emonitor.update(api_url = url, render_status = "JOB_START")


@persistent
def render_pre(scene):
    logging.debug("Start Render")
    url = "http://team.eibriel.com"
    bpy.ops.emonitor.update(api_url = url, render_status = "RENDER_START")


@persistent
def render_post(scene):
    wm = bpy.context.window_manager
    logging.debug("End Render")
    wm.emonitor_RenderingFrame=False
    url = "http://team.eibriel.com"
    bpy.ops.emonitor.update(api_url = url, render_status = "RENDER_END")


@persistent
def render_cancel(scene):
    wm = bpy.context.window_manager
    logging.debug("Job Cancelled")
    wm.emonitor_RenderingJob=False
    wm.emonitor_RenderingFrame=False
    url = "http://team.eibriel.com"
    bpy.ops.emonitor.update(api_url = url, render_status = "JOB_CANCELLED")

@persistent
def render_complete(scene):
    wm = bpy.context.window_manager
    logging.debug("Job Completed")
    wm.emonitor_RenderingJob=False
    wm.emonitor_RenderingFrame=False
    url = "http://team.eibriel.com"
    bpy.ops.emonitor.update(api_url = url, render_status = "RENDER_COMPLETE")

@persistent
def render_write(scene):
    logging.debug("Image Saved")

def buttons_emonitor(self, context):
    wm = bpy.context.window_manager
    self.layout.separator()
    self.layout.operator("emonitor.open", "Monitor")
    prop = self.layout.operator("emonitor.open", "Tweet")
    prop.share = 'TWITTER'
    prop = self.layout.operator("emonitor.open", "Diaspora")
    prop.share = 'DIASPORA'
    self.layout.prop(wm, 'emonitor_enabled')


def register():
    wm = bpy.types.WindowManager
    bpy.types.INFO_MT_render.append(buttons_emonitor)
    wm.emonitor_StartTime = IntProperty(options={'HIDDEN', 'SKIP_SAVE'})
    wm.emonitor_RenderingFrame = BoolProperty(name="Rendering Frame", default=False, options={'HIDDEN', 'SKIP_SAVE'})
    wm.emonitor_RenderingJob = BoolProperty(name="Rendering Job", default=False, options={'HIDDEN', 'SKIP_SAVE'})
    wm.emonitor_JobUUID = StringProperty(name="Job UUID", default="", options={'HIDDEN', 'SKIP_SAVE'})
    wm.emonitor_enabled = BoolProperty(name="Enable eMonitor", default=True, options={'HIDDEN', 'SKIP_SAVE'})

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
