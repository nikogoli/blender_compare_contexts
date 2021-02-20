import bpy
from bpy.props import *


from pathlib import Path
import json


bl_info = {
	"name": "Export Context.copy()",
	"author": "nikogoli",
	"version": (0, 1),
	"blender": (2, 91, 0),
	"location": "Leftest part of each editors header",
	"description": "Place buttons to export context.copy() as json files",
	"warning": "",
	"support": "TESTING",
	"wiki_url": "",
	"tracker_url": "",
	"category": "Custom"
}


# オペレーター
class ExportContextOperator(bpy.types.Operator):
	bl_idname = "wm.export_context_operator"
	bl_label = "Export Context as json File"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		sd_name = context.space_data.bl_rna.name
		if sd_name == "Space":
			file_name = "Topbar.json"
		else:
			sd_name = sd_name.replace("Space ", "").replace(" Space", "")
			file_name = f"{sd_name}.json".

		file_path = Path(prefs.data_dir) / file_name
		override = context.copy()
		out_dic = {k: str(override[k]) for k in override.keys()}

		with out_path.open("w", encoding='utf-8') as fw:
			json.dump(out_dic, fw, ensure_ascii=False)
		self.report({'INFO'}, f"Save {file_name}")
		return {'FINISHED'}


class CombineJsonOperator(bpy.types.Operator):
	bl_idname = "wm.combine_json_operator"
	bl_label = "Combine json File"
	bl_options = {'REGISTER', 'UNDO'}

	name : StringProperty(name="filename", default="Cubeを選択.json")

	def execute(self, context):
		prefs = bpy.context.preferences.addons[__name__].preferences
		data_dir = Path(prefs.data_dir)
		json_paths = [p for p in data_dir.iterdir() if p.is_file()]
		main_dic = {}
		for jp in json_paths:
			with jp.open("r", encoding="utf-8") as fr:
				main_dic[jp.stem] = json.load(fr)

		out_path = Path(prefs.out_dir) / f"{name}.json"
		with out_data_path.open("w", encoding='utf-8') as fw:
			json.dump(main_dic, fw, ensure_ascii=False)
		self.report({'INFO'}, f"Combine {len(json_paths)} files to {name}.json")
		return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(MyVariousOperator.bl_idname, text="CTX", icon='EXPORT')
		

# アドオン設定
class AddonPreferences(bpy.types.AddonPreferences):
	bl_idname = __name__

	data_dir : StringProperty(name="Directory Path: Editors' json files", default=str(Path.cwd() / "temp"), subtype='FILE_PATH')
	out_dir : StringProperty(name="Directory Path: Combined json file", default=str(Path.cwd() / "outcome"), subtype='FILE_PATH')
	name : StringProperty(name="Combined Json File Name", default="Cubeを選択.json")

	def draw(self, context):
		for p in ['data_dir', 'out_dir', 'name']:
			self.layout.prop(self, p)
		self.operator(CombineJsonOperator.bl_idname).name = self.name

#---------------------------------------------------

classname_dic = {
	"HT_header":["VIEW3D","IMAGE","NODE","SEQUENCER","CLIP","DOPESHEET","GRAPH","NLA","TEXT","CONSOLE","INFO","OUTLINER","PROPERTIES","FILEBROWSER","USERPREF"],
	"HT_upper_bar":["TOPBAR"],
}



#---------------------------------------------------


classes = [
	ExportContextOperator,
	CombineJsonOperator,
	AddonPreferences
]

def register():
	for cls in classes:
		bpy.utils.register_class(cls)
	for typ in classname_dic.keys():
		for root_name in classname_dic[typ]:
			target = eval(f"bpy.types.{root_name}_{typ}")
			target.prepend(menu_func)

def unregister():
	for cls in classes:
		bpy.utils.unregister_class(cls)
	for typ in classname_dic.keys():
		for root_name in classname_dic[typ]:
			target = eval(f"bpy.types.{root_name}_{typ}")
			target.remove(menu_func)


if __name__ == "__main__":
	register()