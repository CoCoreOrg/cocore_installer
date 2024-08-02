from setuptools import setup, find_packages

setup(
    name='cocore_installer',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'cocore_installer': ['firecracker_config.json'],
    },
    install_requires=[
        'requests',
        'cryptography',
        'websockets',
    ],
    entry_points={
        'console_scripts': [
            'cocore-install=cocore_installer.install:main',
            'cocore-store-auth-key=cocore_installer.store_auth_key:main',
            'cocore-setup-firecracker=cocore_installer.setup_firecracker:main',
        ],
    },
)
