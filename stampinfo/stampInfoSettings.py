import os
from pathlib import Path

import bpy
from bpy.props import StringProperty, BoolProperty, IntProperty, FloatProperty, EnumProperty

from . import infoImage
from . import stamper
from . import handlers
from .utils import utils

# from stampinfo.__init__ import bl_info

# global vars
if "gbWkDebug" not in vars() and "gbWkDebug" not in globals():
    gbWkDebug = False

if gbWkDebug:
    if "gbWkDebug_DontDeleteTmpFiles" not in vars() and "gbWkDebug_DontDeleteTmpFiles" not in globals():
        gbWkDebug_DontDeleteTmpFiles = True

    if "gbWkDebug_DrawTextLines" not in vars() and "gbWkDebug_DrawTextLines" not in globals():
        gbWkDebug_DrawTextLines = True

else:
    if "gbWkDebug_DontDeleteTmpFiles" not in vars() and "gbWkDebug_DontDeleteTmpFiles" not in globals():
        gbWkDebug_DontDeleteTmpFiles = False

    if "gbWkDebug_DrawTextLines" not in vars() and "gbWkDebug_DrawTextLines" not in globals():
        gbWkDebug_DrawTextLines = False


class UAS_StampInfoSettings(bpy.types.PropertyGroup):
    def version(self):
        """ Return the add-on version in the form of a tupple made by: 
                - a string x.y.z (eg: "1.21.3")
                - an integer. x.y.z becomes xxyyyzzz (eg: "1.21.3" becomes 1021003)
            Return None if the addon has not been found
        """
        return utils.addonVersion("UAS_StampInfo")

    renderRootPath: StringProperty(name="Render Root Path", default="")
    renderRootPathUsed: BoolProperty(default=False)

    innerImageHeight_percentage: FloatProperty(
        name="Inner Height",
        description="Inner Image Height in pixels\nIf this line is red then the borders are out of the image",
        subtype="PERCENTAGE",
        min=1.0,
        max=200.0,
        precision=0,
        default=100.0,
    )

    innerImageHeight: IntProperty(
        name="Inner Height",
        description="Inner Image Height in pixels\nIf this line is red then the borders are out of the image",
        subtype="PIXEL",
        min=0,
        max=6000,
        step=1,
        default=720,
    )

    # innerImageRatio : FloatProperty(
    #     name="Inner Ratio",
    #     description="Inner Image Aspect Ratio (Eg: 16/9, 4/3...).\nIf this line is red then the rendered image ratio\nis the same as the framed image ratio and the\nborders will not be visible; consider\nincreasing the height of the rendered images",
    #     min = 1.0, max = 20.0, step = 0.05, default = 1.777, precision = 3 )

    # ----------------------------------
    #   For DIRECTTOCOMPOSITE mode
    stampRenderResYDirToCompo_percentage: FloatProperty(
        name="Y Res. Output",
        subtype="PERCENTAGE",
        description="Percentage of resolution of the stamp info images relatively to the scene output\nresolution for Direct To Composite mode.\nIf this line is red then the rendered image will be\npartially hidden by the borders",
        min=1.0,
        max=200.0,
        precision=1,
        default=86.0,
    )

    # ----------------------------------
    #   For SEPARATEOUTPUT mode
    stampRenderResX_percentage: FloatProperty(
        name="X Res. Output",
        subtype="PERCENTAGE",
        description="Percentage of resolution of the stamp info images relatively to the scene output resolution.\nIf this line is red then the rendered image will be\npartially hidden by the borders",
        min=1.0,
        max=200.0,
        precision=1,
        default=100.0,
    )

    stampRenderResY_percentage: FloatProperty(
        name="Y Res. Output",
        subtype="PERCENTAGE",
        description="Percentage of resolution of the stamp info images realatively to the scene output resolution.\nIf this line is red then the rendered image will be\npartially hidden by the borders",
        min=1.0,
        max=200.0,
        precision=1,
        default=133.34,
    )

    def activateStampInfo(self, activated):
        _logger.debug(f"\n*** StampInfo is now:  {activated}")
        self.stampInfoUsed = activated

        # if self.stampInfoUsed:
        #     self.registerRenderHandlers()
        # else:
        #     self.clearRenderHandlers()
        # #    if 2 != bpy.context.scene.UAS_StampInfo_Settings['stampInfoRenderMode']:        # not EXISTINGCOMPO
        #     if 'USECOMPOSITINGNODES' != bpy.context.scene.UAS_StampInfo_Settings.stampInfoRenderMode:        # not EXISTINGCOMPO
        #         stamper.clearInfoCompoNodes(bpy.context.scene)

    def stampInfoUsed_StateChanged(self, context):
        _logger.debug(f"\n*** Stamp Info updated. New state: {self.stampInfoUsed}")

        #   self.activateStampInfo(self.stampInfoUsed)
        if self.stampInfoUsed:
            self.registerRenderHandlers()
        else:
            self.clearRenderHandlers()
            #    if 2 != bpy.context.scene.UAS_StampInfo_Settings['stampInfoRenderMode']:        # not EXISTINGCOMPO
            if (
                "USECOMPOSITINGNODES" != bpy.context.scene.UAS_StampInfo_Settings.stampInfoRenderMode
            ):  # not EXISTINGCOMPO
                stamper.clearInfoCompoNodes(bpy.context.scene)

    def get_stampInfoUsed(self):
        val = self.get("stampInfoUsed", True)
        return val

    def set_stampInfoUsed(self, value):
        _logger.debug(f"\n*** set_stampInfoUsed: value: {value}")

        self["stampInfoUsed"] = value

        bpy.context.scene.UAS_StampInfo_Settings.clearRenderHandlers()

        if "USECOMPOSITINGNODES" != bpy.context.scene.UAS_StampInfo_Settings.stampInfoRenderMode:  # not EXISTINGCOMPO
            stamper.clearInfoCompoNodes(bpy.context.scene)

        bpy.context.scene.UAS_StampInfo_Settings.registerRenderHandlers()

        # alternative ne marche pas - crashes
        # if self.stampInfoUsed:
        #     bpy.context.scene.UAS_StampInfo_Settings.registerRenderHandlers()
        # else:
        #     bpy.context.scene.UAS_StampInfo_Settings.clearRenderHandlers()
        #     stamper.clearInfoCompoNodes(bpy.context.scene)

    stampInfoUsed: BoolProperty(
        name="Stamp Info",
        description="Stamp info on rendered images",
        default=False,
        get=get_stampInfoUsed,
        set=set_stampInfoUsed,
        update=stampInfoUsed_StateChanged,
    )

    def get_stampInfoRenderMode(self):
        # if not "stampInfoRenderMode" in self:
        #     if 0==value:
        #         self.stampInfoRenderMode = 'DIRECTTOCOMPOSITE'
        #     elif 1==value:
        #         self.stampInfoRenderMode = 'SEPARATEOUTPUT'
        #     else: self.stampInfoRenderMode = 'USECOMPOSITINGNODES'
        #     prop = None
        #     if not "stampInfoRenderMode" in self:
        #         prop = self.stampInfoRenderMode = 'SEPARATEOUTPUT'

        #     return prop
        # val = self.get("stampInfoRenderMode", 'SEPARATEOUTPUT')
        val = self.get("stampInfoRenderMode", 0)
        return val

    # return self.stampInfoRenderMode     #no

    # values are integers
    def set_stampInfoRenderMode(self, value):
        print(" set_stampInfoRenderMode: value: ", value)

        # no clear if we keep the graph with mode USECOMPOSITINGNODES
        if 2 != value:
            stamper.clearInfoCompoNodes(bpy.context.scene)

        self["stampInfoRenderMode"] = value
        # if 0==value:
        #     self.stampInfoRenderMode = 'DIRECTTOCOMPOSITE'
        # elif 1==value:
        #     self.stampInfoRenderMode = 'SEPARATEOUTPUT'
        # else: self.stampInfoRenderMode = 'USECOMPOSITINGNODES'

    stampInfoRenderMode: EnumProperty(
        name="Mode",
        items=[
            ("DIRECTTOCOMPOSITE", "Direct to Composite", "Stamp the information directly to the output", 0),
            (
                "SEPARATEOUTPUT",
                "Separate Output",
                "Creates another render output at the specified resolution and on which the rendered images have the stamped information",
                1,
            ),
            (
                "USECOMPOSITINGNODES",
                "(Adv.) Use Existing Compo Graph",
                "Advanced and experimental:\nPreserves the state of the compositing window Use Node checkbox so as to restore it after the rendering",
                2,
            ),
        ],
        get=get_stampInfoRenderMode,
        set=set_stampInfoRenderMode,
        default="DIRECTTOCOMPOSITE",
    )

    # ---------- project properties -------------

    projectUsed: BoolProperty(name="Project", description="Stamp project name", default=True, options=set())

    projectName: StringProperty(name="", description="Project name", default="UAS", options=set())

    # ---------- Logo properties -------------

    def buildLogosList(self, context):
        dir = Path(os.path.dirname(os.path.abspath(__file__)) + "\\Logos")
        items = list()
        for img in dir.glob("*.png"):
            # print ("    buildLogosList img.stem: " + img.stem )
            #  items.append ( ( img.stem, img.stem, "" ) )
            items.append((img.name, img.name, ""))

        return items

    def updateLogoPath(self, context):
        #  print("updateLogoPath")
        dir = Path(os.path.dirname(os.path.abspath(__file__)) + "\\Logos")
        #  print("  dir: " + str(dir))
        logoFilepath = str(dir) + "\\" + str(self.logoName)
        #  print("  logoFilepath: " + logoFilepath)
        self.logoFilepath = logoFilepath

    logoName: EnumProperty(
        name="Logo List",
        description="List of the logo files installed with this add-on",
        items=buildLogosList,
        update=updateLogoPath,
    )

    logoUsed: BoolProperty(name="Logo", description="Set and draw the specified logo", default=False)

    logoFilepath: StringProperty(name="", description="File path of the specified logo", default="")

    logoScaleH: FloatProperty(
        name="Scale", description="Set logo scale", min=0.001, max=2.0, step=0.01, default=0.08, precision=3
    )

    logoPosNormX: FloatProperty(
        name="Pos X", description="Logo Position X", min=-1.0, max=1.0, step=0.01, default=0.02, precision=3
    )

    logoPosNormY: FloatProperty(
        name="Pos Y", description="Logo Position Y", min=-1.0, max=1.0, step=0.01, default=0.02, precision=3
    )

    # ---------- video image -------------
    videoDurationUsed: BoolProperty(
        name="Video Duration",
        description="Total number of frames in the output sequence (handles included)",
        default=False,
        options=set(),
    )

    # ---------- video image -------------
    videoFrameUsed: BoolProperty(
        name="Video Frame",
        description="Stamp the index of the current image in the image sequence",
        default=False,
        options=set(),
    )

    videoRangeUsed: BoolProperty(
        name="Video Range",
        description="Stamp the index of the current image in the image sequence",
        default=False,
        options=set(),
    )

    videoHandlesUsed: BoolProperty(
        name="Video Handles",
        description="Stamp the shot handle values in the image sequence range",
        default=True,
        options=set(),
    )

    # ---------- 3d edit frame -------------
    edit3DFrameUsed: BoolProperty(
        name="3D Edit Frame",
        description="Stamp the index of the current image in the 3D edit sequence provided by Shot Manager add-on",
        default=False,
        options=set(),
    )

    edit3DFrame: FloatProperty(
        name="3D Edit Frame Value",
        description="Stamp the index of the current image in the 3D edit sequence provided by Shot Manager add-on",
        default=-1,
    )

    edit3DTotalNumberUsed: BoolProperty(
        name="3D Edit Duration",
        description="Stamp the total number of images in the 3D edit sequence provided by Shot Manager add-on",
        default=False,
        options=set(),
    )

    edit3DTotalNumber: FloatProperty(
        name="3D Edit Duration Value",
        description="Stamp the index of the current image in the 3D edit sequence provided by Shot Manager add-on",
        default=-1,
    )

    framerateUsed: BoolProperty(name="Framerate", description="Stamp current framerate", default=True, options=set())

    # ---------- Scene Frame properties -------------

    currentFrameUsed: BoolProperty(
        name="3D Frame",
        description="Stamp current rendered frame in the 3D scene time context",
        default=True,
        options=set(),
    )

    frameRangeUsed: BoolProperty(
        name="3D Range", description="Stamp frame range in the 3D scene time context", default=True, options=set()
    )

    frameHandlesUsed: BoolProperty(
        name="Shot Handles",
        description="Stamp the shot handle values in the image sequence range",
        default=True,
        options=set(),
    )

    # ---------- file properties -------------
    filenameUsed: BoolProperty(name="File", description="Stamp file name", default=True, options=set())

    filepathUsed: BoolProperty(name="Path", description="Stamp file path", default=True, options=set())

    # ---------- shot manager -------------
    sceneUsed: BoolProperty(name="Scene", description="Stamp scene name", default=True, options=set())

    takeUsed: BoolProperty(name="Take", description="Stamp take index", default=False, options=set())

    shotUsed: BoolProperty(name="Shot", description="Stamp shot name", default=False, options=set())

    # To be filled by a production script or by UAS Shot Manager
    shotName: StringProperty(
        name="Shot Name", description="Enter the name of the current shot", default="Shot Name", options=set()
    )

    shotHandles: IntProperty(
        name="Shot Handles Duration",
        description="Duration of the handles of the shot",
        default=0,
        soft_min=0,
        soft_max=50,
    )

    # To be filled by a production script or by UAS Shot Manager
    takeName: StringProperty(
        name="Take Name", description="Enter the name of the current take", default="Take Name", options=set()
    )

    # ---------- Camera properties -------------
    cameraUsed: BoolProperty(name="Camera", description="Stamp camera name", default=True, options=set())

    cameraLensUsed: BoolProperty(name="Lens", description="Stamp camera lens", default=True, options=set())

    # ---------- Shot duration -------------
    shotDurationUsed: BoolProperty(
        name="Shot Duration",
        description="Duration of the shot (in frames) as defined in the 3D edit (= WITHOUT the handles)",
        default=False,
        options=set(),
    )

    # ---------- Notes properties -------------
    notesUsed: BoolProperty(name="Notes", description="User notes", default=False, options=set())

    notesLine01: StringProperty(name="Notes Line 01", description="Enter notes here", default="Notes...", options=set())
    notesLine02: StringProperty(name="Notes Line 02", description="Enter notes here", options=set())
    notesLine03: StringProperty(name="Notes Line 03", description="Enter notes here", options=set())

    # ---------- Border properties -------------

    borderUsed: BoolProperty(name="Borders", description="Stamp borders", default=True, options=set())

    # regarder https://blender.stackexchange.com/questions/141333/how-controll-rgb-node-with-floatvectorproperty-blender-2-8
    borderColor: bpy.props.FloatVectorProperty(
        name="",
        subtype="COLOR",
        size=4,
        description="Stamp borders",
        min=0.0,
        max=1.0,
        precision=2,
        default=(0.0, 0.0, 0.0, 1.0),
        options=set(),
    )

    # ---------- Date properties -------------

    dateUsed: BoolProperty(name="Date", description="Stamp rendering date", default=False, options=set())

    timeUsed: BoolProperty(name="Time", description="Stamp rendering time", default=False, options=set())

    # ---------- Settings properties -------------
    # https://devtalk.blender.org/t/how-to-change-the-color-picker/9666/7
    # https://docs.blender.org/api/current/bpy.props.html?highlight=floatvectorproperty#bpy.props.FloatVectorProperty

    textColor: bpy.props.FloatVectorProperty(
        name="Text Color",
        subtype="COLOR",
        size=4,
        description="Stamp borders",
        default=(0.65, 0.65, 0.65, 1.0),
        min=0.0,
        max=1.0,
        precision=2,
    )

    fontScaleHNorm: FloatProperty(
        name="Font Size",
        description="Set font size. The scale of the font is normalized relatively to the height of the rendered image",
        min=0.001,
        max=1.0,
        step=0.01,
        default=0.025,
        precision=3,
    )

    interlineHNorm: FloatProperty(
        name="Interline Size",
        description="Set the size of the space between 2 text lines. This size is normalized relatively to the height of the rendered image",
        min=0.000,
        max=0.1,
        step=0.01,
        default=0.015,
        precision=3,
    )

    extPaddingNorm: FloatProperty(
        name="Exterior Padding",
        description="Set the distance between the text and the border of the image. This size is normalized relatively to the height of the rendered image",
        min=0.000,
        max=0.1,
        step=0.01,
        default=0.015,
        precision=3,
    )

    automaticTextSize: BoolProperty(
        name="Automatic Text Size",
        description="Text size is automatically calculated according to the size of the border",
        default=True,
        options=set(),
    )

    # linkTextToBorderEdge : BoolProperty(
    #     name="Link Text to Border",
    #     description="Link the text position to the edge of the borders.\nIf not linked then the text position is relative to the image top and bottom",
    #     default = True )

    offsetToCenterHNorm: FloatProperty(
        name="Offset To Center",
        description="Offset To Center. The offset of the border and text is normalized relatively to the height of the rendered image",
        min=0.000,
        max=1.0,
        step=0.001,
        default=0.0,
        precision=3,
    )

    # settings ###
    stampPropertyLabel: BoolProperty(
        name="Stamp Property Label", description="Stamp Property Label", default=True, options=set()
    )

    stampPropertyValue: BoolProperty(
        name="Stamp Property Value", description="Stamp Property Value", default=True, options=set()
    )

    mediaFistFrameIsZero: BoolProperty(
        name="Output Media First Frame is 0",
        description="Is checked (most common approach) then the first frame of the output\nmedia has index 0 (last then have index (seq. number of frames - 1).\n"
        "If not checked then it has index 1 and the last frame has the index equal to the media duration",
        default=True,
        options=set(),
    )

    # debug properties -------------

    def set_debugMode(self, value):
        # self.debugMode = value
        global gbWkDebug
        global gbWkDebug_DontDeleteTmpFiles
        global gbWkDebug_DrawTextLines

        gbWkDebug = value
        self.debug_DontDeleteCompoNodes = value
        gbWkDebug_DontDeleteTmpFiles = value
        gbWkDebug_DrawTextLines = value

    def get_debugMode(self):
        return self.debugMode

    debugMode: BoolProperty(name="Debug Mode", description="Debug Mode", default=gbWkDebug)
    #    set = set_debugMode,
    #    get = get_debugMode )

    debug_DrawTextLines: BoolProperty(
        name="Debug - Draw Text Lines", description="Debug - Draw Text Lines", default=gbWkDebug_DrawTextLines
    )

    debug_DontDeleteCompoNodes: BoolProperty(default=False)

    # def filePathAndName_valueChanged(self, context):
    #     print(" *** filePathAndName Changed !!! ***")

    # filePathAndName : StringProperty(
    #     name="",
    #     description="File name",
    #     default = "-",
    #     update = filePathAndName_valueChanged )

    # ---------- temp properties -------------

    tmp_usePreviousValues: BoolProperty(name="usePreviousValues", description="usePreviousValues", default=False)

    tmp_previousResolution_x: IntProperty(name="previousResolution_x", description="previousResolution_x", default=1)

    tmp_previousResolution_y: IntProperty(name="previousResolution_y", description="previousResolution_y", default=1)

    tmp_stampRenderResYDirToCompo_percentage: IntProperty(
        name="previousResolution_y Dir To Compo", description="previousResolution_y", default=50
    )

    def renderTmpImageWithStampedInfo(self, scene, currentFrame):
        infoImage.renderTmpImageWithStampedInfo(scene, currentFrame)

    def restorePreviousValues(self, scene):
        scene.render.resolution_x = self.tmp_previousResolution_x
        scene.render.resolution_y = self.tmp_previousResolution_y
        scene.UAS_StampInfo_Settings.stampRenderResYDirToCompo_percentage = (
            self.tmp_stampRenderResYDirToCompo_percentage
        )
        #   scene.UAS_StampInfo_Settings.stampInfoRenderMode = self.tmp_stampInfoRenderMode

        self.tmp_usePreviousValues = False

        # scene.render.resolution_x = tmp_previousResolution_x
        # scene.render.resolution_y = tmp_previousResolution_y
        # scene.UAS_StampInfo_Settings.stampRenderResYDirToCompo_percentage = tmp_stampRenderResYDirToCompo_percentage
        # scene.UAS_StampInfo_Settings.stampInfoRenderMode = tmp_stampInfoRenderMode

        # tmp_usePreviousValues = False

    def clearInfoCompoNodes(self, scene):
        stamper.clearInfoCompoNodes(scene)

    def clearRenderHandlers(self):
        _logger.debug(f"\n ** -- ** clearRenderHandlers ** -- **")

        from .utils import utils_handlers

        # utils_handlers.displayHandlers()

        utils_handlers.removeAllHandlerOccurences(
            handlers.uas_stampinfo_renderInitHandler, handlerCateg=bpy.app.handlers.render_init
        )
        utils_handlers.removeAllHandlerOccurences(
            handlers.uas_stampinfo_renderPreHandler, handlerCateg=bpy.app.handlers.render_pre
        )
        utils_handlers.removeAllHandlerOccurences(
            handlers.uas_stampinfo_renderCompleteHandler, handlerCateg=bpy.app.handlers.render_complete
        )
        utils_handlers.removeAllHandlerOccurences(
            handlers.uas_stampinfo_renderCancelHandler, handlerCateg=bpy.app.handlers.render_cancel
        )

    def registerRenderHandlers(self):
        _logger.debug(f"\n ** -- ** registerRenderHandlers ** -- **")
        # register handler
        # https://docs.blender.org/api/current/bpy.app.handlers.html

        # wkip debug
        #   if gbWkDebug:
        self.clearRenderHandlers()
        _logger.debug(f"\n   (still in registerRenderHandlers)")

        bpy.app.handlers.render_init.append(handlers.uas_stampinfo_renderInitHandler)  # happens once

        bpy.app.handlers.render_pre.append(handlers.uas_stampinfo_renderPreHandler)  # for every frame

        bpy.app.handlers.render_complete.append(handlers.uas_stampinfo_renderCompleteHandler)  # happens once
        bpy.app.handlers.render_cancel.append(handlers.uas_stampinfo_renderCancelHandler)  # happens once

        _logger.debug(f"\n   registerRenderHandlers ]")

    def handlersRegistered(self):
        from .utils import utils_handlers

        handlersOk = False
        funcInHandler = utils_handlers.getHandlerByFunction(
            handlers.uas_stampinfo_renderInitHandler, handlerCateg=bpy.app.handlers.render_init
        )
        handlersOk = funcInHandler is not None

        return handlersOk
