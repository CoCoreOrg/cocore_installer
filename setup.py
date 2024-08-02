from setuptools import setup, find_packages

setup(
    name="cocore_installer",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "requests",
        "cryptography",
    ],
    entry_points={
        'console_scripts': [
            'cocore-install=cocore_installer.install:main',
            'cocore-setup-firecracker=cocore_installer.setup_firecracker:main',
            'cocore-store-auth-key=cocore_installer.store_auth_key:main',
        ],
    },
)