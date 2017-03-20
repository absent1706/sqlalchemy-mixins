from setuptools import setup

"""
1. set "HOME=E:/code/sqlalchemy-mixins"
2. python setup.py sdist upload -r testpypi
   or
   python setup.py sdist upload -r pypi

see http://peterdowns.com/posts/first-time-with-pypi.html
"""

def requirements():
    import os
    filename = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    return [line.rstrip('\n') for line in open(filename).readlines()]

setup(name='sqlalchemy_mixins',
      version='0.1.7',
      description='Active Record, Django-like queries, nested eager load '
                  'and beauty __repr__ for SQLAlchemy',
      url='https://github.com/absent1706/sqlalchemy-mixins',
      download_url = 'https://github.com/absent1706/sqlalchemy-mixins/archive/master.tar.gz',
      author='Alexander Litvinenko',
      author_email='litvinenko1706@gmail.com',
      license='MIT',
      packages=['sqlalchemy_mixins'],
      zip_safe=False,
      include_package_data=True,
      install_requires=[
          "SQLAlchemy >= 1.0",
          "six",
          "typing"
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
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: Implementation :: CPython',
          'Topic :: Database',
      ],
      test_suite='nose.collector',
      tests_require=['nose', 'nose-cover'],
  )