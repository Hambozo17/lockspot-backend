"""
LockSpot URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect
import os


def root_view(request):
    """Root endpoint - API welcome message"""
    return JsonResponse({
        'name': 'LockSpot API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'admin': '/admin/',
            'api': '/api/',
            'health': '/api/health/',
            'docs': '/api/',
            'download': '/download/',
        },
        'message': 'Welcome to LockSpot Smart Locker System API'
    })


def admin_redirect(request):
    """Redirect to admin dashboard"""
    return redirect('/admin/')


def download_page(request):
    """APK Download page - for QR code scanning"""
    html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Download LockSpot App</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #6B4226 0%, #8B5E3C 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 400px;
            width: 100%;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        .logo { font-size: 60px; margin-bottom: 20px; }
        h1 { color: #6B4226; margin-bottom: 10px; font-size: 28px; }
        .subtitle { color: #666; margin-bottom: 30px; font-size: 14px; }
        .download-btn {
            display: inline-block;
            background: linear-gradient(135deg, #6B4226 0%, #8B5E3C 100%);
            color: white;
            padding: 18px 40px;
            border-radius: 30px;
            text-decoration: none;
            font-size: 18px;
            font-weight: bold;
            transition: transform 0.3s, box-shadow 0.3s;
            margin-bottom: 20px;
        }
        .download-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(107, 66, 38, 0.4);
        }
        .features { margin-top: 30px; text-align: left; }
        .feature {
            display: flex;
            align-items: center;
            margin: 15px 0;
            color: #555;
        }
        .feature-icon {
            width: 40px;
            height: 40px;
            background: #f5f0eb;
            border-radius: 10px;
            display: flex;
            justify-content: center;
            align-items: center;
            margin-right: 15px;
            font-size: 20px;
        }
        .version { color: #999; font-size: 12px; margin-top: 30px; }
        .install-note {
            background: #fff3cd;
            border-radius: 10px;
            padding: 15px;
            margin-top: 20px;
            font-size: 12px;
            color: #856404;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🔐</div>
        <h1>LockSpot</h1>
        <p class="subtitle">Smart Locker Rental System</p>
        
        <a href="https://github.com/Hambozo17/LockSpot/releases/download/v1.0.0/app-release.apk" 
           class="download-btn">
            📱 Download APK
        </a>
        
        <div class="features">
            <div class="feature">
                <div class="feature-icon">📍</div>
                <span>Find lockers near you</span>
            </div>
            <div class="feature">
                <div class="feature-icon">🔓</div>
                <span>Easy QR code unlock</span>
            </div>
            <div class="feature">
                <div class="feature-icon">💳</div>
                <span>Secure payments</span>
            </div>
            <div class="feature">
                <div class="feature-icon">📊</div>
                <span>Track your rentals</span>
            </div>
        </div>
        
        <div class="install-note">
            <strong>Installation:</strong> After downloading, open the APK file. 
            You may need to enable "Install from Unknown Sources" in your phone settings.
        </div>
        
        <p class="version">Version 1.0.0 | Android</p>
    </div>
</body>
</html>'''
    return HttpResponse(html, content_type='text/html')


urlpatterns = [
    # Root endpoint
    path('', root_view, name='root'),
    
    # Download page for QR code
    path('download/', download_page, name='download'),
    
    # Admin Dashboard
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/', include('api.urls')),
    
    # API Documentation (DRF browsable API)
    path('api-auth/', include('rest_framework.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

