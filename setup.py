from setuptools import setup, find_packages

setup(
    name="enterprise-aws-observability-constructs",  # Unique, descriptive name
    version="1.0.0",
    description="Enterprise-grade CDK constructs for AWS observability platform",
    author="Your Company Platform Team",
    author_email="platform-team@yourcompany.com",
    url="https://github.com/yourcompany/aws-observability-platform",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "aws-cdk-lib>=2.100.0",
        "constructs>=10.0.0"
    ],
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.9",
        "Topic :: System :: Monitoring",
    ]
)