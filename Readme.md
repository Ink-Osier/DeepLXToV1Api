## 用法

仓库内已包含相关文件和目录，拉到本地后修改 docker-compose.yml 文件里的环境变量后运行`docker-compose up -d`即可。

模型名说明：

- 示例：
    - `deeplx-EN-ZH`: 英文转中文
    - `deeplx-ZH-EN`: 中文转英文
    - `deeplx-EN`: 自动识别语言转英文
    - `deeplx-ZH`: 自动识别语言转中文

## 调用示例：

```json
{
    "messages": [
        {
            "role": "user",
            "content": [
                "Hi"
            ]
        }
    ],
    "stream": true,
    "model": "deeplx-ZH"
}
```

预期响应：

```json
data: {"id": "a0e35ab6-b859-441b-93e6-6391dcb468ed", "object": "chat.completion.chunk", "created": 1709348239.833917, "model": "deeplx-ZH", "choices": [{"index": 0, "delta": {"content": "\u4f60\u597d"}, "finish_reason": null}]}

data: [DONE]


```

## 效果展示:

![image](https://github.com/Ink-Osier/DeepLXToV1Api/assets/133617214/12c60ed1-538b-4a24-8b4d-999e54f8dabd)
