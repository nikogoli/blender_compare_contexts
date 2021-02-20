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
COL_NAMES = [None] * 16
ROW_NAMES = []


def extract_diff_dict(Table, Row_names, Col_names):
	out_dic = {}
	for rn in Row_names:
		if rn in ["area", "region", "space_data", "active_operator"]:
			continue
		values = Table.loc[rn].tolist()
		if len(set(values)) >= 2:
			temp_dic = {x:[] for x in list(set(values))}
			for cn, v in zip(Col_names, values):
				temp_dic[v].append(cn)
			out_dic[rn] = temp_dic

	for key in out_dic.keys():
		for kk in out_dic[key].keys():
			if len(out_dic[key][kk]) == len(Col_names)-1:
				out_dic[key][kk] = "他の全て"
			elif len(out_dic[key][kk]) == 1:
				out_dic[key][kk] = out_dic[key][kk][0]
			elif len(out_dic[key][kk]) >= 5:
				out_dic[key][kk] = "それ以外"
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

	return table, outcome_dic, COL_NAMES, ROW_NAMES


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





#--------- ここから streamlit の表示設定 -------------------


# サイドバーの設定-------------------------

if "初期状態" in context_DATA_dic:
	idx = list(context_DATA_dic.keys()).index("初期状態")
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
* 各エリアにオペレーターを設置し、`bpy.context.copy()` を保存
"""

#-- API Doc 準拠 -------------------

"""
## ◇ API Doc の分類に準拠した表
`項目なし`は、そのエリアの context に該当項目が含まれないことを示す
"""

is_limit = st.checkbox("Global と Screen 以外は関連するエディタのみ表示", True)

table, outcome_dic, COL_NAMES, ROW_NAMES = get_data(Data_name=target_name)
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
		diff_dic = extract_diff_dict(partly_table, partly_row_names, COL_NAMES)
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

	all_diff_dic = extract_diff_dict(table, ROW_NAMES, COL_NAMES)
	st.write(all_diff_dic)
