from export_sanpra.export_sanpra.report.exposure_grouping import execute

def run():
 result={}
 for dimension in ("Currency","Customer","Sales Order","Bank"):
  columns,data,_,chart,summary=execute({"company":"Nutrich Foods Pvt Ltd","group_by":dimension})
  result[dimension]={"columns":len(columns),"rows":len(data),"chart_labels":len(chart["data"]["labels"]),"summary":len(summary),"passed":len(data)==len(chart["data"]["labels"])}
 result["all_passed"]=all(x["passed"] for x in result.values())
 return result
