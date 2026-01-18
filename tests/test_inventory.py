"""Tests for the Repository Inventory."""

import pytest
import tempfile
from pathlib import Path

from codetruth.core.inventory import RepoInventory


@pytest.fixture
def sample_repo():
    """Create a sample repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)

        # Create package.json
        (repo_path / "package.json").write_text('{"name": "test", "dependencies": {"react": "^18.0.0"}}')

        # Create TypeScript files
        (repo_path / "src").mkdir()
        (repo_path / "src" / "index.ts").write_text('''
export const hello = () => console.log("hello");
export default function main() {}
''')

        # Create React component
        (repo_path / "src" / "App.tsx").write_text('''
import React from 'react';

export const App: React.FC = () => {
    const handleClick = () => {};
    return <button onClick={handleClick}>Click</button>;
};
''')

        # Create API route file
        (repo_path / "src" / "api.ts").write_text('''
import express from 'express';
const app = express();
app.get('/users', (req, res) => res.json([]));
app.post('/users', (req, res) => res.json({}));
''')

        yield repo_path


@pytest.mark.asyncio
async def test_detect_languages(sample_repo):
    """Test language detection."""
    inventory = RepoInventory(sample_repo)
    result = await inventory.generate(include_ast=False)

    assert "typescript" in result["languages"]


@pytest.mark.asyncio
async def test_find_api_routes(sample_repo):
    """Test API route detection."""
    inventory = RepoInventory(sample_repo)
    result = await inventory.generate(include_ast=False)

    routes = result["api_routes"]
    assert len(routes) >= 2

    methods = [r["method"] for r in routes]
    assert "GET" in methods
    assert "POST" in methods


@pytest.mark.asyncio
async def test_find_ui_components(sample_repo):
    """Test UI component detection."""
    inventory = RepoInventory(sample_repo)
    result = await inventory.generate(include_ast=False)

    components = result["ui_components"]
    assert len(components) >= 1

    names = [c["name"] for c in components]
    assert "App" in names
