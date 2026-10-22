"""Caller-declared CAD evidence policies; no aesthetic or strength certification."""
from . import verification


def appearance(record, need):
    views = need.get('views')
    if (not isinstance(views, list) or not views or
            any(not isinstance(v, str) or not v.strip() for v in views) or len(set(views)) != len(views)):
        raise ValueError('Appearance requirement needs unique nonempty views')
    if not record.get('reviewer') or not record.get('decision_note'):
        return False
    captures = record.get('captures', [])
    if not isinstance(captures, list):
        return False
    for view in views:
        hits = [c for c in captures if isinstance(c, dict) and c.get('view') == view]
        if len(hits) != 1:
            return False
        capture = hits[0]
        try:
            if verification.file_hash(capture['path']) != capture.get('sha256'):
                return False
        except (KeyError, TypeError, OSError):
            return False
    return True


def probe_bounds(item):
    box = item['probe']
    if box.get('frame') != 'world_mm' or not box.get('source'):
        raise ValueError('Probe requires world_mm frame and source/rationale')
    if box.get('margin_mm', 0) != 0:
        raise ValueError('Solid probe does not permit implicit margins')
    low, high = box['min_mm'], box['max_mm']
    if len(low) != 3 or len(high) != 3:
        raise ValueError('Probe needs three min/max coordinates')
    size = [verification.finite(b)-verification.finite(a) for a, b in zip(low, high)]
    if min(size) <= 0:
        raise ValueError('Probe must have positive dimensions')
    limit = verification.finite(item['limits']['min_fill_fraction'], 'min_fill_fraction')
    if not 0 < limit <= 1:
        raise ValueError('min_fill_fraction must be >0 and <=1')
    volume = verification.finite(size[0]*size[1]*size[2], 'probe volume')
    if volume <= 0:
        raise ValueError('Probe volume must be positive')
    return volume, limit
