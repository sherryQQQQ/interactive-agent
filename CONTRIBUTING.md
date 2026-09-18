# Contributing

Install `pip install -e '.[dev,retrieval]'`, then run `python -m pytest` and the README
demo. Tests use injected fake providers, never API keys or paid calls.

New experiments need a question, frozen selection, explicit execution modes,
budget/checkpoint policy, paired evaluation and failure-path tests. Version
protocol-changing fixes; never reuse incompatible checkpoints.

Do not commit secrets, external corpora, patient information, raw model outputs,
interview notes or run folders. Label synthetic fixtures and link numerical
claims to their protocol and denominator.
