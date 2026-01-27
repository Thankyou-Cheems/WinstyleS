"""
文件系统操作适配器

提供统一的文件操作接口，并支持 Mock 测试。
"""

import hashlib
import shutil
from abc import ABC, abstractmethod
from pathlib import Path


class IFileSystemAdapter(ABC):
    """文件系统适配器接口"""

    @abstractmethod
    def read_text(self, path: str, encoding: str = "utf-8") -> str:
        """读取文本文件"""
        pass

    @abstractmethod
    def read_bytes(self, path: str) -> bytes:
        """读取二进制文件"""
        pass

    @abstractmethod
    def write_text(self, path: str, content: str, encoding: str = "utf-8") -> None:
        """写入文本文件"""
        pass

    @abstractmethod
    def write_bytes(self, path: str, content: bytes) -> None:
        """写入二进制文件"""
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        """检查路径是否存在"""
        pass

    @abstractmethod
    def is_file(self, path: str) -> bool:
        """检查是否是文件"""
        pass

    @abstractmethod
    def is_dir(self, path: str) -> bool:
        """检查是否是目录"""
        pass

    @abstractmethod
    def copy(self, src: str, dst: str) -> None:
        """复制文件"""
        pass

    @abstractmethod
    def get_size(self, path: str) -> int:
        """获取文件大小"""
        pass

    @abstractmethod
    def get_hash(self, path: str, algorithm: str = "sha256") -> str:
        """计算文件哈希"""
        pass

    @abstractmethod
    def list_dir(self, path: str) -> list[str]:
        """列出目录内容"""
        pass


class WindowsFileSystemAdapter(IFileSystemAdapter):
    """真实的 Windows 文件系统适配器"""

    def read_text(self, path: str, encoding: str = "utf-8") -> str:
        """读取文本文件"""
        return Path(path).read_text(encoding=encoding)

    def read_bytes(self, path: str) -> bytes:
        """读取二进制文件"""
        return Path(path).read_bytes()

    def write_text(self, path: str, content: str, encoding: str = "utf-8") -> None:
        """写入文本文件"""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding=encoding)

    def write_bytes(self, path: str, content: bytes) -> None:
        """写入二进制文件"""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)

    def exists(self, path: str) -> bool:
        """检查路径是否存在"""
        return Path(path).exists()

    def is_file(self, path: str) -> bool:
        """检查是否是文件"""
        return Path(path).is_file()

    def is_dir(self, path: str) -> bool:
        """检查是否是目录"""
        return Path(path).is_dir()

    def copy(self, src: str, dst: str) -> None:
        """复制文件"""
        dst_path = Path(dst)
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    def get_size(self, path: str) -> int:
        """获取文件大小"""
        return Path(path).stat().st_size

    def get_hash(self, path: str, algorithm: str = "sha256") -> str:
        """计算文件哈希"""
        h = hashlib.new(algorithm)
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def list_dir(self, path: str) -> list[str]:
        """列出目录内容"""
        return [str(p) for p in Path(path).iterdir()]


class MockFileSystemAdapter(IFileSystemAdapter):
    """
    模拟文件系统适配器 - 用于测试
    """

    def __init__(
        self,
        files: dict[str, str | bytes] | None = None,
    ) -> None:
        """
        Args:
            files: 初始文件数据，格式为 {path: content}
        """
        self._files: dict[str, str | bytes] = files or {}
        self._dirs: set[str] = set()

    def read_text(self, path: str, encoding: str = "utf-8") -> str:
        """读取模拟的文本文件"""
        content = self._files.get(path)
        if content is None:
            raise FileNotFoundError(path)
        if isinstance(content, bytes):
            return content.decode(encoding)
        return content

    def read_bytes(self, path: str) -> bytes:
        """读取模拟的二进制文件"""
        content = self._files.get(path)
        if content is None:
            raise FileNotFoundError(path)
        if isinstance(content, str):
            return content.encode()
        return content

    def write_text(self, path: str, content: str, encoding: str = "utf-8") -> None:
        """写入模拟的文本文件"""
        self._files[path] = content

    def write_bytes(self, path: str, content: bytes) -> None:
        """写入模拟的二进制文件"""
        self._files[path] = content

    def exists(self, path: str) -> bool:
        """检查路径是否存在"""
        return path in self._files or path in self._dirs

    def is_file(self, path: str) -> bool:
        """检查是否是文件"""
        return path in self._files

    def is_dir(self, path: str) -> bool:
        """检查是否是目录"""
        return path in self._dirs

    def copy(self, src: str, dst: str) -> None:
        """复制模拟文件"""
        if src not in self._files:
            raise FileNotFoundError(src)
        self._files[dst] = self._files[src]

    def get_size(self, path: str) -> int:
        """获取模拟文件大小"""
        content = self._files.get(path)
        if content is None:
            raise FileNotFoundError(path)
        if isinstance(content, str):
            return len(content.encode())
        return len(content)

    def get_hash(self, path: str, algorithm: str = "sha256") -> str:
        """计算模拟文件哈希"""
        content = self._files.get(path)
        if content is None:
            raise FileNotFoundError(path)
        if isinstance(content, str):
            content = content.encode()
        return hashlib.new(algorithm, content).hexdigest()

    def list_dir(self, path: str) -> list[str]:
        """列出模拟目录内容"""
        prefix = path.rstrip("/\\") + "/"
        return [p for p in self._files if p.startswith(prefix)]

    def add_file(self, path: str, content: str | bytes) -> None:
        """添加模拟文件（测试辅助方法）"""
        self._files[path] = content

    def add_dir(self, path: str) -> None:
        """添加模拟目录（测试辅助方法）"""
        self._dirs.add(path)
