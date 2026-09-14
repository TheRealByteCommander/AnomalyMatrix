import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { isHeatmapDisplayPath, normalizePath, wantsFullscreen } from './displayRoute.js';

describe('heatmap display route', () => {
  it('treats /heatmap and /display/heatmap as the operator display', () => {
    assert.equal(isHeatmapDisplayPath('/heatmap'), true);
    assert.equal(isHeatmapDisplayPath('/heatmap/'), true);
    assert.equal(isHeatmapDisplayPath('/display/heatmap'), true);
    assert.equal(isHeatmapDisplayPath('/display/heatmap/'), true);
  });

  it('does not treat the main HMI as a display route', () => {
    assert.equal(isHeatmapDisplayPath('/'), false);
    assert.equal(isHeatmapDisplayPath('/configuration'), false);
    assert.equal(normalizePath(''), '/');
  });

  it('reads fullscreen from query params', () => {
    assert.equal(wantsFullscreen(''), false);
    assert.equal(wantsFullscreen('?foo=1'), false);
    assert.equal(wantsFullscreen('?fullscreen=1'), true);
    assert.equal(wantsFullscreen('?fullscreen=true'), true);
    assert.equal(wantsFullscreen('?fullscreen'), true);
    assert.equal(wantsFullscreen('?fs=1'), true);
    assert.equal(wantsFullscreen('?fullscreen=0'), false);
  });
});
