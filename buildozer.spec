[app]

title = انتخاب رشته آفلاین

package.name = entekhabreshteh
package.domain = org.fibiland

source.dir = .
source.include_exts = py,db,png,jpg,jpeg,kv,json,ttf

version = 1.1.0

requirements = python3==3.13.7,hostpython3==3.13.7,kivy,arabic-reshaper,python-bidi==0.4.2

orientation = landscape
fullscreen = 0

android.api = 35
android.minapi = 29
android.ndk = 27c
android.archs = arm64-v8a
android.accept_sdk_license = True

[buildozer]

log_level = 2
warn_on_root = 1
