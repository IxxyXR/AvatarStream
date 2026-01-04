import pytest
from unittest.mock import MagicMock, patch
import os
import sys
import json

# Adjust path to import generate_avatar
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from generate_avatar import AvatarGenerator

def test_create_dummy_gltf(tmp_path):
    output_path = tmp_path / "test.gltf"
    generator = AvatarGenerator("dummy_input.jpg", str(output_path))

    generator.create_dummy_gltf()

    assert output_path.exists()

    with open(output_path, 'r') as f:
        data = json.load(f)
        assert data['asset']['version'] == "2.0"
        assert len(data['meshes']) > 0

def test_progress_reporting(capsys):
    generator = AvatarGenerator("dummy_input.jpg", "dummy.gltf")

    generator.write_progress(50)

    captured = capsys.readouterr()
    assert "PROGRESS: 50" in captured.out

def test_log_step(capsys):
    generator = AvatarGenerator("dummy_input.jpg", "dummy.gltf")

    generator.log_step("Test Step")

    captured = capsys.readouterr()
    assert "Running step: Test Step" in captured.err

def test_run_flow(tmp_path):
    output_path = tmp_path / "output.gltf"
    generator = AvatarGenerator("dummy_input.jpg", str(output_path))

    # Mock time.sleep to speed up test
    with patch('time.sleep'):
        generator.run()

    assert output_path.exists()
