import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('script', ['export-brand-assets.py', 'export-logo-package.py'])
def test_favicon_sizes_and_ico(tmp_path, script):
    Image = pytest.importorskip('PIL.Image')
    path = ROOT / '.agents/skills/brand-asset-producer/scripts' / script
    spec = importlib.util.spec_from_file_location('favicon_export', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    sizes = getattr(module, 'PNG_SIZES', getattr(module, 'SMALL_SIZES', []))
    assert {16, 32, 48, 180, 192, 512}.issubset(sizes)
    for size in [16, 32, 48]:
        Image.new('RGBA', (size,size), 'blue').save(tmp_path/f'mark-{size}.png')
    if script == 'export-brand-assets.py':
        result = module.build_ico(tmp_path, 'mark')
    else:
        result = module.build_ico(tmp_path/'mark.svg', tmp_path, 'mark')
    assert result
    with Image.open(tmp_path/'mark.ico') as ico:
        assert {(16,16),(32,32),(48,48)}.issubset(ico.ico.sizes())
