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
    IntProperty,
)
from bpy.types import PropertyGroup
from math import radians
from mathutils import Vector, Quaternion
from itertools import chain, zip_longest
import numpy as np
import re

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
        ("*", "Fat Stroke"):
            "ストロークを二重にする",
        ("*", "Add New Layer and Mask"):
            "レイヤーを追加してストロークのレイヤーでマスク",
        ("*", "Rename Layers"):
            "複数のレイヤーの名前を変更",
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
        ("*", "Fat Stroke"):
            "Fat Stroke",
        ("*", "Add New Layer and Mask"):
            "Add New Layer and Mask",
        ("*", "Rename Layers"):
            "Rename Layers",
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

def gen_selected_layers(layers):
    """選択中のストロークのレイヤーを返す"""
    for l in layers:
        for s in (s for f in l.frames for s in f.strokes if s.select):
            yield l
            break

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

def rgb_to_srgb(rgb):
    """RGBからsRGBに変換する"""
    return [
        v * 12.92 if v <= 0.0031309 else (v ** (1.0 / 2.4)) * 1.055 - 0.055
        for v in list(rgb)[:3]
    ]

def srgb_to_rgb(srgb):
    """sRGBからRGBに変換する"""
    return [
        v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
        for v in list(srgb)[:3]
    ]

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
            bpy.context.tool_settings.gpencil_paint.brush.color = rgb_to_srgb(vertex_color)

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


class MRGPEN_OT_fat_stroke(bpy.types.Operator):
    """ストロークを二重にする"""
    bl_idname = "mrgpen.fat_stroke"
    bl_label = "Fat Stroke"
    bl_options = {"REGISTER", "UNDO"}

    width: FloatProperty(name="Length", default=.1,)
    position: FloatProperty(name="Position", default=0,)
    is_keep_stroke: BoolProperty(name="Keep Stroke", default=False,)

    is_merge_stroke: BoolProperty(name="Merge", default=False,)

    is_stroke: BoolProperty(name="Stroke", default=True,)
    is_material: BoolProperty(name="Stroke Material", default=False,)
    material_index: IntProperty(name="Stroke Material Index", default=0,)
    stroke_vertex_color: EnumProperty(
        name="Stroke Vertex Color",
        default="NONE",
        items=[
            ("NONE", "None", ""),
            ("COLOR", "Color", ""),
            ("SECONDARY_COLOR", "Secondary Color", ""),
        ],
    )
    stroke_vertex_color_fill: EnumProperty(
        name="Stroke Vertex Color Fill",
        default="NONE",
        items=[
            ("NONE", "None", ""),
            ("COLOR", "Color", ""),
            ("SECONDARY_COLOR", "Secondary Color", ""),
        ],
    )

    is_fill: BoolProperty(name="Fill", default=False,)
    is_material_fill: BoolProperty(name="Fill Material", default=False,)
    material_index_fill: IntProperty(name="Fill Material Index", default=0,)
    fill_vertex_color: EnumProperty(
        name="Fill Vertex Color",
        default="NONE",
        items=[
            ("NONE", "None", ""),
            ("COLOR", "Color", ""),
            ("SECONDARY_COLOR", "Secondary Color", ""),
        ],
    )

    def execute(self, context):
        obj = context.active_object
        data = obj.data

        # Grease Pencil
        if not obj and obj.type == "GPENCIL":
            return {'FINISHED'}

        # ビューポートの情報を取得
        spaces = [x for x in context.area.spaces if x.type == "VIEW_3D"]
        if len(spaces) <= 0:
            return {"FINISHED"}

        view_matrix = spaces[0].region_3d.view_matrix
        matrix_world = obj.matrix_world

        matrix = view_matrix @ matrix_world
        matrix_inverted = view_matrix.inverted() @ matrix_world.inverted()

        layers = data.layers
        width = self.width
        position = self.position

        # カーブ情報を取得
        curve_node = get_curve("FAT_STROKE");
        mapping = curve_node.mapping
        if len(mapping.curves) <= 0:
            return {"FINISHED"}
        curve = mapping.curves[-1]

        # 選択中のストローク全て処理する
        for x in gen_selected_strokes(layers):
            # フレームとストロークの情報を取得
            frame = x["frame"]
            stroke = x["stroke"]

            def gp():
                """ポイント, ビューポート上の位置, 始点からの距離のリストを生成"""
                stroke_points = list(stroke.points)

                sum_length = 0
                for x, y in zip(stroke_points, (stroke_points[:1] + stroke_points)):
                    sum_length += (x.co - y.co).length

                    yield {
                        "point": x,
                        "viewport_co": matrix @ x.co,
                        "length": sum_length,
                    }

            points = list(gp())

            # 最小二乗法でストロークの向きを取得
            x, y = np.vstack([
                (co.x, co.y)
                for co in (
                    p["viewport_co"]
                    for p in points
                )
            ]).T
            A = np.vstack([x, np.full_like(x, 1)]).T
            m, c = np.linalg.lstsq(A, y, rcond=False)[0]
            a = Vector([1, m + c, 0])
            a = a.normalized()

            def g(r):
                """ストロークの位置をずらしたリストを生成する"""

                # 線を増やす方向を決定
                width_vector = a.copy()
                quate = Quaternion([0, 0, 1], radians(r))
                width_vector.rotate(quate)

                # 位置をずらすための絶対位置のベクターも生成
                width_vector_abs = a.copy()
                quate_abs = Quaternion([0, 0, 1], radians(abs(r)))
                width_vector_abs.rotate(quate_abs)

                # ストロークの長さを取得
                length_points = max(point["length"] for point in points)

                for point in points:
                    # 幅を取得
                    w = width * mapping.evaluate(curve, point["length"] / length_points)

                    # 位置を取得
                    pos = position * mapping.evaluate(curve, point["length"] / length_points)

                    # 線の位置を増やす方向に移動してローカル座標に戻す
                    co = point["viewport_co"] + width_vector * w + width_vector_abs * pos
                    co = matrix_inverted @ co

                    yield {
                        **point,
                        "co": co,
                    }

            # 左右のストローク位置を生成
            from_points1 = list(g(-90))
            from_points2 = list(g(90))[::-1]

            if self.is_merge_stroke:
                from_points_list = ((from_points1 + from_points2),)
            else:
                from_points_list = (from_points1, from_points2)

            # オブジェクトのマテリアルの数を取得
            material_length = len(data.materials) - 1

            # ブラシ情報を取得
            brush = bpy.context.tool_settings.gpencil_paint.brush

            # 位置をもとにFillのみのストロークを生成
            if self.is_fill:
                is_material = self.is_material_fill
                material_index = self.material_index_fill
                material_index = max(0, min(material_index, material_length))

                # 設定する色を選択
                vertex_color_fill = None
                if self.fill_vertex_color == "COLOR":
                    vertex_color_fill = srgb_to_rgb(brush.color) + [1]
                elif self.fill_vertex_color == "SECONDARY_COLOR":
                    vertex_color_fill = srgb_to_rgb(brush.secondary_color) + [1]

                for from_points in (from_points1 + from_points2,):
                    # ストロークを生成
                    s = frame.strokes.new()
                    s.vertex_color_fill = vertex_color_fill or stroke.vertex_color_fill

                    if is_material:
                        s.material_index = material_index
                    else:
                        s.material_index = stroke.material_index

                    # ポイントを生成
                    s.points.add(len(from_points))
                    for to_point, from_point in zip(s.points, from_points):
                        to_point.co = from_point["co"]

            # 位置をもとにストロークを生成
            if self.is_stroke:
                is_material = self.is_material
                material_index = self.material_index
                material_index = max(0, min(material_index, material_length))

                # 設定する色を選択
                vertex_color = None
                if self.stroke_vertex_color == "COLOR":
                    vertex_color = srgb_to_rgb(brush.color) + [1]
                elif self.stroke_vertex_color == "SECONDARY_COLOR":
                    vertex_color = srgb_to_rgb(brush.secondary_color) + [1]

                vertex_color_fill = None
                if self.stroke_vertex_color_fill == "COLOR":
                    vertex_color_fill = srgb_to_rgb(brush.color) + [1]
                elif self.stroke_vertex_color_fill == "SECONDARY_COLOR":
                    vertex_color_fill = srgb_to_rgb(brush.secondary_color) + [1]

                for from_points in from_points_list:
                    # ストロークを生成
                    s = frame.strokes.new()
                    s.line_width = stroke.line_width
                    s.vertex_color_fill = stroke.vertex_color_fill

                    if is_material:
                        s.material_index = material_index
                    else:
                        s.material_index = stroke.material_index

                    # ポイントを生成
                    s.points.add(len(from_points))
                    for to_point, from_point in zip(s.points, from_points):
                        to_point.co = from_point["co"]
                        p = from_point["point"]

                        # 濃さ、太さ、色をコピー
                        to_point.pressure = p.pressure
                        to_point.strength = p.strength
                        to_point.vertex_color = vertex_color or p.vertex_color

            if not self.is_keep_stroke:
                # 元のストロークを消す
                frame.strokes.remove(stroke)

        return {'FINISHED'}


class MRGPEN_OT_add_new_layer_and_mask(bpy.types.Operator):
    """新規レイヤーを追加して、選択中のストロークのレイヤーでマスクする"""
    bl_idname = "mrgpen.add_new_layer_and_mask"
    bl_label = "Add New Layer and Mask"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object
        data = obj.data

        # Grease Pencil
        if not obj and obj.type == "GPENCIL":
            return {'FINISHED'}

        # 選択中のストロークがなければ何もしない
        for _ in gen_selected_strokes(data.layers):
            break
        else:
            return {'FINISHED'}

        # 選択中のストロークのレイヤーをアクティブにして新規レイヤーを作成してマスクする
        mrgpen = bpy.ops.mrgpen
        mrgpen.select_layer()
        mrgpen.create_layer()
        mrgpen.mask_layer()

        return {'FINISHED'}


class MRGPEN_OT_rename_layers(bpy.types.Operator):
    """レイヤーを一括でリネームする"""
    bl_idname = "mrgpen.rename_layers"
    bl_label = "Rename Layers"
    bl_options = {"REGISTER", "UNDO"}

    target: EnumProperty(
        name="Target",
        default="STROKE",
        items=[
            ("STROKE", "Stroke", ""),
            ("UNLOCKED", "Unlocked", ""),
            ("VISIBLE", "Visible", ""),
        ],
    )
    type: EnumProperty(
        name="Type",
        default="NEW",
        items=[
            ("NEW", "New", ""),
            ("PREFIX", "Prefix", ""),
            ("SUFFIX", "Suffix", ""),
            ("REPLACE", "Replace", ""),
        ],
    )
    new_name: StringProperty(name="New Name", default="new_name")
    find: StringProperty(name="Find", default=".*")
    is_remove_digits: BoolProperty(name="Digits", default=True)

    def execute(self, context):
        obj = context.active_object
        data = obj.data

        # Grease Pencil
        if not obj and obj.type == "GPENCIL":
            return {'FINISHED'}

        # 選択中のストロークがなければ何もしない
        for _ in gen_selected_strokes(data.layers):
            break
        else:
            return {'FINISHED'}

        target_layers = None
        layers = data.layers
        target = self.target
        if target == "UNLOCKED":
            target_layers = (l for l in layers if not l.lock)
        elif target == "VISIBLE":
            target_layers = (l for l in layers if not l.hide)
        elif target == "STROKE":
            target_layers = gen_selected_layers(layers)

        target_layers_pair = None
        if self.is_remove_digits:
            re_sub = re.compile(r"\.\d+$").sub
            target_layers_pair = ((x, re_sub("", x.info)) for x in target_layers)
        else:
            target_layers_pair = ((x, x.info) for x in target_layers)

        t = self.type
        new_name = self.new_name
        if t == "NEW":
            target_layers_pair = ((x, new_name) for x, name in target_layers_pair)
        elif t == "PREFIX":
            target_layers_pair = ((x, new_name + name) for x, name in target_layers_pair)
        elif t == "SUFFIX":
            target_layers_pair = ((x, name + new_name) for x, name in target_layers_pair)
        elif t == "REPLACE":
            try:
                re_sub = re.compile(self.find).sub
            except:
                return {"FINISHED"}

            target_layers_pair = ((x, re_sub(new_name, name)) for x, name in target_layers)

        for l, name in target_layers_pair:
            l.info = name

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
        is_editable = mode in {"EDIT_GPENCIL", "SCULPT_GPENCIL", "VERTEX_GPENCIL"}
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

                box.operator(MRGPEN_OT_add_new_layer_and_mask.bl_idname,
                    text=pgt("Add New Layer and Mask"))

            box.operator(MRGPEN_OT_rename_layers.bl_idname,
                text=pgt(MRGPEN_OT_rename_layers.bl_label))

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

                brush = bpy.context.tool_settings.gpencil_paint.brush
                box.label(text="Brush Color")
                row = box.row(align=True)
                row.prop(brush, "color", text="")
                row.prop(brush, "secondary_color", text="")

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

                bo(MRGPEN_OT_fat_stroke.bl_idname,
                    text=pgt("Fat Stroke"))
                fat_stroke_curve = get_curve("FAT_STROKE")
                box.template_curve_mapping(fat_stroke_curve, 'mapping')

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
    MRGPEN_OT_fat_stroke,
    MRGPEN_OT_add_new_layer_and_mask,
    MRGPEN_OT_rename_layers,
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
