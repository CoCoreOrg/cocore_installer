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
        'requests == 2.24.0',
        'requests-unixsocket>=0.2.0',
        'six>=1.15.0',
        'urllib3',
        'cryptography',
        'websockets',
        'tornado',
    ],
    entry_points={
        'console_scripts': [
            'cocore-install=cocore_installer.install:main',
            'cocore-store-auth-key=cocore_installer.store_auth_key:main',
            'cocore-setup-firecracker=cocore_installer.setup_firecracker:main',
            'cocore-task-server=cocore_installer.task_server:start_server',
        ],
    },
)
