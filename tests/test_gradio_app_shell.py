def test_build_app_imports():
    from app.main import build_app

    assert callable(build_app)
