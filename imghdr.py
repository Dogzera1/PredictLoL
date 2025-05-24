"""
Módulo imghdr de compatibilidade para Python 3.13
O módulo imghdr foi removido no Python 3.13, mas é necessário para python-telegram-bot
"""

import io
from typing import Optional, BinaryIO, Union

def what(file: Union[str, BinaryIO], h: Optional[bytes] = None) -> Optional[str]:
    """
    Detecta o formato de uma imagem
    Implementação simplificada para compatibilidade
    """
    try:
        if isinstance(file, str):
            with open(file, 'rb') as f:
                header = f.read(32)
        elif hasattr(file, 'read'):
            pos = file.tell() if hasattr(file, 'tell') else None
            header = file.read(32)
            if pos is not None and hasattr(file, 'seek'):
                file.seek(pos)
        else:
            header = h or b''
        
        # Detectar formatos básicos por header
        if header.startswith(b'\xff\xd8\xff'):
            return 'jpeg'
        elif header.startswith(b'\x89PNG\r\n\x1a\n'):
            return 'png'
        elif header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
            return 'gif'
        elif header.startswith(b'RIFF') and b'WEBP' in header[:12]:
            return 'webp'
        elif header.startswith(b'BM'):
            return 'bmp'
        elif header.startswith(b'\x00\x00\x01\x00'):
            return 'ico'
        else:
            return None
            
    except Exception:
        return None

# Aliases para compatibilidade
test_jpeg = lambda h, f: h.startswith(b'\xff\xd8\xff')
test_png = lambda h, f: h.startswith(b'\x89PNG\r\n\x1a\n')
test_gif = lambda h, f: h.startswith(b'GIF87a') or h.startswith(b'GIF89a')
test_webp = lambda h, f: h.startswith(b'RIFF') and b'WEBP' in h[:12]
test_bmp = lambda h, f: h.startswith(b'BM')
test_ico = lambda h, f: h.startswith(b'\x00\x00\x01\x00')

# Lista de testes (compatibilidade)
tests = [
    test_jpeg,
    test_png, 
    test_gif,
    test_webp,
    test_bmp,
    test_ico
] 