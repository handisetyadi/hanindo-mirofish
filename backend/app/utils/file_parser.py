"""
文件解析工具
从多种常见「现实种子」文档中提取文本（与 Config.ALLOWED_EXTENSIONS 对齐）
"""

import os
from pathlib import Path
from typing import List

from ..config import Config


def _read_text_with_fallback(file_path: str) -> str:
    """
    读取文本文件，UTF-8失败时自动探测编码。

    采用多级回退策略：
    1. 首先尝试 UTF-8 解码
    2. 使用 charset_normalizer 检测编码
    3. 回退到 chardet 检测编码
    4. 最终使用 UTF-8 + errors='replace' 兜底
    """
    data = Path(file_path).read_bytes()

    try:
        return data.decode('utf-8')
    except UnicodeDecodeError:
        pass

    encoding = None
    try:
        from charset_normalizer import from_bytes
        best = from_bytes(data).best()
        if best and best.encoding:
            encoding = best.encoding
    except Exception:
        pass

    if not encoding:
        try:
            import chardet
            result = chardet.detect(data)
            encoding = result.get('encoding') if result else None
        except Exception:
            pass

    if not encoding:
        encoding = 'utf-8'

    return data.decode(encoding, errors='replace')


class FileParser:
    """文件解析器（扩展名集合以 Config.ALLOWED_EXTENSIONS 为准）"""

    @staticmethod
    def _allowed_suffixes() -> set:
        return {f'.{e}' for e in Config.ALLOWED_EXTENSIONS}

    @staticmethod
    def _dataframe_to_plain(df) -> str:
        import pandas as pd

        if not isinstance(df, pd.DataFrame):
            return ''
        out = df.fillna('').astype(str)
        return out.to_csv(sep='\t', index=False, header=False).strip()

    @classmethod
    def _read_csv_like(cls, file_path: str, sep: str) -> str:
        import pandas as pd

        last_err: Exception | None = None
        for enc in ('utf-8-sig', 'utf-8', 'gbk', 'cp1252', 'latin-1'):
            try:
                df = pd.read_csv(
                    file_path,
                    sep=sep,
                    encoding=enc,
                    header=None,
                    on_bad_lines='skip',
                )
                return cls._dataframe_to_plain(df)
            except Exception as e:
                last_err = e
        try:
            df = pd.read_csv(
                file_path,
                sep=sep,
                encoding_errors='replace',
                header=None,
                on_bad_lines='skip',
                engine='python',
            )
            return cls._dataframe_to_plain(df)
        except Exception:
            if last_err:
                raise last_err
            raise

    @classmethod
    def _extract_spreadsheet(cls, file_path: str) -> str:
        import pandas as pd

        suffix = Path(file_path).suffix.lower()
        if suffix == '.csv':
            return cls._read_csv_like(file_path, sep=',')
        if suffix == '.tsv':
            return cls._read_csv_like(file_path, sep='\t')
        if suffix in ('.xlsx', '.xlsm'):
            excel = pd.ExcelFile(file_path, engine='openpyxl')
        elif suffix == '.xls':
            excel = pd.ExcelFile(file_path, engine='xlrd')
        else:
            raise ValueError(f"未实现的表格格式: {suffix}")

        parts: List[str] = []
        for sheet_name in excel.sheet_names:
            df = pd.read_excel(excel, sheet_name=sheet_name, header=None)
            body = cls._dataframe_to_plain(df)
            if body.strip():
                parts.append(f"=== Sheet: {sheet_name} ===\n{body}")
        return '\n\n'.join(parts) if parts else ''

    @staticmethod
    def _extract_unstructured(file_path: str) -> str:
        try:
            from unstructured.partition.auto import partition
        except ImportError as e:
            raise ImportError("需要安装 unstructured 以解析该 Office 文档") from e

        elements = partition(filename=str(file_path))
        texts = [
            str(el.text).strip()
            for el in elements
            if getattr(el, 'text', None) and str(el.text).strip()
        ]
        return '\n\n'.join(texts) if texts else ''

    @classmethod
    def extract_text(cls, file_path: str) -> str:
        """
        从文件中提取文本

        Args:
            file_path: 文件路径

        Returns:
            提取的文本内容
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        suffix = path.suffix.lower()
        if suffix not in cls._allowed_suffixes():
            raise ValueError(f"不支持的文件格式: {suffix}")

        if suffix == '.pdf':
            return cls._extract_from_pdf(file_path)
        if suffix in {'.md', '.markdown'}:
            return cls._extract_from_md(file_path)
        if suffix in {'.txt', '.log', '.json', '.xml', '.yaml', '.yml', '.html', '.htm'}:
            return cls._extract_from_txt(file_path)
        if suffix in {'.csv', '.tsv', '.xlsx', '.xls', '.xlsm'}:
            return cls._extract_spreadsheet(file_path)
        if suffix in {'.doc', '.docx', '.ppt', '.pptx', '.rtf'}:
            return cls._extract_unstructured(file_path)

        raise ValueError(f"无法处理的文件格式: {suffix}")

    @staticmethod
    def _extract_from_pdf(file_path: str) -> str:
        """从PDF提取文本"""
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError("需要安装PyMuPDF: pip install PyMuPDF")

        text_parts = []
        with fitz.open(file_path) as doc:
            for page in doc:
                text = page.get_text()
                if text.strip():
                    text_parts.append(text)

        return '\n\n'.join(text_parts)

    @staticmethod
    def _extract_from_md(file_path: str) -> str:
        """从Markdown提取文本，支持自动编码检测"""
        return _read_text_with_fallback(file_path)

    @staticmethod
    def _extract_from_txt(file_path: str) -> str:
        """从TXT提取文本，支持自动编码检测"""
        return _read_text_with_fallback(file_path)

    @classmethod
    def extract_from_multiple(cls, file_paths: List[str]) -> str:
        """
        从多个文件提取文本并合并

        Args:
            file_paths: 文件路径列表

        Returns:
            合并后的文本
        """
        all_texts = []

        for i, file_path in enumerate(file_paths, 1):
            try:
                text = cls.extract_text(file_path)
                filename = Path(file_path).name
                all_texts.append(f"=== 文档 {i}: {filename} ===\n{text}")
            except Exception as e:
                all_texts.append(f"=== 文档 {i}: {file_path} (提取失败: {str(e)}) ===")

        return '\n\n'.join(all_texts)


def split_text_into_chunks(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50
) -> List[str]:
    """
    将文本分割成小块

    Args:
        text: 原始文本
        chunk_size: 每块的字符数
        overlap: 重叠字符数

    Returns:
        文本块列表
    """
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        if end < len(text):
            for sep in ['。', '！', '？', '.\n', '!\n', '?\n', '\n\n', '. ', '! ', '? ']:
                last_sep = text[start:end].rfind(sep)
                if last_sep != -1 and last_sep > chunk_size * 0.3:
                    end = start + last_sep + len(sep)
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap if end < len(text) else len(text)

    return chunks
