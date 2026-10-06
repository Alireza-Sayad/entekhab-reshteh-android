[app]
title = انتخاب رشته آفلاین
package.name = entekhabreshteh
package.domain = org.fibiland
source.dir = .
source.include_exts = py,db,png,jpg,kv,json
version = 1.0.0
requirements = python3,kivy,fpdf2
orientation = landscape
fullscreen = 0

# Android
android.api = 35
android.minapi = 23
android.ndk = 27c
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.permissions = READ_MEDIA_IMAGES

# Build settings
[buildozer]
log_level = 2
warn_on_root = 1
