from pathlib import Path

import base64
import json
import pandas as pd
import requests
import streamlit as st



EDITORS_BY_TYPE = {
	"View3D Context":["3D View"],
	"Buttons Context":["Properties"],
	"Image Context":["Image Editor"],
	"Node Context":["Node Editor"],
	"Text Context":["Text Editor"],
	"Clip Context":["Clip Editor"],
	"Sequencer Context":["Sequence Editor"]
	}


Home_path = Path.cwd()
context_DATA_dic = {p.stem:p for p in Path(Home_path, "outcome").iterdir() if p.is_file()}

Info_path = Home_path / "info" / "contexts_by_doc.json"
with Info_path.open("r", encoding='utf-8') as fr:
	ROW_IN_DOC = json.load(fr)

COL_NAMES = ['3D View','Clip Editor','Console','Dope Sheet Editor','File Browser','Graph Editor','Image Editor','Info','Nla Editor','Node Editor','Outliner','Preferences','Properties','Sequence Editor','Text Editor','Topbar']
ROW_NAMES = list(set(sum([v for v in ROW_IN_DOC.values()], []))).sort()

BE_1st = "初期状態"


def extract_diff_dict(Table, Ignore):
	out_dic = {}
	colnames = Table.columns.tolist()

	for rn in Table.index.tolist():
		if rn in ["area", "region", "space_data", "active_operator"]:
			continue

		values = Table.loc[rn].tolist()
		if Ignore:
			values = [x.split(" at ")[0] for x in values]

		temp_dic = {}
		for cn, v in zip(colnames, values):
			val = v.replace("bpy.data.objects", "D.obs").replace("bpy.data.", "D.")
			if val not in temp_dic:
				temp_dic[val] = f"{cn}"
			else:
				temp_dic[val] = f"{temp_dic[val]}, {cn}"

		if len(list(temp_dic.keys())) >= 2:
			res_dic = {BE_1st:None }
			for key in temp_dic.keys():
				num = len(temp_dic[key].split(", "))
				if num > 1 and num == len(colnames)-1:
					res_dic["他の全て"] = key
				else:
					res_dic[temp_dic[key]] = key
			if res_dic[BE_1st] is None:
				res_dic.pop(BE_1st)
			out_dic[rn] = res_dic
	return out_dic


def compare_list(Pre_list_text, Act_list_text):
	pre_list = Pre_list_text[1:-1].split(",")
	if pre_list == [""]:
		pre_list = []
	act_list = Act_list_text[1:-1].split(",")
	if act_list == [""]:
		act_list = []

	inter_set = set(pre_list) & set(act_list)
	subed = list(set(pre_list) - inter_set)
	added = list(set(act_list) - inter_set)

	if len(subed) == 0 and len(added) >= 1:
		diffs = list(added)[0] if len(added)==1 else list(added)
		text = f"[{','.join(pre_list)}] に {diffs} が加わった"
	elif len(subed) >= 1 and len(added) == 0:
		diffs = list(subed)[0] if len(subed)==1 else list(subed)
		text = f"[{','.join(pre_list)}] から {diffs} が除かれた"
	else:
		sub = list(subed)[0] if len(subed)==1 else list(subed)
		add = list(added)[0] if len(added)==1 else list(added)
		text = f"[{','.join(pre_list)}] において {sub} が除かれ {add} が加わった"
	return text


def compare_data(Outcome_dic, Target_name):
	with context_DATA_dic[Target_name].open("r", encoding='utf-8') as fr:
		comp_dic = json.load(fr)

	result_dic = {}
	for type_name in Outcome_dic.keys():
		partly_talbe = Outcome_dic[type_name]
		editors = partly_talbe.columns.tolist()
		items = partly_talbe.index.tolist()
		type_res_dic = {}
		for itm in items:
			if itm in ["area", "region", "space_data", "active_operator"]:
				continue
			res_itm_for_edi = {}
			for edi in editors:
				act = partly_talbe.at[itm, edi].split(" at")[0].replace("bpy.data.objects", "D.obs").replace("bpy.data.", "D.")
				if itm not in comp_dic[edi]:
					pre = "項目なし"
				else:
					pre = comp_dic[edi][itm].split(" at")[0].replace("bpy.data.objects", "D.obs").replace("bpy.data.", "D.")
				if act != pre:
					act_is_list = act.startswith("[") and act.endswith("]")
					pre_is_list = pre.startswith("[") and pre.endswith("]")
					if act_is_list and pre_is_list:
						result = compare_list(pre, act)
					else:
						result = f"{pre} → {act}"
					if result not in res_itm_for_edi:
						res_itm_for_edi[result] = f"{edi}"
					else:
						res_itm_for_edi[result] = f"{res_itm_for_edi[result]}, {edi}"
			if res_itm_for_edi:
				inverted_dic = {v:k for k, v in res_itm_for_edi.items()}
				for key in inverted_dic.keys():
					edi_num = len(key.split(", "))
					if edi_num == len(COL_NAMES):
						inverted_dic["全て"] = inverted_dic.pop(key)
					elif edi_num == len(COL_NAMES ) -1:
						inverted_dic["他の全て"] = inverted_dic.pop(key)
				type_res_dic[itm] = inverted_dic
		result_dic[type_name] = type_res_dic
	return result_dic


@st.cache
def get_data(Data_name):
	with context_DATA_dic[Data_name].open("r", encoding='utf-8') as fr:
		main_dic = json.load(fr)
	COL_NAMES = sorted(list(main_dic.keys()))
	all_context_keys = sum([list(main_dic[c].keys()) for c in COL_NAMES], [])
	ROW_NAMES = list(set(all_context_keys))

	temp_dic = {x:[] for x in ROW_NAMES}
	for cn in COL_NAMES:
		context = main_dic[cn]
		for rn in ROW_NAMES:
			if rn in context:
				temp_dic[rn].append(context[rn])
			else:
				temp_dic[rn].append("項目なし")

	list_2d = [temp_dic[x] for x in ROW_NAMES]
	table = pd.DataFrame(list_2d, columns=COL_NAMES, index=ROW_NAMES)  

	outcome_dic = {}
	for context_type_name in ROW_IN_DOC.keys():
		row_names_by_type = ROW_IN_DOC[context_type_name]
		list_2d = [temp_dic[rn] if rn in temp_dic else ["項目なし"]*len(COL_NAMES) for rn in row_names_by_type]
		re_idx_table = pd.DataFrame(list_2d, columns=COL_NAMES, index=row_names_by_type)
		outcome_dic[context_type_name] = re_idx_table
	return table, outcome_dic


@st.cache
def get_editor_data(Editor_names):
	result_dic = {edi:{} for edi in Editor_names}
	for d_name in context_DATA_dic.keys():
		with context_DATA_dic[d_name].open("r", encoding='utf-8') as fr:
			data_dic = json.load(fr)
		for edi in Editor_names:
			if result_dic[edi] == {}:
				result_dic[edi] = {d_name: data_dic[edi]}
			else:
				result_dic[edi][d_name] = data_dic[edi]

	outcome_dic = {}
	for edi in Editor_names:
		col_names = list(context_DATA_dic.keys())

		tbdic_by_type = {}
		for ct_type_name in ROW_IN_DOC.keys():
			row_names_by_type = ROW_IN_DOC[ct_type_name]
			temp_dic = {x:[] for x in row_names_by_type}
			for d_name in context_DATA_dic.keys():
				context = result_dic[edi][d_name]
				for rn in row_names_by_type:
					if rn in context:
						temp_dic[rn].append(context[rn])
					else:
						temp_dic[rn].append("項目なし")


			list_2d = [temp_dic[rn] if rn in temp_dic else ["項目なし"]*len(col_names)
						for rn in row_names_by_type]
			table = pd.DataFrame(list_2d, columns=col_names, index=row_names_by_type)
			tbdic_by_type[ct_type_name] = table

		outcome_dic[edi] = tbdic_by_type

	return outcome_dic



#--------- ここから streamlit の表示設定 -------------------


# サイドバーの設定-------------------------

base_is_editor = st.sidebar.checkbox("エディタを基準にして比較を行う", False)

if base_is_editor:
	edi_names = st.sidebar.multiselect("エディタ", COL_NAMES, default=['3D View'])

	if BE_1st in context_DATA_dic:
		shown_datas = [BE_1st] + [x for x in context_DATA_dic.keys() if x != BE_1st]
	else:
		shown_datas = list(context_DATA_dic.keys())
	method = st.sidebar.radio("表示する状態の選択方法", ["Checkbox", "Multi Select"])

	st.sidebar.markdown("◆ 表示する状態")
	if method == "Checkbox":
		data_checks = [st.sidebar.checkbox(name, True) for idx, name in enumerate(shown_datas)]
		data_bools = [x==True for x in data_checks]
		active_datas = [n for b, n in zip(data_bools, shown_datas) if b]
	else:
		active_datas = st.sidebar.multiselect("状態", shown_datas, default=shown_datas)
else:
	if BE_1st in context_DATA_dic:
		idx = list(context_DATA_dic.keys()).index(BE_1st)
	else:
		idx = 0
	target_name = st.sidebar.radio("Blender の状態", list(context_DATA_dic.keys()), index=idx)
	st.sidebar.markdown("---------------------")

	compare_dic = {
			f"「{x.split(' + ')[0]}」と比較" if x!=target_name else "比較しない":x
			for x in context_DATA_dic.keys() }
	compare_name = st.sidebar.radio("2つの状態の比較",
					sorted(list(compare_dic.keys()),reverse=True))

# データフレームの表示-------------------------


def color_style(val):
	color_dic = {"項目なし":'gray', "None":'red', "[]":'blue'}
	if val in color_dic:
		color = color_dic[val]
	else:
		color = 'green'
	return 'color: %s' % color

"""
* Blender 2.91 の初期プロジェクトで取得
"""
ignore_at = st.checkbox("bpy_stcur の 'at'以下の差異を無視する", True)



if base_is_editor:
	"""
	## ◇ エディタを基準にして比較を行う
	`項目なし`は、そのエリアの context に該当項目が含まれないことを示す
	"""

	if edi_names:
		edi_dic = get_editor_data(edi_names)
		REV = {v[0]:k for k,v in EDITORS_BY_TYPE.items()}
		for edi in edi_dic.keys():
			st.markdown(f"### ◇ {edi}")
			ct_types = ["Global Context", "Screen Context"]
			if edi in REV:
				ct_types = ct_types + [REV[edi]]

			for context_type in ct_types:
				st.markdown(f"#### ◇ {context_type}")
				partly_table = edi_dic[edi][context_type]
				df = partly_table.reindex(columns=active_datas)
				st.dataframe(df.style.applymap(color_style))

				diff_dic = extract_diff_dict(df, ignore_at)
				with st.beta_expander("差異　(D = bpy.data,　obs = objects)", expanded=True):
					st.write(diff_dic)
					st.markdown("---------------")

			st.markdown("---------")

else:
	#-- API Doc 準拠 -------------------

	"""
	## ◇ API Doc の分類に準拠した表
	`項目なし`は、そのエリアの context に該当項目が含まれないことを示す
	"""

	is_limit = st.checkbox("Global と Screen 以外は関連するエディタのみ表示", True)
	
	table, outcome_dic = get_data(Data_name=target_name)
	diff_result = None

	if compare_name != "比較しない":
		comp_target = compare_dic[compare_name]
		diff_result = compare_data(outcome_dic, comp_target)


	for context_type in outcome_dic.keys():
		st.markdown(f"### ◇ {context_type}")
		partly_table = outcome_dic[context_type]
		if is_limit:
			if context_type in EDITORS_BY_TYPE:
				partly_table = partly_table[EDITORS_BY_TYPE[context_type]]
		st.dataframe(partly_table.style.applymap(color_style))

		if diff_result is not None:
			partly_compared = diff_result[context_type]
			with st.beta_expander("比較結果　(D = bpy.data,　obs = objects,　bpy_struct において省略あり)", expanded=True):
				st.write(partly_compared)
				
		
		if len(partly_table.columns) >= 2:
			partly_row_names = partly_table.index.tolist()
			diff_dic = extract_diff_dict(partly_table, ignore_at)
			with st.beta_expander("エディタ間の差異 (area, region, space_data, active_operator は除く)"):
				st.write(diff_dic)
				st.markdown("---------------")


	#-- 集計表 -------------------


	st.markdown("------------------")
	with st.beta_expander("◇ 各エリアで取得した context の一覧表"):
		st.markdown("`項目なし`は、そのエリアの context に該当項目が含まれないことを示す")
		st.dataframe(table.style.applymap(color_style))



	#---- エディタによる違い 全体 ----------------------


	st.markdown("------------------")
	with st.beta_expander("◇ エディタ間の差異：全体 (area, region, space_data, active_operator は除く)", expanded=False):

		all_diff_dic = extract_diff_dict(table, ignore_at)
		st.write(all_diff_dic)
