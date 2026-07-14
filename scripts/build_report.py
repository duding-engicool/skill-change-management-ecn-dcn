#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""变更管理（ECN/DCN）记录生成器：读取结构化数据，输出纯文字版 TXT + Markdown。
内置 ECN / DCN 小样本，直接运行 `python build_report.py` 即可产出样例。
产物默认写到当前工作目录（用户目录），不留在技能目录内。
"""
import argparse
import json
import os
import sys

# 内置小样本（演示用，非真实数据）
SAMPLE_ECN = {
    "type": "ECN",
    "no": "ECN-2026-0713-01",
    "title": "密封圈材料由丁腈橡胶改为氟橡胶",
    "applicant": "王工（设计）",
    "date": "2026-07-13",
    "object": {"part_no": "P-10023", "part_name": "出水阀密封圈",
               "current_rev": "C", "new_rev": "D"},
    "change_type": "材料",
    "description": "密封圈材料由丁腈橡胶A（NBR）改为氟橡胶B（FKM），尺寸不变，硬度由 70±5 调为 75±5 Shore A。",
    "reason": "客户要求耐温由 90℃ 提升至 120℃，橡胶A 不满足。",
    "impact": {
        "4m": "料：材料牌号变更；法：检验规范更新；机/人/环：无需变更",
        "cost": "单件成本 +0.3 元",
        "schedule": "验证周期 +5 天",
        "regulatory": "满足客户 CSR 耐温要求；RoHS/REACH 待确认",
        "related_products": "出水阀总成 VA-200（共用该密封圈）",
    },
    "related_docs": [
        {"doc": "BOM VA-200", "action": "版本 C→D"},
        {"doc": "DFMEA VA-200", "action": "更新材料失效模式"},
        {"doc": "控制计划 CP-10023", "action": "更新进料检验特性"},
        {"doc": "检验规范 IS-10023", "action": "更新材质与硬度检验"},
        {"doc": "SOP 装配线3", "action": "无需变更"},
    ],
    "verification": "首批 200 件型式试验（耐温+密封）+ PPAP 提交等级 3",
    "approval": [
        {"role": "设计", "name": "王工", "result": "同意"},
        {"role": "工艺", "name": "李PE", "result": "同意"},
        {"role": "质量", "name": "赵QE", "result": "同意"},
        {"role": "批准", "name": "周经理", "result": "批准"},
    ],
    "switch_plan": "生效日 2026-07-20；旧版库存 500 件用完即止不返工；断点：批次号 B0720 起执行新版。",
    "closure": "PPAP 批准通过，变更闭环归档。",
}

SAMPLE_DCN = {
    "type": "DCN",
    "no": "DCN-2026-0713-02",
    "title": "SOP 装配线3 更新扭矩记录要求",
    "applicant": "李PE（工艺）",
    "date": "2026-07-13",
    "doc_info": {"doc_name": "SOP 装配线3 出水阀总成", "doc_no": "WI-VA200-03",
                 "current_rev": "V2.1", "new_rev": "V2.2"},
    "doc_category": "作业指导书(SOP/WI)",
    "reason": "审核发现扭矩记录未留痕，补充记录栏与自检要求。",
    "description": "在步骤 5（拧紧出水阀）后增加扭矩记录栏；新增操作员自检签名；其余步骤不变。",
    "impact": {
        "affected": "装配线3 全体操作员、IPQC 巡检",
        "related_docs": "检验记录表 RC-VA200（同步增加扭矩栏）",
    },
    "training": "装配线3 全员重新培训并签到，记录在 WI 附件。",
    "approval": [
        {"role": "编制", "name": "李PE", "result": "编制"},
        {"role": "审核", "name": "赵QE", "result": "审核通过"},
        {"role": "批准/文控", "name": "钱文控(DCC)", "result": "批准并发放"},
    ],
    "distribution": "受控分发：装配线3 现场看板、文控服务器；旧版 V2.1 回收作废。",
    "effective_date": "2026-07-18",
    "closure": "新版受控发放完成，旧版已回收，变更闭环。",
}


# ---------------- ECN ----------------
def build_ecn_md(d):
    o = d.get("object", {})
    lines = []
    lines.append(f"# ECN 工程变更记录（{d.get('no','—')}）\n")
    lines.append(f"**变更标题**：{d.get('title','—')}")
    lines.append(f"**申请人**：{d.get('applicant','—')}　**日期**：{d.get('date','—')}")
    lines.append(f"**变更类型**：{d.get('change_type','—')}\n")
    lines.append("## 一、变更对象\n")
    lines.append(f"- 零件/图号：{o.get('part_no','—')}　名称：{o.get('part_name','—')}")
    lines.append(f"- 版本：{o.get('current_rev','—')} → {o.get('new_rev','—')}\n")
    lines.append("## 二、变更内容描述\n")
    lines.append(d.get("description", "（待补充）") + "\n")
    lines.append("## 三、变更原因\n")
    lines.append(d.get("reason", "（待补充）") + "\n")
    imp = d.get("impact", {})
    lines.append("## 四、影响分析\n")
    lines.append(f"- **4M 影响**：{imp.get('4m','待补充')}")
    lines.append(f"- **成本**：{imp.get('cost','待补充')}")
    lines.append(f"- **交期**：{imp.get('schedule','待补充')}")
    lines.append(f"- **法规/CSR**：{imp.get('regulatory','待补充')}")
    lines.append(f"- **关联产品**：{imp.get('related_products','待补充')}\n")
    lines.append("## 五、关联文件同步清单\n")
    lines.append("| 关联文件 | 同步动作 |")
    lines.append("|----------|----------|")
    for r in d.get("related_docs", []):
        lines.append(f"| {r.get('doc','')} | {r.get('action','')} |")
    lines.append("")
    lines.append("## 六、验证方案\n")
    lines.append(d.get("verification", "（待补充）") + "\n")
    lines.append("## 七、评审与批准\n")
    lines.append("| 角色 | 签署人 | 结论 |")
    lines.append("|------|--------|------|")
    for a in d.get("approval", []):
        lines.append(f"| {a.get('role','')} | {a.get('name','')} | {a.get('result','')} |")
    lines.append("")
    lines.append("## 八、切换与实施计划\n")
    lines.append(d.get("switch_plan", "（待补充）") + "\n")
    lines.append("## 九、闭环与归档\n")
    lines.append(d.get("closure", "（待补充）") + "\n")
    lines.append("## 说明\n")
    lines.append("- 本记录为变更受控台账，放行/批准结论由相关签署人判定，技能不替用户做决定。")
    lines.append("- 影响分析与关联文件清单为通用参考维度，企业具体准则「待企业补充」。")
    return "\n".join(lines)


def build_ecn_txt(d):
    o = d.get("object", {})
    imp = d.get("impact", {})
    lines = []
    lines.append("ECN 工程变更记录")
    lines.append("=" * 48)
    lines.append(f"编号：{d.get('no','—')}")
    lines.append(f"变更标题：{d.get('title','—')}")
    lines.append(f"申请人：{d.get('applicant','—')}　日期：{d.get('date','—')}")
    lines.append(f"变更类型：{d.get('change_type','—')}")
    lines.append("")
    lines.append("一、变更对象")
    lines.append("-" * 48)
    lines.append(f"零件/图号：{o.get('part_no','—')}　名称：{o.get('part_name','—')}")
    lines.append(f"版本：{o.get('current_rev','—')} → {o.get('new_rev','—')}")
    lines.append("")
    lines.append("二、变更内容描述")
    lines.append("-" * 48)
    lines.append(d.get("description", "（待补充）"))
    lines.append("")
    lines.append("三、变更原因")
    lines.append("-" * 48)
    lines.append(d.get("reason", "（待补充）"))
    lines.append("")
    lines.append("四、影响分析")
    lines.append("-" * 48)
    lines.append(f"4M 影响：{imp.get('4m','待补充')}")
    lines.append(f"成本：{imp.get('cost','待补充')}")
    lines.append(f"交期：{imp.get('schedule','待补充')}")
    lines.append(f"法规/CSR：{imp.get('regulatory','待补充')}")
    lines.append(f"关联产品：{imp.get('related_products','待补充')}")
    lines.append("")
    lines.append("五、关联文件同步清单")
    lines.append("-" * 48)
    for r in d.get("related_docs", []):
        lines.append(f"- {r.get('doc','')}：{r.get('action','')}")
    lines.append("")
    lines.append("六、验证方案")
    lines.append("-" * 48)
    lines.append(d.get("verification", "（待补充）"))
    lines.append("")
    lines.append("七、评审与批准")
    lines.append("-" * 48)
    for a in d.get("approval", []):
        lines.append(f"- {a.get('role','')}：{a.get('name','')}（{a.get('result','')}）")
    lines.append("")
    lines.append("八、切换与实施计划")
    lines.append("-" * 48)
    lines.append(d.get("switch_plan", "（待补充）"))
    lines.append("")
    lines.append("九、闭环与归档")
    lines.append("-" * 48)
    lines.append(d.get("closure", "（待补充）"))
    lines.append("")
    return "\n".join(lines)


# ---------------- DCN ----------------
def build_dcn_md(d):
    di = d.get("doc_info", {})
    imp = d.get("impact", {})
    lines = []
    lines.append(f"# DCN 文件变更记录（{d.get('no','—')}）\n")
    lines.append(f"**变更标题**：{d.get('title','—')}")
    lines.append(f"**申请人**：{d.get('applicant','—')}　**日期**：{d.get('date','—')}")
    lines.append(f"**文件类别**：{d.get('doc_category','—')}\n")
    lines.append("## 一、变更文件\n")
    lines.append(f"- 文件名称：{di.get('doc_name','—')}　编号：{di.get('doc_no','—')}")
    lines.append(f"- 版本：{di.get('current_rev','—')} → {di.get('new_rev','—')}\n")
    lines.append("## 二、变更内容摘要\n")
    lines.append(d.get("description", "（待补充）") + "\n")
    lines.append("## 三、变更原因\n")
    lines.append(d.get("reason", "（待补充）") + "\n")
    lines.append("## 四、影响分析\n")
    lines.append(f"- **受影响岗位/工序**：{imp.get('affected','待补充')}")
    lines.append(f"- **关联文件**：{imp.get('related_docs','待补充')}\n")
    lines.append("## 五、培训要求\n")
    lines.append(d.get("training", "（如无需培训填“无需”）") + "\n")
    lines.append("## 六、评审与批准 / 文控\n")
    lines.append("| 角色 | 签署人 | 结论 |")
    lines.append("|------|--------|------|")
    for a in d.get("approval", []):
        lines.append(f"| {a.get('role','')} | {a.get('name','')} | {a.get('result','')} |")
    lines.append("")
    lines.append("## 七、生效与受控分发\n")
    lines.append(f"- **生效日期**：{d.get('effective_date','待补充')}")
    lines.append(f"- **分发/作废**：{d.get('distribution','待补充')}\n")
    lines.append("## 八、闭环与归档\n")
    lines.append(d.get("closure", "（待补充）") + "\n")
    lines.append("## 说明\n")
    lines.append("- 本记录为文件受控台账，批准/发放由文控(DCC)与相关签署人判定，技能不替用户做决定。")
    lines.append("- 文件类别与分发要求为通用参考，企业具体文控规则「待企业补充」。")
    return "\n".join(lines)


def build_dcn_txt(d):
    di = d.get("doc_info", {})
    imp = d.get("impact", {})
    lines = []
    lines.append("DCN 文件变更记录")
    lines.append("=" * 48)
    lines.append(f"编号：{d.get('no','—')}")
    lines.append(f"变更标题：{d.get('title','—')}")
    lines.append(f"申请人：{d.get('applicant','—')}　日期：{d.get('date','—')}")
    lines.append(f"文件类别：{d.get('doc_category','—')}")
    lines.append("")
    lines.append("一、变更文件")
    lines.append("-" * 48)
    lines.append(f"文件名称：{di.get('doc_name','—')}　编号：{di.get('doc_no','—')}")
    lines.append(f"版本：{di.get('current_rev','—')} → {di.get('new_rev','—')}")
    lines.append("")
    lines.append("二、变更内容摘要")
    lines.append("-" * 48)
    lines.append(d.get("description", "（待补充）"))
    lines.append("")
    lines.append("三、变更原因")
    lines.append("-" * 48)
    lines.append(d.get("reason", "（待补充）"))
    lines.append("")
    lines.append("四、影响分析")
    lines.append("-" * 48)
    lines.append(f"受影响岗位/工序：{imp.get('affected','待补充')}")
    lines.append(f"关联文件：{imp.get('related_docs','待补充')}")
    lines.append("")
    lines.append("五、培训要求")
    lines.append("-" * 48)
    lines.append(d.get("training", "（如无需培训填“无需”）"))
    lines.append("")
    lines.append("六、评审与批准 / 文控")
    lines.append("-" * 48)
    for a in d.get("approval", []):
        lines.append(f"- {a.get('role','')}：{a.get('name','')}（{a.get('result','')}）")
    lines.append("")
    lines.append("七、生效与受控分发")
    lines.append("-" * 48)
    lines.append(f"生效日期：{d.get('effective_date','待补充')}")
    lines.append(f"分发/作废：{d.get('distribution','待补充')}")
    lines.append("")
    lines.append("八、闭环与归档")
    lines.append("-" * 48)
    lines.append(d.get("closure", "（待补充）"))
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", help="JSON 输入文件路径（缺省用内置小样本）")
    ap.add_argument("--type", choices=["ecn", "dcn"], help="内置样本类型（仅 --input 缺省时生效）")
    ap.add_argument("--out-dir", help="输出目录（缺省为当前工作目录）")
    ap.add_argument("--format", choices=["txt", "md", "all"], default="all",
                    help="输出格式：txt=纯文字版，md=Markdown，all=两者（默认）")
    a = ap.parse_args()

    if a.input:
        try:
            data = json.load(open(a.input, encoding="utf-8"))
        except Exception as e:
            print(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False))
            sys.exit(1)
    else:
        data = SAMPLE_ECN if (a.type or "ecn") == "ecn" else SAMPLE_DCN

    ctype = (data.get("type") or "ECN").upper()
    builders = {
        "ECN": (build_ecn_md, build_ecn_txt),
        "DCN": (build_dcn_md, build_dcn_txt),
    }
    if ctype not in builders:
        print(json.dumps({"status": "error", "message": f"不支持的变更类型: {ctype}"}, ensure_ascii=False))
        sys.exit(1)
    build_md, build_txt_fn = builders[ctype]

    out_dir = a.out_dir or os.getcwd()
    os.makedirs(out_dir, exist_ok=True)

    tag = data.get("no") or data.get("date", "").replace("-", "") or "样例"
    base = f"{ctype}变更记录_{tag}"

    result = {"status": "success", "type": ctype, "files": []}
    if a.format in ("md", "all"):
        md_path = os.path.join(out_dir, base + ".md")
        open(md_path, "w", encoding="utf-8").write(build_md(data))
        result["files"].append(md_path)
    if a.format in ("txt", "all"):
        txt_path = os.path.join(out_dir, base + ".txt")
        open(txt_path, "w", encoding="utf-8").write(build_txt_fn(data))
        result["files"].append(txt_path)

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
