# Privacy Policy

This plugin sends the workflow input text to the vLLM System One URL configured by the Dify workspace administrator. The plugin does not transmit text to an additional external service by design. Network traffic, request logging, and model retention are controlled by the operator of the configured vLLM endpoint and the Dify installation.

No authentication tokens are intentionally written to tool output. Administrators must secure their plugin-runtime network, model API and credentials. The tool does not intentionally store input prompts or output decisions outside the hosting Dify environment.
