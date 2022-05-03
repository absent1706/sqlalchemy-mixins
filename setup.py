from setuptools import setup

"""
0. python3 -m pip install --user --upgrade twine

1. python3 setup.py sdist bdist_wheel
2. python3 -m twine upload dist/*

see https://packaging.python.org/tutorials/packaging-projects/
"""

def requirements():
    import os
    filename = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    return [line.rstrip('\n') for line in open(filename).readlines()]

setup(name='sqlalchemy_mixins',
      version='1.5.3',
      description='Active Record, Django-like queries, nested eager load '
                  'and beauty __repr__ for SQLAlchemy',
      url='https://github.com/absent1706/sqlalchemy-mixins',
      download_url='https://github.com/absent1706/sqlalchemy-mixins/archive/master.tar.gz',
      author='Alexander Litvinenko',
      author_email='litvinenko1706@gmail.com',
      license='MIT',
      packages=['sqlalchemy_mixins'],
      package_data={'sqlalchemy_mixins': ['py.typed', '*.pyi', '**/*.pyi']},
      zip_safe=False,
      include_package_data=True,
      install_requires=[
          "SQLAlchemy >= 1.0",
          "six",
          "typing; python_version < '3.5'"
      ],
      keywords=['sqlalchemy', 'active record', 'activerecord', 'orm',
                'django-like', 'django', 'eager load', 'eagerload',  'repr',
                '__repr__', 'mysql', 'postgresql', 'pymysql', 'sqlite'],
      platforms='any',
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Web Environment',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
          'Programming Language :: Python :: Implementation :: CPython',
          'Topic :: Database',
      ],
      test_suite='nose.collector',
      tests_require=['nose', 'nose-cover'],
  )
