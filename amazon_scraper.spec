# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['run_tracker.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/WebScraper', 'WebScraper'),
    ],
    hiddenimports=[
        'WebScraper.cli',
        'WebScraper.core.amazon_parsers',
        'WebScraper.core.amazon_product_scraper',
        'WebScraper.core.retry_logic',
        'WebScraper.core.utilities',
        'WebScraper.data.database_service',
        'WebScraper.data.product',
        'WebScraper.services.email_service',
        'WebScraper.services.client_metadata',
        'google.auth',
        'google.auth.transport',
        'google_auth_oauthlib',
        'googleapiclient',
        'googleapiclient.discovery',
        'bs4',
        'brotli',
        'dotenv',
        'sqlite3',
        'pickle',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AmazonPriceTracker',  # ← This determines the .exe name
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)