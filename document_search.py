import argparse
from pathlib import Path
import os
import shutil
import docx
import jieba
import json
import re
import time
import zipfile
import rarfile
import tempfile
import io
import sys
import multiprocessing
import traceback
import threading
import pandas as pd
import markdown
import math
from html.parser import HTMLParser
from bs4 import BeautifulSoup
from striprtf.striprtf import rtf_to_text
import email
from email.parser import BytesParser
from email.header import decode_header
from email.utils import parseaddr
import chardet
import extract_msg
import csv
from datetime import datetime

# --- ADDED: 许可证管理器支持 ---
try:
    from license_manager import get_license_manager, Features
    _license_manager_available = True
except ImportError:
    _license_manager_available = False

# 辅助函数，用于检查功能是否可用
def is_feature_available(feature_name):
    """
    检查特定功能是否可用，如果许可证管理器不可用，返回 True
    
    Args:
        feature_name: 要检查的功能名称
        
    Returns:
        bool: 如果功能可用返回 True，否则返回 False
    """
    if not _license_manager_available:
        return True  # 如果许可证管理器不可用，默认所有功能可用
    
    try:
        license_manager = get_license_manager()
        return license_manager.is_feature_available(feature_name)
    except Exception as e:
        print(f"许可证检查错误: {e}")
        return True  # 发生错误时默认功能可用
# --------------------------------

from whoosh.index import create_in, open_dir, exists_in
from whoosh.fields import Schema, TEXT, ID, STORED, NUMERIC, KEYWORD
from whoosh.analysis import Tokenizer, Token, Analyzer
from whoosh.query import Phrase, Term, Prefix, And, Or, Not, Query, NumericRange, Every, FuzzyTerm, Wildcard, TermRange
from whoosh import scoring
from whoosh.qparser import QueryParser, MultifieldParser, OrGroup, GtLtPlugin, PhrasePlugin, SequencePlugin
from PyPDF2 import PdfReader
import pptx
import openpyxl
from datetime import datetime
import csv  # 添加用于写入TSV文件
from tqdm import tqdm  # Added for better progress reporting
from whoosh.highlight import Highlighter, ContextFragmenter, HtmlFormatter
# --- ADDED: Import analysis module ---
from whoosh import analysis
# ------------------------------------

# --- ADDED: Imports for OCR --- 
import pytesseract
from PIL import Image
from pdf2image import convert_from_path, pdfinfo_from_path
from pytesseract import TesseractError # Added
import pdf2image
from pdf2image.exceptions import PDFPopplerTimeoutError, PDFPageCountError # Added exceptions
# ------------------------------

# --- Constants ---
# INDEX_DIR = "indexdir" # Commented out, will be passed as parameter
ALLOWED_EXTENSIONS = ['.txt', '.docx', '.pdf', '.zip', '.rar', '.pptx', '.xlsx', '.md', '.html', '.htm', '.rtf', '.eml', '.msg']

# --- 新增函数用于记录跳过文件的信息 ---
def record_skipped_file(index_dir_path: str, file_path: str, reason: str) -> None:
    """
    记录被跳过的文件信息到TSV文件中。
    
    Args:
        index_dir_path: 索引目录路径
        file_path: 被跳过的文件路径
        reason: 跳过原因
    """
    try:
        # 构建记录文件路径
        log_file_path = os.path.join(index_dir_path, "index_skipped_files.tsv")
        
        # 获取当前时间戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 检查文件是否存在，如果不存在则添加表头
        file_exists = os.path.isfile(log_file_path)
        
        # 以追加模式打开文件
        with open(log_file_path, 'a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            
            # 如果文件不存在，添加表头
            if not file_exists:
                writer.writerow(["文件路径", "跳过原因", "时间"])
            
            # 写入记录
            writer.writerow([file_path, reason, timestamp])
            
    except Exception as e:
        # 如果记录过程中出错，打印错误但不中断程序
        print(f"Warning: Failed to record skipped file {file_path}: {e}", file=sys.stderr)
        pass

# --- 用于处理跳过原因的格式化函数 ---
def format_skip_reason(reason_type: str, detail: str = "") -> str:
    """
    格式化跳过文件的原因，使其更易于理解。
    
    Args:
        reason_type: 跳过类型
        detail: 详细信息
    
    Returns:
        格式化后的原因说明
    """
    reason_map = {
        "password_zip": "需要密码的ZIP文件",
        "password_rar": "需要密码的RAR文件",
        "corrupted_zip": "损坏的ZIP文件",
        "corrupted_rar": "损坏的RAR文件",
        "ocr_timeout": "OCR处理超时",
        "pdf_conversion_timeout": "PDF转换超时",
        "content_too_large": "内容超出大小限制",
        "unsupported_type": "不支持的文件类型",
        "extraction_error": "提取过程出错",
        "missing_dependency": "缺少处理依赖",
        "pdf_timeout": "PDF处理超时或转换错误",
        "content_limit": "内容大小超过限制",
    }
    
    base_reason = reason_map.get(reason_type, "未知原因")
    
    if detail:
        return f"{base_reason} - {detail}"
    return base_reason
# -----------------------------------

# --- ADDED: Configuration for Tesseract and Poppler --- 
# Set the path to the tesseract executable if it's not in PATH
_TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe' # Use double backslashes or raw string
_tesseract_found = False
if os.path.exists(_TESSERACT_CMD):
     pytesseract.pytesseract.tesseract_cmd = _TESSERACT_CMD
     _tesseract_found = True
else:
     if shutil.which('tesseract'):
         # print("Tesseract executable found in PATH.") # COMMENTED OUT
         _tesseract_found = True
     else:
        # print(f"Warning: Tesseract executable not found at {_TESSERACT_CMD} or in PATH. OCR will likely fail.") # COMMENTED OUT
        pass

# Path to the Poppler bin directory
_POPPLER_PATH = r"C:\Program Files\poppler-24.08.0\Library\bin" # Use the path from user screenshot
_poppler_found = False
if os.path.isdir(_POPPLER_PATH) and os.path.exists(os.path.join(_POPPLER_PATH, 'pdfinfo.exe')):
    _poppler_found = True
else:
    # print(f"Warning: Poppler bin directory not found or pdfinfo.exe missing at {_POPPLER_PATH}. PDF to image conversion will likely fail.") # COMMENTED OUT
    pass
# ------------------------------------------------------

# --- Global Index Lock ---
INDEX_ACCESS_LOCK = threading.Lock()

# --- Custom Jieba Tokenizer and Analyzer ---
class ChineseTokenizer(Tokenizer):
    def __call__(self, value, positions=False, chars=False,
                 keeporiginal=False, removestops=True,
                 start_pos=0, start_char=0,
                 mode='', **kwargs):
        assert isinstance(value, str), "ChineseTokenizer expects unicode string"
        seglist = jieba.tokenize(value)
        token_pos = 0
        for (word, start, end) in seglist:
            token = Token(positions=positions, chars=chars, removestops=removestops, mode=mode, **kwargs)
            token.text = word
            token.boost = 1.0
            if keeporiginal:
                token.original = word
            token.stopped = False
            if positions:
                token.pos = token_pos
            if chars:
                token.startchar = start_char + start
                token.endchar = start_char + end
            yield token
            token_pos += 1

class ChineseAnalyzer(Analyzer):
    def __call__(self, value, **kwargs):
        return ChineseTokenizer()(value, **kwargs)

# --- HTML Stripper ---
class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = io.StringIO()
    def handle_data(self, d):
        self.text.write(d)
    def get_data(self):
        return self.text.getvalue()

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def get_schema() -> Schema:
    analyzer = ChineseAnalyzer()
    return Schema(path=ID(stored=True, unique=True),
                  content=TEXT(stored=True, analyzer=analyzer),
                  # --- ADDED: Field for filename search ---
                  filename_text=TEXT(stored=True, analyzer=analysis.StandardAnalyzer()),
                  # ---------------------------------------------------
                  structure_map=STORED,
                  last_modified=NUMERIC(stored=True, sortable=True),
                  file_size=NUMERIC(stored=True, sortable=True),
                  file_type=KEYWORD(stored=True, lowercase=True, scorable=False),
                  # --- ADDED: Field to store OCR indexing status ---
                  indexed_with_ocr=STORED)
                  # -------------------------------------------------

def scan_documents(directory_path: Path) -> list[Path]:
    found_files = []
    if not directory_path.is_dir():
        # print(f"Error: Path is not a directory: {directory_path}") # COMMENTED OUT
        return found_files
    # print(f"Scanning directory: {directory_path}") # COMMENTED OUT
    for item in directory_path.rglob('*'):
        if item.is_file() and item.suffix.lower() in ALLOWED_EXTENSIONS:
            found_files.append(item)
    # print(f"Scan complete. Found {len(found_files)} document(s).") # COMMENTED OUT
    return found_files

def extract_text_from_docx(file_path: Path) -> tuple[str, list[dict]]:
    full_text_list = []
    structure = []
    try:
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            full_text_list.append(text)
            para_info = {"text": text}
            style_name = para.style.name.lower()
            if style_name.startswith('heading'):
                para_info["type"] = "heading"
                try:
                    level = int(style_name.split()[-1])
                    para_info["level"] = level
                except (ValueError, IndexError):
                    para_info["level"] = 1
            else:
                para_info["type"] = "paragraph"
            structure.append(para_info)
        full_text = '\n'.join(full_text_list)
        return full_text, structure
    except Exception as e:
        # print(f"Error reading docx file {file_path}: {e}") # COMMENTED OUT
        return "", []

def extract_text_from_txt(file_path: Path) -> tuple[str, list[dict]]:
    content = ""
    structure = []
    encodings_to_try = ['utf-8', 'gbk', 'gb2312', 'latin-1']
    heading_pattern = re.compile(
        r'^\s*(?:第[一二三四五六七八九十百千万零〇]+[章条]|'  
        r'[零一二三四五六七八九十]+、|'             
        r'[（(][一二三四五六七八九十百千万零〇]+[)）]|' 
        r'[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]|' 
        r'\d+(?:\.\d+)*\.?\s+|'                
        r'第.*?节)\s*$',                         
        re.IGNORECASE
    )
    try:
        for encoding in encodings_to_try:
            try:
                content = file_path.read_text(encoding=encoding)
                if content:
                    lines = content.splitlines()
                    for line in lines:
                        cleaned_line = line.strip()
                        if cleaned_line:
                            if heading_pattern.match(cleaned_line):
                                structure.append({'type': 'heading', 'level': 1, 'text': cleaned_line})
                            else:
                                structure.append({'type': 'paragraph', 'text': cleaned_line})
                if content or structure:
                    break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                # print(f"Error reading txt file {file_path} with encoding {encoding}: {e}") # COMMENTED OUT
                return "", []
        if not content and not structure:
            print(f"Could not decode txt file {file_path} with tried encodings or file is empty.")
            return "", []
    except Exception as e:
        print(f"Error accessing txt file {file_path}: {e}")
        return "", []
    return content, structure

def extract_text_from_pdf(file_path: Path, enable_ocr: bool = True, ocr_lang: str = 'chi_sim+eng', min_chars_for_ocr_trigger: int = 50, timeout: int | None = None) -> tuple[str | None, list[dict]]:
    """
    从PDF文件提取文本，支持基于PyPDF2和OCR的混合方法
    """
    # --- ADDED: 检查PDF支持许可证 ---
    if not is_feature_available(Features.PDF_SUPPORT):
        print(f"PDF支持功能不可用 (未获得许可)")
        raise PermissionError("PDF支持功能需要专业版许可证。")
    # -------------------------------
    
    # 基础异常检查
    if not file_path.exists():
        print(f"PDF文件不存在: {file_path}")
        return None, []
    
    extracted_text = ""
    direct_text = ""
    structure = [] # Initialize structure list

    # 1. Try direct text extraction (using PyPDF2 or similar - currently placeholder)
    #    NOTE: Direct text extraction libraries usually don't have configurable timeouts easily.
    try:
        # --- Placeholder for direct text extraction ---
        # Example using PyPDF2 (if installed):
        # from PyPDF2 import PdfReader
        # reader = PdfReader(file_path)
        # for page in reader.pages:
        #     page_content = page.extract_text()
        #     if page_content:
        #         direct_text += page_content + "\n"
        # direct_text = direct_text.strip()
        # --- End Placeholder ---

        if not enable_ocr:
            print(f"Warning: Direct PDF text extraction not fully implemented or OCR disabled for {file_path.name}. Relying on potentially empty direct_text.")
            pass
    except Exception as e:
        print(f"Error during direct text extraction attempt for {file_path.name}: {e}", file=sys.stderr)
        direct_text = ""

    ocr_needed = enable_ocr and (len(direct_text) < min_chars_for_ocr_trigger)

    if ocr_needed:
        print(f"Info: {file_path.name} direct text insufficient ({len(direct_text)} chars) or not attempted, trying OCR...")
        ocr_texts = []
        try:
            # --- 添加 pdf2image 时间日志 ---
            pdf2image_start_time = time.time()
            print(f"DEBUG: [{file_path.name}] Starting pdf2image conversion at {pdf2image_start_time:.2f}")
            # -------------------------------

            images = pdf2image.convert_from_path(
                            file_path,
                timeout=timeout,
                fmt='jpeg',
                thread_count=1
            )

            # --- 添加 pdf2image 时间日志 ---
            pdf2image_end_time = time.time()
            pdf2image_duration = pdf2image_end_time - pdf2image_start_time
            print(f"DEBUG: [{file_path.name}] Finished pdf2image conversion at {pdf2image_end_time:.2f} (Duration: {pdf2image_duration:.2f}s)")
            # -------------------------------

            for i, image in enumerate(images):
                page_num = i + 1
                try:
                    # --- 添加 Tesseract 时间日志 ---
                    tesseract_start_time = time.time()
                    print(f"DEBUG: [{file_path.name} Page {page_num}] Starting Tesseract OCR at {tesseract_start_time:.2f}")
                    # ------------------------------

                    page_text = pytesseract.image_to_string(image, lang=ocr_lang, timeout=timeout)

                    # --- 添加 Tesseract 时间日志 ---
                    tesseract_end_time = time.time()
                    tesseract_duration = tesseract_end_time - tesseract_start_time
                    print(f"DEBUG: [{file_path.name} Page {page_num}] Finished Tesseract OCR at {tesseract_end_time:.2f} (Duration: {tesseract_duration:.2f}s)")
                    # ------------------------------

                    page_text = page_text.strip()
                    if page_text:
                        ocr_texts.append(page_text)
                    else:
                        pass

                # --- MODIFIED: Return tuple on exceptions ---
                except TesseractError as te:
                    tesseract_fail_time = time.time()
                    print(f"DEBUG: [{file_path.name} Page {page_num}] TesseractError at {tesseract_fail_time:.2f} (Duration before error: {tesseract_fail_time - tesseract_start_time:.2f}s)")
                    err_msg = str(te).lower()
                    if 'timeout' in err_msg or 'process timed out' in err_msg:
                        print(f"Warning: Tesseract OCR timed out (>{timeout}s) for page {page_num} of {file_path.name}.", file=sys.stderr)
                        # 这里不记录跳过的文件，因为该函数无法访问index_dir_path
                        # 记录会在_extract_worker中完成
                        return None, [] # MODIFIED
                    else:
                        print(f"Error during Tesseract OCR for page {page_num} of {file_path.name}: {te}", file=sys.stderr)
                        # 这里不记录跳过的文件，因为该函数无法访问index_dir_path
                        # 记录会在_extract_worker中完成
                        return None, [] # MODIFIED
                except RuntimeError as rte:
                    tesseract_fail_time = time.time()
                    print(f"DEBUG: [{file_path.name} Page {page_num}] RuntimeError at {tesseract_fail_time:.2f} (Duration before error: {tesseract_fail_time - tesseract_start_time:.2f}s)")
                    err_msg = str(rte).lower()
                    if 'timeout' in err_msg:
                        print(f"Warning: Tesseract OCR likely timed out (>{timeout}s) for page {page_num} of {file_path.name}. Error: {rte}", file=sys.stderr)
                        # 这里不记录跳过的文件，因为该函数无法访问index_dir_path
                        # 记录会在_extract_worker中完成
                        return None, [] # MODIFIED
                    else:
                        print(f"Runtime error during Tesseract OCR for page {page_num} of {file_path.name}: {rte}", file=sys.stderr)
                        # 这里不记录跳过的文件，因为该函数无法访问index_dir_path
                        # 记录会在_extract_worker中完成
                        return None, [] # MODIFIED
                except Exception as e:
                    tesseract_fail_time = time.time()
                    print(f"DEBUG: [{file_path.name} Page {page_num}] Exception at {tesseract_fail_time:.2f} (Duration before error: {tesseract_fail_time - tesseract_start_time:.2f}s)")
                    print(f"Unexpected error during OCR for page {page_num} of {file_path.name}: {e}", file=sys.stderr)
                    # 这里不记录跳过的文件，因为该函数无法访问index_dir_path
                    # 记录会在_extract_worker中完成
                    return None, [] # MODIFIED
                # --- End Modification ---

            extracted_text = "\n\n".join(ocr_texts)
            if images:
                 print(f"Info: OCR process completed for {file_path.name}. Total chars: {len(extracted_text)}")

        # --- MODIFIED: Return tuple on exceptions ---
        except PDFPopplerTimeoutError:
            pdf2image_fail_time = time.time()
            print(f"DEBUG: [{file_path.name}] PDFPopplerTimeoutError at {pdf2image_fail_time:.2f} (Duration before error: {pdf2image_fail_time - pdf2image_start_time:.2f}s)")
            print(f"Warning: PDF to image conversion timed out (>{timeout}s) for {file_path.name}.", file=sys.stderr)
            # 这里不记录跳过的文件，因为该函数无法访问index_dir_path
            # 记录会在_extract_worker中完成
            return None, [] # MODIFIED
        except PDFPageCountError as pe:
             print(f"Error getting page count or converting PDF {file_path.name}: {pe}. Skipping OCR.", file=sys.stderr)
             # 这里不记录跳过的文件，因为该函数无法访问index_dir_path
             # 记录会在_extract_worker中完成
             return None, [] # MODIFIED
        except Exception as e:
            pdf2image_fail_time = time.time()
            duration_str = f"(Duration before error: {pdf2image_fail_time - pdf2image_start_time:.2f}s)" if 'pdf2image_start_time' in locals() else ""
            print(f"DEBUG: [{file_path.name}] Exception during PDF conversion at {pdf2image_fail_time:.2f} {duration_str}")
            print(f"Error during PDF processing/conversion for {file_path.name}: {e}", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
            # 这里不记录跳过的文件，因为该函数无法访问index_dir_path
            # 记录会在_extract_worker中完成
            return None, [] # MODIFIED
        # --- End Modification ---

    else:
        extracted_text = direct_text
        # ... (logging) ...

    # --- Generate basic structure from final extracted_text ---
    # Note: If direct_text extraction were implemented, it might populate 'structure' directly.
    # This block ensures structure is generated if only 'extracted_text' is available (e.g., from OCR).
    if not structure and extracted_text: # Generate structure only if it's empty AND text exists
        lines = extracted_text.splitlines()
        for line in lines:
            cleaned_line = line.strip()
            if cleaned_line:
                structure.append({'type': 'paragraph', 'text': cleaned_line})
    # -----------------------------------------------------------

    # MODIFIED: Return tuple, handle potential None for text
    if extracted_text is None:
         return None, [] # Structure is already empty list in this case
    else:
         # Ensure structure is a list even if extraction yielded text but somehow failed structure generation
         final_structure = structure if isinstance(structure, list) else []
         return extracted_text, final_structure

def extract_text_from_pptx(file_path: Path) -> tuple[str, list[dict]]:
    full_text_list = []
    structure = []
    try:
        presentation = pptx.Presentation(file_path)
        for slide_num, slide in enumerate(presentation.slides):
            slide_texts = []
            for shape in slide.shapes:
                if not shape.has_text_frame:
                    continue
                text = shape.text.strip()
                if text:
                    slide_texts.append(text)
                    structure.append({
                        'type': 'paragraph',
                        'text': text,
                        'context': f'Slide {slide_num + 1}'
                    })
            if slide_texts:
                full_text_list.extend(slide_texts)
        full_text = '\n'.join(full_text_list)
        return full_text, structure
    except Exception as e:
        print(f"Error reading pptx file {file_path}: {e}")
        return "", []

def _is_potential_header(row_data: list, non_empty_threshold=0.5, string_threshold=0.5) -> bool:
    if not row_data:
        return False
    non_empty_count = sum(1 for cell in row_data if pd.notna(cell) and str(cell).strip())
    string_count = sum(1 for cell in row_data if isinstance(cell, str) and str(cell).strip() and not str(cell).replace('.', '', 1).isdigit())
    if non_empty_count == 0:
        return False
    return (non_empty_count / len(row_data) >= non_empty_threshold and
            string_count / non_empty_count >= string_threshold)

def extract_text_from_xlsx(file_path: Path) -> tuple[str, list[dict]]:
    full_text_list = []
    structure = []
    MAX_HEADER_CHECK_ROWS = 10
    try:
        excel_data = pd.read_excel(file_path, sheet_name=None, header=None, keep_default_na=False)
    except Exception as e:
        print(f"Error reading Excel file {file_path}: {e}")
        return "", []
    for sheet_name, df_initial in excel_data.items():
        if df_initial.empty:
            continue
        header_row_index = -1
        best_header_score = -1
        potential_header_idx = -1
        for i in range(min(MAX_HEADER_CHECK_ROWS, len(df_initial))):
            row_values = df_initial.iloc[i].tolist()
            current_score = sum(1 for cell in row_values if pd.notna(cell) and isinstance(cell, str) and str(cell).strip() and not str(cell).replace('.', '', 1).isdigit())
            is_plausible = any(isinstance(cell, str) and str(cell).strip() for cell in row_values)
            if is_plausible and current_score > best_header_score:
                best_header_score = current_score
                potential_header_idx = i
            elif best_header_score == -1 and is_plausible:
                potential_header_idx = i
        if potential_header_idx != -1 and best_header_score >= 1:
            header_row_index = potential_header_idx
            print(f"Detected header in '{sheet_name}' at row {header_row_index + 1}")
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row_index, keep_default_na=False)
                df = df.dropna(axis=0, how='all')
                df = df.dropna(axis=1, how='all')
                df = df.fillna('')
                headers = [str(h).strip() for h in df.columns]
                for idx, row in df.iterrows():
                    excel_row_num = idx + header_row_index + 2
                    row_values = [str(cell).strip() for cell in row.tolist()]
                    row_texts_for_full_text = [h for h in headers if h] + [v for v in row_values if v]
                    if row_texts_for_full_text:
                        full_text_list.append(" ".join(row_texts_for_full_text))
                    if any(row_values):
                        searchable_row_text = " ".join(filter(None, row_values))
                        structure.append({
                            'type': 'excel_row',
                            'sheet_name': str(sheet_name),
                            'row_index': excel_row_num,
                            'headers': headers,
                            'values': row_values,
                            'text': searchable_row_text
                        })
            except Exception as e:
                print(f"Error re-reading sheet '{sheet_name}' with header at row {header_row_index + 1}: {e}")
                sheet_text = df_initial.to_string(index=False, header=False)
                full_text_list.append(sheet_text)
                structure.append({'type': 'paragraph', 'text': f"Content from sheet '{sheet_name}' (header detection failed)."})
        else:
            print(f"Warning: Could not detect header in sheet '{sheet_name}'. Indexing as plain text.")
            sheet_text = df_initial.to_string(index=False, header=False)
            cleaned_sheet_text = "\n".join(line.strip() for line in sheet_text.splitlines() if line.strip())
            if cleaned_sheet_text:
                full_text_list.append(cleaned_sheet_text)
                structure.append({
                    'type': 'paragraph',
                    'text': cleaned_sheet_text,
                    'context': f"Sheet: {sheet_name} (No header detected)"
                })
    full_text = '\n'.join(full_text_list)
    return full_text, structure

def extract_text_from_md(file_path: Path) -> tuple[str, list[dict]]:
    """Extract text and structure from a Markdown file."""
    # --- ADDED: 检查Markdown支持许可证 ---
    if not is_feature_available(Features.MARKDOWN_SUPPORT):
        print(f"Markdown支持功能不可用 (未获得许可)")
        raise PermissionError("Markdown支持功能需要专业版许可证。")
    # ------------------------------------
    
    if not file_path.exists():
        return "", []
    
    content = ""
    structure = []
    encodings_to_try = ['utf-8', 'gbk', 'gb2312']
    try:
        raw_md_content = None
        for encoding in encodings_to_try:
            try:
                raw_md_content = file_path.read_text(encoding=encoding)
                if raw_md_content is not None:
                    break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"Error reading md file {file_path} with encoding {encoding}: {e}")
                return "", []
        if raw_md_content is None:
            print(f"Could not decode md file {file_path} with tried encodings or file is empty.")
            return "", []
        html_content = markdown.markdown(raw_md_content)
        content = strip_tags(html_content).strip()
        if content:
            structure.append({'type': 'paragraph', 'text': content})
        print(f"MD Extracted Text (first 500 chars): {content[:500]}")
        return content, structure
    except ImportError:
        print("Error: markdown library not installed. Please run: pip install Markdown")
        return "", []

def extract_text_from_html(file_path: Path) -> tuple[str, list[dict]]:
    print(f"Attempting to extract text from HTML/HTM: {file_path}")
    content = ""
    structure = []
    try:
        raw_html_bytes = file_path.read_bytes()
        if not raw_html_bytes:
            print(f"Warning: HTML/HTM file is empty: {file_path}")
            return "", []
        detected = chardet.detect(raw_html_bytes)
        encoding = detected.get('encoding')
        confidence = detected.get('confidence', 0)
        print(f"Chardet detected encoding: {encoding} with confidence: {confidence:.2f}")
        html_content_decoded = None
        if encoding and confidence > 0.7:
            try:
                html_content_decoded = raw_html_bytes.decode(encoding, errors='replace')
                print(f"Decoded using chardet result: {encoding}")
            except Exception as e:
                print(f"Warning: Failed to decode using detected encoding '{encoding}': {e}")
        if html_content_decoded is None:
            for enc in ['utf-8', 'gbk', 'gb18030', 'latin-1']:
                try:
                    html_content_decoded = raw_html_bytes.decode(enc, errors='strict')
                    print(f"Decoded using fallback encoding: {enc}")
                    break
                except UnicodeDecodeError:
                    continue
            if html_content_decoded is None:
                print(f"Warning: Could not decode HTML/HTM, using utf-8 with replacements.")
                html_content_decoded = raw_html_bytes.decode('utf-8', errors='replace')
        soup = BeautifulSoup(html_content_decoded, 'lxml')
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
        content = ' '.join(soup.stripped_strings)
        if content:
            structure.append({'type': 'paragraph', 'text': content})
        print(f"Successfully extracted HTML/HTM content (length: {len(content)}): {file_path}")
        print(f"Extracted sample: {content[:500]}{'...' if len(content) > 500 else ''}")
        return content, structure
    except Exception as e:
        print(f"Error processing html/htm file {file_path}: {e}")
        # traceback.print_exc(file=sys.stderr) # COMMENTED OUT
        return "", []

def extract_text_from_rtf(file_path: Path) -> tuple[str, list[dict]]:
    content = ""
    structure = []
    encodings_to_try = ['utf-8', 'gbk', 'gb2312', 'latin-1']
    try:
        rtf_content = None
        for encoding in encodings_to_try:
            try:
                rtf_content = file_path.read_text(encoding=encoding)
                if rtf_content is not None and rtf_content.strip().startswith('{\\rtf'):
                    break
                else:
                    rtf_content = None
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"Error reading rtf file {file_path} with encoding {encoding}: {e}")
                return "", []
        if rtf_content is None:
            print(f"Could not decode rtf file {file_path} with tried encodings or file doesn't start with RTF marker.")
            return "", []
        content = rtf_to_text(rtf_content, errors="ignore").strip()
        if content:
            structure.append({'type': 'paragraph', 'text': content})
        return content, structure
    except Exception as e:
        print(f"Error processing rtf file {file_path}: {e}")
        return "", []

def extract_text_from_eml(file_path: Path) -> tuple[str, list[dict]]:
    """Extract text from an EML file."""
    # --- ADDED: 检查邮件支持许可证 ---
    if not is_feature_available(Features.EMAIL_SUPPORT):
        print(f"邮件支持功能不可用 (未获得许可)")
        raise PermissionError("邮件支持功能需要专业版许可证。")
    # -----------------------------
    
    if not file_path.exists():
        return "", []
    
    full_text_list = []
    structure = []
    try:
        raw_bytes = file_path.read_bytes()
        if not raw_bytes:
            return "", []
        parser = BytesParser()
        msg = parser.parsebytes(raw_bytes)
        def decode_header_simple(header_value):
            if not header_value:
                return ""
            decoded_parts = []
            for part, encoding in decode_header(header_value):
                if isinstance(part, bytes):
                    try:
                        decoded_parts.append(part.decode(encoding or 'utf-8', errors='replace'))
                    except LookupError:
                        decoded_parts.append(part.decode('utf-8', errors='replace'))
                else:
                    decoded_parts.append(part)
            return "".join(decoded_parts)
        subject = decode_header_simple(msg.get('Subject'))
        sender = decode_header_simple(msg.get('From'))
        recipient = decode_header_simple(msg.get('To'))
        cc = decode_header_simple(msg.get('Cc'))
        date_str = msg.get('Date')
        if subject:
            structure.append({'type': 'heading', 'level': 1, 'text': f"主题: {subject}"})
            full_text_list.append(subject)
        if sender:
            realname, email_addr = parseaddr(sender)
            clean_sender = f"{realname} <{email_addr}>" if realname else sender
            structure.append({'type': 'metadata', 'text': f"发件人: {clean_sender}"})
            full_text_list.append(f"发件人: {clean_sender}")
        if recipient:
            structure.append({'type': 'metadata', 'text': f"收件人: {recipient}"})
            full_text_list.append(f"收件人: {recipient}")
        if cc:
            structure.append({'type': 'metadata', 'text': f"抄送: {cc}"})
            full_text_list.append(f"抄送: {cc}")
        if date_str:
            structure.append({'type': 'metadata', 'text': f"日期: {date_str}"})
            full_text_list.append(f"日期: {date_str}")
        body_content = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition'))
                if 'attachment' not in content_disposition and content_type.startswith('text/'):
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or 'utf-8'
                    try:
                        body_content += payload.decode(charset, errors='replace')
                    except LookupError:
                        body_content += payload.decode('utf-8', errors='replace')
        else:
            payload = msg.get_payload(decode=True)
            charset = msg.get_content_charset() or 'utf-8'
            try:
                body_content = payload.decode(charset, errors='replace')
            except LookupError:
                body_content = payload.decode('utf-8', errors='replace')
        if body_content:
            lines = body_content.splitlines()
            for line in lines:
                cleaned_line = line.strip()
                if cleaned_line:
                    structure.append({'type': 'paragraph', 'text': cleaned_line})
                    full_text_list.append(cleaned_line)
        full_text = '\n'.join(full_text_list)
        return full_text, structure
    except Exception as e:
        print(f"Error extracting EML {file_path}: {e}")
        # traceback.print_exc(file=sys.stderr) # COMMENTED OUT
        return "", []

def extract_text_from_msg(file_path: Path) -> tuple[str, list[dict]]:
    # --- ADDED: 检查邮件支持许可证 ---
    if not is_feature_available(Features.EMAIL_SUPPORT):
        print(f"邮件支持功能不可用 (未获得许可)")
        raise PermissionError("邮件支持功能需要专业版许可证。")
    # -----------------------------
    
    print(f"Attempting to extract text from MSG: {file_path.name}")
    full_text_list = []
    structure = []
    try:
        msg = extract_msg.Message(str(file_path))
        if msg.subject:
            structure.append({'type': 'heading', 'level': 1, 'text': f"主题: {msg.subject}"})
            full_text_list.append(msg.subject)
        if msg.sender:
            structure.append({'type': 'metadata', 'text': f"发件人: {msg.sender}"})
            full_text_list.append(f"发件人: {msg.sender}")
        if msg.to:
            structure.append({'type': 'metadata', 'text': f"收件人: {msg.to}"})
            full_text_list.append(f"收件人: {msg.to}")
        if msg.cc:
            structure.append({'type': 'metadata', 'text': f"抄送: {msg.cc}"})
            full_text_list.append(f"抄送: {msg.cc}")
        if msg.date:
            structure.append({'type': 'metadata', 'text': f"日期: {msg.date}"})
            full_text_list.append(f"日期: {msg.date}")
        body_to_process = None
        processed_html_body = False
        if hasattr(msg, 'htmlBody') and msg.htmlBody:
            print("MSG Body: Attempting to process HTML body.")
            html_bytes = None
            try:
                if isinstance(msg.htmlBody, bytes):
                    html_bytes = msg.htmlBody
                elif isinstance(msg.htmlBody, str):
                    html_bytes = msg.htmlBody.encode('utf-8', errors='ignore')
                if html_bytes:
                    detected = chardet.detect(html_bytes)
                    encoding = detected.get('encoding')
                    confidence = detected.get('confidence', 0)
                    html_content_decoded = None
                    if encoding and confidence > 0.7:
                        try:
                            html_content_decoded = html_bytes.decode(encoding, errors='replace')
                            print(f"MSG HTML Body: Decoded using chardet result: {encoding}")
                        except Exception as e:
                            print(f"MSG HTML Body: Warning - Failed using chardet '{encoding}': {e}")
                    if html_content_decoded is None:
                        for enc in ['utf-8', 'gbk', 'gb18030']:
                            try:
                                html_content_decoded = html_bytes.decode(enc, errors='strict')
                                print(f"MSG HTML Body: Decoded using fallback: {enc}")
                                break
                            except Exception:
                                continue
                        if html_content_decoded is None:
                            html_content_decoded = html_bytes.decode('utf-8', errors='replace')
                            print(f"MSG HTML Body: Decoded using final fallback utf-8 (replace)")
                    if html_content_decoded:
                        soup = BeautifulSoup(html_content_decoded, 'lxml')
                        for script_or_style in soup(["script", "style"]):
                            script_or_style.decompose()
                        body_to_process = ' '.join(soup.stripped_strings)
                        if body_to_process:
                            print(f"MSG Body: Successfully processed HTML body (length {len(body_to_process)}).")
                            processed_html_body = True
                        else:
                            print("MSG Body: Processed HTML body resulted in empty text.")
                else:
                    print("MSG Body: msg.htmlBody was string but failed to re-encode to bytes.")
            except Exception as e:
                print(f"MSG Body: Error processing HTML body: {e}")
                body_to_process = None
        if not processed_html_body:
            print("MSG Body: HTML body not found or failed, falling back to plain text body.")
            if msg.body:
                body_text = msg.body
                print(f"MSG Body (Raw Plain Text Fallback, first 500 chars): {body_text[:500]}")
                body_to_process = body_text
            else:
                print("MSG Body: Plain text body is also empty.")
                body_to_process = ""
        if body_to_process:
            body_lines = body_to_process.splitlines()
            for line in body_lines:
                cleaned_line = line.strip()
                if cleaned_line:
                    structure.append({'type': 'paragraph', 'text': cleaned_line})
                    full_text_list.append(cleaned_line)
        else:
            print("MSG Body: No processable body content found (HTML or Plain Text).")
        full_text = '\n'.join(full_text_list)
        print(f"Extracted full text from {file_path.name} (first 500 chars): {full_text[:500]}")
        return full_text, structure
    except Exception as e:
        print(f"Error processing MSG file {file_path}: {e}")
        # traceback.print_exc(file=sys.stderr) # COMMENTED OUT
        return "", []

def index_documents(writer, content_dict: dict[Path, tuple[str, list[dict]]]):
    print(f"Adding {len(content_dict)} documents to the index...")
    indexed_count = 0
    for path_obj, (text_content, structure) in content_dict.items():
        if not text_content:
            print(f"Skipping indexing for {path_obj.name} due to empty content.")
            continue
        try:
            try:
                relative_path_str = str(path_obj.relative_to(Path.cwd()))
            except ValueError:
                relative_path_str = str(path_obj.resolve())
            structure_json = json.dumps(structure, ensure_ascii=False)
            writer.add_document(path=relative_path_str,
                                content=text_content,
                                structure_map=structure_json)
            indexed_count += 1
        except Exception as e:
            print(f"Error indexing document {path_obj}: {e}")
    print(f"Successfully added {indexed_count} documents to writer.")

def get_positive_terms(q: Query) -> set[str]:
    """Recursively extract positive terms (not under a NOT) from a query tree."""
    positive_terms = set()
    if isinstance(q, Term):
        positive_terms.add(q.text)
    elif isinstance(q, (And, Or)):
        for subq in q.children():
            positive_terms.update(get_positive_terms(subq))
    elif isinstance(q, Phrase):
        positive_terms.update(q.words)
    # Ignore terms under Not, Prefix, Wildcard, Every, etc. for highlighting purposes
    # You might want to refine this for Prefix/Wildcard if needed
    return positive_terms

# --- ADDED BACK: convert_term_to_prefix function --- 
def convert_term_to_prefix(q: Query, fieldname: str = "content") -> Query:
    """Recursively convert Term queries to Prefix queries within a Query tree."""
    if isinstance(q, Term) and q.fieldname == fieldname:
        # Only convert Terms in the specified field
        return Prefix(q.fieldname, q.text)
    elif isinstance(q, (And, Or)):
        # Recursively process children of And/Or groups
        return q.__class__([convert_term_to_prefix(subq, fieldname) for subq in q.children()])
    elif isinstance(q, Not):
        # For Not queries, process the *inner* query
        # Whoosh Not object holds its child query in the .query attribute
        return Not(convert_term_to_prefix(q.query, fieldname))
    else:
        # Return other query types (like Prefix, Wildcard, Every, etc.) unchanged
        return q
# --- END ADDED BACK --- 

def search_index(query_str: str,
                 index_dir_path: str, # Added parameter
                 search_mode: str = 'phrase',
                 # --- ADDED: Parameter for search scope ---
                 search_scope: str = 'fulltext',
                 # -----------------------------------------
                 min_size_kb: int | None = None,
                 max_size_kb: int | None = None,
                 start_date: str | None = None,  # Changed to string (e.g., "2023-01-01")
                 end_date: str | None = None,    # Changed to string (e.g., "2023-12-31")
                 file_type_filter: list[str] | None = None,
                 sort_by: str = 'relevance',
                 case_sensitive: bool = False) -> list[dict]: # ADDED case_sensitive param
    # --- MODIFIED: Include search_scope in debug log ---
    print(f"--- Starting search --- Query: '{query_str}', Mode: {search_mode}, Scope: {search_scope}")
    # ---------------------------------------------------
    print(f"Filters - Size: {min_size_kb}-{max_size_kb}KB, Date: {start_date}-{end_date}, Types: {file_type_filter}") # Debug
    print(f"Case Sensitive: {case_sensitive} (Note: Currently ignored by backend)") # ADDED Debug for case_sensitive

    processed_results = [] # <--- Initialize a new list to store processed hits
    if not Path(index_dir_path).exists() or not exists_in(index_dir_path):
        print(f"Error: Index directory '{index_dir_path}' not found.")
        return processed_results # <--- Return the empty processed list

    # --- Determine target field based on scope --- ADDED
    target_field = "filename_text" if search_scope == 'filename' else "content"
    print(f"Searching in field: '{target_field}'")
    # --------------------------------------------
    
    # --- 检查许可证状态，确定当前可访问的文件类型 ---
    allowed_file_types = {'.docx', '.txt', '.html', '.htm', '.rtf', '.xlsx', '.pptx'} # 基础版允许的文件类型
    
    # 如果用户有相应的许可证，添加专业版文件类型
    if is_feature_available(Features.PDF_SUPPORT):
        allowed_file_types.add('.pdf')
    if is_feature_available(Features.MARKDOWN_SUPPORT):
        allowed_file_types.add('.md')
    if is_feature_available(Features.EMAIL_SUPPORT):
        allowed_file_types.add('.eml')
        allowed_file_types.add('.msg')
    
    print(f"Current license allows file types: {allowed_file_types}")
    # -------------------------------------------

    ix = open_dir(index_dir_path)
    searcher = ix.searcher(weighting=scoring.BM25F())
    # --- Use analyzer associated with the target field (or default) --- MODIFIED
    analyzer = ix.schema[target_field].analyzer if target_field in ix.schema else ChineseAnalyzer()
    # -------------------------------------------------------------------

    text_query = None
    parsed_query_obj = None # Store the parsed query object
    if query_str:
        # --- MODIFIED: Handle filename search directly first --- 
        if search_scope == 'filename':
            target_field = "filename_text"
            analyzer = ix.schema[target_field].analyzer if target_field in ix.schema else analysis.StandardAnalyzer() # Ensure standard analyzer for filename
            # Always use Wildcard for filename search, ignore search_mode
            text_query = Wildcard(target_field, f"*{query_str}*")
            print(f"Constructed Wildcard query for filename: {text_query}")
        else: # Handle fulltext search based on search_mode
            target_field = "content"
            analyzer = ix.schema[target_field].analyzer if target_field in ix.schema else ChineseAnalyzer()
            # --- Original logic for fulltext based on mode --- 
            if search_mode == 'phrase':
                terms = [token.text for token in analyzer(query_str)]
                if terms:
                    text_query = Phrase(target_field, terms)
                    print(f"Constructed Phrase query on '{target_field}': {text_query}")
                    if text_query:
                        parsed_query_obj = text_query # Store phrase query object
                else:
                    print(f"Phrase query for '{target_field}' is empty after analysis.")
            elif search_mode == 'fuzzy':
                parser = QueryParser(target_field, schema=ix.schema)
                # --- Check for Wildcards --- 
                if '*' in query_str or '?' in query_str:
                    print(f"Wildcard detected in query for '{target_field}': '{query_str}'")
                    try:
                        text_query = parser.parse(query_str)
                        print(f"Parsed Wildcard query on '{target_field}': {text_query}")
                        if text_query:
                            parsed_query_obj = text_query # Store wildcard query object
                    except Exception as e:
                        print(f"Error parsing wildcard query on '{target_field}': {e}")
                        text_query = None
                        parsed_query_obj = None
                else: # Not a wildcard query
                    # --- Fuzzy/Prefix Logic for fulltext --- 
                    try: # <<< Corrected indentation
                        parsed_q = parser.parse(query_str)
                        parsed_query_obj = parsed_q # Store parsed object before conversion
                        print(f"Parsed Keyword query on '{target_field}': {parsed_q}")
                        # Convert to prefix for fulltext search
                        text_query = convert_term_to_prefix(parsed_q, fieldname=target_field)
                        if text_query != parsed_q:
                            print(f"-> Converted terms to prefix on '{target_field}': {text_query}")
                    except Exception as e:
                        print(f"Error parsing fuzzy query on '{target_field}': {e}")
                        text_query = None
                        parsed_query_obj = None
            else:
                print(f"Error: Unknown search mode '{search_mode}' for fulltext search")
        # --- END MODIFIED --- 
    else:
        print("No text query provided.")

    size_filter_query = None
    min_bytes = min_size_kb * 1024 if min_size_kb is not None else None
    max_bytes = max_size_kb * 1024 if max_size_kb is not None else None
    if min_bytes is not None or max_bytes is not None:
        size_filter_query = NumericRange("file_size", min_bytes, max_bytes)
        print(f"Constructed Size filter query: {size_filter_query}")
    date_filter_query = None
    start_timestamp = None
    end_timestamp = None
    if start_date:
        try:
            dt_start = datetime.strptime(start_date, '%Y-%m-%d')
            start_timestamp = dt_start.timestamp()
        except ValueError as e:
            print(f"Error parsing start_date '{start_date}': {e}. Expected format: YYYY-MM-DD")
    if end_date:
        try:
            dt_end = datetime.strptime(end_date, '%Y-%m-%d')
            dt_end = dt_end.replace(hour=23, minute=59, second=59, microsecond=999999)
            end_timestamp = dt_end.timestamp()
        except ValueError as e:
            print(f"Error parsing end_date '{end_date}': {e}. Expected format: YYYY-MM-DD")
    if start_timestamp is not None or end_timestamp is not None:
        date_filter_query = NumericRange("last_modified", start_timestamp, end_timestamp)
        print(f"Constructed Date filter query: {date_filter_query}")
    file_type_query = None
    if file_type_filter:
        lower_case_filters = [ftype.lower().lstrip('.') for ftype in file_type_filter if ftype]
        if lower_case_filters:
            type_queries = [Term("file_type", ftype) for ftype in lower_case_filters]
            if len(type_queries) == 1:
                file_type_query = type_queries[0]
            else:
                file_type_query = Or(type_queries)
            print(f"Constructed File Type filter query: {file_type_query}")
        else:
            print("File type filter list was empty or contained only empty strings.")

    # Combine all queries
    all_queries = []
    if text_query:
        all_queries.append(text_query)
    if size_filter_query:
        all_queries.append(size_filter_query)
    if date_filter_query:
        all_queries.append(date_filter_query)
    if file_type_query:
        all_queries.append(file_type_query)

    final_query = None
    if not all_queries:
        # --- If only filter criteria are present, search everything --- MODIFIED
        # print("Error: No search criteria (text, size, date, or type filter) provided.")
        print("No specific text query, searching based on filters only.")
        final_query = Every() # Match all documents if no criteria, filters will apply later
    elif len(all_queries) == 1:
        final_query = all_queries[0]
    else:
        final_query = And(all_queries)
        print(f"Combined query: {final_query}")

    # Sorting logic (remains the same)
    sort_field = None
    reverse = False
    if sort_by == 'date_asc':
        sort_field = 'last_modified'
        reverse = False
    elif sort_by == 'date_desc':
        sort_field = 'last_modified'
        reverse = True
    elif sort_by == 'size_asc':
        sort_field = 'file_size'
        reverse = False
    elif sort_by == 'size_desc':
        sort_field = 'file_size'
        reverse = True
    elif sort_by == 'relevance':
        sort_field = None  # Default Whoosh scoring
    else:
        print(f"Warning: Unknown sort_by option '{sort_by}', defaulting to relevance.")
        sort_field = None

    # --- 修改搜索结果处理逻辑，过滤掉许可证无法访问的文件类型 ---
    results = searcher.search(final_query, limit=100, sortedby=sort_field, reverse=reverse) # Increased limit
    
    # --- Result Processing and Highlighting (Conditional) --- MODIFIED
    if results:
        print(f"Found {len(results)} document hit(s):")
        matched_contexts = 0
        
        # --- MODIFIED: Get positive terms for highlighting --- 
        # Only prepare for content highlighting if scope is fulltext and we have a parsed query
        positive_terms_for_highlighting = set()
        if search_scope == 'fulltext' and parsed_query_obj:
            positive_terms_for_highlighting = get_positive_terms(parsed_query_obj)
            print(f"DEBUG: Positive terms for highlighting: {positive_terms_for_highlighting}")
        # -----------------------------------------------------
        
        for hit in results:
            file_path = hit.get('path', "(未知文件)")
            file_type = hit.get('file_type', '')
            
            # --- 检查当前许可证是否允许访问该文件类型 ---
            if file_type and not any(file_type.endswith(allowed_ext) for allowed_ext in allowed_file_types):
                print(f"Skipping result for {file_path} due to license restrictions (type: {file_type})")
                continue  # 跳过此结果，不添加到返回列表
            # -----------------------------------------
            
            # --- Basic result structure (always included) ---
            basic_result_info = {
                'file_path': file_path,
                'last_modified': hit.get('last_modified', 0),
                'file_size': hit.get('file_size', 0),
                'file_type': file_type,
                'score': hit.score
            }
            # -----------------------------------------------
            
            # --- Content-based processing only for fulltext search ---
            if search_scope == 'fulltext' and query_str: # Only process structure if doing text search in content
                added_paragraphs_in_hit = set()
                structure = []
                structure_map_json = hit.get('structure_map')
                if structure_map_json:
                    try:
                        structure = json.loads(structure_map_json)
                    except json.JSONDecodeError:
                        print(f"Error parsing structure for {file_path}")
                        # Add the basic info even if structure fails
                        processed_results.append(basic_result_info)
                        continue
                else:
                    print(f"Warning: No structure information for {file_path}")
                    # Add the basic info if no structure
                    processed_results.append(basic_result_info)
                    continue

                found_match_in_content = False # Flag to track if any block matched
                for i, block in enumerate(structure):
                    block_text = block.get('text', '')
                    block_type = block.get('type')
                    # Initialize markers/highlights
                    final_marked_paragraph = ""
                    final_marked_heading = ""
                    final_marked_excel_values = None
                    is_relevant_block = False # Reset for each block

                    # Helper for fuzzy highlighting (now uses specific positive terms)
                    def fuzzy_highlighter(text, terms_to_highlight):
                        if not isinstance(text, str) or not terms_to_highlight:
                            return str(text)
                        temp_text = text
                        for term in terms_to_highlight:
                            def replace_func(matchobj):
                                return f"__HIGHLIGHT_START__{matchobj.group(0)}__HIGHLIGHT_END__"
                            # Use regex to match whole word unless term contains wildcard?
                            # For now, simple substring match might be okay if terms are from parser
                            temp_text = re.sub(re.escape(term), replace_func, temp_text, flags=re.IGNORECASE)
                        return temp_text
                        
                    # Helper for phrase highlighting (remains mostly the same, but should ideally use positive phrase)
                    def phrase_highlighter(text, phrase):
                        if not isinstance(text, str) or not phrase:
                            return str(text)
                        phrase_pattern = re.compile(re.escape(phrase), flags=re.IGNORECASE)
                        def replace_phrase_func(matchobj):
                            return f"__HIGHLIGHT_START__{matchobj.group(0)}__HIGHLIGHT_END__"
                        return phrase_pattern.sub(replace_phrase_func, text)

                    # Check if block is relevant based on search mode and content
                    if search_mode == 'phrase':
                        match = re.search(re.escape(query_str), block_text, flags=re.IGNORECASE)
                        if match:
                           is_relevant_block = True
                           highlighted_block_text = phrase_highlighter(block_text, query_str)
                           if block_type == 'heading' or block_type == 'metadata':
                               final_marked_heading = highlighted_block_text
                           elif block_type == 'excel_row':
                               original_excel_values = block.get('values', [])
                               marked_excel_values = []
                               for cell_value in original_excel_values:
                                   marked_excel_values.append(phrase_highlighter(cell_value, query_str))
                               final_marked_excel_values = marked_excel_values
                           else: # paragraph
                               final_marked_paragraph = highlighted_block_text
                               
                    elif search_mode == 'fuzzy':
                        contains_term = False
                        # --- MODIFIED: Check against positive terms only --- 
                        if positive_terms_for_highlighting:
                            # Check block text first
                            if block_text:
                                block_text_lower = block_text.lower()
                                for term in positive_terms_for_highlighting:
                                    if term in block_text_lower:
                                        contains_term = True
                                        break
                            # If not in text, check excel values if applicable
                            if not contains_term and block_type == 'excel_row':
                                original_excel_values = block.get('values', [])
                                for cell_value in original_excel_values:
                                    if isinstance(cell_value, str):
                                        cell_lower = cell_value.lower()
                                        for term in positive_terms_for_highlighting:
                                            if term in cell_lower:
                                                contains_term = True
                                                break
                                    if contains_term:
                                        break
                        # -----------------------------------------------
                                        
                        if contains_term:
                           is_relevant_block = True
                           # --- MODIFIED: Pass positive terms to highlighter --- 
                           if block_type == 'heading' or block_type == 'metadata':
                               final_marked_heading = fuzzy_highlighter(block_text, positive_terms_for_highlighting)
                           elif block_type == 'excel_row':
                               original_excel_values = block.get('values', [])
                               marked_excel_values = []
                               for cell_value in original_excel_values:
                                   marked_excel_values.append(fuzzy_highlighter(cell_value, positive_terms_for_highlighting))
                               final_marked_excel_values = marked_excel_values
                           else: # paragraph
                               final_marked_paragraph = fuzzy_highlighter(block_text, positive_terms_for_highlighting)
                           # -------------------------------------------------
                               
                    # If the block was relevant, create a detailed result entry
                    if is_relevant_block:
                        if block_text not in added_paragraphs_in_hit: # Avoid duplicate paragraphs from same file hit
                            result_block = {
                                **basic_result_info, # Include basic info
                                'type': block_type,
                                'level': block.get('level'),
                                'paragraph': block.get('text') if block_type != 'heading' and block_type != 'metadata' and block_type != 'excel_row' else None,
                                'heading': block.get('text') if block_type == 'heading' or block_type == 'metadata' else None,
                                'excel_sheet': block.get('sheet_name'),
                                'excel_row_idx': block.get('row_index'),
                                'excel_headers': block.get('headers'),
                                'excel_values': final_marked_excel_values if final_marked_excel_values is not None else block.get('values'), # Use marked or original
                                'marked_paragraph': final_marked_paragraph,
                                'marked_heading': final_marked_heading,
                                # Keep score from basic_result_info
                            }
                            # print(f"MATCHED BLOCK: {result_block}") # Too verbose
                            processed_results.append(result_block)
                            found_match_in_content = True
                            matched_contexts += 1
                            added_paragraphs_in_hit.add(block_text)
                            
                # If after checking all blocks, no content match was found for this hit
                # (This shouldn't happen often with fulltext search, but as a fallback)
                if not found_match_in_content:
                    print(f"Note: Hit found for {file_path} but no specific content block matched/highlighted.")
                    processed_results.append(basic_result_info) # Add basic info
                    
            else: # If search_scope is 'filename' OR query_str is empty (filter only search)
                # Just add the basic file info, no content highlighting needed here
                processed_results.append(basic_result_info)
        # End of loop through hits
    else:
        print("No document hits found for the query.")
        
    # Close searcher and index
    if searcher: searcher.close()
    if ix: ix.close()
    print(f"--- Search complete. Returning {len(processed_results)} processed results. ---")
    return processed_results

# --- MODIFIED: Accept a dictionary --- 
# def _extract_worker(item_data: tuple) -> dict:
def _extract_worker(worker_args: dict) -> dict:
# -----------------------------------
    """Worker function for multiprocessing pool to extract text from files.
    
    Args:
        worker_args: Dictionary containing parameters. Now using direct parameters instead of item_data tuple.
    
    Returns:
        Dictionary with extraction results including content, metadata, and error info if any.
    """
    result = {}
    # --- NEW logic to fix KeyError ---
    try:
        path_key = worker_args['path_key']
        file_type = worker_args['file_type']  
        # 获取用于内容提取的原始文件路径
        archive_path_abs = worker_args.get('archive_path_abs')
        member_name = worker_args.get('member_name')
        enable_ocr = worker_args.get('enable_ocr', False)
        original_mtime = worker_args.get('original_mtime')
        original_fsize = worker_args.get('original_fsize')
        display_name = worker_args.get('display_name') or path_key
        extraction_timeout = worker_args.get('extraction_timeout')
        content_limit_bytes = worker_args.get('content_limit_bytes', 0)
        index_dir_path = worker_args.get('index_dir_path', '')  # Added for license checking
        # 获取原始文件路径（如果存在）
        orig_file_path = worker_args.get('orig_file_path', '')
        
        # 添加到结果字典的基本信息
        result = {
            'path_key': path_key,  # 这是索引键，可能是标准化的
            'display_name': display_name,  # 用于显示的名称
            'original_mtime': original_mtime,
            'original_fsize': original_fsize,
            'file_type': file_type,
        }
        
        # 如果有原始文件路径，添加到结果
        if orig_file_path:
            result['orig_file_path'] = orig_file_path

        # --- For archive files, extract using member_name and archive_path_abs ---
        if file_type == 'archive' and archive_path_abs and member_name:
            try:
                # 确保archive_path_abs是Path对象
                if not isinstance(archive_path_abs, Path):
                    archive_path_abs = Path(archive_path_abs)
                    
                content = ""
                metadata = []
                
                # 处理不同类型的压缩文件
                archive_ext = archive_path_abs.suffix.lower()
                member_ext = Path(member_name).suffix.lower()
                
                # 提取内容
                if archive_ext == '.zip':
                    with zipfile.ZipFile(archive_path_abs, 'r') as zf:
                        with zf.open(member_name) as f:
                            # 根据成员文件类型提取内容
                            if member_ext == '.pdf':
                                # --- Pass member_name for better identification ---
                                temp_pdf = io.BytesIO(f.read())
                                # --- ADDED: 传递timeout和OCR设置给PDF提取函数 ---
                                content, metadata = extract_text_from_pdf(
                                    temp_pdf, 
                                    enable_ocr=enable_ocr,
                                    timeout=extraction_timeout
                                )
                                # 记录OCR使用情况
                                result['ocr_enabled_for_file'] = enable_ocr
                            # ... 其他文件类型处理 ...
                
                # 将提取的内容添加到结果
                if content is not None:
                    result['content'] = content
                    result['metadata'] = metadata
                else:
                    result['error'] = "内容提取失败 (返回None)"
                    
            except Exception as e:
                # 捕获提取过程中的任何错误
                result['error'] = f"提取错误: {str(e)}"
                print(f"Error extracting from archive {path_key}: {e}")
                
        # --- For regular files, extract using file_path ---
        else:  # file_type == 'file'
            try:
                # 从path_key获取文件路径
                file_path = Path(orig_file_path if orig_file_path else path_key)
                
                # 确保文件存在
                if not file_path.exists():
                    result['error'] = f"文件不存在: {file_path}"
                    return result
                
                content = ""
                metadata = []
                file_ext = file_path.suffix.lower()
                
                # 根据文件类型提取内容
                if file_ext == '.pdf':
                    # --- ADDED: 传递timeout和OCR设置给PDF提取函数 ---
                    content, metadata = extract_text_from_pdf(
                        file_path, 
                        enable_ocr=enable_ocr,
                        timeout=extraction_timeout
                    )
                    # 记录OCR使用情况
                    result['ocr_enabled_for_file'] = enable_ocr
                # ... 其他文件类型处理 ...
                
                # 将提取的内容添加到结果
                if content is not None:
                    result['content'] = content
                    result['metadata'] = metadata
                else:
                    result['error'] = "内容提取失败 (返回None)"
                    
            except Exception as e:
                # 捕获提取过程中的任何错误
                result['error'] = f"提取错误: {str(e)}"
                print(f"Error extracting from file {path_key}: {e}")
    
    except Exception as e:
        # 捕获顶层异常，确保工作线程不会崩溃
        result = {
            'path_key': worker_args.get('path_key', 'unknown'),
            'display_name': worker_args.get('display_name', 'unknown'),
            'error': f"工作线程异常: {str(e)}"
        }
        print(f"Worker exception: {e}")
        
    return result

# --- ADDED: Function to read license-skipped files ---
def read_license_skipped_files(index_dir_path: str) -> dict:
    """
    读取因许可证限制而被跳过的文件记录
    
    Args:
        index_dir_path: 索引目录路径
        
    Returns:
        dict: 包含被跳过文件路径的字典，键为文件路径，值为跳过原因
    """
    skipped_files = {}
    log_file_path = os.path.join(index_dir_path, "index_skipped_files.tsv")
    
    if not os.path.exists(log_file_path):
        print(f"跳过文件记录不存在: {log_file_path}")
        return skipped_files
        
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            # 跳过表头
            next(reader, None)
            
            for row in reader:
                if len(row) >= 3:
                    file_path, reason, timestamp = row[0], row[1], row[2]
                    # 仅关注因许可证限制而跳过的文件
                    if "许可证限制" in reason:
                        skipped_files[file_path] = reason
                        
        print(f"读取了 {len(skipped_files)} 个因许可证限制而跳过的文件记录")
    except Exception as e:
        print(f"读取跳过文件记录时出错: {e}")
    
    return skipped_files
# ---------------------------------------------------

# --- ADDED: Function to update skipped files record ---
def update_skipped_files_record(index_dir_path: str, processed_license_files: dict):
    """
    更新跳过文件记录，删除已经重新处理的许可证限制文件记录
    
    Args:
        index_dir_path: 索引目录路径
        processed_license_files: 已处理的许可证限制文件字典
    """
    if not processed_license_files:
        return  # 没有需要更新的记录
        
    log_file_path = os.path.join(index_dir_path, "index_skipped_files.tsv")
    if not os.path.exists(log_file_path):
        return  # 文件不存在，无需更新
        
    try:
        # 读取所有记录
        all_records = []
        with open(log_file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            # 保存表头
            header = next(reader, None)
            if not header:
                return  # 空文件或只有表头
                
            all_records.append(header)
            
            # 读取并过滤记录
            for row in reader:
                if len(row) >= 3:
                    file_path, reason, timestamp = row[0], row[1], row[2]
                    # 如果不是已处理的许可证限制文件，则保留
                    if file_path not in processed_license_files:
                        all_records.append(row)
        
        # 写回过滤后的记录
        with open(log_file_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            for row in all_records:
                writer.writerow(row)
                
        print(f"已从跳过文件记录中删除 {len(processed_license_files)} 个已处理的许可证限制文件")
    except Exception as e:
        print(f"更新跳过文件记录时出错: {e}")
# ------------------------------------------------------

# --- MODIFIED: Add enable_ocr parameter --- 
# def create_or_update_index(directory_path_str: str, index_dir_path: str):
def create_or_update_index(source_directories: list[str], index_dir_path: str, enable_ocr: bool = True, extraction_timeout: int | None = None, txt_content_limit_kb: int | None = None): # Add new parameter with default None
# ------------------------------------------
    """Creates or updates the Whoosh index for the given list of source directories.
    Yields status messages and progress updates.
    Args:
        source_directories: List of paths to the directories containing documents. # MODIFIED
        index_dir_path: Path to store the Whoosh index.
        enable_ocr: Whether to enable OCR for PDF files during indexing.
        extraction_timeout: Timeout in seconds for single file extraction.
        txt_content_limit_kb: Maximum content size in KB to index for .txt files (0 or None means no limit).
    """
    print("Index Update: Acquiring index lock...")
    INDEX_ACCESS_LOCK.acquire()
    print("Index Update: Lock acquired.")
    ix = None
    writer = None
    update_performed = False
    try:
        # --- Initial Safety Checks and Setup ---
        if not source_directories:
            yield {'type': 'error', 'message': '错误: 未提供任何要索引的源文件夹。'}
            INDEX_ACCESS_LOCK.release()
            print("Index Update: Lock released early (no source directories).")
            return

        valid_source_dirs = []
        for dir_str in source_directories:
            doc_directory = Path(dir_str)
            if not doc_directory.is_dir():
                yield {'type': 'warning', 'message': f"警告: 跳过无效或不存在的源文件夹: {dir_str}"}
            else: # Corrected indentation
                valid_source_dirs.append(doc_directory) # Store valid Path objects

        if not valid_source_dirs:
            yield {'type': 'error', 'message': '错误: 提供的所有源文件夹均无效。'}
            INDEX_ACCESS_LOCK.release()
            print("Index Update: Lock released early (all source directories invalid).")
            return
        # -----------------------------------------------------------

        # --- ADDED: 读取因许可证限制而跳过的文件记录 ---
        original_license_skipped_files = read_license_skipped_files(index_dir_path)
        license_skipped_files = original_license_skipped_files.copy()  # 创建副本以便后续比较
        
        if license_skipped_files:
            yield {'type': 'status', 'message': f'发现 {len(license_skipped_files)} 个因许可证限制而跳过的文件记录'}
        # -----------------------------------------------

        index_path = Path(index_dir_path)
        schema = get_schema()
        indexed_files = {}
        try:
            # Yield phase status
            yield {'type': 'status', 'message': '阶段: 正在读取现有索引...'}
            print("Index Update: Reading existing index data...")
            if exists_in(index_path):
                ix_read = None
                try:
                    # ... (existing logic to read index into indexed_files) ...
                    ix_read = open_dir(index_path, schema=schema)
                    if ix_read.schema != schema:
                        yield {'type': 'warning', 'message': f"索引 Schema 已更改。建议完全重建索引以应用更改。"}
                    with ix_read.searcher() as searcher:
                        for fields in searcher.all_stored_fields():
                            path_str = fields.get('path')
                            last_mod = fields.get('last_modified')
                            was_indexed_with_ocr = fields.get('indexed_with_ocr', False)
                            if path_str and last_mod is not None:
                                # --- MODIFIED: 直接使用存储的路径作为键，无需再次标准化 ---
                                path_key = path_str
                                indexed_files[path_key] = {'mtime': last_mod, 'was_ocr': was_indexed_with_ocr}
                    yield {'type': 'status', 'message': f'现有索引包含 {len(indexed_files)} 个条目。'}
                except Exception as e:
                    yield {'type': 'warning', 'message': f'读取现有索引时出错: {e}。将尝试作为新索引处理。'}
                    indexed_files = {}
                finally:
                    if ix_read:
                        ix_read.close()
            else:
                yield {'type': 'status', 'message': '现有索引未找到。'}
                indexed_files = {}
        finally:
            print("Index Update: Releasing lock after read phase...")
            INDEX_ACCESS_LOCK.release() # Release lock after reading
            print("Index Update: Lock released after read phase.")

        # --- Initialize accumulators and counters before the loop ---
        yield {'type': 'status', 'message': '阶段: 正在扫描文件系统并对比变更...'}
        doc_extensions = {'.docx', '.txt', '.pdf', '.pptx', '.xlsx', '.md', '.html', '.htm', '.rtf', '.eml', '.msg'}
        archive_extensions = {'.zip', '.rar'}
        added_count, updated_count, deleted_count, skipped_count, error_count = 0, 0, 0, 0, 0
        # --- Store data as tuples for extraction worker ---
        # to_index_list: list[tuple(path_key, mtime, fsize, type, archive_path?, member_name?)]
        to_index_list = []
        # ------------------------------------------------
        to_delete = set(indexed_files.keys()) # Initialize with all known paths
        update_performed = False
        processed_count = 0 # Counter for progress across all directories

        # --- Check for Unrar Tool (Moved before walk) --- 
        # ... (existing unrar check logic) ...
        can_process_rar = True # Assume True initially, check below
        if '.rar' in archive_extensions:
            try:
                rarfile.tool_setup()
                yield {'type': 'status', 'message': '找到 unrar 工具，将处理 .rar 文件。'}
            except rarfile.RarCannotExec as e:
                can_process_rar = False
                yield {'type': 'warning', 'message': f'未找到 unrar 工具或无法执行 ({e})。将跳过 .rar 文件处理。'}
            except Exception as e:
                can_process_rar = False
                yield {'type': 'warning', 'message': f'检查 unrar 工具时出错: {e}。将跳过 .rar 文件处理。'}

        # --- MODIFIED: Outer loop for source directories ---
        total_dirs = len(valid_source_dirs)
        for dir_index, current_scan_dir in enumerate(valid_source_dirs):
            yield {'type': 'status', 'message': f'开始扫描目录 {dir_index + 1}/{total_dirs}: {current_scan_dir}'}
            print(f"--- Scanning Directory: {current_scan_dir} ---")

            # --- Walk for Scanning and Comparison (Now inside the loop) ---
            try:
                # --- MODIFIED: Update initial progress phase label ---
                yield {'type': 'progress', 'current': processed_count, 'total': 0, 'phase': f'扫描目录 {dir_index + 1}/{total_dirs}: {current_scan_dir.name}', 'detail': ''}

                for root, dirs, files in os.walk(current_scan_dir):
                    root_path = Path(root) # Corrected indentation
                    dirs[:] = [d for d in dirs if not d.startswith('.')] # Skip hidden dirs
                    
                    current_level_files = [] # Store items found at this directory level
                    
                    for filename in files:
                        if filename.startswith('.'): # Skip hidden files
                            continue
                            
                        file_path = root_path / filename
                        item_data = None
                        file_ext = file_path.suffix.lower() # Corrected indentation

                        try:
                            if file_ext in doc_extensions:
                                # --- MODIFIED: 使用标准化路径作为键 ---
                                file_abs_path = str(file_path.resolve())
                                path_key = normalize_path_for_index(file_abs_path, source_directories)
                                stats = file_path.stat() # Corrected indentation
                                mtime = stats.st_mtime # Corrected indentation
                                fsize = stats.st_size
                                item_data = (path_key, mtime, fsize, 'file', file_abs_path)  # 保存原始绝对路径用于内容提取
                                current_level_files.append(item_data)
                            elif file_ext in archive_extensions: # Corrected indentation
                                if file_ext == '.rar' and not can_process_rar: # Corrected indentation
                                    skipped_count += 1
                                    continue
                                # --- MODIFIED: 使用标准化路径作为键的基础 ---
                                archive_path_abs = str(file_path.resolve()) # Corrected indentation
                                archive_path_str = normalize_path_for_index(archive_path_abs, source_directories)
                                yield {'type': 'status', 'message': f'处理压缩文件: {file_path.name}'}
                                archive_members = []
                                if file_ext == '.zip':
                                    try:
                                        with zipfile.ZipFile(file_path, 'r') as zf:
                                            archive_members = zf.infolist()
                                    except RuntimeError as e:
                                        # 捕获可能的密码错误
                                        if 'password required' in str(e).lower() or 'encrypted file' in str(e).lower():
                                            # 添加记录跳过的文件
                                            record_skipped_file(
                                                index_dir_path,
                                                str(file_path),
                                                format_skip_reason("password_zip")
                                            )
                                            yield {'type': 'warning', 'message': f'跳过受密码保护的 ZIP 文件: {file_path.name}'}
                                            error_count += 1
                                            continue  # 跳过这个文件，处理下一个
                                        else:
                                            # 其他 RuntimeError，保持原有逻辑
                                            raise  # 重新抛出异常，将由外层异常处理捕获
                                    except zipfile.BadZipFile as e:
                                        # 明确处理损坏的 ZIP 文件
                                        # 添加记录跳过的文件
                                        record_skipped_file(
                                            index_dir_path,
                                            str(file_path),
                                            format_skip_reason("corrupted_zip", str(e))
                                        )
                                        yield {'type': 'warning', 'message': f'跳过损坏的 ZIP 文件: {file_path.name} ({e})'}
                                        error_count += 1
                                        continue  # 跳过这个文件，处理下一个
                                elif file_ext == '.rar':
                                    try:
                                        with rarfile.RarFile(file_path, 'r') as rf:
                                            archive_members = rf.infolist()
                                    except rarfile.PasswordRequired as e:
                                        # 明确处理需要密码的 RAR 文件
                                        # 添加记录跳过的文件
                                        record_skipped_file(
                                            index_dir_path,
                                            str(file_path),
                                            format_skip_reason("password_rar")
                                        )
                                        yield {'type': 'warning', 'message': f'跳过受密码保护的 RAR 文件: {file_path.name}'}
                                        error_count += 1
                                        continue  # 跳过这个文件，处理下一个
                                    except rarfile.BadRarFile as e:
                                        # 检查错误信息是否提示加密但无密码提供
                                        if 'password required' in str(e).lower() or 'encrypted file' in str(e).lower():
                                            # 添加记录跳过的文件
                                            record_skipped_file(
                                                index_dir_path,
                                                str(file_path),
                                                format_skip_reason("password_rar")
                                            )
                                            yield {'type': 'warning', 'message': f'跳过受密码保护的 RAR 文件: {file_path.name}'}
                                            error_count += 1
                                            continue
                                        else:
                                            # 明确处理损坏的 RAR 文件
                                            # 添加记录跳过的文件
                                            record_skipped_file(
                                                index_dir_path,
                                                str(file_path),
                                                format_skip_reason("corrupted_rar", str(e))
                                            )
                                            yield {'type': 'warning', 'message': f'跳过损坏的 RAR 文件: {file_path.name} ({e})'}
                                            error_count += 1
                                            continue  # 跳过这个文件，处理下一个
                                for member in archive_members:
                                    if member.is_dir(): continue
                                    member_filename_path = Path(member.filename)
                                    if member_filename_path.name.startswith('.'): continue # Corrected indentation
                                    member_ext = member_filename_path.suffix.lower()
                                    if member_ext in doc_extensions:
                                        normalized_member_filename = member.filename.replace('\\', '/')
                                        virtual_path = f"{archive_path_str}::{normalized_member_filename}"
                                        member_mtime = 0 # Corrected indentation
                                        member_fsize = 0 # Corrected indentation
                                        if file_ext == '.zip':
                                            dt_tuple = member.date_time + (0, 0, -1)
                                            try: 
                                                member_mtime = time.mktime(dt_tuple)
                                            except ValueError: 
                                                member_mtime = file_path.stat().st_mtime # Fallback
                                            member_fsize = member.file_size
                                        elif file_ext == '.rar':
                                            member_mtime = member.mtime if hasattr(member, 'mtime') else file_path.stat().st_mtime
                                            member_fsize = member.file_size if hasattr(member, 'file_size') else 0
                                        # --- MODIFIED: 保存原始绝对路径用于内容提取 ---
                                        item_data_archive = (virtual_path, member_mtime, member_fsize, 'archive', file_path.resolve(), member.filename)
                                        current_level_files.append(item_data_archive)
                        except (FileNotFoundError, zipfile.BadZipFile, rarfile.BadRarFile, NotImplementedError, OSError) as e:
                            yield {'type': 'warning', 'message': f'处理文件 {file_path.name} 时跳过: {e}'}
                            # 添加记录跳过文件的调用
                            if 'password required' in str(e).lower() or 'encrypted file' in str(e).lower():
                                record_skipped_file(
                                    index_dir_path,
                                    str(file_path),
                                    format_skip_reason("password_zip", f"需要密码: {str(e)}")
                                )
                            elif isinstance(e, zipfile.BadZipFile):
                                record_skipped_file(
                                    index_dir_path,
                                    str(file_path),
                                    format_skip_reason("corrupted_zip", str(e))
                                )
                            elif isinstance(e, rarfile.BadRarFile):
                                record_skipped_file(
                                    index_dir_path,
                                    str(file_path),
                                    format_skip_reason("corrupted_rar", str(e))
                                )
                            else:
                                record_skipped_file(
                                    index_dir_path,
                                    str(file_path),
                                    format_skip_reason("extraction_error", str(e))
                                )
                            error_count += 1
                            continue # Corrected indentation
                        except Exception as e: # Corrected indentation
                            yield {'type': 'error', 'message': f'处理文件 {file_path} 时发生意外错误: {e}'}
                            # 添加记录跳过文件的调用
                            record_skipped_file(
                                index_dir_path,
                                str(file_path),
                                format_skip_reason("extraction_error", str(e))
                            )
                            error_count += 1
                            continue # Corrected indentation

                    # --- Compare files found at this level --- 
                    for item_data in current_level_files:
                        path_key = item_data[0]
                        mtime = item_data[1]
                        fsize = item_data[2]

                        yield {'type': 'status', 'message': f'对比: {Path(path_key).name if "::" not in path_key else path_key.split("::")[1]}'} # Corrected indentation
                        processed_count += 1 # Increment total processed count

                        if path_key in indexed_files:
                            # Existing file, check if updated
                            print(f"  Found in existing index. Removing from to_delete.") # DEBUG
                            to_delete.discard(path_key) # File exists, don't delete it
                            stored_info = indexed_files[path_key] # Corrected indentation
                            stored_mtime = stored_info['mtime'] # Corrected indentation
                            stored_was_ocr = stored_info.get('was_ocr', False) # Corrected indentation

                            needs_update = False
                            # 1. Check mtime (Primary trigger)
                            if mtime > stored_mtime:
                                needs_update = True
                                print(f"    Update needed (mtime changed)") # DEBUG
                            else:
                                # 2. Check if OCR setting changed from False to True for PDF
                                current_file_ext = Path(path_key.split('::')[0]).suffix.lower() if '::' not in path_key else Path(path_key.split('::')[1]).suffix.lower()
                                if current_file_ext == '.pdf':
                                    if enable_ocr and not stored_was_ocr:
                                        needs_update = True
                                        print(f"    Update needed (OCR newly enabled for this PDF)") # DEBUG
                                
                                # --- ADDED: 检查是否是因许可证限制而跳过的文件 ---
                                if path_key in license_skipped_files:
                                    needs_update = True
                                    print(f"    Update needed (previously skipped due to license limitation)")
                                    # 从跳过文件记录中移除，因为将要重新处理
                                    license_skipped_files.pop(path_key, None)
                                # -------------------------------------------------
                                
                                # --- REMOVED的不必要的超时检查 ---
                                # elif extraction_timeout == 0: 
                                #     needs_update = True
                                #     print(f"    Update needed (Timeout is now 0, ensuring full PDF processing)") 
                                # --------------------------------

                            if needs_update:
                                to_index_list.append(item_data) # Add to list for extraction
                                updated_count += 1 # Count as updated
                                update_performed = True
                                print(f"    Marked for update/re-index.") # Corrected indentation
                            else: # Corrected structure/indentation
                                print(f"    No changes detected.") # Corrected indentation
                                # No changes, do nothing (already removed from to_delete)
                                pass
                        else: # Corrected structure/indentation
                            # New file
                            print(f"  New file found.") # Corrected indentation
                            to_index_list.append(item_data) # Add to list for extraction
                            added_count += 1 # Count as added
                            update_performed = True # Corrected indentation
                            print(f"    Marked for add.") # Corrected indentation

                        # --- MODIFIED: Update progress phase label inside loop ---
                        # Update progress after processing a level
                        yield {'type': 'progress', 'current': processed_count, 'total': 0, 'phase': f'扫描目录 {dir_index + 1}/{total_dirs}: {current_scan_dir.name} (已对比 {processed_count} 文件)', 'detail': f'已对比 {processed_count} 文件'}

            except Exception as e_walk:
                yield {'type': 'error', 'message': f'扫描目录 {current_scan_dir} 时出错: {e_walk}'}
                error_count += 1
                continue # Continue to the next directory

            yield {'type': 'status', 'message': f'完成扫描目录: {current_scan_dir}'}
            print(f"--- Finished Scanning Directory: {current_scan_dir} ---")
        # --- End of Outer Loop ---

        # --- At this point, to_index_list contains all items to add/update ---
        # --- and to_delete contains all items from original index not found/kept during scan ---
        print(f"--- Scan Complete ---")
        print(f"Items to Add/Update: {len(to_index_list)}")
        print(f"Items to Delete: {len(to_delete)}")
        deleted_count = len(to_delete) # Final count of items to be deleted

        # --- Extraction Phase ---
        # ... (Existing extraction logic using `to_index_list`) ...
        # Should work as is, but needs `to_index_list` as input
        yield {'type': 'status', 'message': f'阶段: 提取 {len(to_index_list)} 个文件的内容...'}
        extraction_results = {} # Stores {path_key: extracted_data_dict}
        extraction_errors = 0
        if to_index_list:
            # Prepare arguments for multiprocessing pool
            worker_args_list = []
            for item_data in to_index_list:
                path_key = item_data[0]  # 标准化路径键
                file_type_param = item_data[3]  # 文件类型: 'file' 或 'archive'
                
                # 新格式: (path_key, mtime, fsize, file_type, orig_file_path, [member_name])
                # 获取原始文件路径用于内容提取（第5个元素，如果存在）
                orig_file_path = str(item_data[4]) if len(item_data) > 4 else path_key
                # 压缩包内成员名称（第6个元素，如果存在）
                member_name = item_data[5] if len(item_data) > 5 else None
                
                # Extract file extension correctly for OCR check AND TXT limit check
                if member_name and '::' in path_key:
                    # 对于压缩包中的文件，从member_name提取扩展名
                    current_file_ext = Path(member_name).suffix.lower()
                else:
                    # 对于普通文件，从原始文件路径提取扩展名
                    current_file_ext = Path(orig_file_path).suffix.lower()
                
                should_ocr = enable_ocr and current_file_ext == '.pdf'

                # --- ADDED: Determine content limit bytes for this file --- 
                content_limit_bytes = 0
                if current_file_ext == '.txt' and txt_content_limit_kb and txt_content_limit_kb > 0:
                    content_limit_bytes = txt_content_limit_kb * 1024
                # ----------------------------------------------------------

                # --- Convert timeout 0 to None ---
                actual_timeout_for_worker = None if extraction_timeout == 0 else extraction_timeout
                # ---------------------------------
                
                # 构建worker参数字典，包含新增的orig_file_path
                worker_args_list.append({
                    'path_key': path_key,
                    'file_type': file_type_param,
                    'archive_path_abs': orig_file_path if file_type_param == 'archive' else None,
                    'member_name': member_name,
                    'enable_ocr': should_ocr,
                    'original_mtime': item_data[1],
                    'original_fsize': item_data[2],
                    'display_name': Path(path_key).name if "::" not in path_key else path_key.split("::")[1],
                    'extraction_timeout': actual_timeout_for_worker,
                    'content_limit_bytes': content_limit_bytes,
                    'index_dir_path': index_dir_path,
                    'orig_file_path': orig_file_path  # 添加原始文件路径
                })

            # Use multiprocessing pool
            # ... (The rest of the extraction multiprocessing pool logic) ...
            # This part seems complex and involves _extract_worker
            # Let's assume it correctly processes worker_args_list and populates extraction_results

            num_workers = max(1, multiprocessing.cpu_count() // 2)
            chunk_size = max(1, math.ceil(len(worker_args_list) / num_workers))
            print(f"Starting extraction pool with {num_workers} workers, chunk size {chunk_size}")
            extraction_progress_counter = 0 # Counter for extraction progress

            try:
                with multiprocessing.Pool(processes=num_workers) as pool:
                    # Use imap_unordered for progress reporting as results come in
                    # Wrap worker_args_list with tqdm for a visual progress bar in console
                    with tqdm(total=len(worker_args_list), desc="Extracting Content", unit="file") as pbar_extract:
                        for result in pool.imap_unordered(_extract_worker, worker_args_list, chunksize=chunk_size):
                            extraction_progress_counter += 1
                            if result and result.get('path_key'):
                                path_key = result['path_key']
                                display_name = result.get('display_name', path_key) # Use display name from result

                                # --- MODIFIED: Always store the result --- 
                                # Store the result dictionary regardless of whether it contains an 'error' key.
                                # The presence of the 'error' key will be checked during the writing phase.
                                extraction_results[path_key] = result # Corrected indentation
                                # ----------------------------------------

                                # --- Report status based on error key --- 
                                if result.get('error'):
                                    yield {'type': 'warning', 'message': f'提取内容失败 ({display_name}): {result["error"]}'}
                                    extraction_errors += 1 # Increment error count
                                else:
                                    yield {'type': 'status', 'message': f'提取完成: {display_name}'}
                                # ---------------------------------------
                            else:
                                # Handle cases where worker might return None or invalid dict
                                yield {'type': 'warning', 'message': '提取工作线程返回无效结果。'}
                                extraction_errors += 1 # Count this as an error too

                            # Update progress bar and yield progress update
                            pbar_extract.update(1)
                            # Need a display name even if result is invalid for progress detail
                            progress_display_name = display_name if 'display_name' in locals() else "未知文件"
                            yield {'type': 'progress', 'current': extraction_progress_counter, 'total': len(worker_args_list), 'phase': '提取内容', 'detail': f'提取中: {progress_display_name}'}

            except Exception as pool_error:
                yield {'type': 'error', 'message': f'内容提取过程中发生严重错误: {pool_error}'}
                # traceback.print_exc() # COMMENTED OUT
                # Optionally clear results and stop? Or try to proceed with partial results?
                # For now, let's signal error and proceed to writing whatever we got
                error_count += len(worker_args_list) - len(extraction_results) # Estimate errors
            finally:
                print(f"Extraction finished. Success: {len(extraction_results)}, Errors: {extraction_errors}")

        # --- Writing Phase --- 
        # Acquire lock again for writing
        print("Index Update: Acquiring write lock...")
        INDEX_ACCESS_LOCK.acquire()
        print("Index Update: Write lock acquired.")
        ix = None # Reset ix before opening for write
        writer = None # Reset writer

        # ... (Existing logic to open index for writing, delete entries in to_delete, add/update entries in extraction_results) ...
        yield {'type': 'status', 'message': '阶段: 写入索引变更...'}
        yield {'type': 'progress', 'current': 0, 'total': deleted_count + len(extraction_results), 'phase': '写入索引', 'detail': f'写入中: 共 {deleted_count + len(extraction_results)} 条目'}
        written_count = 0
        try:
            if not exists_in(index_path):
                index_path.mkdir(parents=True, exist_ok=True)
                ix = create_in(index_path, schema)
                yield {'type': 'status', 'message': '创建了新的索引库。'}
            else:
                try:
                    ix = open_dir(index_path, schema=schema)
                except Exception as e: # Catch potential schema mismatch or corruption
                    yield {'type': 'error', 'message': f'打开现有索引失败: {e}. 尝试删除并重建...'}
                    try: # Added try
                        shutil.rmtree(index_path) # Corrected indentation
                        index_path.mkdir(parents=True, exist_ok=True)
                        ix = create_in(index_path, schema)
                        yield {'type': 'status', 'message': '已删除旧索引并创建新索引库。'}
                        to_delete.clear() # If we recreated, deletions are implicitly handled (Corrected indentation)
                        deleted_count = 0 # Reset deleted count as we start fresh
                    except Exception as e_recreate: # Corrected indentation
                        yield {'type': 'error', 'message': f'删除或重建索引失败: {e_recreate}. 索引操作中止。'} # Corrected indentation
                        raise # Re-raise to indicate failure

            if ix: # Proceed only if index is successfully opened/created
                writer = ix.writer(limitmb=256, procs=max(1, multiprocessing.cpu_count() // 2), multisegment=True) # Corrected indentation

                # 1. Delete documents marked for deletion
                if to_delete:
                    yield {'type': 'status', 'message': f'正在删除 {deleted_count} 个旧条目...'}
                    print(f"--- Deleting {deleted_count} entries ---") # DEBUG (Corrected indentation)
                    with tqdm(total=deleted_count, desc="Deleting Entries", unit="entry") as pbar_delete:
                        for path_key in to_delete: # Corrected indentation
                            print(f"  Deleting: {path_key}") # DEBUG
                            writer.delete_by_term('path', path_key) # Corrected indentation
                            written_count += 1 # Corrected indentation
                            pbar_delete.update(1) # Corrected indentation
                            yield {'type': 'progress', 'current': written_count, 'total': deleted_count + len(extraction_results), 'phase': '写入索引 (删除)', 'detail': f'删除中: {Path(path_key).name if "::" not in path_key else path_key.split("::")[1]}'}

                # 2. Update/Add documents based on extraction results
                update_add_count = len(extraction_results) # Corrected indentation
                if update_add_count > 0:
                    yield {'type': 'status', 'message': f'正在添加/更新 {update_add_count} 个条目...'}
                    print(f"--- Adding/Updating {update_add_count} entries ---") # DEBUG
                    with tqdm(total=update_add_count, desc="Writing Entries", unit="entry") as pbar_write:
                        for path_key, extracted_data in extraction_results.items(): # Corrected indentation
                            # --- MODIFIED LOGIC: Handle errors but always write metadata --- 
                            if not extracted_data: # Handle potential None result from worker
                                yield {'type': 'warning', 'message': f'收到无效的提取结果，跳过写入: {path_key}'}
                                continue # Skip only if the entire result dict is missing

                            # Check for extraction error BUT DO NOT skip writing metadata
                            extraction_error = extracted_data.get('error')
                            if extraction_error:
                                yield {'type': 'warning', 'message': f'提取失败，但仍索引元数据 ({extracted_data.get("display_name", path_key)}): {extraction_error}'}
                                # Content will be empty string based on _extract_worker logic

                            display_name = extracted_data.get("display_name", path_key)
                            # Modify debug print to indicate metadata-only indexing
                            print(f"  Writing: {display_name} {'(metadata only)' if extraction_error else ''}") # DEBUG log clarification

                            # --- Always call update_document --- 
                            writer.update_document( # Corrected indentation
                                path=path_key,
                                # text_content should already be "" if error occurred in _extract_worker
                                content=extracted_data.get('text_content', ''),
                                filename_text=extracted_data.get('filename', ''),
                                structure_map=json.dumps(extracted_data.get('structure', [])),
                                last_modified=extracted_data.get('mtime', 0.0), # Use mtime from extraction result
                                file_size=extracted_data.get('fsize', 0),       # Use fsize from extraction result
                                file_type=extracted_data.get('file_type', ''),
                                indexed_with_ocr=extracted_data.get('ocr_enabled_for_file', False), # Use flag from result
                                # --- ADDED: Store truncation flag in index (optional) ---
                                # content_was_truncated=extracted_data.get('content_truncated', False) 
                                # ^^^ Requires adding 'content_was_truncated' field to the schema
                            )
                            # --- END MODIFIED LOGIC --- 

                            written_count += 1 # Corrected indentation
                            pbar_write.update(1) # Corrected indentation
                            # Yield status and progress regardless of extraction error, as metadata is written
                            yield {'type': 'status', 'message': f'写入: {display_name}', 'detail': f'写入中: {display_name}'}
                            yield {'type': 'progress', 'current': written_count, 'total': deleted_count + update_add_count, 'phase': '写入索引 (添加/更新)', 'detail': f'写入中: {display_name}'}

                yield {'type': 'status', 'message': '正在提交索引更改 (优化)...'} # Corrected indentation
                print("--- Committing index writer (optimize=True) ---") # DEBUG (Corrected indentation)
                # --- RE-ENABLE COMMIT ---
                writer.commit(optimize=True)
                # print("--- COMMIT SKIPPED FOR STEP 1 TESTING ---") # REMOVED this line
                # ------------------------
                writer = None # Indicate commit was successful
                yield {'type': 'status', 'message': '索引更新提交成功。'}
                print("--- Index commit finished ---") # DEBUG (Corrected indentation)

        except Exception as e:
            yield {'type': 'error', 'message': f'写入索引时发生严重错误: {e}'}
            # traceback.print_exc() # COMMENTED OUT
            if writer: # If error occurred before commit
                yield {'type': 'status', 'message': '正在取消索引更改...'}
                writer.cancel()
                yield {'type': 'status', 'message': '索引更改已取消。'}
        finally:
            if writer: # Should ideally be None if commit succeeded/skipped or error occurred
                try:
                    writer.cancel() # Cancel if not committed
                    yield {'type': 'status', 'message': '索引写入器已取消 (清理)。'}
                except Exception as e_cancel:
                    yield {'type': 'warning', 'message': f'清理索引写入器时出错: {e_cancel}'}
            if ix:
                ix.close()
            INDEX_ACCESS_LOCK.release() # Release write lock
            print("Index Update: Write lock released.")
            yield {'type': 'status', 'message': '索引锁已释放。'}

        final_added = added_count # Use counts tracked during scan
        final_updated = updated_count # Use counts tracked during scan
        final_deleted = deleted_count # Use count from to_delete set size
        final_errors = error_count + extraction_errors # Combine scan/processing errors and extraction errors

        # --- ADDED: 更新跳过文件记录，删除已处理的许可证限制文件 ---
        if original_license_skipped_files:
            # 计算已处理的文件（存在于原始列表但不在当前列表中的文件）
            processed_license_files = {path: reason for path, reason in original_license_skipped_files.items() 
                                      if path not in license_skipped_files}
            processed_count = len(processed_license_files)
            
            if processed_count > 0:
                yield {'type': 'status', 'message': f'已重新处理 {processed_count} 个之前因许可证限制而跳过的文件'}
                # 更新跳过文件记录，传入已处理的文件列表
                update_skipped_files_record(index_dir_path, processed_license_files)
        # ---------------------------------------------------------

        yield {'type': 'complete', 'summary': {
                'message': f'索引更新完成。添加: {final_added}, 更新: {final_updated}, 删除: {final_deleted}, 错误/跳过: {final_errors}',
                'added': final_added,
                'updated': final_updated,
                'deleted': final_deleted,
                'errors': final_errors
            }}
        print("--- Indexing Process Complete ---") # DEBUG

    except Exception as e_outer:
        yield {'type': 'error', 'message': f'索引过程中发生未处理的严重错误: {e_outer}'}
        # traceback.print_exc() # COMMENTED OUT
        # Ensure lock is released if held
        if INDEX_ACCESS_LOCK.locked():
            INDEX_ACCESS_LOCK.release()
            print("Index Update: Lock released in outer exception handler.")

# --- MODIFIED: 添加路径标准化函数用于索引键生成 ---
def normalize_path_for_index(path_str, source_dirs=None):
    """
    标准化路径用于索引键。
    如果是压缩包内的文件，保留原始格式 (archive_path::member_name)。
    对于普通文件，尽量使用与源目录的相对路径。
    
    Args:
        path_str: 要标准化的路径字符串
        source_dirs: 可选的源目录列表，用于尝试构建相对路径
    
    Returns:
        标准化后的路径字符串，用作索引键
    """
    if "::" in path_str:  # 压缩包内文件格式已经是 archive_path::member_name
        return path_str
        
    path_obj = Path(path_str)
    abs_path = str(path_obj.resolve())
    
    # 如果提供了源目录，尝试创建相对路径
    if source_dirs:
        for src_dir in source_dirs:
            src_dir_path = Path(src_dir).resolve()
            try:
                # 检查当前路径是否位于该源目录下
                if path_obj.is_relative_to(src_dir_path):
                    # 创建相对于源目录的路径，并添加源目录标识前缀
                    rel_path = path_obj.relative_to(src_dir_path)
                    return f"{src_dir_path.name}:/{rel_path}"
            except (ValueError, AttributeError):
                # Path.is_relative_to 在某些Python版本中可能不可用
                # 使用字符串方式检查
                try:
                    abs_src = str(src_dir_path)
                    if abs_path.startswith(abs_src):
                        rel_part = abs_path[len(abs_src):].lstrip('\\/')
                        return f"{src_dir_path.name}:/{rel_part}"
                except Exception:
                    pass
    
    # 如果无法创建相对路径，至少确保使用一致的分隔符格式
    return abs_path.replace('\\', '/')

def main():
    print("--- Script Started ---")
    parser = argparse.ArgumentParser(description="Index and search documents (standalone mode).")
    parser.add_argument("directory", nargs='?', default=None, help="The directory to index (required for indexing).")
    parser.add_argument("-s", "--search", help="Keyword(s) to search for in the index.")
    parser.add_argument("--index-dir", default="indexdir", help="Path to the index directory.") 
    parser.add_argument("--reindex", action="store_true", help="Force re-indexing even if only searching.")
    parser.add_argument("--min-size", type=int, help="Minimum file size in KB.")
    parser.add_argument("--max-size", type=int, help="Maximum file size in KB.")
    parser.add_argument("--start-date", help="Start date for file modification (format: YYYY-MM-DD).")
    parser.add_argument("--end-date", help="End date for file modification (format: YYYY-MM-DD).")
    parser.add_argument("--file-types", nargs='*', help="File types to filter (e.g., pdf docx).")
    parser.add_argument("--sort-by", choices=['relevance', 'date_asc', 'date_desc', 'size_asc', 'size_desc'], default='relevance', help="Sort results by: relevance, date_asc, date_desc, size_asc, size_desc.")
    args = parser.parse_args()
    print(f"Arguments parsed: {args}")
    if args.search and not args.reindex:
        print("--- Standalone Search Mode ---")
        search_results = search_index(
            args.search,
            index_dir_path=args.index_dir, # Use argument
            search_mode='fuzzy',  # Default to fuzzy search for CLI
            min_size_kb=args.min_size,
            max_size_kb=args.max_size,
            start_date=args.start_date,
            end_date=args.end_date,
            file_type_filter=args.file_types,
            sort_by=args.sort_by
        )
        if search_results:
            print("\n--- Search Results (Structured) ---")
            for result in search_results:
                print(f"File: {result['file_path']}")
                if result.get('heading'):
                    print(f"  Heading (L{result.get('level', '')}): {result['heading']}")
                if result.get('marked_heading'):
                    print(f"  Highlighted Heading: {result['marked_heading']}")
                if result.get('paragraph'):
                    print(f"  Context: {result['paragraph']}")
                if result.get('marked_paragraph'):
                    print(f"  Highlighted Context: {result['marked_paragraph']}")
                if result.get('excel_headers') and result.get('excel_values'):
                    print(f"  Excel Sheet: {result['excel_sheet']}, Row: {result['excel_row_idx']}")
                    for header, value in zip(result['excel_headers'], result['excel_values']):
                        print(f"    {header}: {value}")
                print(f"  Score: {result['score']}")
                print("-" * 20)
        else:
            print("Search returned no results.")
        print("--- Search Complete ---")
        return
    if args.directory:
        print("--- Standalone Indexing/Update Mode ---")
        start_time = time.time()
        for status_data in create_or_update_index(args.directory, args.index_dir):
            msg_type = status_data.get('type')
            message = status_data.get('message', '')
            prefix = "" if msg_type == 'status' else f"{msg_type.upper()}: "
            print(prefix + message)
        end_time = time.time()
        print(f"\n总耗时: {end_time - start_time:.2f} 秒")
        if args.reindex and args.search:
            print("\n--- Running search after re-indexing ---")
            search_results = search_index(
                args.search,
                index_dir_path=args.index_dir, # Use argument
                search_mode='fuzzy',
                min_size_kb=args.min_size,
                max_size_kb=args.max_size,
                start_date=args.start_date,
                end_date=args.end_date,
                file_type_filter=args.file_types,
                sort_by=args.sort_by
            )
            if search_results:
                print("\n--- Search Results (Structured) ---")
                for result in search_results:
                    print(f"File: {result['file_path']}")
                    if result.get('heading'):
                        print(f"  Heading (L{result.get('level', '')}): {result['heading']}")
                    if result.get('marked_heading'):
                        print(f"  Highlighted Heading: {result['marked_heading']}")
                    if result.get('paragraph'):
                        print(f"  Context: {result['paragraph']}")
                    if result.get('marked_paragraph'):
                        print(f"  Highlighted Context: {result['marked_paragraph']}")
                    if result.get('excel_headers') and result.get('excel_values'):
                        print(f"  Excel Sheet: {result['excel_sheet']}, Row: {result['excel_row_idx']}")
                        for header, value in zip(result['excel_headers'], result['excel_values']):
                            print(f"    {header}: {value}")
                    print(f"  Score: {result['score']}")
                    print("-" * 20)
            else:
                print("Search returned no results.")
            print("--- Search Complete ---")
    else:
        if not args.search:
            parser.print_help()
    print("--- Script Finished ---")

if __name__ == "__main__":
    main()
