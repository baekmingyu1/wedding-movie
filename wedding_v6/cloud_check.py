from pathlib import Path
import json,hashlib,sys
B=Path(__file__).resolve().parent
manifest=json.loads((B/'manifest.json').read_text(encoding='utf-8'))
for item in manifest:
    p=B/item['path']
    assert p.is_file(),str(p)
    assert p.stat().st_size==item['bytes'],str(p)
    assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],str(p)
media=json.loads((B/'video_work/media.json').read_text(encoding='utf-8'))
assert len(media)==46 and all((B/m['path']).exists() for m in media)
import make_reference_v6 as v
assert sum(s['frames'] for s in v.SCENES)==7410
assert len(v.SCENES)==37
assert Path(v.m.AUDIO).exists()
for kind in ['hand','bold','serif','italic','script','sans']:v.font(40,kind)
for kind in ['ko','en','sans']:v.m.font(30,kind)
print(json.dumps({'files_verified':len(manifest),'media':len(media),'scenes':37,'seconds':247,'fonts':'loaded','ffmpeg':v.m.FF},ensure_ascii=False))
