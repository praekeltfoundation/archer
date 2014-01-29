from setuptools import setup

setup(
    name="archer",
    version="0.1",
    url='http://github.com/praekelt/archer',
    license='BSD',
    description="Future of Content Delivery",
    long_description=open('README.rst', 'r').read(),
    author='Praekelt',
    author_email='dev@praekelt.com',
    packages=[
        "archer",
    ],
    package_data={},
    include_package_data=True,
    install_requires=[
        'Twisted',
        'aludel',
        'treq',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Networking',
        'Framework :: Twisted',
    ],
)
