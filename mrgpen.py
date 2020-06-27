import bpy
from bpy.app import translations
from bpy.app.translations import pgettext as pgt
from random import random
from bpy.props import (
    StringProperty,
    EnumProperty,
    BoolProperty,
    PointerProperty,
    FloatProperty,
)
from bpy.types import PropertyGroup
from mathutils import Vector
from itertools import chain

bl_info = {
    "name": "Mr.GPen",
    "blender": (2, 80, 0),
    "category": "Object",
}

translation_dict = {
    "ja_JP": {
        ("*", "Create New Layer"):
            "新しいレイヤーを作成",
        ("*", "Select Stroke Layer"):
            "ストロークのレイヤーを選択",
        ("*", "Add Stroke Mask"):
            "ストロークのレイヤーをマスク",
        ("*", "Hide Stroke Layer"):
            "ストロークのレイヤーを隠す",
        ("*", "Isolate Stroke Layer"):
            "ストロークのレイヤー以外を表示",
        ("*", "Lock Stroke Layer"):
            "ストロークのレイヤーを固定",
        ("*", "Isolate Lock Stroke Layer"):
            "ストロークのレイヤー以外を固定",
        ("*", "Set Random Tint Stroke"):
            "ストロークの色をランダム化",
        ("*", "Set Random Tint Brush"):
            "ブラシの色をランダム化",
        ("*", "Move Active Layer"):
            "ストロークをアクティブレイヤーに移動",
        ("*", "Select Same Layer Stroke"):
            "選択中のストロークと同じレイヤーのストロークを選択する",
        ("*", "Hide Stroke Material"):
            "ストロークのマテリアルを隠す",
        ("*", "Isolate Stroke Material"):
            "ストロークのマテリアル以外を隠す",
        ("*", "Lock Stroke Material"):
            "ストロークのマテリアルを固定",
        ("*", "Isolate Lock Stroke Material"):
            "ストロークのマテリアル以外を固定",
        ("*", "Deselect All Strokes"):
            "全てのストロークの選択解除",
        ("*", "No Selected Stroke."):
            "ストロークが選択させていません",
        ("*", "Pick Vertex Stroke Color"):
            "ストロークの線の色を取得",
        ("*", "Pick Vertex Fill Color"):
            "ストロークの塗りつぶし色を取得",
        ("*", "Nearest Fill Color Stroke"):
            "塗りつぶし色が近いストローク",
        ("*", "Nearest Stroke Color Stroke"):
            "線の色が近いストローク",
        ("*", "Fade Stroke Edge"):
            "線の端をフェードアウト",
        ("*", "Init Thickness"):
            "線の太さを初期化",
        ("*", "Init Strength"):
            "線の濃さを初期化",
    },
    "en_US": {
        ("*", "Create New Layer"):
            "Create New Layer",
        ("*", "Select Stroke Layer"):
            "Select Stroke Layer",
        ("*", "Add Stroke Mask"):
            "Add Stroke Mask",
        ("*", "Hide Stroke Layer"):
            "Hide Stroke Layer",
        ("*", "Isolate Stroke Layer"):
            "Isolate Stroke Layer",
        ("*", "Lock Stroke Layer"):
            "Lock Stroke Layer",
        ("*", "Isolate Lock Stroke Layer"):
            "Isolate Lock Stroke Layer",
        ("*", "Set Random Tint Stroke"):
            "Set Random Tint Stroke",
        ("*", "Set Random Tint Brush"):
            "Set Random Tint Brush",
        ("*", "Move Active Layer"):
            "Move Active Layer",
        ("*", "Select Same Layer Stroke"):
            "Select Same Layer Stroke",
        ("*", "Hide Stroke Material"):
            "Hide Stroke Material",
        ("*", "Isolate Stroke Material"):
            "Isolate Stroke Material",
        ("*", "Lock Stroke Material"):
            "Lock Stroke Material",
        ("*", "Isolate Lock Stroke Material"):
            "Isolate Lock Stroke Material",
        ("*", "Deselect All Strokes"):
            "Deselect All Strokes",
        ("*", "No Selected Stroke."):
            "No Selected Stroke.",
        ("*", "Pick Vertex Stroke Color"):
            "Pick Vertex Stroke Color",
        ("*", "Pick Vertex Fill Color"):
            "Pick Vertex Fill Color",
        ("*", "Nearest Fill Color Stroke"):
            "Nearest Fill Color Stroke",
        ("*", "Nearest Stroke Color Stroke"):
            "Nearest Stroke Color Stroke",
        ("*", "Fade Stroke Edge"):
            "Fade Stroke Edge",
        ("*", "Init Thickness"):
            "Init Thickness",
        ("*", "Init Strength"):
            "Init Strength",
    },
}

def gen_strokes(layers):
    """全ストロークを返す"""
    yield from (
        {
            "layer": l,
            "frame": f,
            "stroke": s,
        }
        for l in layers
        for f in l.frames
        for s in f.strokes
    )

def gen_points(layers):
    """全ポイントを返す"""
    yield from (
        {
            "point": p,
            **s,
        }
        for s in gen_strokes(layers)
        for p in s["stroke"].points
    )

def gen_selected_points(layers):
    """選択中のポイントを返す"""
    yield from (
        {
            "point": p,
            **s,
        }
        for s in gen_selected_strokes(layers)
        for p in s["stroke"].points
        if p.select
    )

def gen_selected_strokes(layers):
    """選択中のストロークを返す"""
    yield from (
        s
        for s in gen_strokes(layers)
        if s["stroke"].select
    )

def get_selected_layers(layers):
    """選択中のレイヤーを返す"""
    return {x["layer"].info: x["layer"] for x in gen_selected_points(layers)}

def get_curve(name):
    """Node Groupに作成したCurve Nodeを返す"""
    node_name = "MRGPEN_NODE_{}".format(name)

    node_groups = bpy.data.node_groups
    nodes = None
    if node_name in node_groups:
        nodes = node_groups[node_name].nodes
    else:
        nodes = node_groups.new(
            name=node_name,
            type="CompositorNodeTree",
        ).nodes

    node = None
    if len(nodes) <= 0:
        node = nodes.new(type="CompositorNodeCurveRGB")
    else:
        node = nodes[0]

    node.mapping.initialize()

    return node

class MRGPEN_OT_select_layer(bpy.types.Operator):
    """選択中のストロークのレイヤーを選択する"""
    bl_idname = "mrgpen.select_layer"
    bl_label = "Select Stroke Layer"

    def execute(self, context):
        obj = context.active_object
        data = obj.data

        # Grease Pencil
        if not obj and obj.type == "GPENCIL":
            return {'FINISHED'}

        layers = data.layers

        # 先頭1件をアクティブにする
        for x in gen_selected_points(layers):
            layers.active = x["layer"]
            break

        return {'FINISHED'}


class MRGPEN_OT_select_same_layer_stroke(bpy.types.Operator):
    """選択中のストロークと同じレイヤーのストロークを全て選択する"""
    bl_idname = "mrgpen.select_same_layer_stroke"
    bl_label = "Select_Same_Layer_Stroke"

    def execute(self, context):
        obj = context.active_object
        data = obj.data

        # Grease Pencil
        if not obj and obj.type == "GPENCIL":
            return {'FINISHED'}

        layers = data.layers

        for selected_stroke in gen_selected_strokes(layers):
            strokes = (
                s
                for f in selected_stroke['layer'].frames
                for s in f.strokes
            )
            for s in strokes:
                s.select = True

            break

        return {'FINISHED'}


class MRGPEN_OT_toggle_hide(bpy.types.Operator):
    """選択中のストロークのレイヤーの表示・非表示を切り替える"""
    bl_idname = "mrgpen.toggle_hide"
    bl_label = "Hide Stroke Layer"

    def execute(self, context):
        obj = context.active_object
        data = obj.data

        # Grease Pencil
        if not obj and obj.type == "GPENCIL":
            return {'FINISHED'}

        layers = data.layers
        active_layers = get_selected_layers(layers).values()

        r = all(x.hide for x in active_layers)
        for x in active_layers:
            x.hide = not r

        return {'FINISHED'}


class MRGPEN_OT_toggle_hide_other(bpy.types.Operator):
    """選択中のストロークのレイヤー以外の表示・非表示を切り替える"""
    bl_idname = "mrgpen.toggle_hide_other"
    bl_label = "Isolate Stroke Layer"

    def execute(self, context):
        obj = context.active_object
        data = obj.data

        # Grease Pencil
        if not obj and obj.type == "GPENCIL":
            return {'FINISHED'}

        layers = data.layers
        active_layers = get_selected_layers(layers)

        other_layers = [x for x in layers if x.info not in active_layers]
        r = all(x.hide for x in other_layers)
        for x in other_layers:
            x.hide = not r

        return {'FINISHED'}


class MRGPEN_OT_toggle_lock(bpy.types.Operator):
    """選択中のストロークのレイヤーのロック・アンロックを切り替える"""
    bl_idname = "mrgpen.toggle_lock"
    bl_label = "Lock Stroke Layer"

    def execute(self, context):
        obj = context.active_object
        data = obj.data

        # Grease Pencil
        if not obj and obj.type == "GPENCIL":
            return {'FINISHED'}

        layers = data.layers
        active_layers = get_selected_layers(layers).values()

        r = all(x.lock for x in active_layers)
        for x in active_layers:
            x.lock = not r

        return {'FINISHED'}


class MRGPEN_OT_toggle_lock_other(bpy.types.Operator):
    """選択中のストロークのレイヤー以外のロック・アンロックを切り替える"""
    bl_idname = "mrgpen.toggle_lock_other"
    bl_label = "Isolate Lock Stroke Layer"

    def execute(self, context):
        obj = context.active_object
        data = obj.data

        # Grease Pencil
        if not obj and obj.type == "GPENCIL":
            return {'FINISHED'}

        layers = data.layers
        active_layers = get_selected_layers(layers)

        other_layers = [x for x in layers if x.info not in active_layers]
        r = all(x.lock for x in other_layers)
        for x in other_layers:
            x.lock = not r

        return {'FINISHED'}


class MRGPEN_OT_toggle_hide_material(bpy.types.Operator):
    """選択中のストロークのマテリアルの表示・非表示を切り替える"""
    bl_idname = "mrgpen.toggle_hide_material"
    bl_label = "Hide Stroke Material"

    def execute(self, context):
        obj = context.active_object
        data = obj.data

        # Grease Pencil
        if not obj and obj.type == "GPENCIL":
            return {'FINISHED'}

        layers = data.layers
        selected_stroke_list = [x["stroke"] for x in gen_selected_strokes(layers)]
        selected_material_index_list = list({x.material_index for x in selected_stroke_list})

        material_slots = obj.material_slots

        selected_stroke_material_list = [material_slots[x] for x in selected_material_index_list]

        r = all(x.material.grease_pencil.hide for x in selected_stroke_material_list)
        for x in selected_stroke_material_list:
            x.material.grease_pencil.hide = not r

        return {'FINISHED'}


class MRGPEN_OT_toggle_hide_material_other(bpy.types.Operator):
    """選択中じゃないストロークのマテリアルの表示・非表示を切り替える"""
    bl_idname = "mrgpen.toggle_hide_material_other"
    bl_label = "Isolate Stroke Material"

    def execute(self, context):
        obj = context.active_object
        data = obj.data

        # Grease Pencil
        if not obj and obj.type == "GPENCIL":
            return {'FINISHED'}

        layers = data.layers
        selected_stroke_list = [x["stroke"] for x in gen_selected_strokes(layers)]
        selected_material_index_sets = {x.material_index for x in selected_stroke_list}

        material_slots = obj.material_slots

        selected_stroke_material_list = [material_slots[x] for x in list(selected_material_index_sets)]
        other_stroke_material_list = [
            y
            for y in (
                x
                for i, x in enumerate(material_slots)
                if i not in selected_material_index_sets
            )
            if hasattr(y.material, 'grease_pencil')
            and y.material.grease_pencil
        ]

        r = all(x.material.grease_pencil.hide for x in other_stroke_material_list)
        for x in other_stroke_material_list:
            x.material.grease_pencil.hide = not r

        return {'FINISHED'}


class MRGPEN_OT_toggle_lock_material(bpy.types.Operator):
    """選択中のストロークのマテリアルの固定・非固定を切り替える"""
    bl_idname = "mrgpen.toggle_lock_material"
    bl_label = "Lock Stroke Material"

    def execute(self, context):
        obj = context.active_object
        data = obj.data

        # Grease Pencil
        if not obj and obj.type == "GPENCIL":
            return {'FINISHED'}

        layers = data.layers
        selected_stroke_list = [x["stroke"] for x in gen_selected_strokes(layers)]
        selected_material_index_list = list({x.material_index for x in selected_stroke_list})

        material_slots = obj.material_slots

        selected_stroke_material_list = [material_slots[x] for x in selected_material_index_list]

        r = all(x.material.grease_pencil.lock for x in selected_stroke_material_list)
        for x in selected_stroke_material_list:
            x.material.grease_pencil.lock = not r

        return {'FINISHED'}


class MRGPEN_OT_toggle_lock_material_other(bpy.types.Operator):
    """選択中じゃないストロークのマテリアルの固定・非固定を切り替える"""
    bl_idname = "mrgpen.toggle_lock_material_other"
    bl_label = "Isolate Lock Stroke Material"

    def execute(self, context):
        obj = context.active_object
        data = obj.data

        # Grease Pencil
        if not obj and obj.type == "GPENCIL":
            return {'FINISHED'}

        layers = data.layers
        selected_stroke_list = [x["stroke"] for x in gen_selected_strokes(layers)]
        selected_material_index_sets = {x.material_index for x in selected_stroke_list}

        material_slots = obj.material_slots

        selected_stroke_material_list = [material_slots[x] for x in list(selected_material_index_sets)]
        other_stroke_material_list = [
            y
            for y in (
                x
                for i, x in enumerate(material_slots)
                if i not in selected_material_index_sets
            )
            if hasattr(y.material, 'grease_pencil')
            and y.material.grease_pencil
        ]

        r = all(x.material.grease_pencil.lock for x in other_stroke_material_list)
        for x in other_stroke_material_list:
            x.material.grease_pencil.lock = not r

        return {'FINISHED'}


class MRGPEN_OT_move_active_layer(bpy.types.Operator):
    """選択中のストロークをアクティブレイヤーに移動する"""
    bl_idname = "mrgpen.move_active_layer"
    bl_label = "Move Active Layer"

    def execute(self, context):
        obj = context.active_object
        data = obj.data

        # Grease Pencil
        if not obj and obj.type == "GPENCIL":
            return {'FINISHED'}

        bpy.ops.gpencil.move_to_layer(layer=data.layers.active_index)

        return {'FINISHED'}


class MRGPEN_OT_mask_layer(bpy.types.Operator):
    """アクティブレイヤーのマスクに選択中のストロークのレイヤーを追加する"""
    bl_idname = "mrgpen.mask_layer"
    bl_label = "Add Stroke Mask"

    def execute(self, context):
        obj = context.active_object
        data = obj.data

        # Grease Pencil
        if not obj and obj.type == "GPENCIL":
            return {'FINISHED'}

        layers = data.layers

        # マスクを有効化
        layers.active.use_mask_layer = True

        # 選択中のストロークのレイヤーを全てマスクに追加
        for x in get_selected_layers(layers).values():
            layers.active.mask_layers.add(x)

        return {'FINISHED'}


class MRGPEN_OT_create_layer(bpy.types.Operator):
    """アクティブレイヤーの名前で新規レイヤーを生成する"""
    bl_idname = "mrgpen.create_layer"
    bl_label = "Add New Layer"

    def execute(self, context):
        obj = context.active_object
        data = obj.data

        # Grease Pencil
        if not obj and obj.type == "GPENCIL":
            return {'FINISHED'}

        layers = data.layers

        # アクティブレイヤーの名前を取得
        note = layers.active_note
        layers.new(name=note)

        return {'FINISHED'}


class MRGPEN_OT_set_random_tint_color(bpy.types.Operator):
    """アクティブレイヤーにランダムな色を設定する"""
    bl_idname = "mrgpen.set_random_tint_color"
    bl_label = "Set Random Tint Stroke"

    def execute(self, context):
        obj = context.active_object
        data = obj.data

        # Grease Pencil
        if not obj and obj.type == "GPENCIL":
            return {'FINISHED'}

        layers = data.layers

        vertex_color_fill = (random(), random(), random(), 1)
        vertex_color = (random(), random(), random(), 1)
        for x in gen_selected_strokes(layers):
            x["stroke"].vertex_color_fill = vertex_color_fill

            for y in x["stroke"].points:
                y.vertex_color = vertex_color

        return {'FINISHED'}


class MRGPEN_OT_set_random_tint_color_brush(bpy.types.Operator):
    """ブラシにランダムな色を設定する"""
    bl_idname = "mrgpen.set_random_tint_color_brush"
    bl_label = "Set Random Tint Brush"

    def execute(self, context):
        obj = context.active_object
        data = obj.data

        # Grease Pencil
        if not obj and obj.type == "GPENCIL":
            return {'FINISHED'}

        layers = data.layers

        vertex_color = (random(), random(), random())

        bpy.context.tool_settings.gpencil_paint.brush.color = vertex_color

        return {'FINISHED'}


class MRGPEN_OT_pick_vertex_color(bpy.types.Operator):
    """選択中のストロークの色をブラシに設定する"""
    bl_idname = "mrgpen.pick_vertex_color"
    bl_label = "Pick Vertex Color"

    type: EnumProperty(
        name="",
        default="FILL",
        items=[
            ("STROKE", "Stroke", ""),
            ("FILL", "Fill", ""),
        ],
    )

    def execute(self, context):
        obj = context.active_object
        data = obj.data

        # Grease Pencil
        if not obj and obj.type == "GPENCIL":
            return {'FINISHED'}

        layers = data.layers

        vertex_color = None
        for x in gen_selected_strokes(layers):
            stroke = x["stroke"]

            if self.type == "FILL":
                vertex_color = stroke.vertex_color_fill[:3]

            elif self.type == "STROKE":
                for y in stroke.points:
                    vertex_color = y.vertex_color[:3]
                    break
            break

        if vertex_color:
            bpy.context.tool_settings.gpencil_paint.brush.color = vertex_color

        return {'FINISHED'}


class MRGPEN_OT_deselect_all_strokes(bpy.types.Operator):
    """非表示・固定も含めた全てのストロークの選択を解除する"""
    bl_idname = "mrgpen.deselect_all_strokes"
    bl_label = "Deselect All Strokes"

    def execute(self, context):
        obj = context.active_object
        data = obj.data

        # Grease Pencil
        if not obj and obj.type == "GPENCIL":
            return {'FINISHED'}

        layers = data.layers

        # 選択中レイヤーを非選択にする
        for x in gen_selected_strokes(layers):
            x["stroke"].select = False

        return {'FINISHED'}


class MRGPEN_OT_select_nearest_color(bpy.types.Operator):
    """選択中のストロークと近い頂点色のストロークを選択する"""
    bl_idname = "mrgpen.select_nearest_color"
    bl_label = "Select Nearest Color"
    bl_options = {"REGISTER", "UNDO"}

    target: EnumProperty(
        default="FILL",
        items=[
            ("STROKE", "Stroke", ""),
            ("FILL", "Fill", ""),
        ],
    )
    type: EnumProperty(
        default="SELECT",
        items=[
            ("SELECT", "Select", ""),
            ("DESELECT", "Deselect", ""),
        ],
    )
    threshold: FloatProperty(default=.01,)

    def execute(self, context):
        obj = context.active_object
        data = obj.data

        # Grease Pencil
        if not obj and obj.type == "GPENCIL":
            return {'FINISHED'}

        layers = data.layers

        # 全ストロークと、選択中のストロークの色を取得
        targets = None
        selected_colors = None
        if self.target == "FILL":
            # 塗りつぶし
            targets = ((x["stroke"], x["stroke"].vertex_color_fill) for x in gen_strokes(layers))
            selected_colors = (x["stroke"].vertex_color_fill for x in gen_selected_strokes(layers))
        else:
            # 線
            targets = ((x["point"], x["point"].vertex_color) for x in gen_points(layers))
            selected_colors = (x["point"].vertex_color for x in gen_selected_points(layers))

        # 各色をベクトルに変換する
        targets = ((t, Vector(x)) for t, x in targets)
        selected_colors = tuple(Vector(y) for y in {tuple(x) for x in selected_colors})

        # しきい値より近い色だけを取得
        threshold = self.threshold
        nearest_color_targets = (
            target
            for target, color in targets
            for selected_color in selected_colors
            if (color - selected_color).length / 2 <= threshold
        )

        # 選択したストロークを選択・非選択状態にする
        is_type = self.type == "SELECT"
        for target in nearest_color_targets:
            target.select = is_type

        return {'FINISHED'}


class MRGPEN_OT_fade_stroke_edge(bpy.types.Operator):
    """選択中のストロークに入り抜きを設定する"""
    bl_idname = "mrgpen.fade_stroke_edge"
    bl_label = "Fade Stroke Edge"
    bl_options = {"REGISTER", "UNDO"}

    is_presure: BoolProperty(name="Pressure", default=True)
    is_strength: BoolProperty(name="Strength", default=False)

    is_start: BoolProperty(name="Start", default=True,)
    is_end: BoolProperty(name="End", default=True,)

    is_init_thickness: BoolProperty(name="Init Thickness", default=False,)
    thickness: FloatProperty(name="Thickness", default=3,)

    is_init_strength: BoolProperty(name="Init Strength", default=False,)
    strength: FloatProperty(name="Strength", default=1,)

    length: FloatProperty(name="Length", default=.1,)

    def execute(self, context):
        obj = context.active_object
        data = obj.data

        # Grease Pencil
        if not obj and obj.type == "GPENCIL":
            return {'FINISHED'}

        layers = data.layers
        length = self.length

        # 線の太さを初期化
        if self.is_init_thickness:
            thickness = self.thickness
            for x in gen_selected_points(layers):
                x["point"].pressure = thickness

        # 線の濃さを初期化
        if self.is_init_thickness:
            strength = self.strength
            for x in gen_selected_points(layers):
                x["point"].strength = strength

        curve_node = get_curve("ENTRY_AND_EXIT");
        mapping = curve_node.mapping
        if len(mapping.curves) <= 0:
            return {"FINISHED"}
        curve = mapping.curves[-1]

        def get_points(is_reverse=False):
            """ポイントと距離を返す"""
            points_list = (list(x["stroke"].points) for x in gen_selected_strokes(layers))

            if is_reverse:
                # 逆順
                points_list = (x[::-1] for x in points_list)

            for points in points_list:
                pair_points = zip(points[:1] + points, points)

                s = 0
                for a, b in pair_points:
                    s += (a.co - b.co).length

                    if s > length:
                        break

                    yield b, mapping.evaluate(curve, s / length)

        # 設定対象のポイントを取得
        gen_points = []
        if self.is_start:
            # 始点から
            gen_points = chain(gen_points, get_points(False))

        if self.is_end:
            # 終点から
            gen_points = chain(gen_points, get_points(True))

        # 太さ、濃さを設定
        is_presure = self.is_presure
        is_strength = self.is_strength
        for point, value in gen_points:
            if is_presure:
                point.pressure = point.pressure * value
            if is_strength:
                point.strength = point.strength * value

        return {'FINISHED'}


class MRGPEN_PT_view_3d_label(bpy.types.Panel):
    """3D画面横のパネルのUI"""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Edit"
    bl_label = "Mr.GPen"

    def draw(self, context):
        layout = self.layout

        mode = context.mode
        wm = context.window_manager.mrgpen

        o = layout.operator
        layers = context.active_object.data.layers

        is_selected = False
        layer = None
        stroke = None
        point = None
        for x in gen_selected_points(layers):
            layer = x["layer"];
            stroke = x["stroke"];
            point = x["point"];
            is_selected = True
            break

        # 特定のモードかどうか
        is_editable = mode in {"EDIT_GPENCIL", "SCULPT_GPENCIL"}
        is_paintable = mode in {"PAINT_GPENCIL",}

        # レイヤー関係の機能
        if layout.active:
            layout.prop(layers.active, "info", text="Active")

        if is_selected and is_editable:
            layout.prop(layer, "info", text="Stroke")

        def submenu(layout, name, text):
            """開閉メニューを生成"""
            is_collapse = getattr(wm, name)
            r = layout.row()
            r.alignment = "LEFT"
            r.prop(
                wm,
                name,
                icon="TRIA_DOWN" if is_collapse else "TRIA_RIGHT",
                text=text,
                emboss=False,
            )

            return is_collapse

        box = layout.box()
        if submenu(box, "is_collapse_layer", "Layer"):
            box.operator(MRGPEN_OT_create_layer.bl_idname,
                text=pgt("Add New Layer"))
            if is_editable and is_selected:
                box.operator(MRGPEN_OT_move_active_layer.bl_idname,
                    text=pgt("Move Active Layer"))

        # 選択関係の機能
        if is_editable and is_selected:
            box = layout.box()
            if submenu(box, "is_collapse_select", "Select"):
                bo = box.operator
                bo(MRGPEN_OT_select_layer.bl_idname,
                    text=pgt("Select Stroke Layer"))
                bo(MRGPEN_OT_select_same_layer_stroke.bl_idname, text=pgt("Select Same Layer Stroke"))
                bo(MRGPEN_OT_deselect_all_strokes.bl_idname,
                    text=pgt("Deselect All Strokes"))

                # 頂点色を使った選択
                box.separator()
                box.label(text=pgt("Nearest Fill Color Stroke"))
                row = box.row(align=True)
                snc_sf = row.operator(MRGPEN_OT_select_nearest_color.bl_idname,
                    text=pgt("Select"))
                snc_sf.type = "SELECT"
                snc_sf.target = "FILL"
                snc_sf.threshold = wm.color_threshold

                snc_df = row.operator(MRGPEN_OT_select_nearest_color.bl_idname,
                    text=pgt("Deselect"))
                snc_df.type = "DESELECT"
                snc_df.target = "FILL"
                snc_df.threshold = wm.color_threshold

                box.label(text=pgt("Nearest Stroke Color Stroke"))
                row = box.row(align=True)
                snc_ss = row.operator(MRGPEN_OT_select_nearest_color.bl_idname,
                    text=pgt("Select"))
                snc_ss.type = "SELECT"
                snc_ss.target = "STROKE"
                snc_ss.threshold = wm.color_threshold

                snc_ds = row.operator(MRGPEN_OT_select_nearest_color.bl_idname,
                    text=pgt("Deselect"))
                snc_ds.type = "DESELECT"
                snc_ds.target = "STROKE"
                snc_ds.threshold = wm.color_threshold

                box.prop(wm, "color_threshold", text="Threshold")
                box.separator()

        # ストロークのレイヤー関係の機能
        if is_editable and is_selected:
            box = layout.box()
            if submenu(box, "is_collapse_stroke_layer", "Stroke Layer"):
                bo = box.operator
                bo(MRGPEN_OT_toggle_hide.bl_idname,
                    text=pgt("Hide Stroke Layer"))
                bo(MRGPEN_OT_toggle_hide_other.bl_idname,
                    text=pgt("Isolate Stroke Layer"))
                bo(MRGPEN_OT_toggle_lock.bl_idname,
                    text=pgt("Lock Stroke Layer"))
                bo(MRGPEN_OT_toggle_lock_other.bl_idname,
                    text=pgt("Isolate Lock Stroke Layer"))

        # ストロークのマテリアル関係の機能
        if is_editable and is_selected:
            box = layout.box()
            if submenu(box, "is_collapse_stroke_material", "Stroke Material"):
                bo = box.operator
                bo(MRGPEN_OT_toggle_hide_material.bl_idname,
                    text=pgt("Hide Stroke Material"))
                bo(MRGPEN_OT_toggle_hide_material_other.bl_idname,
                    text=pgt("Isolate Stroke Material"))
                bo(MRGPEN_OT_toggle_lock_material.bl_idname,
                    text=pgt("Lock Stroke Material"))
                bo(MRGPEN_OT_toggle_lock_material_other.bl_idname,
                    text=pgt("Isolate Lock Stroke Material"))

        # 頂点色関係の機能
        if (is_editable and is_selected) or is_paintable:
            box = layout.box()
            if submenu(box, "is_collapse_vertex_color", "Vertex Color"):
                bo = box.operator

                box.prop(bpy.context.tool_settings.gpencil_paint.brush, "color", text="Brush Color")

                # 選択中のストロークの頂点色を表示
                if is_selected:
                    box.prop(point, "vertex_color")
                    box.prop(stroke, "vertex_color_fill")

                    pick_vertex_color = bo(MRGPEN_OT_pick_vertex_color.bl_idname,
                        text=pgt("Pick Vertex Stroke Color"),
                        )
                    pick_vertex_color.type = "STROKE"

                    pick_vertex_color = bo(MRGPEN_OT_pick_vertex_color.bl_idname,
                        text=pgt("Pick Vertex Fill Color"),
                        )
                    pick_vertex_color.type = "FILL"

                    bo(MRGPEN_OT_set_random_tint_color.bl_idname,
                        text=pgt("Set Random Tint Stroke"))

                bo(MRGPEN_OT_set_random_tint_color_brush.bl_idname,
                    text=pgt("Set Random Tint Brush"))

        # その他の機能
        if is_editable and is_selected:
            box = layout.box()
            if submenu(box, "is_collapse_other", "Other"):
                bo = box.operator

                bo(MRGPEN_OT_mask_layer.bl_idname,
                    text=pgt("Add Stroke Mask"))

                bo(MRGPEN_OT_fade_stroke_edge.bl_idname,
                    text=pgt("Fade Stroke Edge"))
                curve_entry_and_exit = get_curve("ENTRY_AND_EXIT")
                box.template_curve_mapping(curve_entry_and_exit, 'mapping')

        if is_editable and not is_selected:
            layout.label(text=pgt("No Selected Stroke."))

    @classmethod
    def poll(self, context):
        o = context.active_object
        return (o and o.type == "GPENCIL")

class MRGPEN_WindowManager(PropertyGroup):
    is_collapse_layer: BoolProperty(default=True)
    is_collapse_select: BoolProperty(default=True)
    is_collapse_stroke_layer: BoolProperty(default=True)
    is_collapse_stroke_material: BoolProperty(default=True)
    is_collapse_vertex_color: BoolProperty(default=True)
    is_collapse_other: BoolProperty(default=True)
    color_threshold: FloatProperty(default=.01)


classes = [
    MRGPEN_OT_select_layer,
    MRGPEN_OT_mask_layer,
    MRGPEN_OT_create_layer,
    MRGPEN_OT_toggle_hide,
    MRGPEN_OT_toggle_hide_other,
    MRGPEN_OT_toggle_lock,
    MRGPEN_OT_toggle_lock_other,
    MRGPEN_OT_move_active_layer,
    MRGPEN_OT_set_random_tint_color,
    MRGPEN_OT_set_random_tint_color_brush,
    MRGPEN_PT_view_3d_label,
    MRGPEN_OT_select_same_layer_stroke,
    MRGPEN_OT_toggle_hide_material,
    MRGPEN_OT_toggle_hide_material_other,
    MRGPEN_OT_toggle_lock_material,
    MRGPEN_OT_toggle_lock_material_other,
    MRGPEN_OT_deselect_all_strokes,
    MRGPEN_OT_pick_vertex_color,
    MRGPEN_WindowManager,
    MRGPEN_OT_select_nearest_color,
    MRGPEN_OT_fade_stroke_edge,
]

def register():
    for x in classes:
        bpy.utils.register_class(x)

    translations.register(__name__, translation_dict)
    bpy.types.WindowManager.mrgpen = PointerProperty(type=MRGPEN_WindowManager)


def unregister():
    translations.unregister(__name__)

    for x in classes:
        bpy.utils.unregister_class(x)

    del bpy.types.WindowManager.mrgpen

if __name__ == "__main__":
    register()
