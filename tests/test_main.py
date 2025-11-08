import importlib.util
import sys
from fastapi.testclient import TestClient

# Load main.py as a module regardless of sys.path
spec = importlib.util.spec_from_file_location("main", "./main.py")
main = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = main
spec.loader.exec_module(main)

client = TestClient(main.app)

def test_root():
    r = client.get('/')
    assert r.status_code == 200
    data = r.json()
    assert data.get('status') == 'healthy'

def test_health():
    r = client.get('/health')
    assert r.status_code == 200
    data = r.json()
    assert data.get('service') == 'ai-ml'
