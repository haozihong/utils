#!/usr/bin/env python3
import os, sys
import piexif
import time
from PIL import Image

exif_time_fmt = '%Y:%m:%d %H:%M:%S'
exif_time_key = 'EXIF DateTimeDigitized'
subifd_time_key = piexif.ExifIFD.DateTimeDigitized
ifd0_time_key = piexif.ImageIFD.DateTime

dir_in=''
try: dir_in = sys.argv[1]
except: pass

for root, dirs, files in os.walk(dir_in):
    for fname in files:
        fpath = os.path.join(root, fname)
        froot, fext = os.path.splitext(fpath)
        if fext not in {'.jpg'}: continue
        print(fpath)
        with Image.open(fpath) as im:
            if 'exif' not in im.info: continue
            exif_dict = piexif.load(im.info["exif"])

            if subifd_time_key not in exif_dict['Exif']: continue
            subifd_time_b = exif_dict['Exif'][subifd_time_key]
            subifd_time_str = subifd_time_b.decode()
            subifd_time_sec = time.mktime(time.strptime(subifd_time_str, exif_time_fmt))

            if ifd0_time_key in exif_dict['0th']:
                ifd0_time_str = exif_dict['0th'][ifd0_time_key].decode()
                ifd0_time_sec = time.mktime(time.strptime(ifd0_time_str, exif_time_fmt))
                if abs(subifd_time_sec - ifd0_time_sec) > 60: 
                    # print('ifd0 diff -', ifd0_time_str, subifd_time_str)
                    exif_dict['0th'][piexif.ImageIFD.DateTime] = subifd_time_b
                    try:
                        # See bug https://github.com/hMatoba/Piexif/issues/95
                        exif_bytes = piexif.dump(exif_dict)
                    except:
                        del exif_dict['Exif'][piexif.ExifIFD.SceneType]
                        exif_bytes = piexif.dump(exif_dict)

                    im.save(fpath, "jpeg", exif=exif_bytes)

            f_mtime_sec = os.stat(fpath).st_mtime
            if abs(f_mtime_sec - subifd_time_sec) > 60: 
                # print('mtime -', time.strftime(exif_time_fmt, time.gmtime(f_mtime_sec)), exif_time_str)
                os.utime(fpath, (subifd_time_sec, subifd_time_sec))
