import hashlib
import hmac
import time
from urllib.parse import urlencode

from rest_framework import viewsets
from rest_framework.decorators import action
from .models import Data
from .serializers import DataSerializer

from django.shortcuts import get_object_or_404
from django.http import Http404, FileResponse, HttpResponseForbidden
from django.conf import settings

from rest_framework.response import Response # from viewsets doc
from rest_framework import permissions, status
from rest_framework.parsers import MultiPartParser, FormParser

# A ViewSet class is simply a type of class-based View,
# that does not provide any method handlers such as .get() or .post(),
# and instead provides actions such as .list() and .create().

# Typically, rather than explicitly registering the views in a viewset
# in the urlconf, you'll register the viewset with a router class,
# that automatically determines the urlconf for you.

# 禁止预览的可执行文件类型
FORBIDDEN_EXTENSIONS = {
    'exe', 'sh', 'py', 'pyc', 'pyo', 'pyd', 'bat', 'cmd', 'com',
    'js', 'vbs', 'ps1', 'psm1', 'psd1', 'sh', 'bash', 'zsh', 'fish',
    'csh', 'ksh', 'tcl', 'expect', 'pl', 'pm', 'php', 'php3', 'php4',
    'php5', 'php7', 'phar', 'rb', 'rhtml', 'rjs', 'rxml', 'erb',
    'go', 'rs', 'java', 'class', 'jar', 'war', 'ear', 'dll', 'so',
    'dylib', 'app', 'msi', 'apk', 'ipa', 'deb', 'rpm', 'pkg'
}

# 支持预览的文件类型
PREVIEWABLE_TYPES = {
    'image': {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg', 'ico'},
    'pdf': {'pdf'}
}

def get_file_type(extension):
    """根据文件扩展名判断文件类型"""
    ext = extension.lower()
    if ext in PREVIEWABLE_TYPES['image']:
        return 'image'
    if ext in PREVIEWABLE_TYPES['pdf']:
        return 'pdf'
    return 'other'

def is_forbidden_extension(extension):
    """检查文件扩展名是否为禁止预览的类型"""
    return extension.lower() in FORBIDDEN_EXTENSIONS

def generate_preview_signature(file_id, timestamp, secret_key):
    """生成预览 URL 的签名"""
    message = f"{file_id}:{timestamp}".encode('utf-8')
    secret = secret_key.encode('utf-8')
    return hmac.new(secret, message, hashlib.sha256).hexdigest()

def verify_preview_signature(file_id, timestamp, signature, secret_key):
    """验证预览 URL 的签名"""
    expected_signature = generate_preview_signature(file_id, timestamp, secret_key)
    return hmac.compare_digest(expected_signature, signature)

class DataViewSet(viewsets.ModelViewSet):
    queryset = Data.objects.all()
    serializer_class = DataSerializer

    permission_classes = (permissions.AllowAny,) # we assume that we have a session user
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, format=None):
        serializer = DataSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        deleted = skipped = 0
        for k, v in kwargs.items():
            for id_str in v.split(','):
                try:
                    self.perform_destroy(Data.objects.get(pk=int(id_str)))
                    deleted += 1
                except (Data.DoesNotExist, ValueError):
                    skipped += 1
        return Response({'deleted': deleted, 'skipped': skipped}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='preview-url')
    def get_preview_url(self, request, pk=None):
        """生成带时效性的预览 URL"""
        file_obj = get_object_or_404(Data, pk=pk)
        filename = file_obj.file.name
        extension = filename.split('.')[-1].lower() if '.' in filename else ''
        
        # 检查是否为禁止预览的类型
        if is_forbidden_extension(extension):
            return Response(
                {'error': 'Forbidden file type', 'message': 'This file type cannot be previewed'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 生成 10 分钟有效的 URL
        timestamp = int(time.time())
        signature = generate_preview_signature(pk, timestamp, settings.SECRET_KEY)
        
        # 构建预览 URL
        preview_url = request.build_absolute_uri(
            f'/api/files/{pk}/preview/?t={timestamp}&s={signature}'
        )
        
        file_type = get_file_type(extension)
        
        return Response({
            'preview_url': preview_url,
            'file_type': file_type,
            'filename': filename,
            'expires_in': 600  # 10 分钟
        })

    @action(detail=True, methods=['get'], url_path='preview')
    def preview(self, request, pk=None):
        """预览文件 - 校验签名和时效性"""
        # 获取并验证参数
        timestamp = request.query_params.get('t')
        signature = request.query_params.get('s')
        
        if not timestamp or not signature:
            return HttpResponseForbidden('Missing required parameters')
        
        try:
            timestamp = int(timestamp)
        except ValueError:
            return HttpResponseForbidden('Invalid timestamp')
        
        # 检查是否过期（10 分钟）
        current_time = int(time.time())
        if current_time - timestamp > 600:
            return HttpResponseForbidden('Preview URL has expired')
        
        # 验证签名
        if not verify_preview_signature(pk, timestamp, signature, settings.SECRET_KEY):
            return HttpResponseForbidden('Invalid signature')
        
        # 获取文件
        file_obj = get_object_or_404(Data, pk=pk)
        filename = file_obj.file.name
        extension = filename.split('.')[-1].lower() if '.' in filename else ''
        
        # 再次检查文件类型（安全冗余）
        if is_forbidden_extension(extension):
            return HttpResponseForbidden('Forbidden file type')
        
        # 返回文件
        try:
            file_path = file_obj.file.path
            # 根据文件类型设置 Content-Type
            content_type = 'application/octet-stream'
            file_type = get_file_type(extension)
            
            if file_type == 'image':
                if extension in ['jpg', 'jpeg']:
                    content_type = 'image/jpeg'
                elif extension == 'png':
                    content_type = 'image/png'
                elif extension == 'gif':
                    content_type = 'image/gif'
                elif extension == 'bmp':
                    content_type = 'image/bmp'
                elif extension == 'webp':
                    content_type = 'image/webp'
                elif extension == 'svg':
                    content_type = 'image/svg+xml'
                elif extension == 'ico':
                    content_type = 'image/x-icon'
            elif file_type == 'pdf':
                content_type = 'application/pdf'
            
            response = FileResponse(open(file_path, 'rb'), content_type=content_type)
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            return response
        except FileNotFoundError:
            raise Http404("File not found")
