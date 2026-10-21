import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {execFileSync} from 'node:child_process';

const options = {};
for (let i = 2; i < process.argv.length; i += 2) {
  if (!process.argv[i]?.startsWith('--') || !process.argv[i + 1]) throw Error('参数必须为 --key value');
  options[process.argv[i].slice(2)] = process.argv[i + 1];
}
for (const key of ['tasks', 'ccn-root', 'work-root', 'review-dir', 'node-modules', 'python']) {
  if (!options[key]) throw Error(`缺少 --${key}`);
}
const directory = path.resolve(options['review-dir']);
const helper = path.join(path.dirname(fileURLToPath(import.meta.url)), 'review_workbook.py');
const runPython = (...args) => execFileSync(options.python,
  [helper, ...args, '--work-root', options['work-root'], '--review-dir', directory], {stdio: 'inherit'});
// Resolve bundled dependencies without modifying the repository or dependency runtime.
const require = createRequire(path.join(path.resolve(options['node-modules']), '_ccn_resolve.cjs'));
const {Workbook, SpreadsheetFile} = await import(pathToFileURL(require.resolve('@oai/artifact-tool')).href);
runPython('prepare', '--tasks', options.tasks, '--ccn-root', options['ccn-root']);
const manifestPath = path.join(directory, 'manifest.json');
const bytes = await fs.readFile(manifestPath);
const manifest = JSON.parse(bytes.toString('utf8'));
const manifestHash = crypto.createHash('sha256').update(bytes).digest('hex');
const wb = Workbook.create();
const main = wb.worksheets.add('审阅表');
const choices = wb.worksheets.add('分类枚举');
const links = [];
const count = manifest.rows.length, end = count + 7, approval = manifest.approval_row;
const parents = Object.keys(manifest.registry);
const pairs = parents.flatMap(p => manifest.registry[p].map(c => [p, c]));
const col = n => {let s = ''; for (; n; n = Math.floor((n - 1) / 26)) s = String.fromCharCode(65 + (n - 1) % 26) + s; return s;};
function style(sheet, range, widths) {
  sheet.showGridLines = false;
  sheet.getRange(range).format.font = {name: 'Microsoft YaHei', size: 11, color: '#253247'};
  sheet.getRange(range).format.wrapText = true;
  sheet.getRange(range).format.verticalAlignment = 'center';
  widths.forEach((w, i) => sheet.getRangeByIndexes(0, i, Number(range.match(/\d+$/)[0]), 1).format.columnWidthPx = w);
}
function heading(sheet, range) {
  sheet.getRange(range).format = {fill: '#243B60', font: {name: 'Microsoft YaHei', size: 11, bold: true, color: '#FFFFFF'},
    horizontalAlignment: 'center', verticalAlignment: 'center', wrapText: true, rowHeight: 34};
}
function title(sheet, text, last) {
  sheet.getRange(`A2:${last}2`).merge(); sheet.getRange('A2').values = [[text]];
  sheet.getRange(`A2:${last}2`).format.rowHeight = 34;
  sheet.getRange('A2').format.font = {size: 17, bold: true, color: '#243B60'};
}
function link(sheet, index, cell, target) {
  links.push({sheet: index, cell, target});
  sheet.getRange(cell).format.font = {color: '#1663AC', underline: 'single'};
}
style(main, `A1:K${approval+3}`, [65,235,340,340,210,270,480,300,260,240,210]);
title(main, `CCN 快报人工审阅 · ${count} 项任务`, 'K');
main.getRange('A4:K4').merge();
main.getRange('A4').values = [['先选人工一级，再选对应二级；两列留空保留 AI 分类。更换一级后旧二级不自动清空，不匹配时标红。']];
main.getRange('A5:K5').merge();
main.getRange('A5').values = [['API 字段取自本轮任务快照。本地目录与信息源可点击。一级直归须符合综述规则。']];
main.getRange('A7:K7').values = [['API 编号','API 任务编号','API 任务主题','API 任务信息源（URL）','API 指定分类','AI 当前分类','交付件目录（本地）','目录内容','人工一级分类（下拉）','人工二级分类（联动）','分类选择检查']];
heading(main, 'A7:K7');
main.getRange(`A8:K${end}`).values = manifest.rows.map(r => [...r, '', '', '']);
manifest.rows.forEach((row, i) => {
  const r = i + 8;
  main.getRange(`A${r}:K${r}`).format.rowHeight = 100;
  main.getRange(`A${r}:H${r}`).format.fill = i % 2 ? '#F2F5F9' : '#FFFFFF';
  link(main, 1, `D${r}`, row[3]); link(main, 1, `G${r}`, pathToFileURL(row[6]).href);
  main.getRange(`J${r}`).dataValidation = {rule: {type: 'list', formula1: `INDIRECT(IF($I${r}="","CCN_EMPTY","CCN_SUB_"&LEFT($I${r},2)))`}};
  main.getRange(`K${r}`).formulas = [[`=IF(AND(I${r}="",J${r}=""),"保留AI分类",IF(I${r}="","请先选一级",IF(J${r}="","待选二级（综述可留空）",IF(COUNTIFS('分类枚举'!$B$5:$B$${4+pairs.length},I${r},'分类枚举'!$C$5:$C$${4+pairs.length},J${r})=1,"有效","二级不匹配，请重选"))))`]];
});
main.getRange(`I8:J${end}`).format.fill = '#FFF2CC';
main.getRange(`I8:I${end}`).dataValidation = {rule: {type: 'list', formula1: 'CCN_PRIMARY'}};
main.getRange(`I8:K${end}`).conditionalFormats.addCustom(`AND($J8<>"",COUNTIFS('分类枚举'!$B$5:$B$${4+pairs.length},$I8,'分类枚举'!$C$5:$C$${4+pairs.length},$J8)=0)`, {fill: '#FCE4D6', font: {color: '#9C2424', bold: true}});
main.getRange(`A${approval}:B${approval+2}`).values = [['批次结论','待审核'],['审核人',''],['审核日期','']];
main.getRange(`B${approval}:B${approval+2}`).format.fill = '#FFF2CC';
main.getRange(`B${approval}`).dataValidation = {rule: {type: 'list', values: ['待审核','通过','修改后再审']}};
main.freezePanes.freezeRows(7); main.freezePanes.freezeColumns(2);
style(choices, `A1:${col(5+parents.length)}${Math.max(pairs.length, parents.length)+4}`, [65,430,290,30,430]);
choices.getRange('I1:I2').values = [['批次快照 SHA-256', manifestHash]];
title(choices, `分类枚举：${parents.length} 个一级，${pairs.length} 个二级`, 'C');
choices.getRange('A4:C4').values = [['序号','一级分类','二级分类']]; heading(choices, 'A4:C4');
choices.getRange(`A5:C${4+pairs.length}`).values = pairs.map((p,i) => [i+1,...p]);
choices.getRange(`E5:E${4+parents.length}`).values = parents.map(p => [p]);
parents.forEach((p,i) => {
  const c=col(i+6), kids=manifest.registry[p];
  choices.getRange(`${c}4`).values=[[p]]; choices.getRange(`${c}5:${c}${4+kids.length}`).values=kids.map(x=>[x]);
  choices.getRange(`${c}4:${c}${4+kids.length}`).format.columnWidthPx=300;
});
choices.getRange(`A5:C${4+pairs.length}`).format.rowHeight=25;
// Exercise dependent status formulas without retaining synthetic inputs.
for (const [p,c,want] of [[parents[0],pairs[0][1],'有效'],['',pairs[0][1],'请先选一级'],['','','保留AI分类']]) {
  main.getRange('I8:J8').values=[[p,c]];wb.recalculate();
  if(main.getRange('K8').values[0][0]!==want)throw Error('分类检查公式验证失败');
}
main.getRange('I8:J8').values=[['','']]; wb.recalculate();
const scan=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?',options:{useRegex:true,maxResults:10},maxChars:1000});
await fs.writeFile(path.join(directory,'formula-scan.ndjson'),scan.ndjson);
for(const [sheetName,range] of [['审阅表',`A1:K${Math.min(end,12)}`],['分类枚举',`A1:C${Math.min(4+pairs.length,18)}`]]) {
  const image=await wb.render({sheetName,range,scale:1,format:'png'});
  await fs.writeFile(path.join(directory,`${sheetName}-preview.png`),new Uint8Array(await image.arrayBuffer()));
}
await (await SpreadsheetFile.exportXlsx(wb)).save(path.join(directory,'review.xlsx'));
await fs.writeFile(path.join(directory,'links.json'),JSON.stringify(links));
runPython('finish');
console.log(`Created ${path.join(directory,'review.xlsx')} (${count} tasks, ${manifest.evidence.length} files)`);
