#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import pdfplumber
from tqdm import tqdm

def is_header_footer(text):
    """
    判断文本是否为页眉或页脚
    """
    if not text:
        return True
    
    # 过滤掉纯数字（可能是页码）
    if text.strip().isdigit():
        return True
    
    
    # 检测页码标记，如 "--- 第 15 页 ---"
    if re.match(r"^--- 第 \d+ 页 ---$", text.strip()):
        return True
    
    # 过滤掉常见的页眉页脚内容，但避免过滤只包含"页"或"Page of"的实际内容
    common_header_footer = ['©', '版权所有']
    
    # 检查是否为页眉页脚的常见模式，而不是仅包含这些词的正文内容
    if text.strip() == '页' or text.strip() == 'Page':
        return True
    
    # 检查组合模式，如"第X页"或"Page X of Y"
    if re.match(r'^第\s*\d+\s*页$', text.strip()) or re.match(r'^Page\s*\d+\s*of\s*\d+$', text.strip()):
        return True
    
    return any(keyword in text for keyword in common_header_footer)

def should_merge_lines(line1, line2):
    """
    判断两行是否应该合并
    """
    if not line1 or not line2:
        return False
    
    # 如果第一行以标点符号结尾，不合并
    end_punctuation = ['。', '！', '？', '；', '：', '.', '!', '?', ';', ':']
    if any(line1.endswith(p) for p in end_punctuation):
        return False
    
    # 如果第二行以标点符号开头，不合并
    start_punctuation = ['。', '！', '？', '；', '：', '.', '!', '?', ';', ':']
    if any(line2.startswith(p) for p in start_punctuation):
        return False
    
    # 如果两行都是短句，不合并
    if len(line1) < 10 and len(line2) < 10:
        return False
    
    return True

def merge_lines(lines):
    """
    合并应该合并的行
    """
    if not lines:
        return []
    
    merged_lines = []
    current_line = lines[0]
    
    for next_line in lines[1:]:
        if should_merge_lines(current_line, next_line):
            current_line += next_line
        else:
            merged_lines.append(current_line)
            current_line = next_line
    
    merged_lines.append(current_line)
    return merged_lines


def is_section_title(line):
    """
    判断是否为章节标题
    支持以下格式：
    1. 第X章 标题
    2. 第X节 标题
    """
    if not line or not line.strip():
        return False
    
    line = line.strip()
    
    # 匹配"第X章"格式
    if re.match(r'^第[一二三四五六七八九十百千万零0-9]+章$', line):
        print(f"匹配到章节：{line}")
        return True
    
    # 匹配"第X章 标题"格式
    if re.match(r'^第[一二三四五六七八九十百千万零0-9]+章[ ]+', line):
        print(f"匹配到章节：{line}")
        return True
    
    # 匹配"第X节 标题"格式
    if re.match(r'^第[一二三四五六七八九十百千万零0-9]+节[ ]+', line):
        return True
    
    return False

def identify_structure(text):
    """
    识别文本的结构，判断是前言、章节标题、小节标题还是正文
    """
    # 去除空格并转小写用于匹配
    text_lower = text.lower().strip()
    
    # 目录匹配
    if re.match(r'^(目\s*录|目\s*次|CONTENTS|TABLE OF CONTENTS)$', text_lower, re.IGNORECASE):
        return "toc_header", text
    
    
    # 前言/序言匹配
    if re.match(r'^(前言|序言|引言|致谢|序|preface|introduction|acknowledgement)$', text_lower):
        return "preface", text
    
    # 匹配"第X章"格式 
    chapter_match = re.match(r'^第[一二三四五六七八九十百千万零0-9]+章$', text)
    if chapter_match:
        print(f"匹配到章节2：{text}")
        return "chapter", text  # 保留完整章节名
    
    # 章节匹配（第X章/第X章 标题）
    chapter_match = re.match(r'^第[一二三四五六七八九十百千万零0-9]+章[ 　]+', text)
    if chapter_match:
        print(f"匹配到章节2：{text}")
        return "chapter", text  # 保留完整章节名
    
    
    # 小节匹配（1.1/1.1.1 格式）
    section_match = re.match(r'^([0-9]+\.[0-9.]+)[\s\.．]+(.*)', text)
    if section_match:
        return "section", text
    
    # 小节匹配（第X节）
    section_match2 = re.match(r'^第[一二三四五六七八九十百千万零0-9]+节[\s　]*', text)
    if section_match2:
        return "section", text
    
    # 附录匹配
    if re.match(r'^(附录|appendix)[\s　a-zA-Z]*', text_lower):
        return "appendix", text
    
    # 参考文献匹配
    if re.match(r'^(参考文献|references)$', text_lower):
        return "references", text
    
    # 默认为正文
    return "content", text

def convert_pdf_to_text(pdf_path, output_path=None):
    """
    将PDF文件转换为原始文本格式，不进行任何处理
    
    Args:
        pdf_path (str): PDF文件路径
        output_path (str, optional): 输出文件路径，如果不指定则使用PDF文件名
    """
    if not os.path.exists(pdf_path):
        print(f"错误：文件 {pdf_path} 不存在")
        return False, None
    
    if output_path is None:
        output_path = os.path.splitext(pdf_path)[0] + '.raw'
    
    try:
        # 收集所有文本
        all_text = []
        
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"开始提取PDF文件：{pdf_path}")
            print(f"总页数：{total_pages}")
            
            for page_num, page in enumerate(tqdm(pdf.pages, desc="提取原始文本"), 1):
                text = page.extract_text()
                if text:
                    # 添加页码标记以便于后续处理
                    all_text.append(f"--- 第 {page_num} 页 ---\n{text}\n")
        
        # 写入原始文本文件
        print(f"写入原始文本文件：{output_path}")
        with open(output_path, 'w', encoding='utf-8') as raw_file:
            raw_file.write('\n'.join(all_text))
        
        print(f"\n原始文本提取完成！输出文件：{output_path}")
        return True, output_path
    
    except Exception as e:
        print(f"提取过程中出现错误：{str(e)}")
        import traceback
        traceback.print_exc()
        return False, None

def convert_raw_to_markdown(raw_path, output_path=None):
    """
    将原始文本文件转换为Markdown格式，专注于处理文档内容中的章节标题
    
    Args:
        raw_path (str): 原始文本文件路径
        output_path (str, optional): 输出文件路径，如果不指定则使用原文件名
    """
    if not os.path.exists(raw_path):
        print(f"错误：文件 {raw_path} 不存在")
        return False
    
    if output_path is None:
        output_path = os.path.splitext(raw_path)[0] + '.md'
    
    try:
        # 读取原始文本
        print(f"读取原始文本文件：{raw_path}")
        with open(raw_path, 'r', encoding='utf-8') as raw_file:
            content = raw_file.read()
        
        # 分割成行
        lines = content.split('\n')
        all_text_lines = []
        
        # 去除页码标记和过滤页眉页脚
        current_lines = []
        for line in lines:
            # 跳过页码标记行            
            if line.startswith("--- 第") and line.endswith("页 ---"):
                if current_lines:
                    all_text_lines.extend(current_lines)
                    current_lines = []
                continue
            
            # 过滤空行和页眉页脚
            if line.strip() and not is_header_footer(line.strip()):
                # 检查是否为章节标题或特殊标题
                if is_section_title(line.strip()) or identify_structure(line.strip())[0] in ["preface", "chapter", "section", "appendix", "references"]:
                    # 如果有未处理的行，先添加
                    if current_lines:
                        all_text_lines.extend(current_lines)
                        current_lines = []
                    # 直接添加标题
                    all_text_lines.append(line.strip())
                else:
                    current_lines.append(line.strip())
        
        # 添加最后一组行
        if current_lines:
            all_text_lines.extend(current_lines)
        
        # 合并行（不合并标题）
        print("处理文本格式...")
        processed_lines = []
        i = 0
        while i < len(all_text_lines):
            line = all_text_lines[i]
            
            # 如果是标题，不合并
            if is_section_title(line) or identify_structure(line)[0] in ["preface", "chapter", "section", "appendix", "references"]:
                processed_lines.append(line)
                i += 1
            else:
                # 找出可能需要合并的连续非标题行
                non_title_lines = [line]
                j = i + 1
                while j < len(all_text_lines) and not (is_section_title(all_text_lines[j]) or 
                      identify_structure(all_text_lines[j])[0] in ["preface", "chapter", "section", "appendix", "references"]):
                    non_title_lines.append(all_text_lines[j])
                    j += 1
                
                # 合并这些行
                merged = merge_lines(non_title_lines)
                processed_lines.extend(merged)
                i = j
        
        # 处理文档结构
        print("分析文档结构...")
        structured_content = []
        
        for line in processed_lines:
            # 识别文档结构
            structure_type, content = identify_structure(line)
            
            # 如果是正文内容，直接添加
            if structure_type == "content":
                structured_content.append((structure_type, content))
            # 如果是目录相关，跳过
            elif structure_type in ["toc_header", "toc_item"]:
                continue
            # 其他类型作为标题处理
            else:
                structured_content.append((structure_type, content))
        
        # 写入Markdown文件
        print(f"写入Markdown文件：{output_path}")
        with open(output_path, 'w', encoding='utf-8') as md_file:
            for structure_type, content in structured_content:
                if structure_type == "preface":
                    md_file.write(f"# {content}\n\n")
                    md_file.write("---\n\n")
                elif structure_type == "chapter":
                    md_file.write(f"# {content}\n\n")
                    md_file.write("---\n\n")
                elif structure_type == "section":
                    md_file.write(f"## {content}\n\n")
                elif structure_type == "appendix":
                    md_file.write(f"# {content}\n\n")
                    md_file.write("---\n\n")
                elif structure_type == "references":
                    md_file.write(f"# {content}\n\n")
                    md_file.write("---\n\n")
                else:  # 正文内容
                    md_file.write(f"{content}\n\n")
            
            # 在文档末尾添加转换信息
            md_file.write("\n\n---\n\n")
            md_file.write("*由PDF2MD自动转换生成*\n")
        
        print(f"\n转换完成！输出文件：{output_path}")
        return True
    
    except Exception as e:
        print(f"转换过程中出现错误：{str(e)}")
        import traceback
        traceback.print_exc()
        return False

def convert_pdf_to_markdown(pdf_path, output_path=None):
    """
    将PDF文件转换为Markdown格式，首先生成原始文本文件，然后基于原始文件生成Markdown
    如果.raw文件已存在，则直接使用该文件进行转换
    
    Args:
        pdf_path (str): PDF文件路径
        output_path (str, optional): 输出文件路径，如果不指定则使用PDF文件名
    """
    if not os.path.exists(pdf_path):
        print(f"错误：文件 {pdf_path} 不存在")
        return False
    
    # 确定输出文件路径
    if output_path is None:
        md_output_path = os.path.splitext(pdf_path)[0] + '.md'
    else:
        md_output_path = output_path
    
    # 确定原始文本文件路径
    raw_output_path = os.path.splitext(pdf_path)[0] + '.raw'
    
    # 检查.raw文件是否已存在
    if os.path.exists(raw_output_path):
        print(f"发现已存在的原始文本文件：{raw_output_path}")
        print("将直接使用该文件进行转换...")
        raw_path = raw_output_path
    else:
        # 如果.raw文件不存在，则从PDF生成
        print(f"未找到原始文本文件，将从PDF生成：{raw_output_path}")
        success, raw_path = convert_pdf_to_text(pdf_path, raw_output_path)
        if not success:
            print("生成原始文本文件失败，无法继续进行Markdown转换")
            return False
    
    # 基于原始文本文件生成Markdown文件
    success = convert_raw_to_markdown(raw_path, md_output_path)
    if not success:
        print("生成Markdown文件失败")
        return False
    
    return True

def main():
    if len(sys.argv) < 2:
        print("使用方法：python pdf2md.py <PDF文件路径> [输出文件路径]")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    convert_pdf_to_markdown(pdf_path, output_path)

if __name__ == "__main__":
    main() 