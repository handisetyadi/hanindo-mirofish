/**
 * Allowed seed-document extensions (must stay in sync with backend Config.ALLOWED_EXTENSIONS).
 */
export const UPLOAD_ACCEPT_EXTENSIONS = [
  'pdf',
  'md',
  'markdown',
  'txt',
  'csv',
  'tsv',
  'xlsx',
  'xls',
  'xlsm',
  'doc',
  'docx',
  'ppt',
  'pptx',
  'html',
  'htm',
  'xml',
  'json',
  'rtf',
  'yaml',
  'yml',
  'log'
]

/** `accept` attribute for <input type="file"> */
export const UPLOAD_ACCEPT_ATTR = UPLOAD_ACCEPT_EXTENSIONS.map((e) => `.${e}`).join(',')

export function isAllowedUploadFilename(name) {
  if (!name || !name.includes('.')) return false
  const ext = name.split('.').pop().toLowerCase()
  return UPLOAD_ACCEPT_EXTENSIONS.includes(ext)
}
