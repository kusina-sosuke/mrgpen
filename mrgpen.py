import bpy
from bpy.app import translations
from bpy.app.translations import pgettext as pgt
from random import random

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
    },
}

def gen_selected_points(layers):
    """選択中のポイントを返す"""
    yield from (
        {
            "layer": l,
            "frame": f,
            "stroke": s,
            "point": p,
        }
        for l in layers
        for f in l.frames
        for s in f.strokes
        if s.select
        for p in s.points
        if p.select
    )

def gen_selected_strokes(layers):
    """選択中のストロークを返す"""
    yield from (
        {
            "layer": l,
            "frame": f,
            "stroke": s,
        }
        for l in layers
        for f in l.frames
        for s in f.strokes
        if s.select
    )

def get_selected_layers(layers):
    """選択中のレイヤーを返す"""
    return {x["layer"].info: x["layer"] for x in gen_selected_points(layers)}

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


class MRGPEN_PT_view_3d_label(bpy.types.Panel):
    """3D画面横のパネルのUI"""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Edit"
    bl_label = "Mr.GPen"

    def draw(self, context):
        layout = self.layout

        mode = context.mode

        o = layout.operator

        o(MRGPEN_OT_create_layer.bl_idname,
            text=pgt("Add New Layer"))

        if mode in {"EDIT_GPENCIL", "SCULPT_GPENCIL"}:
            # エディットモードのときだけ表示
            layers = context.active_object.data.layers

            for x in gen_selected_points(layers):
                layout.split()
                layout.prop(x["layer"], "info", text="Stroke")
                layout.prop(layers.active, "info", text="Active")
                o(MRGPEN_OT_select_layer.bl_idname,
                    text=pgt("Select Stroke Layer"))
                o(MRGPEN_OT_select_same_layer_stroke.bl_idname,
                    text=pgt("Select Same Layer Stroke"))
                o(MRGPEN_OT_deselect_all_strokes.bl_idname,
                    text=pgt("Deselect All Strokes"))
                o(MRGPEN_OT_move_active_layer.bl_idname,
                    text=pgt("Move Active Layer"))

                layout.split()
                o(MRGPEN_OT_toggle_hide.bl_idname,
                    text=pgt("Hide Stroke Layer"))
                o(MRGPEN_OT_toggle_hide_other.bl_idname,
                    text=pgt("Isolate Stroke Layer"))
                o(MRGPEN_OT_toggle_lock.bl_idname,
                    text=pgt("Lock Stroke Layer"))
                o(MRGPEN_OT_toggle_lock_other.bl_idname,
                    text=pgt("Isolate Lock Stroke Layer"))

                layout.split()
                o(MRGPEN_OT_toggle_hide_material.bl_idname,
                    text=pgt("Hide Stroke Material"))
                o(MRGPEN_OT_toggle_hide_material_other.bl_idname,
                    text=pgt("Isolate Stroke Material"))
                o(MRGPEN_OT_toggle_lock_material.bl_idname,
                    text=pgt("Lock Stroke Material"))
                o(MRGPEN_OT_toggle_lock_material_other.bl_idname,
                    text=pgt("Isolate Lock Stroke Material"))

                layout.split()
                o(MRGPEN_OT_set_random_tint_color.bl_idname,
                    text=pgt("Set Random Tint Stroke"))
                o(MRGPEN_OT_mask_layer.bl_idname,
                    text=pgt("Add Stroke Mask"))
                break

    @classmethod
    def poll(self, context):
        o = context.active_object
        return (o and o.type == "GPENCIL")

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
    MRGPEN_PT_view_3d_label,
    MRGPEN_OT_select_same_layer_stroke,
    MRGPEN_OT_toggle_hide_material,
    MRGPEN_OT_toggle_hide_material_other,
    MRGPEN_OT_toggle_lock_material,
    MRGPEN_OT_toggle_lock_material_other,
    MRGPEN_OT_deselect_all_strokes,
]

def register():
    for x in classes:
        bpy.utils.register_class(x)

    translations.register(__name__, translation_dict)


def unregister():
    translations.unregister(__name__)

    for x in classes:
        bpy.utils.unregister_class(x)


if __name__ == "__main__":
    register()
