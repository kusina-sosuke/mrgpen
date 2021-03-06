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
    FloatVectorProperty,
    IntProperty,
    CollectionProperty,
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
        ("*", "Remove Stroke Mask"):
            "ストロークのレイヤーをマスクを削除",
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
        ("*", "Move New Layer"):
            "ストロークを新しいレイヤーに移動する",
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
        ("*", "Rotate Points"):
            "点の位置を循環",
    },
    "en_US": {
        ("*", "Create New Layer"):
            "Create New Layer",
        ("*", "Select Stroke Layer"):
            "Select Stroke Layer",
        ("*", "Add Stroke Mask"):
            "Add Stroke Mask",
        ("*", "Remove Stroke Mask"):
            "Remove Stroke Mask",
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
        ("*", "Move New Layer"):
            "Move New Layer",
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
        ("*", "Rotate Points"):
            "Rotate Points",
    },
}

def gen_strokes(layers):
    """全ストロークを返す"""
    materials = layers.data.materials

    yield from (
        {
            "layer": l,
            "frame": l.active_frame,
            "stroke": s,
        }
        for l in layers
        if not l.lock
        for s in l.active_frame.strokes
        if not materials[s.material_index].grease_pencil.lock
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

def get_selected_strokes(layers):
    """選択中のストロークのリストを返す"""
    return sorted(gen_selected_strokes(layers), key=lambda x:x["stroke"].select_index)

def gen_selected_layers(layers):
    """選択中のストロークのレイヤーを返す"""
    materials = layers.data.materials

    for l in layers:
        if l.lock:
            # ロック中レイヤーは除外
            continue

        g = (
            s
            for s in l.active_frame.strokes
            if s.select and not materials[s.material_index].grease_pencil.lock
        )
        for s in g:
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


def filter_layers(layers, regex):
    """レイヤーをフィルタリングする"""
    try:
        # 選択中のフィルター設定でフィルタリング
        re_match = re.compile(regex).match
        filtered_layers = (
            x
            for x in layers
            if re_match(x.info)
        )
    except:
        filtered_layers = iter(layers)

    yield from filtered_layers


class MRGPEN_UL_layer_filters(bpy.types.UIList):
    """レイヤーフィルター一覧
    """
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        """リストを描画する"""
        self.use_filter_sort_reverse = False

        layout_type = self.layout_type
        if layout_type in {"DEFAULT"}:
            # 表示
            row1 = layout.row()
            row1.prop(item, "regex", text="", emboss=False)

            row2 = layout.row(align=True)

            obj = context.active_object
            data = obj.data
            layers = data.layers
            regex = item.regex

            # フィルターごとに表示・非表示を切り替えるボタン
            def c(method, key, icon_on, icon_off):
                value = all(getattr(x, key) for x in filter_layers(layers, regex))
                elm = row2.operator(
                    MRGPEN_OT_edit_layer_or_material.bl_idname,
                    icon=icon_on if value else icon_off,
                    text="",
                    emboss=False,
                )
                elm.method = method
                elm.target = "FILTERS"
                elm.value = not value
                elm.name = regex

            c("HIDE", "hide", "HIDE_ON", "HIDE_OFF")
            c("LOCK", "lock", "LOCKED", "UNLOCKED")

    def filter_items(self, context, data, prop):
        """表示するレイヤーフィルターをフィルタする"""
        data_list = getattr(data, prop)

        func = bpy.types.UI_UL_list

        # 名前フィルタ
        if self.filter_name:
            result_list = func.filter_items_by_name(
                self.filter_name,
                self.bitflag_filter_item,
                data_list,
                "regex",
            )
        else:
            result_list = [self.bitflag_filter_item] * len(data_list)

        return result_list, []

    def draw_filter(self, context, layout):
        row = layout.row()
        row.prop(self, "filter_name", text="")


class MRGPEN_UL_layer_list(bpy.types.UIList):
    """レイヤー一覧
    """
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        """リストを描画する"""
        self.use_filter_sort_reverse = True

        layout_type = self.layout_type
        if layout_type in {"DEFAULT"}:
            # 表示
            row1 = layout.row()
            row1.prop(item, "info", text="", emboss=False)

            row2 = layout.row(align=True)
            row2.prop(item, "use_mask_layer", text="", emboss=False,
                icon="MOD_MASK" if item.use_mask_layer else "LAYER_ACTIVE")
            row2.prop(item, "use_onion_skinning", text="", emboss=False,
                icon="ONIONSKIN_ON" if item.use_onion_skinning else "ONIONSKIN_OFF")
            row2.prop(item, "hide", text="", emboss=False)
            row2.prop(item, "lock", text="", emboss=False)

    def filter_items(self, context, data, prop):
        """表示するレイヤーをフィルタする"""
        data_list = getattr(data, prop)

        func = bpy.types.UI_UL_list
        bitflag_filter_item = self.bitflag_filter_item

        # 名前フィルタ
        if self.filter_name:
            result_list = func.filter_items_by_name(
                self.filter_name,
                bitflag_filter_item,
                data_list,
                "info",
            )
        else:
            result_list = [bitflag_filter_item] * len(data_list)

        try:
            # 選択中のフィルター設定でフィルタリング
            re_match = re.compile(data.mrgpen.layer_filter.regex).match
            result_list = [
                y and (bitflag_filter_item if re_match(x.info) else 0)
                for x, y in zip(data_list, result_list)
            ]
        except:
            pass

        return result_list, []

    def draw_filter(self, context, layout):
        row = layout.row()
        row.prop(self, "filter_name", text="")


class MRGPEN_UL_selected_stroke_layer_list(bpy.types.UIList):
    """選択中ストロークのレイヤー一覧
    """
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        """リストを描画する"""
        self.use_filter_sort_reverse = True

        layout_type = self.layout_type
        if layout_type in {"DEFAULT"}:
            # 表示
            row1 = layout.row()
            row1.prop(item, "info", text="", emboss=False)

            row2 = layout.row(align=True)
            row2.prop(item, "use_mask_layer", text="", emboss=False,
                icon="MOD_MASK" if item.use_mask_layer else "LAYER_ACTIVE")
            row2.prop(item, "use_onion_skinning", text="", emboss=False,
                icon="ONIONSKIN_ON" if item.use_onion_skinning else "ONIONSKIN_OFF")
            row2.prop(item, "hide", text="", emboss=False)
            row2.prop(item, "lock", text="", emboss=False)

    def filter_items(self, context, data, prop):
        """表示するレイヤーをフィルタする"""
        data_list = getattr(data, prop)

        func = bpy.types.UI_UL_list
        bitflag_filter_item = self.bitflag_filter_item

        # 名前フィルタ
        if self.filter_name:
            result_list = func.filter_items_by_name(
                self.filter_name,
                bitflag_filter_item,
                data_list,
                "info",
            )
        else:
            result_list = [bitflag_filter_item] * len(data_list)

        # 選択中のフィルター設定でフィルタリング
        selected_layer_set = {x.info for x in gen_selected_layers(data_list)}
        result_list = [
            y and (bitflag_filter_item if x.info in selected_layer_set else 0)
            for x, y in zip(data_list, result_list)
        ]

        return result_list, []

    def draw_filter(self, context, layout):
        row = layout.row()
        row.prop(self, "filter_name", text="")


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
        for x in get_selected_strokes(layers):
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


class MRGPEN_OT_edit_layer_or_material(bpy.types.Operator):
    """ロック・アンロック、表示・非表示を切り替える"""
    bl_idname = "mrgpen.edit_layer_or_material"
    bl_label = "Edit Layer or Material"
    bl_options = {"REGISTER", "UNDO"}

    method: EnumProperty(
        name="Method",
        default="LOCK",
        items=[
            ("LOCK", "Lock", ""),
            ("HIDE", "Hide", ""),
        ],
    )
    target: EnumProperty(
        name="Target",
        default="FILTERS",
        items=[
            ("FILTERS", "Filters", ""),
            ("STROKE", "Stroke", ""),
        ],
    )
    value: BoolProperty(
        name="Value",
        default=True,
    )
    is_solo: BoolProperty(
        name="Solo",
        default=False,
    )
    name: StringProperty(
        name="Name",
        default="",
    )

    def execute(self, context):
        obj = context.active_object
        data = obj.data

        # Grease Pencil
        if not obj and obj.type == "GPENCIL":
            return {'FINISHED'}

        layers = data.layers
        target = self.target
        is_lock = self.method == "LOCK"
        value = self.value

        # 操作対象のレイヤーを取得
        filtered_layers = []
        if target == "FILTERS":
            filtered_layers = filter_layers(layers, self.name)
        elif target == "STROKE":
            filtered_layers = gen_selected_layers(layers)

        # 対象外のレイヤーを対象にする
        if self.is_solo:
            rejected_layers = {x.info for x in filtered_layers}
            filtered_layers = (x for x in layers if x.info not in rejected_layers)

        if is_lock:
            # ロック
            for x in filtered_layers:
                x.lock = value
        else:
            # 表示
            for x in filtered_layers:
                x.hide = value

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
    bl_options = {"REGISTER", "UNDO"}

    method: EnumProperty(
        default="ADD",
        items=[
            ("ADD", "Add", ""),
            ("REMOVE", "Remove", ""),
        ],
    )
    is_init: BoolProperty(
        name="Init",
        default=False,
    )
    is_invert: BoolProperty(
        name="Invert",
        default=False,
    )

    def execute(self, context):
        obj = context.active_object
        data = obj.data

        # Grease Pencil
        if not obj and obj.type == "GPENCIL":
            return {'FINISHED'}

        layers = data.layers

        if not layers.active:
            return {"FINISHED"}

        is_add = self.method == "ADD"
        active = layers.active
        mask_layers = active.mask_layers
        is_invert = self.is_invert

        # マスクを有効化
        active.use_mask_layer = True

        # マスクを初期化
        if self.is_init:
            for x in mask_layers:
                mask_layers.remove(x)

        # 選択中のストロークのレイヤーを全てマスクに追加
        for x in get_selected_layers(layers).values():
            if is_add:
                mask_layers.add(x)
                l = mask_layers[-1]
                l.invert = is_invert
            else:
                info = x.info
                while info in mask_layers:
                    mask_layers.remove(mask_layers[x.info])

        return {'FINISHED'}


class MRGPEN_OT_add_new_layer(bpy.types.Operator):
    """アクティブレイヤーの名前で新規レイヤーを生成する"""
    bl_idname = "mrgpen.add_new_layer"
    bl_label = "Add New Layer"
    bl_options = {"REGISTER", "UNDO"}

    position: EnumProperty(
        name="Position",
        default="UP",
        items=[
            ("UP", "Up", ""),
            ("DOWN", "Down", ""),
        ],
    )

    is_move: BoolProperty(
        name="Move",
        default=False,
    )
    is_mask: BoolProperty(
        name="Mask",
        default=False,
    )
    is_active_stroke: BoolProperty(
        name="Active Stroke Layer",
        default=False,
    )

    is_use_active_pass_index: BoolProperty(
        name="Use Active Pass Index",
        default=False,
    )
    pass_index: IntProperty(
        name="Pass Index",
        default=0,
    )

    def execute(self, context):
        obj = context.active_object
        data = obj.data
        mrgpen = bpy.ops.mrgpen
        ops = bpy.ops

        # Grease Pencil
        if not obj and obj.type == "GPENCIL":
            return {'FINISHED'}

        layers = data.layers

        # 選択中のストロークをアクティブに変更
        if self.is_active_stroke:
            mrgpen.select_layer()

        # 旧アクティブレイヤーの情報を取得
        old_active = layers.active
        old_note = layers.active_note

        # 新規レイヤー作成
        layers.new(name=old_note)

        new_active = layers.active

        # 新規レイヤーのPass Indexを設定
        pass_index = 0
        if self.is_use_active_pass_index:
            pass_index = old_active.pass_index
        else:
            pass_index = self.pass_index

        new_active.pass_index = pass_index

        # アクティブレイヤーの下に移動
        if self.position == "DOWN":
            ops.gpencil.layer_move(type="DOWN")

        # 選択中のストロークのレイヤーでマスク
        if self.is_mask:
            mrgpen.mask_layer(method="ADD", is_init=False, is_invert=False)

        # 選択中のストロークをアクティブレイヤーに移動
        if self.is_move:
            ops.gpencil.move_to_layer(
                layer=layers.active_index
            )

        return {'FINISHED'}


class MRGPEN_OT_remove_stroke_layers(bpy.types.Operator):
    """選択中ストロークのレイヤーを削除する"""
    bl_idname = "mrgpen.remove_stroke_layers"
    bl_label = "Remove Stroke Layers"
    bl_options = {"REGISTER", "UNDO"}

    target: EnumProperty(
        default="STROKE",
        items=[
            ("STROKE", "Selected Stroke", ""),
            ("LAYER_FILTER", "Layer Filter", ""),
            ("EMPTY", "Empty", ""),
        ],
    )
    is_lock: BoolProperty(
        name="Lock",
        default=False,
    )
    is_hide: BoolProperty(
        name="Hide",
        default=False,
    )

    def execute(self, context):
        obj = context.active_object
        data = obj.data
        ops = bpy.ops

        # Grease Pencil
        if not obj and obj.type == "GPENCIL":
            return {'FINISHED'}

        layers = data.layers
        is_lock = self.is_lock
        is_hide = self.is_hide

        target_layers = None
        if self.target == "STROKE":
            target_layers = gen_selected_layers(layers)
        elif self.target == "EMPTY":
            target_layers = (x for x in layers if sum(len(y.strokes) for y in x.frames) <= 0)
        elif self.target == "LAYER_FILTER":
            target_layers = data.mrgpen.active_filtered_layers

        # レイヤーを削除
        for l in target_layers:
            if (is_hide and l.hide) or (is_lock and l.lock):
                # 隠しているかロックがかけられていたら何もしない
                continue

            layers.remove(l)

        layers.update()

        return {'FINISHED'}


class MRGPEN_OT_set_random_tint_color(bpy.types.Operator):
    """ストロークにランダムな色を設定する"""
    bl_idname = "mrgpen.set_random_tint_color"
    bl_label = "Set Random Tint Stroke"
    bl_options = {"REGISTER", "UNDO"}

    target: EnumProperty(
        name="Target",
        default="SELECTED_STROKE",
        items=[
            ("SELECTED_STROKE", "Selected Stroke", ""),
            ("SELECTED_STROKE_LAYER", "Selected Stroke Layer", ""),
            ("ACTIVE_LAYER", "Active Layer", ""),
            ("LAYER_FILTER", "Layer Filter", ""),
        ],
    )
    is_individual: BoolProperty(name="Individual", default=False)
    is_same_stroke_fill: BoolProperty(name="Same Color", default=False)

    def execute(self, context):
        obj = context.active_object
        data = obj.data

        # Grease Pencil
        if not obj and obj.type == "GPENCIL":
            return {'FINISHED'}

        layers = data.layers

        # 塗りつぶし色
        vertex_color_fill = None
        if self.is_individual:
            vertex_color_fill = lambda: (random(), random(), random(), 1)
        else:
            c = (random(), random(), random(), 1)
            vertex_color_fill = lambda: c

        # 線色
        vertex_color = None
        if self.is_same_stroke_fill:
            vertex_color = vertex_color_fill
        else:
            vertex_color = lambda: (random(), random(), random(), 1)

        # 設定対象のストロークを取得
        target_strokes = []
        if self.target == "SELECTED_STROKE":
            target_strokes = (x["stroke"] for x in gen_selected_strokes(layers))
        elif self.target == "SELECTED_STROKE_LAYER":
            target_strokes = (y for x in gen_selected_layers(layers) for y in x.active_frame.strokes)
        elif self.target == "ACTIVE_LAYER":
            target_strokes = layers.active.active_frame.strokes
        elif self.target == "LAYER_FILTER":
            target_strokes = (y for x in data.mrgpen.active_filtered_layers for y in x.active_frame.strokes)

        # 色をストロークに設定
        for x in target_strokes:
            x.vertex_color_fill = vertex_color_fill()

            for y in x.points:
                y.vertex_color = vertex_color()

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


class MRGPEN_OT_rotate_points(bpy.types.Operator):
    """形状を保ったままポイントを回転させる"""
    bl_idname = "mrgpen.rotate_points"
    bl_label = "Rotate Points"
    bl_options = {"REGISTER", "UNDO"}

    count: IntProperty(
        name="Count",
        default=1,
        min=0,
    )
    is_reverse: BoolProperty(
        name="Reverse",
        default=False,
    )
    is_switch: BoolProperty(
        name="Switch Direction",
        default=False,
    )

    def execute(self, context):
        obj = context.active_object
        data = obj.data

        # Grease Pencil
        if not obj and obj.type == "GPENCIL":
            return {'FINISHED'}

        count = self.count
        is_reverse = self.is_reverse

        # 選択中のストロークがなければ何もしない
        for s in gen_selected_strokes(data.layers):
            stroke = s['stroke']
            points = stroke.points

            # 回転する回数
            c = count % len(points)

            # 各ポイントの位置を取得
            co_list = [x.co.copy() for x in points]

            if is_reverse:
                # 逆順にする
                co_list = co_list[::-1]

            # ポイントと置き換え後の位置のジェネレータを生成
            co_list = co_list[c:] + co_list[:c]
            target_points_co = zip(points, co_list)

            for point, co in target_points_co:
                # 位置を置き換える
                point.co = co

        if self.is_switch:
            # 向きだけ変える
            bpy.ops.gpencil.stroke_flip()

        return {'FINISHED'}


class MRGPEN_OT_move_stroke_layers(bpy.types.Operator):
    """選択したストロークのレイヤーの位置を変える"""
    bl_idname = "mrgpen.move_stroke_layers"
    bl_label = "Move Stroke Layers"
    bl_options = {"REGISTER", "UNDO"}

    count: IntProperty(
        name="Count",
        default=1,
    )
    from_active: BoolProperty(
        name="From Active",
        default=False,
    )

    def execute(self, context):
        obj = context.active_object
        data = obj.data

        # Grease Pencil
        if not obj and obj.type == "GPENCIL":
            return {'FINISHED'}

        count = self.count
        layers = data.layers
        selected_layers = list(gen_selected_layers(layers))

        if self.from_active:
            active_index = layers.active_index
            selected_layers_index_min = min(layers.find(x.info) for x in selected_layers)

            count = count + active_index - selected_layers_index_min
            if active_index < selected_layers_index_min:
                count += 1

        if count > 0:
            selected_layers = selected_layers[::-1]
            direction = "UP"
        elif count < 0:
            direction = "DOWN"

        for _ in range(abs(count)):
            for l in selected_layers:
                layers.move(l, direction)

        return {'FINISHED'}


class MRGPEN_OT_add_layer_filter(bpy.types.Operator):
    """レイヤーのフィルター設定を追加する"""
    bl_idname = "mrgpen.add_layer_filter"
    bl_label = "Add Layer Filter"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object
        data = obj.data

        # Grease Pencil
        if not obj and obj.type == "GPENCIL":
            return {'FINISHED'}

        layer_filters = data.mrgpen.layer_filters

        layer_filters.add()

        return {'FINISHED'}


class MRGPEN_OT_remove_layer_filter(bpy.types.Operator):
    """レイヤーのフィルター設定を削除する"""
    bl_idname = "mrgpen.remove_layer_filter"
    bl_label = "Remove Layer Filter"
    bl_options = {"REGISTER", "UNDO"}

    index: IntProperty(
        name="Index",
        default=0,
    )

    def execute(self, context):
        obj = context.active_object
        data = obj.data

        # Grease Pencil
        if not obj and obj.type == "GPENCIL":
            return {'FINISHED'}

        layer_filters = data.mrgpen.layer_filters
        index = self.index

        if 0 <= index < len(layer_filters):
            layer_filters.remove(index)

        return {'FINISHED'}


class MRGPEN_OT_pick_sample_length(bpy.types.Operator):
    """選択中のストロークからsample値を取得する"""
    bl_idname = "mrgpen.pick_sample_length"
    bl_label = "Pick Sample Length"
    bl_options = {"REGISTER", "UNDO"}

    method: EnumProperty(
        name="Method",
        default="average",
        items=[
            ("average", "Average", ""),
            ("min", "Min", ""),
            ("max", "Max", ""),
        ],
    )

    def execute(self, context):
        obj = context.active_object
        data = obj.data

        # Grease Pencil
        if not obj and obj.type == "GPENCIL":
            return {'FINISHED'}

        layers = data.layers

        # 取得に使用するメソッド
        method = getattr(np, self.method)

        # 選択中ストロークの最初の一つから長さを計算する
        for x in gen_selected_strokes(layers):
            # 全点取得
            p = [y.co for y in x["stroke"].points]

            # 各点の距離を取得して、メソッドで計算
            a = method([y for y in ((a - b).length for a, b in zip(p, p[1:])) if y > 0])

            # メニューの長さに設定する
            context.window_manager.mrgpen.sample_length = a
            break

        return {'FINISHED'}


class MRGPEN_MT_add_new_layer_menu(bpy.types.Menu):
    """新規レイヤー作成のメニュー"""
    bl_label = "Mr.GPen Add New Layer Menu"

    def draw(self, context):
        layout = self.layout
        mode = context.mode
        layers = context.active_object.data.layers

        # 特定のモードかどうか
        is_editable = mode in {"EDIT_GPENCIL", "SCULPT_GPENCIL", "VERTEX_GPENCIL"}

        is_selected = False
        for x in gen_selected_points(layers):
            is_selected = True
            break

        ano = layout.operator(MRGPEN_OT_add_new_layer.bl_idname,
            text=pgt("Add New Layer"))
        ano.is_move = False
        ano.is_mask = False
        ano.is_active_stroke = False

        if is_editable and is_selected:
            ano = layout.operator(MRGPEN_OT_add_new_layer.bl_idname,
                text=pgt("Move New Layer"))
            ano.is_move = True
            ano.is_mask = False
            ano.is_active_stroke = False

            ano = layout.operator(MRGPEN_OT_add_new_layer.bl_idname,
                text=pgt("Add New Layer and Mask"))
            ano.is_move = False
            ano.is_mask = True
            ano.is_active_stroke = True

        rsl = layout.operator(MRGPEN_OT_remove_stroke_layers.bl_idname,
            text=pgt("Remove Stroke Layers"))
        rsl.target = "STROKE"

        rsl = layout.operator(MRGPEN_OT_remove_stroke_layers.bl_idname,
            text=pgt("Remove Empty Layers"))
        rsl.target = "EMPTY"

    @classmethod
    def poll(self, context):
        o = context.active_object
        return (o and o.type == "GPENCIL")


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
        data = context.active_object.data
        layers = data.layers

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
        if layers.active:
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
            box_row = box.row()
            box_column1 = box_row.column()

            box_column2 = box_row.column()
            box_column2_1 = box_column2.column(align=True)
            box_column2_2 = box_column2.column(align=True)

            box_column2_1.operator(MRGPEN_OT_add_new_layer.bl_idname,
                text="",
                icon="ADD",
            )
            box_column2_1.operator(MRGPEN_OT_remove_stroke_layers.bl_idname,
                text="",
                icon="REMOVE",
            )

            # レイヤー追加のメニュー
            box_column2_1.menu("MRGPEN_MT_add_new_layer_menu", icon="DOWNARROW_HLT", text="")

            if is_editable and is_selected:
                box_column1.operator(MRGPEN_OT_move_active_layer.bl_idname,
                    text=pgt("Move Active Layer"))

            box_column1.operator(MRGPEN_OT_rename_layers.bl_idname,
                text=pgt(MRGPEN_OT_rename_layers.bl_label))

            if is_editable and is_selected:
                msl = box_column2_2.operator(MRGPEN_OT_move_stroke_layers.bl_idname,
                    text="",
                    icon="TRIA_UP")
                msl.count = 1
                msl = box_column2_2.operator(MRGPEN_OT_move_stroke_layers.bl_idname,
                    text="",
                    icon="TRIA_DOWN")
                msl.count = -1

            # レイヤーのフィルターリスト
            box.label(text="Filters")
            row = box.row()
            column1 = row.column(align=True)
            column2 = row.column(align=True)

            if data.mrgpen.layer_filter:
                column1.prop(data.mrgpen.layer_filter, "regex", text="")

            column1.template_list(
                "MRGPEN_UL_layer_filters",
                "",
                data.mrgpen,
                "layer_filters",
                data.mrgpen,
                "layer_filter_index",
            )
            column1.template_list(
                "MRGPEN_UL_layer_list",
                "",
                data,
                "layers",
                data.layers,
                "active_index",
            )

            column2.operator(MRGPEN_OT_add_layer_filter.bl_idname, text="", icon="ADD")
            dlf = column2.operator(MRGPEN_OT_remove_layer_filter.bl_idname, text="", icon="REMOVE")
            dlf.index = data.mrgpen.layer_filter_index

        # 選択関係の機能
        box = layout.box()
        if submenu(box, "is_collapse_select", "Select"):
            row = box.row()
            column1 = row.column()
            column2 = row.column()
            column2.scale_x = .125
            column2_1 = column2.column(align=True)
            column2_2 = column2.column(align=True)

            column1.template_list(
                "MRGPEN_UL_selected_stroke_layer_list",
                "",
                data,
                "layers",
                data.layers,
                "active_index",
            )
            # 選択ストロークのレイヤーを一括で表示・非表示を切り替えるボタン
            def c(method, key, icon_on, icon_off):
                value = all(getattr(x, key) for x in gen_selected_layers(layers))
                elm = column2_1.operator(
                    MRGPEN_OT_edit_layer_or_material.bl_idname,
                    icon=icon_on if value else icon_off,
                    text="",
                    emboss=False,
                )
                elm.method = method
                elm.target = "STROKE"
                elm.value = not value
                elm.name = ""

            c("HIDE", "hide", "HIDE_ON", "HIDE_OFF")
            c("LOCK", "lock", "LOCKED", "UNLOCKED")

            rl = column2_2.operator(MRGPEN_OT_rename_layers.bl_idname,
                text="R")
            rl.target = "STROKE"

            if is_editable and is_selected:
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
                    # 選択中ポイントのカラー
                    r = box.row()
                    r.alignment = "LEFT"
                    r.prop(
                        wm,
                        "is_show_all_vertex_color",
                        icon="TRIA_DOWN" if wm.is_show_all_vertex_color else "TRIA_RIGHT",
                        text="Vertex Color",
                        emboss=False,
                    )
                    if wm.is_show_all_vertex_color:
                        r = box.grid_flow(
                            align=True,
                            even_columns=True,
                            even_rows=True,
                        )
                        for x in gen_selected_points(layers):
                            c = r.column(align=True)
                            c.prop(
                                x["point"],
                                "vertex_color",
                                text="",
                            )
                            c.ui_units_x = 1
                    else:
                        box.prop(wm, "vertex_color", text="")

                    # 選択中ストロークの塗りつぶしカラー
                    r = box.row()
                    r.alignment = "LEFT"
                    r.prop(
                        wm,
                        "is_show_all_vertex_color_fill",
                        icon="TRIA_DOWN" if wm.is_show_all_vertex_color_fill else "TRIA_RIGHT",
                        text="Vertex Fill Color",
                        emboss=False,
                    )
                    if wm.is_show_all_vertex_color_fill:
                        r = box.grid_flow(
                            align=True,
                            even_columns=True,
                            even_rows=True,
                        )
                        for x in gen_selected_strokes(layers):
                            c = r.column(align=True)
                            c.prop(
                                x["stroke"],
                                "vertex_color_fill",
                                text="",
                            )
                            c.ui_units_x = 1
                    else:
                        box.prop(wm, "vertex_color_fill", text="")

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

        if is_editable and is_selected:
            box = layout.box()
            if submenu(box, "is_collapse_points", "Points"):
                box.prop(wm, "strength", text="Strength")
                box.prop(wm, "pressure", text="Pressure")
                box.prop(wm, "vertex_color", text="Color")
                box.operator(MRGPEN_OT_rotate_points.bl_idname,
                    text=pgt("Rotate Points"))

                ss = box.operator("gpencil.stroke_sample")

                r = box.row(align=True)
                r.prop(wm, "sample_length", text="Sample Length")
                r.operator(MRGPEN_OT_pick_sample_length.bl_idname,
                    icon="EYEDROPPER",
                    text="")

                ss.length = wm.sample_length

        if is_editable and is_selected:
            box = layout.box()
            if submenu(box, "is_collapse_strokes", "Strokes"):
                box.prop(wm, "line_width", text="Width")
                box.prop(wm, "hardness", text="Hardness")
                box.prop(wm, "vertex_color_fill", text="Fill")
                box.prop(wm, "draw_cyclic", text="Cyclic")

                box.prop(wm, "start_cap_mode", text="Start Cap Mode")
                box.prop(wm, "end_cap_mode", text="End Cap Mode")

                box.label(text="Texture")
                box.prop(wm, "uv_translation", text="Location")
                box.prop(wm, "uv_rotation", text="Rotation")
                box.prop(wm, "uv_scale", text="Scale")

        # その他の機能
        if is_editable and is_selected:
            box = layout.box()
            if submenu(box, "is_collapse_other", "Other"):
                bo = box.operator

                asm = bo(MRGPEN_OT_mask_layer.bl_idname,
                    text=pgt("Add Stroke Mask"))
                asm.method = "ADD"
                asm.is_init = False

                asm = bo(MRGPEN_OT_mask_layer.bl_idname,
                    text=pgt("Remove Stroke Mask"))
                asm.method = "REMOVE"
                asm.is_init = False

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

def edit_strokes_attr(self, target, name, value=None, default_value=None):
    """選択中の全てのストロークのプロパティを取得・設定する"""
    obj = bpy.context.active_object
    data = obj.data

    # Grease Pencil
    if not obj and obj.type == "GPENCIL":
        return

    layers = data.layers

    strokes = []
    if target == "stroke":
        strokes = gen_selected_strokes(layers)
    elif target == "point":
        strokes = gen_selected_points(layers)

    if value is not None:
        # set
        for x in strokes:
            setattr(x[target], name, value)
    elif default_value is not None:
        # get
        for x in strokes:
            return getattr(x[target], name)
        else:
            return default_value


class MRGPEN_LayerFilters(PropertyGroup):
    regex: StringProperty(default=".+")


cap_mode_list = [
    (*x, "", i) for i, x in enumerate([
        ("ROUND", "Round"),
        ("FLAT", "Flat"),
    ])
]
cap_mode_dict = {key:value for key, _, _, value in cap_mode_list}
cap_mode_num_dict = {key:value for value, _, _, key in cap_mode_list}


class MRGPEN_WindowManager(PropertyGroup):
    is_collapse_layer: BoolProperty(default=True)
    is_collapse_select: BoolProperty(default=True)
    is_collapse_stroke_layer: BoolProperty(default=True)
    is_collapse_stroke_material: BoolProperty(default=True)
    is_collapse_vertex_color: BoolProperty(default=True)
    is_show_all_vertex_color: BoolProperty(default=False)
    is_show_all_vertex_color_fill: BoolProperty(default=False)
    is_collapse_other: BoolProperty(default=True)
    is_collapse_strokes: BoolProperty(default=True)
    is_collapse_points: BoolProperty(default=True)
    color_threshold: FloatProperty(default=.01)
    vertex_color: FloatVectorProperty(
        size=4,
        subtype="COLOR",
        min=0,
        max=1,
        get=lambda self: edit_strokes_attr(self, "point", "vertex_color", default_value=(0, 0, 0, 0,)),
        set=lambda self, v: edit_strokes_attr(self, "point", "vertex_color", value=v),
    )
    vertex_color_fill: FloatVectorProperty(
        size=4,
        subtype="COLOR",
        min=0,
        max=1,
        get=lambda self: edit_strokes_attr(self, "stroke", "vertex_color_fill", default_value=(0, 0, 0, 0,)),
        set=lambda self, v: edit_strokes_attr(self, "stroke", "vertex_color_fill", value=v),
    )
    hardness: FloatProperty(
        min=0,
        max=1,
        get=lambda self: edit_strokes_attr(self, "stroke", "hardness", default_value=1),
        set=lambda self, v: edit_strokes_attr(self, "stroke", "hardness", value=v),
    )
    line_width: FloatProperty(
        get=lambda self: edit_strokes_attr(self, "stroke", "line_width", default_value=1),
        set=lambda self, v: edit_strokes_attr(self, "stroke", "line_width", value=v),
    )
    uv_rotation: FloatProperty(
        get=lambda self: edit_strokes_attr(self, "stroke", "uv_rotation", default_value=1),
        set=lambda self, v: edit_strokes_attr(self, "stroke", "uv_rotation", value=v),
    )
    uv_scale: FloatProperty(
        get=lambda self: edit_strokes_attr(self, "stroke", "uv_scale", default_value=1),
        set=lambda self, v: edit_strokes_attr(self, "stroke", "uv_scale", value=v),
    )
    uv_translation: FloatVectorProperty(
        size=2,
        subtype="TRANSLATION",
        get=lambda self: edit_strokes_attr(self, "stroke", "uv_translation", default_value=1),
        set=lambda self, v: edit_strokes_attr(self, "stroke", "uv_translation", value=v),
    )
    pressure: FloatProperty(
        min=0,
        get=lambda self: edit_strokes_attr(self, "point", "pressure", default_value=1),
        set=lambda self, v: edit_strokes_attr(self, "point", "pressure", value=v),
    )
    strength: FloatProperty(
        min=0,
        max=1,
        get=lambda self: edit_strokes_attr(self, "point", "strength", default_value=1),
        set=lambda self, v: edit_strokes_attr(self, "point", "strength", value=v),
    )
    draw_cyclic: BoolProperty(
        get=lambda self: edit_strokes_attr(self, "stroke", "draw_cyclic", default_value=False),
        set=lambda self, v: edit_strokes_attr(self, "stroke", "draw_cyclic", value=v),
    )
    start_cap_mode: EnumProperty(
        get=lambda self: cap_mode_dict[edit_strokes_attr(self, "stroke", "start_cap_mode", default_value="ROUND")],
        set=lambda self, v: edit_strokes_attr(self, "stroke", "start_cap_mode", value=cap_mode_num_dict[v]),
        items=[
            ("ROUND", "Round", ""),
            ("FLAT", "Flat", ""),
        ],
    )
    end_cap_mode: EnumProperty(
        get=lambda self: cap_mode_dict[edit_strokes_attr(self, "stroke", "end_cap_mode", default_value="ROUND")],
        set=lambda self, v: edit_strokes_attr(self, "stroke", "end_cap_mode", value=cap_mode_num_dict[v]),
        items=cap_mode_list,
    )
    sample_length: FloatProperty(
        name="Sample Length",
        default=.01,
        min=0,
    )


class MRGPEN_GreasePencil(PropertyGroup):
    """グリースペンシルのmrgpen拡張プロパティ"""
    layer_filters: CollectionProperty(
        name="Layer Filters",
        type=MRGPEN_LayerFilters,
    )
    layer_filter_index: IntProperty(
        name="Layer Filter Index",
        default=0,
    )

    @property
    def layer_filter(self):
        layer_filters = self.layer_filters
        layer_filter_index = self.layer_filter_index

        if not (0 <= layer_filter_index < len(layer_filters)):
            return

        return layer_filters[layer_filter_index]

    @property
    def active_filtered_layers(self):
        layer_filters = self.layer_filters
        layer_filter_index = self.layer_filter_index

        obj = bpy.context.active_object
        if not obj and obj.type == "GPENCIL":
            return []

        layer_filter = self.layer_filter
        if not layer_filter:
            return []

        return list(filter_layers(obj.data.layers, layer_filter.regex))


classes = [
    MRGPEN_OT_select_layer,
    MRGPEN_OT_mask_layer,
    MRGPEN_OT_add_new_layer,
    MRGPEN_OT_remove_stroke_layers,
    MRGPEN_OT_toggle_hide,
    MRGPEN_OT_toggle_hide_other,
    MRGPEN_OT_toggle_lock,
    MRGPEN_OT_toggle_lock_other,
    MRGPEN_OT_move_active_layer,
    MRGPEN_OT_set_random_tint_color,
    MRGPEN_OT_set_random_tint_color_brush,
    MRGPEN_PT_view_3d_label,
    MRGPEN_MT_add_new_layer_menu,
    MRGPEN_OT_select_same_layer_stroke,
    MRGPEN_OT_toggle_hide_material,
    MRGPEN_OT_toggle_hide_material_other,
    MRGPEN_OT_toggle_lock_material,
    MRGPEN_OT_toggle_lock_material_other,
    MRGPEN_OT_deselect_all_strokes,
    MRGPEN_OT_pick_vertex_color,
    MRGPEN_UL_layer_filters,
    MRGPEN_UL_layer_list,
    MRGPEN_UL_selected_stroke_layer_list,
    MRGPEN_LayerFilters,
    MRGPEN_WindowManager,
    MRGPEN_GreasePencil,
    MRGPEN_OT_select_nearest_color,
    MRGPEN_OT_fade_stroke_edge,
    MRGPEN_OT_fat_stroke,
    MRGPEN_OT_rename_layers,
    MRGPEN_OT_rotate_points,
    MRGPEN_OT_move_stroke_layers,
    MRGPEN_OT_add_layer_filter,
    MRGPEN_OT_remove_layer_filter,
    MRGPEN_OT_edit_layer_or_material,
    MRGPEN_OT_pick_sample_length,
]

def register():
    for x in classes:
        bpy.utils.register_class(x)

    translations.register(__name__, translation_dict)
    bpy.types.WindowManager.mrgpen = PointerProperty(type=MRGPEN_WindowManager)
    bpy.types.GreasePencil.mrgpen = PointerProperty(type=MRGPEN_GreasePencil)


def unregister():
    translations.unregister(__name__)

    for x in classes:
        bpy.utils.unregister_class(x)

    del bpy.types.WindowManager.mrgpen
    del bpy.types.GreasePencil.mrgpen

if __name__ == "__main__":
    register()
