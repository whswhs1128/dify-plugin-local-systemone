# Local System One for Dify — node inputs edition (v0.0.3)

Tool plugin wrapping a self-hosted vLLM `/v1/systemone` endpoint. **All three decision arguments are required tool-node inputs**, matching an existing Dify OpenAPI custom tool.

## Configuration

Provider settings: `base_url` (without `/v1/systemone`) and optional `api_key`. **No model ID in provider settings.**

Tool node `Classify Intent` required **String** inputs:

| Input | Example | Purpose |
|---|---|---|
| `model` | value of `data[0].id` from `GET /v1/models` | exact vLLM model ID |
| `state` | bind to `START / sys.query` | text to decide |
| `questions` | see JSON below | full System One questions object as a JSON **string**, without outer `model`/`state` |

Paste the following into `questions` (standard JSON; **double quotes** are required):

```json
{
  "route": {
    "type": "choice",
    "instructions": "判断用户主要意图，只选择最合适的处理流程。",
    "criteria": {
      "knowledge_base": "查询企业内部知识库、内部制度、私有文档或上传资料",
      "web_search": "联网获取最新新闻、实时价格、政策或外部信息",
      "none": "普通闲聊、创作、编程、翻译和一般知识问答"
    }
  }
}
```

### Tool outputs

- `route` — `answers.route.choice` when `route` is asked. Connect IF/ELSE using exact matches `knowledge_base` / `web_search` / `none`.
- `probability`, `probabilities` — relative model probabilities if present, not calibrated accuracy.
- `answers` — **complete** response answers. Supports different question keys and types.
- `diagnostics` — diagnostic fields when returned by vLLM.

For non-route questions, `route` is empty but the answers are still available.

## Packaging

Download a full `dify-plugin-linux-amd64` CLI (not `dify-plugin-slim-linux-amd64`) from https://github.com/langgenius/dify-plugin-daemon/releases.

From the project parent directory:

```bash
./dify-plugin-linux-amd64 plugin package ./local-systemone-v0.0.3 -o local_systemone-0.0.2.difypkg
```

Set the `author` in `manifest.yaml`, `provider/local_systemone.yaml`, `tools/classify_intent.yaml` before publishing. As this has a new version number (`0.0.2`), install/update in Dify and **reselect the new tool inputs in the workflow**. Do not assume old node bindings migrate automatically.

## Notes

- The plugin runtime must reach the configured vLLM host. `127.0.0.1` from the plugin usually does not refer to your vLLM container.
- The backend must support the selected model on `/v1/systemone`. Registration of the route alone is not enough.
- This is a source template. Python syntax and YAML structure have been checked; live Dify SDK packaging and remote inference must be tested in your environment.
- `questions` is a JSON string and accepts arbitrary named decision questions, provided each question has a `type`.
- Outbound connections are confined by the endpoint configured by the workspace operator. Administrators should protect private addresses and review SSRF exposure before public Marketplace publication.

## v0.0.3: Dify parameter visibility fix

Changed `model`, `state`, and `questions` from `form: llm` to `form: form`, for visible workflow-node inputs in Dify versions where `llm` form parameters do not appear in the tool configuration. The API invocation logic has not changed. Re-add the tool node to reload its parameter schema.
# dify-plugin-local-systemone
