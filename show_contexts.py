from pathlib import Path

import json
import pandas as pd
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


def extract_diff_as_dict(Table):
	out_dic = {}
	colnames = Table.columns.tolist()

	for rn in Table.index.tolist():
		if rn in ["area", "region", "space_data", "active_operator"]:
			continue
		values = Table.loc[rn].tolist()

		temp_dic = {}
		for cn, v in zip(colnames, values):
			if v not in temp_dic:
				temp_dic[v] = f"{cn}"
			else:
				temp_dic[v] = f"{temp_dic[v]}, {cn}"

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


def compare_data(Active_name, Compare_name, Reduce_dic):
	if (Reduce_dic["BS"] or Reduce_dic["BD"]) and Reduce_dic["NOT_TABLE"]:
		Reduce_dic["NOT_TABLE"] = False
	actvie_dic = get_data(Active_name, Reduce_dic)[1]
	comp_dic = get_data(Compare_name, Reduce_dic)[1]

	result_dic = {}
	for type_name in actvie_dic.keys():
		partly_tb_act = actvie_dic[type_name]
		partly_tb_pre = comp_dic[type_name]

		editors = partly_tb_act.columns.tolist()
		items = partly_tb_act.index.tolist()
		type_res_dic = {}
		for itm in items:
			if itm in ["area", "region", "space_data", "active_operator"]:
				continue
			res_itm_for_edi = {}
			for edi in editors:
				act = partly_tb_act.at[itm, edi]
				pre = partly_tb_pre.at[itm, edi]
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
					elif edi_num > 1 and edi_num == len(COL_NAMES ) -1:
						inverted_dic["他の全て"] = inverted_dic.pop(key)
				type_res_dic[itm] = inverted_dic
		result_dic[type_name] = type_res_dic
	return result_dic


@st.cache
def get_data(Data_name, Reduce_dic):
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
				if Reduce_dic["AT"]:
					value = context[rn].split(" at ")[0]
				else:
					value = context[rn]
				if not Reduce_dic["NOT_TABLE"]:
					if Reduce_dic["BS"]:
						value = value.replace("<bpy_struct", "<b_s")
					if Reduce_dic["BD"]:
						value = value.replace("bpy.data.objects", "D.obs").replace("bpy.data.", "D.")
				temp_dic[rn].append(value)
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
def get_editor_data(Editor_names, Reduce_dic):
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
						if Reduce_dic["AT"]:
							value = context[rn].split(" at ")[0]
						else:
							value = context[rn]
						if not Reduce_dic["NOT_TABLE"]:
							if Reduce_dic["BS"]:
								value = value.replace("<bpy_struct", "<b_s")
							if Reduce_dic["BD"]:
								value = value.replace("bpy.data.objects", "D.obs").replace("bpy.data.", "D.")
						temp_dic[rn].append(value)
					else:
						temp_dic[rn].append("項目なし")


			list_2d = [temp_dic[rn] if rn in temp_dic else ["項目なし"]*len(col_names)
						for rn in row_names_by_type]
			table = pd.DataFrame(list_2d, columns=col_names, index=row_names_by_type)
			tbdic_by_type[ct_type_name] = table

		outcome_dic[edi] = tbdic_by_type

	return outcome_dic



#--------- ここから streamlit の表示設定 -------------------


# モード設定の表示-------------------------


def color_style(val):
	color_dic = {"項目なし":'gray', "None":'red', "[]":'blue'}
	if val in color_dic:
		color = color_dic[val]
	else:
		color = 'green'
	return 'color: %s' % color

"""
# context.copy() の結果を比較する
"""
reduce_at = st.checkbox("bpy_struct の 'at'以下の差異を無視する", True)
st.empty()
page_mode = st.radio("context の比較方法",
			["Blender の状態を固定して、エディタ同士を比較する",
			 "エディタを固定して Blender の状態同士を比較する"])

st.markdown("省略の設定")
red_col1, red_col2, red_col3 = st.beta_columns(3)
reduce_bs = red_col1.checkbox("'<bpy_stcur' → '<b_s'", True)
reduce_bd = red_col2.checkbox("'bpy.data' → 'D'、 'objects' → 'obs'", True)
not_aply_table = red_col3.checkbox("表では省略を適用しない", False)
st.markdown("------------------")

REDUCE_DIC = {"AT":reduce_at, "BS":reduce_bs, "BD":reduce_bd,
			"NOT_TABLE":not_aply_table}

# サイドバーの設定-------------------------


if page_mode == "Blender の状態を固定して、エディタ同士を比較する":
	if BE_1st in context_DATA_dic:
		idx = list(context_DATA_dic.keys()).index(BE_1st)
	else:
		idx = 0
	target_name = st.sidebar.radio("Blender の状態", list(context_DATA_dic.keys()), index=idx)
	st.sidebar.markdown("---------------------")

	compare_dic = {
			f"「{x.split(' + ')[0]}」と比較" if x!=target_name else "比較しない":x
			for x in context_DATA_dic.keys() }
	compare_item = st.sidebar.radio("2つの状態の比較",
					sorted(list(compare_dic.keys()),reverse=True))
else:
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



# データフレームの表示-------------------------


if page_mode == "エディタを固定して Blender の状態同士を比較する":
	"""
	## ◇ Blender の状態同士を比較する
	`項目なし`は、そのエリアの context に該当項目が含まれないことを示す
	"""

	if edi_names:
		edi_dic = get_editor_data(edi_names, REDUCE_DIC)
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

				diff_dic = extract_diff_as_dict(df)
				with st.beta_expander("差異　(D = bpy.data,　obs = objects)", expanded=True):
					st.write(diff_dic)
					st.markdown("---------------")

			st.markdown("---------")

else:
	#-- API Doc 準拠 -------------------

	"""
	## ◇ API Doc の分類に準拠した表
	*　`項目なし`は、そのエリアの context に該当項目が含まれないことを示す
	* Global と Screen 以外は関連するエディタのみを表示
	"""

	table, outcome_dic = get_data(target_name, REDUCE_DIC)
	diff_result = None

	if compare_item != "比較しない":
		comp_name = compare_dic[compare_item]
		diff_result = compare_data(target_name, comp_name, REDUCE_DIC)


	for context_type in outcome_dic.keys():
		st.markdown(f"### ◇ {context_type}")
		partly_table = outcome_dic[context_type]
		if context_type in EDITORS_BY_TYPE:
			partly_table = partly_table[EDITORS_BY_TYPE[context_type]]
		st.dataframe(partly_table.style.applymap(color_style))

		if diff_result is not None:
			partly_compared = diff_result[context_type]
			with st.beta_expander("比較結果", expanded=True):
				st.write(partly_compared)
				
		
		if len(partly_table.columns) >= 2:
			partly_row_names = partly_table.index.tolist()
			diff_dic = extract_diff_as_dict(partly_table)
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

		all_diff_dic = extract_diff_as_dict(table)
		st.write(all_diff_dic)
