# LocalModel Create Command

Use `local-ai create` to validate and install a `LocalModel.yaml` package file.

```bash
local-ai create -f LocalModel.yaml
```

This installs the package under:

```text
data/models/<name>/LocalModel.yaml
```

To set the package as the active model preset after installing it:

```bash
local-ai create -f LocalModel.yaml --activate
```

After creation, use the package anywhere a model name is accepted:

```bash
local-ai run --model <name> "Write a short reply"
local-ai chat --model <name>
```
