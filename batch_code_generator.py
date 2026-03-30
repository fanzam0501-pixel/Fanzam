#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
条形码/二维码批量生成工具
支持：Code128、Code39、EAN13、QR Code
"""

import os
from barcode import Code128, Code39, EAN13
from barcode.writer import ImageWriter
import qrcode
from PIL import Image

def generate_barcode(data, output_path, barcode_type='code128', size=(300, 150)):
    """
    生成条形码
    
    Args:
        data: 条形码内容
        output_path: 保存路径
        barcode_type: 条形码类型 (code128, code39, ean13)
        size: 图片尺寸 (宽, 高)
    """
    try:
        if barcode_type.lower() == 'code128':
            barcode_class = Code128
        elif barcode_type.lower() == 'code39':
            barcode_class = Code39
        elif barcode_type.lower() == 'ean13':
            barcode_class = EAN13
        else:
            barcode_class = Code128
        
        # 生成条形码
        barcode_obj = barcode_class(data, writer=ImageWriter())
        
        # 设置选项
        options = {
            'write_text': True,  # 显示文字
            'module_height': 15,
            'quiet_zone': 3,
            'font_size': 12,
        }
        
        # 保存
        barcode_obj.save(output_path.replace('.png', ''), options=options)
        
        # 调整尺寸
        if os.path.exists(output_path):
            img = Image.open(output_path)
            img = img.resize(size, Image.Resampling.LANCZOS)
            img.save(output_path)
        
        return True
    except Exception as e:
        print(f"生成条形码失败 [{data}]: {e}")
        return False

def generate_qr(data, output_path, size=300, error_correction=qrcode.constants.ERROR_CORRECT_H):
    """
    生成二维码
    
    Args:
        data: 二维码内容
        output_path: 保存路径
        size: 图片尺寸（像素）
        error_correction: 容错级别
    """
    try:
        qr = qrcode.QRCode(
            version=None,
            error_correction=error_correction,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        # 生成图片
        img = qr.make_image(fill_color="black", back_color="white")
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        img.save(output_path)
        
        return True
    except Exception as e:
        print(f"生成二维码失败 [{data}]: {e}")
        return False

def batch_generate_from_list(data_list, output_dir, code_type='barcode', barcode_format='code128', size=(300, 150)):
    """
    根据列表批量生成
    
    Args:
        data_list: 数据列表
        output_dir: 输出目录
        code_type: 'barcode' 或 'qrcode'
        barcode_format: 条形码格式 (code128, code39, ean13)
        size: 图片尺寸
    """
    os.makedirs(output_dir, exist_ok=True)
    
    success_count = 0
    for i, data in enumerate(data_list, 1):
        safe_data = str(data).replace('/', '_').replace(':', '_')
        output_path = os.path.join(output_dir, f"{safe_data}.png")
        
        if code_type == 'barcode':
            if generate_barcode(data, output_path, barcode_format, size):
                success_count += 1
                print(f"[{i}/{len(data_list)}] 条形码已生成: {data}")
        else:
            if generate_qr(data, output_path, size[0]):
                success_count += 1
                print(f"[{i}/{len(data_list)}] 二维码已生成: {data}")
    
    print(f"\n完成！成功生成 {success_count}/{len(data_list)} 个")
    return success_count

def generate_from_file(file_path, output_dir, code_type='barcode', barcode_format='code128', size=(300, 150)):
    """
    从文件读取数据批量生成（每行一个）
    """
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data_list = [line.strip() for line in f if line.strip()]
    
    print(f"从文件读取到 {len(data_list)} 条数据")
    batch_generate_from_list(data_list, output_dir, code_type, barcode_format, size)

def generate_sequence(prefix, start, end, output_dir, code_type='barcode', barcode_format='code128', size=(300, 150)):
    """
    生成序列号（如 SN001 ~ SN100）
    
    Args:
        prefix: 前缀（如 'SN'）
        start: 起始编号
        end: 结束编号
        output_dir: 输出目录
    """
    data_list = [f"{prefix}{str(i).zfill(len(str(end)))}" for i in range(start, end + 1)]
    batch_generate_from_list(data_list, output_dir, code_type, barcode_format, size)

# ==================== 示例用法 ====================
if __name__ == "__main__":
    import sys
    
    # 示例1：批量生成条形码（从列表）
    # data_list = ["SN:5504AJML26440001", "SN:5504AJML26440002", "SN:5504AJML26440003"]
    # batch_generate_from_list(data_list, "./barcodes_output", code_type='barcode', barcode_format='code128', size=(400, 200))
    
    # 示例2：批量生成二维码
    # data_list = ["https://example.com/1", "https://example.com/2", "https://example.com/3"]
    # batch_generate_from_list(data_list, "./qrcodes_output", code_type='qrcode', size=(300, 300))
    
    # 示例3：从文件读取生成
    # generate_from_file("data.txt", "./output", code_type='barcode')
    
    # 示例4：生成序列号（SN0001 ~ SN0340）
    # generate_sequence("SN:", 55040001, 55040340, "./serial_barcodes", code_type='barcode', size=(400, 200))
    
    print("批量生成工具已加载")
    print("\n使用方法：")
    print("1. 从列表生成：batch_generate_from_list(data_list, output_dir, code_type='barcode')")
    print("2. 从文件生成：generate_from_file('data.txt', output_dir)")
    print("3. 生成序列号：generate_sequence('SN:', 1, 100, output_dir)")
    print("\ncode_type: 'barcode' 或 'qrcode'")
    print("barcode_format: 'code128', 'code39', 'ean13'")
