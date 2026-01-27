"""
哈希工具 - 文件完整性校验
"""

import hashlib
from pathlib import Path
from typing import Dict


def compute_hash(
    file_path: str,
    algorithm: str = "sha256",
    chunk_size: int = 8192,
) -> str:
    """
    计算文件的哈希值
    
    Args:
        file_path: 文件路径
        algorithm: 哈希算法，默认 sha256
        chunk_size: 读取块大小
        
    Returns:
        十六进制哈希字符串
    """
    h = hashlib.new(algorithm)
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    
    return h.hexdigest()


def verify_hash(
    file_path: str,
    expected_hash: str,
    algorithm: str = "sha256",
) -> bool:
    """
    验证文件哈希值
    
    Args:
        file_path: 文件路径
        expected_hash: 预期的哈希值
        algorithm: 哈希算法
        
    Returns:
        哈希是否匹配
    """
    try:
        actual_hash = compute_hash(file_path, algorithm)
        return actual_hash.lower() == expected_hash.lower()
    except (OSError, IOError):
        return False


def compute_hashes_for_directory(
    directory: str,
    algorithm: str = "sha256",
    pattern: str = "*",
) -> Dict[str, str]:
    """
    计算目录下所有文件的哈希值
    
    Args:
        directory: 目录路径
        algorithm: 哈希算法
        pattern: 文件匹配模式
        
    Returns:
        {相对路径: 哈希值} 的字典
    """
    dir_path = Path(directory)
    hashes: Dict[str, str] = {}
    
    for file_path in dir_path.rglob(pattern):
        if file_path.is_file():
            relative_path = file_path.relative_to(dir_path)
            hashes[str(relative_path)] = compute_hash(str(file_path), algorithm)
    
    return hashes


def generate_checksum_file(
    directory: str,
    output_file: str = "checksums.sha256",
    algorithm: str = "sha256",
) -> None:
    """
    生成校验和文件
    
    格式与 sha256sum 兼容:
    <hash>  <filename>
    
    Args:
        directory: 目录路径
        output_file: 输出文件名
        algorithm: 哈希算法
    """
    dir_path = Path(directory)
    output_path = dir_path / output_file
    
    hashes = compute_hashes_for_directory(directory, algorithm)
    
    with open(output_path, "w", encoding="utf-8") as f:
        for relative_path, file_hash in sorted(hashes.items()):
            # 使用 Unix 风格的路径分隔符以保持兼容性
            unix_path = relative_path.replace("\\", "/")
            f.write(f"{file_hash}  {unix_path}\n")


def verify_checksum_file(
    directory: str,
    checksum_file: str = "checksums.sha256",
    algorithm: str = "sha256",
) -> tuple[bool, list[str]]:
    """
    验证校验和文件
    
    Args:
        directory: 目录路径
        checksum_file: 校验和文件名
        algorithm: 哈希算法
        
    Returns:
        (是否全部通过, 失败的文件列表) 的元组
    """
    dir_path = Path(directory)
    checksum_path = dir_path / checksum_file
    
    if not checksum_path.exists():
        return False, ["checksum file not found"]
    
    failed_files: list[str] = []
    
    with open(checksum_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            # 解析 "<hash>  <filename>" 格式
            parts = line.split("  ", 1)
            if len(parts) != 2:
                continue
            
            expected_hash, relative_path = parts
            
            # 转换为本地路径
            file_path = dir_path / relative_path.replace("/", "\\")
            
            if not file_path.exists():
                failed_files.append(f"{relative_path} (missing)")
            elif not verify_hash(str(file_path), expected_hash, algorithm):
                failed_files.append(f"{relative_path} (hash mismatch)")
    
    return len(failed_files) == 0, failed_files
