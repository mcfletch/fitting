import os

from setuptools import setup, find_packages

if __name__ == "__main__":
    setup(
        name='fitting',
        version='1.0.0',
        description='fitting',
        long_description='fitting',
        classifiers=[
            "Programming Language :: Python",
            "Framework :: Django",
            "Topic :: Internet :: WWW/HTTP",
            "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
        author='VRPlumber Consulting Inc.',
        author_email='mcfletch@vrplumber.com',
        url='http://www.github.com/mcfletch/fitting',
        keywords='django',
        packages=find_packages(),
        include_package_data=True,
        license='MIT',
        # Dev-only requirements:
        # nose
        # pychecker
        # coverage
        # globalsub
        package_data = {
            'fitting': [
                'templates/fitting/*.html',
                'static/js/*',
                'static/css/*',
                'static/img/*',
            ],
        },
        install_requires=[
            'django',
            'django-annoying',
            'south',
        ],
        scripts = [
        ],
        entry_points = dict(
            console_scripts = [
            ],
        ),
    )

