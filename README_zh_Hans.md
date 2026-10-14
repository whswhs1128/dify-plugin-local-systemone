# Dify 本地 System One 插件 v0.0.3（修复节点输入框）

按照已有的 OpenAPI 自定义工具，**model / state / questions 三个字段全部保留为工作流节点必填输入**，不再把模型 ID 放在插件配置页。

## 配置

插件配置页只填写 `base_url`（例：`http://10.10.10.159:8000`）和可选 `api_key`。不得在公开发布包里写死私人地址。

节点 `Classify Intent` 的三个可见必填输入（YAML 使用 `form: form`）：

- `model`（String，必填）：填写 `GET /v1/models` 返回的 `id`，不是自己猜的模型名。
- `state`（String，必填）：绑定 Dify 开始节点 `sys.query`。
- `questions`（String，必填）：将下述完整 **JSON 对象**粘贴到该字段中；可用工作流变量动态指定。

```json
{
  "route": {
    "type": "choice",
    "instructions": "根据用户的问题，选择最合适的处理流程。",
    "criteria": {
      "knowledge_base": "需要查询内部知识库、企业制度及上传资料",
      "web_search": "需要联网查询实时数据、新闻和公开资料",
      "none": "普通闲聊、文本创作、编程及一般知识问答"
    }
  }
}
```

这是 JSON 字符串，不是 Python dict，也不需要嵌套 `model` 和 `state`。JSON 中布尔值写 `true/false`（若需要）。

## 输出变量

`route`（分类标签）、`probability`（相对概率）、`probabilities`（各标签概率）、`answers`（完整决策结果）、`diagnostics`（诊断信息）。

IF/ELSE 的三个条件分别使用 `route 等于 knowledge_base`、`route 等于 web_search`、`route 等于 none`。

## 打包

```bash
cd ~/dify-plugins
./dify-plugin-linux-amd64 plugin package ./local-systemone-v0.0.3 -o local_systemone-0.0.3.difypkg
```

使用正式 `dify-plugin-linux-amd64`，不要使用 slim 版本。

安装升级版后，**删除工作流里的旧插件节点并重新添加新版节点**，将三个参数重新绑定。原来的 `query` 参数已经移除，所以旧节点的参数不会自动匹配。

这是插件源码模板，已完成 Python/YAML 静态检查，仍需要你在 Dify 环境中测试实际运行。

## v0.0.3 修复说明

原版 v0.0.2 的 `form: llm` 参数在部分 Dify 版本的工具节点配置中不会显示输入框。新版把 `model`、`state`、`questions` 全部改成 `form: form`，并增加输入提示。Python 的 System One 调用及输出行为不变。

升级插件后，在工作流中删除旧节点，从新版本重新添加工具节点，以刷新参数元数据；确保 IF/ELSE 分支连接到新节点。
