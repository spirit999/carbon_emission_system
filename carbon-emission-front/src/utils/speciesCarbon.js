/**
 * 解析 /carbonEmission/listSpeciesCarbon 的 data 字段：
 * 新接口为 { list: [...], actualYear }，旧接口可能直接为数组。
 */
export function extractSpeciesCarbonList(data) {
  if (data == null) return [];
  if (Array.isArray(data)) return data;
  if (data.list != null && Array.isArray(data.list)) return data.list;
  return [];
}

export function rowToSpeciesAmount(row) {
  if (!row || typeof row !== 'object') return 0;
  const raw = row.emissionAmount != null ? row.emissionAmount : row.amount;
  const n = Number(raw);
  return Number.isFinite(n) ? n : 0;
}

export function rowToSpeciesName(row) {
  if (!row || typeof row !== 'object') return '-';
  return row.objectCategory || row.category || '-';
}
