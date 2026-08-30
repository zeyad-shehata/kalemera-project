import urllib.request
import json
import io
import sys
import os
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.storage_service import storage_service

def run_test():
    print("=== KALMERA E2E Storage & Upload Verification ===")

    # 1. Login as Admin
    login_data = json.dumps({'phone': '01000000001', 'password': 'admin123'}).encode('utf-8')
    req = urllib.request.Request(
        'http://127.0.0.1:8002/api/auth/login',
        data=login_data,
        headers={'Content-Type': 'application/json'}
    )
    resp = urllib.request.urlopen(req)
    cookie = resp.headers.get('Set-Cookie').split(';')[0]
    print("[1/5] Admin logged in successfully.")

    # 2. Check storage overview
    req_storage = urllib.request.Request(
        'http://127.0.0.1:8002/api/storage/overview',
        headers={'Cookie': cookie}
    )
    storage_info = json.loads(urllib.request.urlopen(req_storage).read())
    print(f"[2/5] Storage Overview: {storage_info['total_app_mb']} MB used ({storage_info['usage_percent']}% of 5GB)")

    # 3. Create high-res 2000x2000 image in memory
    raw_img = Image.new('RGB', (2000, 2000), color=(180, 100, 50))
    img_io = io.BytesIO()
    raw_img.save(img_io, format='JPEG', quality=95)
    img_bytes = img_io.getvalue()
    print(f"[3/5] Generated large test photo: {len(img_bytes) / 1024:.1f} KB (2000x2000 px)")

    # 4. Multipart upload
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    body = bytearray()

    def add_field(name, value):
        body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode('utf-8'))

    add_field('name', 'وجبة برجر سبيشال تيست')
    add_field('name_en', 'Special Burger Meal Test')
    add_field('category_id', '1')
    add_field('price', '125.0')
    add_field('stock', '50')
    add_field('description', 'وجبة برجر مميزة')
    add_field('description_en', 'Special burger meal with fries')

    body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="burger_large.jpg"\r\nContent-Type: image/jpeg\r\n\r\n'.encode('utf-8'))
    body.extend(img_bytes)
    body.extend(f'\r\n--{boundary}--\r\n'.encode('utf-8'))

    req_upload = urllib.request.Request(
        'http://127.0.0.1:8002/api/products/',
        data=body,
        headers={
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'Cookie': cookie
        }
    )
    upload_resp = json.loads(urllib.request.urlopen(req_upload).read())
    prod_id = upload_resp['id']
    image_url = upload_resp['image_path']
    print(f"[4/5] Product created (ID: {prod_id}) with image path: {image_url}")

    # 5. Verify physical WebP optimization
    saved_path = storage_service.resolve_physical_path(image_url)
    assert saved_path is not None, "Saved file could not be resolved"
    assert saved_path.exists(), "Saved file does not exist on disk"
    assert saved_path.suffix == ".webp", f"Expected .webp extension, got {saved_path.suffix}"
    
    optimized_size = saved_path.stat().st_size
    print(f"[5/5] Optimized WebP size on disk: {optimized_size / 1024:.1f} KB (Compressed by {((len(img_bytes) - optimized_size) / len(img_bytes))*100:.1f}%)")

    # Clean up test product
    req_del = urllib.request.Request(
        f'http://127.0.0.1:8002/api/products/{prod_id}',
        headers={'Cookie': cookie},
        method='DELETE'
    )
    urllib.request.urlopen(req_del)
    print("[CLEANUP] Test product and image deleted cleanly.")
    print("=== ALL RE-ARCHITECTURE & STORAGE TESTS PASSED SUCCESSFULLY! ===")

if __name__ == '__main__':
    run_test()
