# Xiaodu MCP Home Assistant Custom Integration v2 Fixed

适配 xiaodu-token-proxy v2/v2-fixed 标准 API：

- `GET /api/devices`
- `POST /api/speak`
- `POST /api/command`
- `POST /api/take_photo`

并适配真实设备字段：

- `client_id`
- `cuid`
- `device_name`
- `online_status` / `online`
- `location.house` / `location.floor` / `location.room`

不再传 `userid`。

## 通过 HACS 安装

1. 打开 HACS。
2. 进入右上角菜单，选择 `Custom repositories`。
3. Repository 填入：`https://github.com/linzhonghong/xiaodu_mcp_ha`
4. Category 选择：`Integration`
5. 添加后搜索 `Xiaodu MCP` 并安装。
6. 重启 Home Assistant。
7. 进入 `Settings → Devices & services → Add Integration → Xiaodu MCP`

填写 token-proxy 根地址，例如：

```text
http://192.168.1.20:8088
```

不要填 `/sse`，不要填 `/mcp/`。

## 安装

把 `custom_components/xiaodu_mcp` 复制到 Home Assistant：

```text
/config/custom_components/xiaodu_mcp
```

重启 Home Assistant，然后：

```text
Settings → Devices & services → Add Integration → Xiaodu MCP
```

填写 token-proxy 根地址，例如：

```text
http://192.168.1.20:8088
```

不要填 `/sse`，不要填 `/mcp/`。

## 自动化示例

### 通过服务播报

```yaml
action:
  - action: xiaodu_mcp.speak
    target:
      device_id: 你的_xiaodu_设备_id
    data:
      text: "门口有人按门铃，请注意查看。"
```

### 通过 text 实体播报

```yaml
action:
  - action: text.set_value
    target:
      entity_id: text.xxx_bo_bao_wen_ben
    data:
      value: "门口有人按门铃，请注意查看。"
```

### 拍照

```yaml
action:
  - action: button.press
    target:
      entity_id: button.xxx_pai_zhao
```

或者：

```yaml
action:
  - action: xiaodu_mcp.take_photo
    target:
      device_id: 你的_xiaodu_设备_id
```

## 实体

每台设备会创建：

- 状态 sensor
- 测试播报 button
- 拍照 button
- 最近拍照 camera
- 播报文本 text
- 自然语言指令 text
